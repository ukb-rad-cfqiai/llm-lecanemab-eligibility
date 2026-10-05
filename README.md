# Lecanemab eligibility pre-screening experiments

Code and prompts for the experiments reported in **"Locally deployed large language model for real-world Lecanemab eligibility pre-screening"**, published in *Alzheimer's & Dementia: Diagnosis, Assessment & Disease Monitoring*. 

The workflow extracts structured findings from clinical letters, applies the study's eligibility rules, and compares model decisions with human reference labels and a deterministic rule-based comparator.

## Repository contents

| Path | Purpose |
| --- | --- |
| `llm_content_extraction.py` | Runs the prompts and merges the extracted fields into the input workbook. |
| `rule_based_content_extraction.py` | Extracts rule-based findings and caches the comparator's decisions. |
| `evaluate_content_extraction.py` | Loads cached rule-based results, classifies LLM outputs, and creates metrics and reports. |
| `prompts/prompt_diagnose_kognition.md` | Extracts cognitive impairment, etiology, amyloid biomarkers, and MMSE results. |
| `prompts/prompt_komorbiditaeten_anamnese.md` | Extracts stroke, seizure, and depression history. |
| `prompts/prompt_mrt_befunde.md` | Extracts brain MRI findings. |
| `prompts/prompt_systemerkrankungen_medikation.md` | Extracts systemic conditions and medications. |
| `utils/data/paths.py` | Resolves input, cache, and evaluation output paths from environment variables. |
| `utils/data/models.py` | Pydantic schemas for the prompt outputs. |
| `utils/llm_inference/prompts.py` | Prompt steps, file paths, and output schemas. |
| `utils/llm_inference/config.py` | UKB-GPT endpoint settings and model availability check. |
| `utils/llm_inference/worker.py` | Parallel worker setup, request retries, and warm-up logic. |
| `utils/llm_inference/server.py` | Model requests and response validation. |
| `utils/llm_inference/cache.py` | Reads and writes JSONL inference caches. |
| `utils/llm_inference/statistics.py` | Writes inference statistics workbooks. |
| `utils/evaluation/eligibility.py` | Shared eligibility classification rules for LLM and rule-based findings. |
| `utils/evaluation/statistics.py` | Evaluation metrics, bootstrap intervals, and paired comparisons. |
| `utils/evaluation/reports.py` | Evaluation tables and figures. |
| `utils/rule_based/cache.py` | Stores and validates the precomputed rule-based results. |
| `utils/rule_based/patterns.py` | Feature fields and patterns for the deterministic extractor. |
| `utils/rule_based/extraction.py` | Rule-based extraction of findings from clinical letters. |
| `utils/ukb_gpt_profiles/gpt-oss-120b.env` | Local batch inference settings for UKB-GPT. |
| `utils/ukb_gpt_profiles/gpt-oss-120b.toml` | Model deployment and GPU worker configuration. |
| `requirements.txt` | Python dependencies for extraction and evaluation. |
| `.gitignore` | Excludes local input workbooks and generated files. |
| `README.md` | Repository overview and usage instructions. |

## Requirements

The inference step needs an OpenAI API-compatible endpoint serving `openai/gpt-oss-120b`. It must provide `/v1/models` and chat completions with JSON schema response formatting. Two local options are:

- The paper experiments used a local [UKB-GPT](https://github.com/ukbonn/ukb-gpt) deployment at [commit `3be3e82`](https://github.com/ukbonn/ukb-gpt/commit/3be3e823a50d5a3ddd74c8b5f9d4370c824e183b). The supplied [inference profile](utils/ukb_gpt_profiles/gpt-oss-120b.env) and [deployment configuration](utils/ukb_gpt_profiles/gpt-oss-120b.toml) describe the experiment's `openai/gpt-oss-120b` setup on eight NVIDIA A100 80 GB GPUs. The extraction code can also use a directly started vLLM container, as shown below.

- Start [vLLM directly in a container](https://docs.vllm.ai/en/latest/deployment/docker/). With Docker, the NVIDIA Container Toolkit, suitable GPUs, and the model available through Hugging Face, run:

  ```bash
  docker run --rm --gpus all --ipc=host \
    -p 127.0.0.1:8000:8000 \
    -v "$HOME/.cache/huggingface:/root/.cache/huggingface" \
    vllm/vllm-openai:latest \
    --model openai/gpt-oss-120b \
    --tensor-parallel-size 2 \
    --max-model-len 65536 \
    --gpu-memory-utilization 0.90
  ```

  This example uses two GPUs for one vLLM instance. Adjust the GPU count and memory settings for your hardware. In another terminal, point the extraction script at its API with `export API_BASE_URL=http://127.0.0.1:8000/v1`.

Install the Python dependencies with:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The model ID and worker count are defined near the top of `llm_content_extraction.py`. Request and retry settings are in `utils/llm_inference/worker.py`. Adapt them if using a different deployment.

## Run the experiments

Run the commands below from the repository root.

Set the workbook and output paths if you want them outside the repository. The extraction and evaluation scripts use the same `INPUT_TABLE_PATH` and `RESULTS_CACHE_DIR`:

```bash
export INPUT_TABLE_PATH=/path/outside/repository/input_table.xlsx
export RESULTS_CACHE_DIR=/path/outside/repository/results_cache
export EVALUATION_RESULTS_DIR=/path/outside/repository/evaluation_results
```

Without these variables, the scripts use `input_table.xlsx`, `results_cache/`, and `evaluation_results/` in the repository root.

1. Prepare `input_table.xlsx` at `INPUT_TABLE_PATH` with at least these columns:

   | Column | Content |
   | --- | --- |
   | `studyAnonId` | Unique study identifier for each row. |
   | `doctors_letters` | Clinical letter text to process. |

2. Start either inference option described under Requirements. By default, the extraction script checks `http://127.0.0.1:30000/v1` and expects the model ID `openai/gpt-oss-120b`. Set `API_BASE_URL` to use another address, such as `http://127.0.0.1:8000/v1` for the vLLM example. Set `API_KEY` if your endpoint requires one.

3. Run extraction:

   ```bash
   python llm_content_extraction.py
   ```

   The script runs all four prompts for each nonempty letter, writes per-step JSONL results to `RESULTS_CACHE_DIR`, and adds `llm_...` extraction columns to the workbook at `INPUT_TABLE_PATH`. Existing cached results are reused on subsequent runs.

4. Run the deterministic rule-based extraction:

   ```bash
   python rule_based_content_extraction.py
   ```

   This writes `rule_based_content_extraction.jsonl` to `RESULTS_CACHE_DIR`. It contains the extracted fields, matched evidence, and eligibility decisions. Rerun this step if the clinical letters or rule-based code change.

5. Add reference labels to the workbook at `INPUT_TABLE_PATH`. The evaluation requires a consensus label column named `eligible_class_Consense` or `eligible_class_Consensus`. Optional human rater columns can be named `eligible_class_Rater1`, `eligible_class_Rater2`, and so on. Labels are `eligible`, `not eligible`, or `potentially eligible`.

6. Run evaluation:

   ```bash
   python evaluate_content_extraction.py
   ```

   The script evaluates the model and cached rule-based decisions against the reference labels. It reads detailed model outputs and rule-based results from `RESULTS_CACHE_DIR` and writes tables, figures, audits, and disagreement reports to `EVALUATION_RESULTS_DIR`. It stops if the rule-based cache is missing or stale.
