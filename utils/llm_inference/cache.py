"""Read and append cached inference results in JSONL format."""

import json
import logging
import os

script_name = 'llm_server'


def write_jsonl(out_dict, json_path ):
    """Append one result record to a JSONL cache file."""
    try:
        # Ensure the directory exists before writing
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'a', encoding='utf-8') as fout:
            fout.write(json.dumps(out_dict, ensure_ascii=False) + '\n')
    except Exception as e:
        logging.error(f"{script_name}: writing to JSON {json_path}: {e}. Data: {out_dict}")

def get_saved_results_data(json_path, data_str=None, id_key='studyAnonId'):
    """Load cached JSONL records keyed by study identifier."""
    json_data = {}
    # Ensure directory exists before trying to read
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    try:
        with open(json_path, 'r', encoding='utf-8') as fin:
            for line in fin:
                try:
                    data = json.loads(line)
                    item_id = data.get(id_key)
                    if item_id is not None:
                         json_data[str(item_id)] = data
                    else:
                         logging.warning(f"{script_name}:  Skipping line without {id_key} in {json_path}: {line.strip()}")
                except json.JSONDecodeError:
                    logging.warning(f"{script_name}: Skipping invalid JSON line in {json_path}: {line.strip()}")
    except FileNotFoundError:
        logging.warning(f"{script_name}: Log file {json_path} not found, starting fresh.")
    except Exception as e:
        logging.error(f"{script_name}: reading log file {json_path}: {e}")

    logging.info(f"{script_name}: Loaded {len(json_data)} existing {data_str} results from {os.path.basename(json_path)}.")
    return json_data
