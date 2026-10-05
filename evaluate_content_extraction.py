"""Evaluate extracted findings against reference labels and write reports."""
import os
import re
import json
import pandas as pd
import seaborn as sns
from utils.data.paths import INPUT_TABLE_PATH, RESULTS_CACHE_DIR, EVALUATION_RESULTS_DIR
from utils.llm_inference.prompts import PROMPT_STEP_NAMES
from utils.rule_based.patterns import RULE_BASED_FEATURE_FIELDS
from utils.rule_based.cache import (
    TEXT_COLUMN,
    RULE_BASED_PREFIX,
    load_rule_based_results,
)
from utils.evaluation.eligibility import classify_patient_eligibility, parse_list_from_string

from utils.evaluation.statistics import (
    calculate_class_specific_metrics,
    calculate_metrics as calculate_reporting_metrics,
    paired_classifier_comparison,
)
from utils.evaluation.reports import (
    create_confusion_matrix_figures,
    create_performance_and_agreement_figures,
    write_paired_comparison_files,
    write_summary_files,
)


# --- Configuration ---
INPUT_FILE_PATH = INPUT_TABLE_PATH
OUTPUT_DIR = EVALUATION_RESULTS_DIR
CACHE_DIR = RESULTS_CACHE_DIR

RULE_BASED_DISPLAY_NAME = 'Deterministic rule-based comparator'
REFERENCE_DISPLAY_NAME = 'Consensus'
DATASET_SLUG = 'holdout'
RUN_PAIRED_COMPARISON = True

# --- Visualization Settings ---
sns.set_theme(style="whitegrid", context="paper", font_scale=1.3)

# --- Labels Definition ---
LABELS = ['eligible', 'not eligible', 'potentially eligible']

# --- Helper Functions ---
def get_clean_name(name):
    """Cleans technical column names for plot display."""
    if name == 'Consensus': return 'Consensus'
    if name == RULE_BASED_PREFIX: return RULE_BASED_DISPLAY_NAME
    if name == RULE_BASED_DISPLAY_NAME: return RULE_BASED_DISPLAY_NAME

    normalized_name = re.sub(r'[\s-]+', '_', str(name).strip()).casefold()
    if normalized_name in {'eligible_class_consense', 'eligible_class_consensus'}:
        return 'Consensus'

    rater_match = re.fullmatch(r'eligible_class_rater_?(\d+)', normalized_name)
    if rater_match:
        return f"Rater {rater_match.group(1)}"
    
    # Clean Rater names
    if normalized_name.startswith('eligible_class_'):
        clean = normalized_name.replace('eligible_class_', '', 1).replace('_', ' ').title()
        if 'Consense' in clean: return 'Consensus'
        return clean
        
    # Clean Model names (Model Name Agnostic)
    # 1. Handle paths like "meta/llama-3" -> "llama-3"
    if '/' in name:
        name = name.split('/')[-1]
        
    # 2. Remove first segment if hyphens exist (e.g. "openai-gpt-oss..." -> "gpt-oss...")
    if '-' in name:
        parts = name.split('-')
        # Safety check: Only split if there is more than one part, otherwise return as is
        if len(parts) > 1:
            return '-'.join(parts[1:])
            
    return name


def detect_human_label_columns(columns):
    """Return the actual consensus and rater column names, ignoring header case.

    Some workbooks use headers such as ``eligible_class_Consense`` or
    ``eligible_class_Rater2``.  Matching those headers case-sensitively silently
    made Rater1 the fallback ground truth and omitted Rater2 from all results.
    """
    normalized_columns = {
        column: re.sub(r'[\s-]+', '_', str(column).strip()).casefold()
        for column in columns
    }

    consensus_aliases = {'eligible_class_consense', 'eligible_class_consensus'}
    consensus_candidates = [
        column for column, normalized in normalized_columns.items()
        if normalized in consensus_aliases
    ]

    numbered_raters = []
    for position, (column, normalized) in enumerate(normalized_columns.items()):
        match = re.fullmatch(r'eligible_class_rater_?(\d+)', normalized)
        if match:
            numbered_raters.append((int(match.group(1)), position, column))

    rater_columns = [
        column for _, _, column in sorted(numbered_raters, key=lambda item: (item[0], item[1]))
    ]

    consensus_column = consensus_candidates[0] if consensus_candidates else None
    if consensus_column is None:
        rater1 = next(
            (column for number, _, column in numbered_raters if number == 1),
            None,
        )
        consensus_column = rater1

    return consensus_column, rater_columns

