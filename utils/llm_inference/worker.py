"""Initialize inference workers and process prompted extraction jobs."""

import os
import random
import sys
import time

import httpx
from dotenv import load_dotenv
from openai import Client

from .server import call_llm


CALL_LLM_ARGS = {'sampling_kwargs': {'max_tokens': 32768, "extra_body": {"reasoning_effort": "medium", "top_k": 0, "top_p": 1.0 }}, "temperature": 1.0, 'verbose': False}
REQUEST_PER_SECOND_UNTIL_NB_WORKERS_HAVE_BUILDUP = 50
OTHER_ERROR_MAX_ATTEMPTS = 5
API_ERROR_MAX_ATTEMPTS = 100
API_ERROR_BASE_WAIT_TIME = 60


# Global variables inside worker process
client_global = None
llm_name_global = None
worker_has_already_sent_requests = False
nb_workers_global = 1
dotenv_path_global = None

def init_worker(llm_name, base_url, api_key, dotenv_path, nb_workers):
    """
    Initialize the client and worker-wide state.
    """
    global client_global, llm_name_global, worker_has_already_sent_requests, nb_workers_global, dotenv_path_global
    llm_name_global = llm_name
    nb_workers_global = nb_workers
    dotenv_path_global = dotenv_path
    worker_has_already_sent_requests = False # Reset for this process
    
    max_init_attempts = 5
    init_attempt = 0

    while client_global is None and init_attempt < max_init_attempts:
        init_attempt += 1
        try:
            timeout_seconds = CALL_LLM_ARGS.get('sampling_kwargs', {}).get('timeout', 86400)
            long_timeout_client = httpx.Client(timeout=timeout_seconds)
            
            client_global = Client(
                base_url=base_url,
                api_key=api_key,
                timeout=timeout_seconds,
                http_client=long_timeout_client
            )
        except Exception as e:
            if init_attempt < max_init_attempts:
                time.sleep(random.uniform(5, 15))
            else:
                print(f"FATAL ERROR during worker initialization: {e}", file=sys.stderr)
                client_global = None

def _load_dynamic_settings():
    """Loads settings from .env, using global constants as defaults."""
    if dotenv_path_global and os.path.exists(dotenv_path_global):
        load_dotenv(dotenv_path=dotenv_path_global, override=True)
    
    return {
        'req_per_sec': int(os.getenv('REQUEST_PER_SECOND_UNTIL_NB_WORKERS_HAVE_BUILDUP', REQUEST_PER_SECOND_UNTIL_NB_WORKERS_HAVE_BUILDUP)),
        'other_error_max': int(os.getenv('OTHER_ERROR_MAX_ATTEMPTS', OTHER_ERROR_MAX_ATTEMPTS)),
        'api_error_max': int(os.getenv('API_ERROR_MAX_ATTEMPTS', API_ERROR_MAX_ATTEMPTS)),
        'api_wait_time': int(os.getenv('API_ERROR_BASE_WAIT_TIME', API_ERROR_BASE_WAIT_TIME))
    }

def process_job(job_data):
    """
    Process one job with retry and warm-up logic.
    """
    global worker_has_already_sent_requests, client_global

    if client_global is None:
        return {
            'studyAnonId': job_data.get('studyAnonId'), 
            'step_name': job_data.get('step_name'),
            'status': 'error',
            'error_type': 'ClientInitializationFailed'
        }

    config_settings = _load_dynamic_settings()

    studyAnonId = job_data['studyAnonId']
    report = job_data['report']
    step_name = job_data['step_name']
    
    prompt_template = job_data['prompt_template']
    pydantic_model = job_data['pydantic_model']
    classes_to_extract = job_data['classes_to_extract']

    messages = [{"role": "user", "content": prompt_template.replace('{doctors_letter}', report)}]
    response_format = {"type": "json_schema", "json_schema": {"name": pydantic_model.__name__, "schema": pydantic_model.model_json_schema()}}

    # --- Warmup Logic ---
    # If this is the first time this worker sends a request, wait a random amount of time
    # to prevent all X workers hitting the server at exact same millisecond.
    if not worker_has_already_sent_requests:
        # Total time to ramp up = Workers / Reqs_per_sec
        # e.g. 1000 workers / 10 rps = 100 seconds ramp up
        startup_spread = nb_workers_global / max(1, config_settings['req_per_sec'])
        sleep_time = random.uniform(0, startup_spread)
        time.sleep(sleep_time)
        worker_has_already_sent_requests = True

    # --- Retry Loop ---
    successful_call = False
    attempts_api_error = 0
    attempts_other_error = 0
    call_results = {}
    
    while not successful_call and (attempts_api_error < config_settings['api_error_max']) and (attempts_other_error < config_settings['other_error_max']):
        try:
            call_results = call_llm(
                model_name=llm_name_global,
                client=client_global,
                studyAnonId=studyAnonId,
                messages=messages,
                response_format=response_format,
                pydantic_model_to_validate=pydantic_model,
                **CALL_LLM_ARGS
            )
            successful_call = call_results.get("successful_call", False)
            
            if not successful_call:
                statistics = call_results.get("statistics", {})
                error_message = statistics.get("call_error_msg", "")
                
                # Check if it is a rate limit or API connection error
                if 'APIConnectionError' in error_message or 'APIError' in error_message or 'RateLimitError' in error_message:
                    wait_base = config_settings['api_wait_time']
                    sleep_time = random.uniform(wait_base * 0.5, wait_base * 1.5)
                    time.sleep(sleep_time)
                    attempts_api_error += 1
                else:
                    attempts_other_error += 1
                    
        except Exception as e:
            attempts_other_error += 1
            call_results = {'successful_call': False, 'statistics': {'call_error_msg': f"Exception in loop: {str(e)}"}}


    # --- Post-Processing ---
    statistics = call_results.get("statistics", {})
    llm_output_dict = call_results.get("llm_output_dict")
    llm_output_reasoning = call_results.get("llm_output_reasoning")

    if not successful_call:
         return {
            'studyAnonId': studyAnonId,
            'step_name': step_name,
            'status': 'error',
            'report': report,
            'error_type': 'LLMCallFailedAfterRetries',
            'last_llm_output': call_results.get("llm_output_raw_content"),
            'statistics': statistics
        }

    try:
        extracted_values = {}
        for class_name in classes_to_extract:
            data_entry = llm_output_dict.get(class_name)
            if data_entry and isinstance(data_entry, dict):
                value = data_entry.get('Extraktion')
                extracted_values[class_name] = tuple(value) if isinstance(value, list) else value
            else:
                extracted_values[class_name] = None

        return {
            'studyAnonId': studyAnonId,
            'step_name': step_name,
            'status': 'success',
            'extracted_values': extracted_values,
            'llm_output': llm_output_dict,
            'llm_output_reasoning': llm_output_reasoning,
            'report': report,
            'statistics': statistics
        }
    except Exception as e:
        error_msg = f"ExtractionException: {e}"
        return {
            'studyAnonId': studyAnonId,
            'step_name': step_name,
            'status': 'error',
            'report': report,
            'error_type': error_msg,
            'statistics': {'call_error_msg': error_msg}
        }
