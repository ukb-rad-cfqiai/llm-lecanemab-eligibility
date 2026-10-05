"""Precompute the deterministic comparator from the input workbook."""

import json
import os

import pandas as pd

from utils.data.paths import INPUT_TABLE_PATH
from utils.evaluation.eligibility import classify_patient_eligibility
from utils.rule_based.cache import (
    ID_COLUMN,
    TEXT_COLUMN,
    RULE_BASED_PREFIX,
    RULE_BASED_CACHE_PATH,
    SOURCE_HASH_COLUMN,
    RULE_CODE_HASH_COLUMN,
    source_text_sha256,
    rule_code_sha256,
    validated_study_ids,
)
from utils.rule_based.extraction import (
    extract_rule_based_features,
    summarize_rule_based_trace,
)
from utils.rule_based.patterns import RULE_BASED_FEATURE_FIELDS


def build_rule_based_dataframe(input_df):
    """Build one cached result row per study without changing the input table."""
    ids = validated_study_ids(input_df)
    rule_code_hash = rule_code_sha256()
    rows = []
    for study_id, report in zip(ids, input_df[TEXT_COLUMN]):
        features, trace = extract_rule_based_features(report)
        row = {
            ID_COLUMN: study_id,
            SOURCE_HASH_COLUMN: source_text_sha256(report),
            RULE_CODE_HASH_COLUMN: rule_code_hash,
        }
        row.update(
            (f'{RULE_BASED_PREFIX}_{field}', features[field])
            for field in RULE_BASED_FEATURE_FIELDS
        )
        row[f'{RULE_BASED_PREFIX}_match_summary'] = json.dumps(
            summarize_rule_based_trace(trace), ensure_ascii=False
        )
        row[f'{RULE_BASED_PREFIX}_match_trace'] = trace
        decision = classify_patient_eligibility(row, RULE_BASED_PREFIX)
        row[f'{RULE_BASED_PREFIX}_eligible_class'] = decision['class']
        row[f'{RULE_BASED_PREFIX}_reasons'] = decision['reasons']
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    """Read the input workbook and cache rule-based extraction results."""
    input_df = pd.read_excel(INPUT_TABLE_PATH)
    results_df = build_rule_based_dataframe(input_df)
    os.makedirs(os.path.dirname(RULE_BASED_CACHE_PATH), exist_ok=True)
    results_df.to_json(
        RULE_BASED_CACHE_PATH, orient='records', lines=True, force_ascii=False
    )
    print(f"Wrote {len(results_df)} rule-based results to {RULE_BASED_CACHE_PATH}")


if __name__ == '__main__':
    main()