def load_jsonl_data_for_model(model_name):
    """Load per-step cached LLM responses indexed by study ID."""
    print(f"--- Loading cached JSONL data for model: {model_name} ---")
    extraction_script_name = 'llm_content_extraction'
    step_names = PROMPT_STEP_NAMES

    model_data = {}
    model_name_folder_friendly = model_name.replace('/', '-')
    
    for step_name in step_names:
        model_data[step_name] = {}
        file_path = os.path.join(CACHE_DIR, f'{extraction_script_name}_{step_name}_{model_name_folder_friendly}.jsonl')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        study_id = str(data.get('studyAnonId'))
                        if study_id: model_data[step_name][study_id] = data
                    except json.JSONDecodeError: pass
    return model_data

def write_rule_based_audit(df, consensus_col):
    """Write rule-based decisions and extracted fields to an audit workbook."""
    if f'{RULE_BASED_PREFIX}_eligible_class' not in df.columns:
        return

    audit_cols = ['studyAnonId', consensus_col, f'{RULE_BASED_PREFIX}_eligible_class',
                  f'{RULE_BASED_PREFIX}_reasons', f'{RULE_BASED_PREFIX}_match_summary']
    audit_cols.extend([f'{RULE_BASED_PREFIX}_{field}' for field in RULE_BASED_FEATURE_FIELDS])
    audit_cols = [col for col in audit_cols if col in df.columns]

    audit_df = df[audit_cols].copy()
    audit_path = os.path.join(OUTPUT_DIR, 'rule_based_baseline_audit.xlsx')
    audit_df.to_excel(audit_path, index=False)
    print(f"  -> Wrote rule-based audit file: {audit_path}")

def generate_rule_based_disagreement_reports(df, gt_col):
    """Write evidence reports for rule-based disagreements with consensus."""
    print("  -> Generating detailed disagreement reports for the rule-based baseline...")
    prediction_col = f'{RULE_BASED_PREFIX}_eligible_class'
    reasons_col = f'{RULE_BASED_PREFIX}_reasons'

    if prediction_col not in df.columns:
        return

    disagreements = df[df[gt_col] != df[prediction_col]].copy()
    if disagreements.empty:
        return

    files = {}
    try:
        for label in LABELS:
            filename = f'disagreement_{label.replace(" ", "_")}_{RULE_BASED_PREFIX}.md'
            writer = open(os.path.join(OUTPUT_DIR, filename), 'w', encoding='utf-8')
            files[label] = writer
            writer.write(f"# Disagreement Report: Ground Truth '{label}'\n")
            writer.write(
                f"**System:** {RULE_BASED_DISPLAY_NAME} | **Comparison:** vs {gt_col}\n\n"
            )
            writer.write(
                "> **Consensus limitation:** The dataset stores the consensus label, but not the "
                "doctor's rationale for that label. This report therefore explains the automated "
                "decision only.\n\n"
            )

        for _, row in disagreements.iterrows():
            study_id = str(row['studyAnonId'])
            gt_class = row[gt_col]
            prediction = row[prediction_col]
            writer = files.get(gt_class)
            if not writer:
                continue

            report = row.get(TEXT_COLUMN, '')
            trace = row.get(f'{RULE_BASED_PREFIX}_match_trace', {})
            reasons = row.get(reasons_col, [])
            if not isinstance(reasons, (list, tuple)):
                reasons = parse_list_from_string(reasons)

            writer.write(f"## Patient ID: {study_id}\n")
            writer.write(f"- **GT:** `{gt_class}` | **Pred:** `{prediction}`\n\n")

            writer.write("### Rule-Based Reasons\n")
            if reasons:
                for reason in reasons:
                    writer.write(f"- {reason}\n")
            else:
                writer.write("*(No specific reasons logged)*\n")

            writer.write("\n### Complete Rule Extraction Review\n")
            writer.write(
                "Every value below was available to the eligibility classifier. A value not "
                "represented in **Rule-Based Reasons** did not trigger a classification reason "
                "under the implemented rules.\n\n"
            )
            for field in RULE_BASED_FEATURE_FIELDS:
                value = row.get(f'{RULE_BASED_PREFIX}_{field}')
                writer.write(f"- `{field}`: `{value}`\n")

            writer.write("\n### Matched Rule Evidence\n")
            if trace:
                for field in RULE_BASED_FEATURE_FIELDS:
                    matches = trace.get(field, [])
                    if not matches:
                        continue
                    writer.write(f"#### `{field}`\n")
                    for match in matches:
                        writer.write(f"- **Rule label:** `{match.get('label', 'N/A')}`\n")
                        writer.write(f"  - **Matched text:** *\"{match.get('match', 'N/A')}\"*\n")
                        writer.write(f"  - **Context:** {match.get('context', 'N/A')}\n")
            else:
                writer.write(
                    "*(No positive text matches; the decision was driven by missing/default features.)*\n"
                )

            writer.write("\n### Source Report\n")
            report_lines = str(report).splitlines() or ['']
            for line in report_lines:
                writer.write(f"> {line}\n")
            writer.write("\n---\n")
    finally:
        for writer in files.values():
            writer.close()

