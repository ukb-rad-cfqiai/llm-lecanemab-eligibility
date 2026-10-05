"""Run the LLM content extraction experiment."""

import multiprocessing
import os
import sys
import time
from collections import defaultdict

import numpy as np
import pandas as pd
from tqdm import tqdm

from utils.data.paths import INPUT_TABLE_PATH, RESULTS_CACHE_DIR
from utils.llm_inference.cache import get_saved_results_data, write_jsonl
from utils.llm_inference.config import load_inference_settings, verify_inference_stack
from utils.llm_inference.prompts import prompt_steps_dict
from utils.llm_inference.statistics import create_and_save_statistics_summary
from utils.llm_inference.worker import init_worker, process_job


script_dir = os.path.dirname(os.path.abspath(__file__))
script_name = os.path.basename(__file__).split('.')[0]
NB_WORKERS = 256
CSV_SEPERATOR = ';'
INFERENCE_PROFILE_PATH = os.path.join(
    script_dir, "utils", "ukb_gpt_profiles", "gpt-oss-120b.env",
)
EXPECTED_MODEL_ID = "openai/gpt-oss-120b"
join = os.path.join
os.environ["TOKENIZERS_PARALLELISM"] = "false"
input_table_path = INPUT_TABLE_PATH


def main():
    """Run all prompt steps and merge their outputs into the input workbook."""
    script_start_time = time.time()
    os.makedirs(RESULTS_CACHE_DIR, exist_ok=True)

    # --- 1. Basic Setup ---
    base_url, llm_name, api_key = load_inference_settings(INFERENCE_PROFILE_PATH, EXPECTED_MODEL_ID)
    verify_inference_stack(base_url, llm_name, api_key)
    print(f"{script_name}: Using {llm_name} via {base_url}.")
    llm_name_folder_friendly = llm_name.replace('/', '-')
    dotenv_path = INFERENCE_PROFILE_PATH

    # --- 2. Data Loading ---
    if input_table_path.endswith('.csv'): df = pd.read_csv(input_table_path, sep=CSV_SEPERATOR)
    else: df = pd.read_excel(input_table_path)
    
    df.dropna(subset=['doctors_letters'], inplace=True)
    df['studyAnonId'] = df['studyAnonId'].astype(str)
    print(f'{script_name}: Loaded {len(df)} reports.')

    # --- 3. Load Prompts & Prepare Paths ---
    step_file_map = {}
    
    for step_name, config in prompt_steps_dict.items():
        try:
            with open(config["prompt_txt_file"], 'r', encoding='utf-8') as f:
                prompt_text = f.read()
        except FileNotFoundError:
            print(f"ERROR: Prompt file missing for {step_name}"); sys.exit(1)
            
        jsonl = join(RESULTS_CACHE_DIR, f'{script_name}_{step_name}_{llm_name_folder_friendly}.jsonl')
        jsonl_err = join(RESULTS_CACHE_DIR, f'{script_name}_{step_name}_{llm_name_folder_friendly}_error.jsonl')
        
        step_file_map[step_name] = {
            'jsonl': jsonl,
            'jsonl_error': jsonl_err,
            'prompt_text': prompt_text,
            'cache_success': get_saved_results_data(jsonl, f'{step_name}_successful'),
            'cache_error': get_saved_results_data(jsonl_err, f'{step_name}_error')
        }

    # --- 4. Create FLATTENED Job List ---
    jobs_to_run = []
    results_storage = defaultdict(dict) 

    for _, row in df.iterrows():
        sid = str(row['studyAnonId'])
        report = row['doctors_letters']
        
        for step_name, config in prompt_steps_dict.items():
            file_info = step_file_map[step_name]
            
            if sid in file_info['cache_success']:
                entry = file_info['cache_success'][sid]
                results_storage[sid][step_name] = {
                    'status': 'success', 
                    'extracted_values': entry.get('extracted_values'), 
                    'statistics': entry.get('statistics', {})
                }
            elif sid in file_info['cache_error']:
                entry = file_info['cache_error'][sid]
                results_storage[sid][step_name] = {
                    'status': 'error', 
                    'statistics': entry.get('statistics', {})
                }
            else:
                jobs_to_run.append({
                    'studyAnonId': sid,
                    'report': report,
                    'step_name': step_name,
                    'prompt_template': file_info['prompt_text'],
                    'pydantic_model': config['pydantic_model'],
                    'classes_to_extract': config['classes_to_extract']
                })

    # --- 5. Execute Parallel ---
    total_jobs = len(jobs_to_run)
    active_workers = min(NB_WORKERS, total_jobs) if total_jobs > 0 else 1
    
    print(f"{script_name}: Processing {total_jobs} new jobs with {active_workers} active workers.")
    print(f"{script_name}: (Existing results loaded from cache: {len(df)*len(prompt_steps_dict) - total_jobs})")

    if total_jobs > 0:
        # PASSING active_workers as nb_workers to init_worker so logic scales correctly
        init_args = (llm_name, base_url, api_key, dotenv_path, active_workers)
        
        with multiprocessing.Pool(processes=active_workers, initializer=init_worker, initargs=init_args) as pool:
            for result in tqdm(pool.imap_unordered(process_job, jobs_to_run), total=total_jobs):
                sid = result['studyAnonId']
                step = result['step_name']
                status = result['status']
                
                file_paths = step_file_map[step]
                
                if status == 'success':
                    write_jsonl(result, file_paths['jsonl'])
                    mem_res = result.copy()
                    mem_res.pop('llm_output', None)
                    mem_res.pop('llm_output_reasoning', None)
                    mem_res.pop('report', None)
                    results_storage[sid][step] = mem_res
                else:
                    write_jsonl(result, file_paths['jsonl_error'])
                    results_storage[sid][step] = result

    # --- 6. Re-Assembly & Merging ---
    print(f"{script_name}: Assembling final table...")
    
    all_stats_list = []
    step_dfs = {} 

    for step_name in prompt_steps_dict.keys():
        extracted_list = []
        stats_list = []
        
        for _, row in df.iterrows():
            sid = str(row['studyAnonId'])
            res = results_storage[sid].get(step_name)
            
            if res and res.get('status') == 'success':
                extracted_list.append(res.get('extracted_values', {}))
                s = res.get('statistics', {})
                s['studyAnonId'] = sid; s['step_name'] = step_name
                stats_list.append(s)
            else:
                extracted_list.append(np.nan)
                if res:
                    s = res.get('statistics', {})
                    s['studyAnonId'] = sid; s['step_name'] = step_name
                    stats_list.append(s)

        all_stats_list.extend(stats_list)
        
        temp_series = pd.Series(extracted_list, index=df.index)
        valid_mask = temp_series.apply(lambda x: isinstance(x, dict))
        
        if valid_mask.any():
            normalized = pd.json_normalize(temp_series[valid_mask])
            normalized.index = df.index[valid_mask]
            normalized.columns = [f"llm_{llm_name_folder_friendly}_{c}" for c in normalized.columns]
            step_dfs[step_name] = normalized

    # --- 7. Merge into Main DF ---
    for step_df in step_dfs.values():
        cols_to_drop = [c for c in step_df.columns if c in df.columns]
        if cols_to_drop: df.drop(columns=cols_to_drop, inplace=True)
        df = df.join(step_df)

    # --- 8. Final Stats & Save ---
    if all_stats_list:
        create_and_save_statistics_summary(
            all_stats_list, script_start_time, llm_name_folder_friendly,
            RESULTS_CACHE_DIR, script_name,
        )

    original_cols = ['studyAnonId', 'doctors_letters']
    all_llm_cols = sorted([col for col in df.columns if col.startswith('llm_')])
    other_cols = [col for col in df.columns if col not in original_cols and col not in all_llm_cols]
    final_cols = [c for c in (original_cols + other_cols + all_llm_cols) if c in df.columns]
    df = df[final_cols]

    if input_table_path.endswith('.xlsx'):
        df.to_excel(input_table_path, index=False)
    else:
        df.to_csv(input_table_path, index=False, sep=CSV_SEPERATOR)
        
    print(f"{script_name}: Completed successfully. Results in {input_table_path}")

if __name__ == '__main__':
    if sys.platform != 'win32':
        multiprocessing.set_start_method('fork', force=True)
    main()
