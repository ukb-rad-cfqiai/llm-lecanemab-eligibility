"""Inference server requests, validation, and response handling."""

import time, logging, traceback, json, random
from typing import List, Dict, Optional, Type, Any, Callable
from openai import APIConnectionError, APIError, Client 
from pydantic import ValidationError, BaseModel

script_name = 'llm_server'


# --- CUSTOM EXCEPTION CLASSES ---
class PostProcessingError(Exception):
    """Raised when the user-provided postprocessing function fails."""
    pass

class CustomValidationError(Exception):
    """Raised when the user-provided custom validation function returns errors."""
    pass


# --- LLM calling function ---
def call_llm(
    model_name: str,
    client: Client, 
    studyAnonId: str, 
    messages: List[Dict[str, str]], 
    verbose: bool = True, 
    response_format: Optional[Dict] = None, 
    sampling_kwargs: Optional[Dict] = None, 
    pydantic_model_to_validate: Optional[Type[BaseModel]] = None, 
    custom_model_validate_function: Optional[Callable[[Any], List[str]]] = None, 
    postprocessing_function: Optional[Callable[[Any], Any]] = None,
) -> Dict[str, Any]:
    """
    Executes a robust LLM inference call with built-in error handling, JSON parsing, 
    Pydantic validation, post-processing, and detailed statistics gathering.
    """
    if client is None:
        raise ValueError("A valid OpenAI client instance must be provided.")

    active_sampling_kwargs = {} if sampling_kwargs is None else sampling_kwargs.copy()
    
    # Ensure timeout if not present (fallback)
    if 'timeout' not in active_sampling_kwargs:
        active_sampling_kwargs['timeout'] = 86400

    active_sampling_kwargs['stream'] = False

    if response_format is not None:
        active_sampling_kwargs['response_format'] = response_format
    
    llm_output_raw_content = None
    llm_output_dict = None
    llm_output_raw_reasoning = None
    successful_call = False
    structured_pydantic_obj = None
    
    # Initialize llm_source default
    llm_source = "N/A"
  
    statistics = {
        "call_error_msg": None,
        "llm_source": "N/A",
        "num_input_tokens": 0,
        "num_output_tokens": 0,
        "num_reason_tokens": 0,
        "output_tokens_per_sec": 0.0,
        "end_to_end_latency": 0.0
    }
    
    time.sleep(random.uniform(0, 1))
    start_time_for_latency = time.time()

    call_error_msg = None
    processing_error = False
    
    try:

        start_time = time.time()
        
        # --- API Call ---
        api_response = client.chat.completions.with_raw_response.create(
            model=model_name,
            messages=messages,
            **active_sampling_kwargs
        )
        
        response = api_response.parse() 
        headers = api_response.headers
        
        llm_source = headers.get("X-LLM-Source", "Source-Header-Missing")
        statistics["llm_source"] = llm_source

        if response is None:
            # --- ENHANCED DEBUGGING: BODY + KWARGS ---
            try:
                raw_body = api_response.text
            except Exception as e_read:
                raw_body = f"<Could not read raw body: {e_read}>"

            status_code = getattr(api_response, 'status_code', 'Unknown')
            
            debug_msg = (
                f"The server returned an empty or unparsable response body. "
                f"HTTP {status_code}. Raw Body Preview: {str(raw_body)[:1000]}. "
            )
            
            if verbose: 
                logging.error(f"CRITICAL API ERROR [{studyAnonId}]: {debug_msg}")
                logging.error(f"DEBUG: Active Sampling Kwargs used: {json.dumps(active_sampling_kwargs, default=str)}")

            # Raise APIError with the detailed message
            raise APIError(
                message=debug_msg, 
                request=getattr(api_response, 'http_request', None), 
                body=None
            )

        
        # --- Statistics ---
        if response.usage:
            statistics["num_input_tokens"] = response.usage.prompt_tokens
            statistics["num_output_tokens"] = response.usage.completion_tokens
        
        llm_output_raw_reasoning = getattr(response.choices[0].message, 'reasoning_content', None)
        if llm_output_raw_reasoning and isinstance(llm_output_raw_reasoning, str):
            llm_output_raw_reasoning = remove_surrogates(llm_output_raw_reasoning)
            statistics["num_reason_tokens"] = len(llm_output_raw_reasoning)

        llm_output_raw_content = response.choices[0].message.content
        if isinstance(llm_output_raw_content, str):
            llm_output_raw_content = remove_surrogates(llm_output_raw_content)


        # --- Parsing & Validation ---
        if response_format:
            try:
                # 1. JSON Parsing
                if isinstance(llm_output_raw_content, dict):
                    llm_output_dict = llm_output_raw_content
                elif isinstance(llm_output_raw_content, str):
                    start_brace = llm_output_raw_content.find('{')
                    if start_brace != -1:
                        llm_output_raw_content_trimmed = llm_output_raw_content[start_brace:]
                        num_opening = llm_output_raw_content_trimmed.count('{')
                        num_closing = llm_output_raw_content_trimmed.count('}')
                        if num_opening > num_closing:
                            llm_output_raw_content_trimmed += '}' * (num_opening - num_closing)
                        llm_output_dict = json.loads(llm_output_raw_content_trimmed)
                    else:
                        if verbose: logging.error(f"studyAnonId: {studyAnonId} ... No JSON object found in the output")
                        raise json.JSONDecodeError("No JSON object found in the output.", llm_output_raw_content, 0)
                else:
                    if verbose: logging.error(f"studyAnonId: {studyAnonId} ...Unexpected response content type: {type(llm_output_raw_content)}")
                    raise TypeError(f"Unexpected response content type: {type(llm_output_raw_content)}")

                if pydantic_model_to_validate and llm_output_dict:
                    # 2. Pydantic Parsing
                    structured_pydantic_obj = pydantic_model_to_validate.model_validate(llm_output_dict)
                    
                    # 3. Post-Processing
                    if postprocessing_function:
                        try:
                            structured_pydantic_obj = postprocessing_function(structured_pydantic_obj)
                            # Sync the dict back with the object for consistency
                            llm_output_dict = structured_pydantic_obj.model_dump(mode='json', by_alias=True)
                        except Exception as pe:
                            if verbose:
                                logging.error(f"FATAL: Post-processing crashed for {studyAnonId}.")
                                logging.error(traceback.format_exc()) 
                                try:
                                    logging.error(f"JSON causing crash: {json.dumps(llm_output_dict, indent=2)}")
                                except: pass
                            
                            raise PostProcessingError(str(pe)) from pe

                    # 4. Custom Validation
                    if custom_model_validate_function:
                        validation_errors = custom_model_validate_function(structured_pydantic_obj)
                        if validation_errors:
                            if verbose:
                                logging.error(f"CUSTOM VALIDATION FAILURE for {studyAnonId}: Invalid Keys/Errors Found: {validation_errors}")

                            raise CustomValidationError(f"Invalid keys: {validation_errors}")

            except (json.JSONDecodeError, ValueError, TypeError, ValidationError, AttributeError, PostProcessingError, CustomValidationError) as e:
                # Explicit Error Type Mapping
                if isinstance(e, PostProcessingError):
                    error_type = "CustomPostprocessingError"
                elif isinstance(e, CustomValidationError):
                    error_type = "CustomValidationError"
                elif isinstance(e, ValidationError):
                    error_type = "PydanticValidationError"
                elif isinstance(e, json.JSONDecodeError):
                    error_type = "JSONDecodeError"
                elif isinstance(e, TypeError):
                    error_type = "JSONStructureError-TypeError"
                elif isinstance(e, AttributeError):
                    error_type = "CodeLogicError-AttributeError"
                elif isinstance(e, ValueError):
                    error_type = "ValueError"
                else:
                    error_type = f"UnhandledProcessingError-{type(e).__name__}"
                
                call_error_msg = f"Server: {llm_source}; Warning {studyAnonId}: {error_type} - {e}"
                if verbose: logging.error(call_error_msg)
                processing_error = True
        
        if not processing_error:
            successful_call = True

    except APIConnectionError as e: 
        call_error_msg = f"Server: {llm_source}; {studyAnonId}: APIConnectionError - {e}"
        if verbose: logging.error(call_error_msg)

    except APIError as e: 
        call_error_msg = f"Server: {llm_source}; {studyAnonId}: APIError - Type={e.type} Message={e.message}"
        if verbose: logging.error(f"{script_name}: {call_error_msg}")

    except Exception as e:
        call_error_msg = f"Server: {llm_source}; {studyAnonId}: Unexpected error - {type(e).__name__}: {e}"
        if verbose: traceback.print_exc()
    
    latency = time.time() - start_time_for_latency
    statistics["end_to_end_latency"] = latency
    if successful_call and statistics["num_output_tokens"] > 0 and latency > 0:
        statistics["output_tokens_per_sec"] = statistics["num_output_tokens"] / latency

    if not successful_call:
        if not call_error_msg:
            call_error_msg = f"Server: {llm_source}; Call failed without a specific error message."
        statistics["call_error_msg"] = call_error_msg
        
    return {"successful_call": successful_call, 
            "llm_output_raw_content": llm_output_raw_content, 
            "llm_output_raw_reasoning": llm_output_raw_reasoning, 
            "llm_output_dict": llm_output_dict, 
            "structured_pydantic_obj": structured_pydantic_obj, 
            "statistics": statistics}

# --- Function to Encode to utf-8 ignoring errors to remove the lone surrogates as this sometimes occured in gpt-oss outputs
def remove_surrogates(text):
    """Remove invalid Unicode surrogate characters from text."""
    if isinstance(text, str):
        return text.encode('utf-8', 'ignore').decode('utf-8')
    return text