def find_extraction_source_for_reason(reason_string, study_id, model_output_data):
    """Find LLM evidence fields related to one eligibility reason."""
    keyword_map = {
        "Depression": ["depression_status", "depression_schweregrad"],
        "Ätiologie": ["kognitive_stoerung_aetiologie"],
        "Immunerkrankung": ["immunologische_erkrankung"],
        "Gerinnungsstörung": ["gerinnungsstoerung"],
        "Immunsuppression": ["immunosuppression"],
        "Antikoagulation": ["antikoagulation"],
        "Kognition": ["kognitive_stoerung_praesenz", "kognitive_stoerung_schweregrad"],
        "Amyloid": ["pathologische_amyloid_biomarker"],
        "MMSE": ["mini_mental_status_test_ergebnis"],
        "MRT": ["MRT_haemorrhagie", "MRT_siderose", "MRT_ischaemie", "MRT_fazekas", "MRT_cerebrale_amyloidangiopathie", "MRT_gehirn_untersuchung_erhalten"],
        "Hämorrhagie": ["MRT_haemorrhagie"],
        "Siderose": ["MRT_siderose"],
        "Ischämie": ["MRT_ischaemie"],
        "Fazekas": ["MRT_fazekas"],
        "CAA": ["MRT_cerebrale_amyloidangiopathie"],
        "Schlaganfall": ["krankengeschichte_schlaganfall"],
        "Epilepsie": ["krankengeschichte_epileptischer_anfall"]
    }
    found_details = []
    relevant_keys = set()
    for key, json_fields in keyword_map.items():
        if key.lower() in reason_string.lower():
            relevant_keys.update(json_fields)
    
    if not relevant_keys: return None

    for step_name, studies in model_output_data.items():
        if study_id in studies:
            llm_out = studies[study_id].get('llm_output', {})
            for k in relevant_keys:
                if k in llm_out:
                    item = llm_out[k]
                    found_details.append({
                        'key': k,
                        'value': item.get('Extraktion'),
                        'reasoning': item.get('Begruendung_Extraktion', 'N/A'),
                        'quote': item.get('Zitat_Nennung', 'N/A')
                    })
    return found_details

def get_all_model_extraction_sources(study_id, model_output_data):
    """Collect all cached LLM extraction details for one study."""
    details_by_field = {}
    for step_name, studies in model_output_data.items():
        if study_id not in studies:
            continue
        llm_output = studies[study_id].get('llm_output', {})
        if not isinstance(llm_output, dict):
            continue
        for field, item in llm_output.items():
            if field not in RULE_BASED_FEATURE_FIELDS or not isinstance(item, dict):
                continue
            details_by_field[field] = {
                'value': item.get('Extraktion'),
                'reasoning': item.get('Begruendung_Extraktion', 'N/A'),
                'quote': item.get('Zitat_Nennung', 'N/A'),
            }
    return details_by_field

