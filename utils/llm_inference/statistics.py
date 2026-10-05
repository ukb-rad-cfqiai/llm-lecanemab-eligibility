"""Summarize inference request statistics in an Excel workbook."""

import os
import time

import pandas as pd


def create_and_save_statistics_summary(stats_list, script_start_time, llm_name_folder_friendly, results_cache_dir, script_name):
    """Write inference statistics to a summary workbook."""
    if not stats_list: return
    stats_df = pd.DataFrame(stats_list)
    
    summary_file_path = os.path.join(results_cache_dir, f'{script_name}_{llm_name_folder_friendly}_statistics_summary.xlsx')
    print(f"\n{script_name}: Generating statistics summary at: {summary_file_path}")

    numeric_cols = ["num_input_tokens", "num_output_tokens", "num_reason_tokens", "output_tokens_per_sec", "end_to_end_latency"]
    for col in numeric_cols:
        if col in stats_df.columns: stats_df[col] = pd.to_numeric(stats_df[col], errors='coerce')

    available = [c for c in numeric_cols if c in stats_df.columns]
    if available:
        summary = stats_df[available].describe().transpose()
        summary['sum'] = stats_df[available].sum()
        summary['IQR'] = summary['75%'] - summary['25%']
    else:
        summary = pd.DataFrame()

    total_script_time = time.time() - script_start_time
    summary = pd.concat([summary, pd.DataFrame({'sum': [total_script_time]}, index=['total_script_time_seconds'])])
    
    if 'call_error_msg' in stats_df.columns:
        errs = stats_df['call_error_msg'].notna().sum()
        summary = pd.concat([summary, pd.DataFrame({'sum': [errs]}, index=['failed_llm_calls_count'])])

    with pd.ExcelWriter(summary_file_path, engine='openpyxl') as writer:
        summary.to_excel(writer, sheet_name='Summary')
        stats_df.to_excel(writer, sheet_name='Raw Statistics', index=False)