def generate_detailed_disagreement_reports(df, model_name, model_output_data, gt_col):
    """Write model disagreement reports with extraction evidence."""
    print(f"  -> Generating detailed disagreement reports for {model_name}...")
    model_prefix = f"llm_{model_name.replace('/', '-')}"
    llm_col = f'{model_prefix}_eligible_class'
    
    disagreements = df[df[gt_col] != df[llm_col]].copy()
    if disagreements.empty: return

    files = {}
    for label in LABELS:
        fname = f'disagreement_{label.replace(" ", "_")}_{model_name.replace("/", "-")}.md'
        files[label] = open(os.path.join(OUTPUT_DIR, fname), 'w', encoding='utf-8')
        files[label].write(f"# Disagreement Report: Ground Truth '{label}'\n")
        files[label].write(f"**Model:** {model_name} | **Comparison:** vs {gt_col}\n\n")
        files[label].write(
            "> **Consensus limitation:** The dataset stores the consensus label, but not the "
            "doctor's rationale for that label. This report therefore explains the model's "
            "decision only.\n\n"
        )

    for _, row in disagreements.iterrows():
        study_id = str(row['studyAnonId'])
        gt_class = row[gt_col]
        llm_class = row[llm_col]
        llm_reasons = row[f'{model_prefix}_reasons']
        if not isinstance(llm_reasons, (list, tuple)):
            llm_reasons = parse_list_from_string(llm_reasons)

        writer = files.get(gt_class)
        if not writer: continue

        writer.write(f"## Patient ID: {study_id}\n")
        writer.write(f"- **GT:** `{gt_class}` | **Pred:** `{llm_class}`\n\n")
        writer.write("### Model Reasons:\n")
        
        if not llm_reasons: writer.write("*(No specific reasons logged)*\n")
        
        for reason in llm_reasons:
            writer.write(f"#### \"{reason}\"\n")
            details = find_extraction_source_for_reason(reason, study_id, model_output_data)
            if details:
                for d in details:
                    writer.write(f"- **Extracted:** `{d['value']}` ({d['key']})\n")
                    writer.write(f"  - **Reasoning:** {d['reasoning']}\n")
                    if d['quote'] != 'N/A': writer.write(f"  - **Quote:** *\"{d['quote']}\"*\n")
            else: writer.write("- *(Detailed trace not found)*\n")
            writer.write("\n")

        writer.write("### Complete Model Extraction Review\n")
        writer.write(
            "Every value below was available to the eligibility classifier. A value not "
            "represented in **Model Reasons** did not trigger a classification reason under "
            "the implemented rules.\n\n"
        )
        extraction_sources = get_all_model_extraction_sources(study_id, model_output_data)
        for field in RULE_BASED_FEATURE_FIELDS:
            classifier_value = row.get(f'{model_prefix}_{field}')
            writer.write(f"#### `{field}`\n")
            writer.write(f"- **Value used by classifier:** `{classifier_value}`\n")

            detail = extraction_sources.get(field)
            if detail:
                writer.write(f"- **Raw model extraction:** `{detail['value']}`\n")
                writer.write(f"- **Model reasoning:** {detail['reasoning']}\n")
                if detail['quote'] != 'N/A':
                    writer.write(f"- **Source quote:** *\"{detail['quote']}\"*\n")
            else:
                writer.write("- *(Detailed extraction trace not found in cached JSONL output.)*\n")
            writer.write("\n")

        writer.write("### Source Report\n")
        report = row.get(TEXT_COLUMN, '')
        report_lines = str(report).splitlines() or ['']
        for line in report_lines:
            writer.write(f"> {line}\n")
        writer.write("\n")
        writer.write("---\n")

    for f in files.values(): f.close()

def calculate_metrics(y_true, y_pred, system_name, reference_name):
    """Compute reporting metrics for predictions against reference labels."""
    return calculate_reporting_metrics(
        y_true, y_pred, system_name, reference_name, LABELS
    )


def build_prediction_agents(df, models, raters, consensus_col, baseline_agents):
    """Collect human, model, and baseline prediction series for plots."""
    agents = []
    for rater in raters:
        if rater == consensus_col:
            continue
        agents.append({
            'name': get_clean_name(rater),
            'series': df[rater],
            'file_stem': rater,
        })
    for model in models:
        agents.append({
            'name': get_clean_name(model),
            'series': df[f"llm_{model.replace('/', '-')}_eligible_class"],
            'file_stem': model.replace('/', '-'),
        })
    for baseline_agent in baseline_agents:
        agents.append({
            'name': get_clean_name(baseline_agent),
            'series': df[f'{baseline_agent}_eligible_class'],
            'file_stem': baseline_agent,
        })
    return agents


def create_summary_and_plots(all_metrics, class_metrics, df, models, consensus_col,
                             raters, baseline_agents=None):
    """Write evaluation tables and figures for all prediction agents."""
    print("\n--- Creating Final Summaries and Plots ---")
    baseline_agents = baseline_agents or []
    prediction_agents = build_prediction_agents(
        df, models, raters, consensus_col, baseline_agents
    )
    write_summary_files(
        all_metrics, class_metrics, df[consensus_col], prediction_agents,
        REFERENCE_DISPLAY_NAME, LABELS, OUTPUT_DIR,
    )
    create_confusion_matrix_figures(
        df[consensus_col], prediction_agents, REFERENCE_DISPLAY_NAME, LABELS,
        OUTPUT_DIR, DATASET_SLUG,
    )
    create_performance_and_agreement_figures(
        all_metrics, df[consensus_col], prediction_agents,
        REFERENCE_DISPLAY_NAME, LABELS, OUTPUT_DIR, DATASET_SLUG,
    )


def main():
    """Load study data and cached results, then run the evaluation."""
    print("--- Starting Evaluation ---")
    
    if not os.path.exists(INPUT_FILE_PATH):
        print(f"FATAL: {INPUT_FILE_PATH} not found.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    df = pd.read_excel(INPUT_FILE_PATH)
    print(f"Loaded {len(df)} rows.")

    # 1. Ground Truth logic
    consense_col, rater_cols = detect_human_label_columns(df.columns)
    if consense_col is None:
        print("FATAL: No GT column found.")
        return

    has_explicit_consensus = get_clean_name(consense_col) == 'Consensus'
    if not has_explicit_consensus:
        print(
            f"[WARNING] No explicit consensus column found; using '{consense_col}' "
            "as ground truth. That rater cannot also be benchmarked against itself."
        )

    print(f"Consensus column: {consense_col}")
    print(f"Rater columns: {rater_cols}")
    
    # Normalize
    for col in [consense_col] + rater_cols:
        if col in df.columns:
            valid = df[col].notna()
            df.loc[valid, col] = df.loc[valid, col].astype(str).str.strip().str.lower()
    
    # --- START OF CHANGES ---
    # Verbose Filtering
    initial_count = len(df)
    
    # 1. Identify and remove rows with missing Ground Truth
    nan_rows = df[df[consense_col].isna()]
    if not nan_rows.empty:
        print(f"\n[WARNING] Dropping {len(nan_rows)} rows due to missing value in '{consense_col}':")
        for idx, row in nan_rows.iterrows():
            sid = row.get('studyAnonId', f"Row {idx}")
            print(f"  - ID: {sid}")
    
    df = df.dropna(subset=[consense_col])

    # 2. Identify and remove rows with invalid Ground Truth labels
    # (Values not in the allowed LABELS list)
    invalid_mask = ~df[consense_col].isin(LABELS)
    invalid_rows = df[invalid_mask]
    
    if not invalid_rows.empty:
        print(f"\n[WARNING] Dropping {len(invalid_rows)} rows due to invalid label in '{consense_col}':")
        print(f"  Allowed labels: {LABELS}")
        for idx, row in invalid_rows.iterrows():
            sid = row.get('studyAnonId', f"Row {idx}")
            val = row[consense_col]
            print(f"  - ID: {sid} | Found Value: '{val}'")
            
    df = df[~invalid_mask]

    if len(df) < initial_count:
        print(f"-> Dataset reduced from {initial_count} to {len(df)} rows.\n")

    # 1.5. Check consistency of other Raters (Warnings only)
    # If a rater has a value not in LABELS, it will disappear from Confusion Matrices.
    print("--- Checking Rater Data Quality ---")
    for rater in rater_cols:
        if rater == consense_col: continue # Already checked
        
        # Check for values not in the allowed list
        bad_rater_rows = df[~df[rater].isin(LABELS)]
        
        if not bad_rater_rows.empty:
            print(f"[WARNING] '{rater}' contains {len(bad_rater_rows)} invalid values.")
            print(f"          These will be EXCLUDED from Confusion Matrices (causing sum < {len(df)}):")
            for idx, row in bad_rater_rows.iterrows():
                sid = row.get('studyAnonId', f"Row {idx}")
                val = row[rater]
                print(f"  - ID: {sid} | Invalid Value: '{val}'")
        else:
            print(f"  - {rater}: OK (All {len(df)} rows valid)")
    print("")

    # 2. Detect Models
    potential = set()
    for c in df.columns:
        if c.startswith('llm_') and not c.endswith('eligible_class') and not c.endswith('reasons'):
            parts = c.split('_')
            if len(parts) >= 3: potential.add(parts[1])
    models = sorted(list(potential))
    print(f"Models: {models}")

    all_metrics = []
    class_metrics = []
    baseline_agents = []

    # 3. Process Human Raters
    print("\n--- Evaluating Humans ---")
    for r in rater_cols:
        if r != consense_col:
            system_name = get_clean_name(r)
            m = calculate_metrics(
                df[consense_col], df[r], system_name, REFERENCE_DISPLAY_NAME
            )
            all_metrics.append(m)
            class_metrics.extend(calculate_class_specific_metrics(
                df[consense_col], df[r], system_name,
                REFERENCE_DISPLAY_NAME, LABELS,
            ))
            print("  {}: Kappa={:.2f}".format(
                system_name, m["Cohen's kappa"]
            ))

    # 4. Process precomputed rule-based results
    df = load_rule_based_results(df)
    baseline_agents.append(RULE_BASED_PREFIX)
    pred_col = f'{RULE_BASED_PREFIX}_eligible_class'
    m_rule = calculate_metrics(
        df[consense_col], df[pred_col], RULE_BASED_DISPLAY_NAME,
        REFERENCE_DISPLAY_NAME,
    )
    all_metrics.append(m_rule)
    class_metrics.extend(calculate_class_specific_metrics(
        df[consense_col], df[pred_col], RULE_BASED_DISPLAY_NAME,
        REFERENCE_DISPLAY_NAME, LABELS,
    ))
    print("  {}: Kappa={:.2f}".format(
        RULE_BASED_DISPLAY_NAME, m_rule["Cohen's kappa"]
    ))
    write_rule_based_audit(df, consense_col)
    generate_rule_based_disagreement_reports(df, consense_col)

    # 5. Process Models
    print("\n--- Evaluating Models ---")
    for model in models:
        model_prefix = f"llm_{model}"
        res = df.apply(lambda row: classify_patient_eligibility(row, model_prefix), axis=1)
        df[f'{model_prefix}_eligible_class'] = [r['class'] for r in res]
        df[f'{model_prefix}_reasons'] = [r['reasons'] for r in res]

        # Model vs Consensus
        pred_col = f'{model_prefix}_eligible_class'
        system_name = get_clean_name(model)
        m_cons = calculate_metrics(
            df[consense_col], df[pred_col], system_name, REFERENCE_DISPLAY_NAME
        )
        all_metrics.append(m_cons)
        class_metrics.extend(calculate_class_specific_metrics(
            df[consense_col], df[pred_col], system_name,
            REFERENCE_DISPLAY_NAME, LABELS,
        ))
        print("  {}: Kappa={:.2f}".format(
            system_name, m_cons["Cohen's kappa"]
        ))

        # Detailed Reports
        model_jsonl = load_jsonl_data_for_model(model)
        generate_detailed_disagreement_reports(df, model, model_jsonl, consense_col)

    # 6. Paired LLM-vs-rule-based comparison on the same cases
    paired_rows = []
    if RUN_PAIRED_COMPARISON:
        rule_pred_col = f'{RULE_BASED_PREFIX}_eligible_class'
        for model in models:
            model_pred_col = f"llm_{model}_eligible_class"
            paired_rows.append(paired_classifier_comparison(
                df[consense_col], df[model_pred_col], df[rule_pred_col],
                get_clean_name(model), RULE_BASED_DISPLAY_NAME, LABELS,
            ))
    write_paired_comparison_files(paired_rows, OUTPUT_DIR)

    # 7. Tables and publication figures
    create_summary_and_plots(
        all_metrics, class_metrics, df, models, consense_col,
        rater_cols, baseline_agents,
    )
    print("\nDone.")

if __name__ == '__main__':
    main()
