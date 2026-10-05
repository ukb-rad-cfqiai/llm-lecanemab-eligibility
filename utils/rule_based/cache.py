"""Storage and alignment of precomputed rule-based extraction results."""

import hashlib
import os
from pathlib import Path

import pandas as pd

from utils.data.paths import RESULTS_CACHE_DIR
from .patterns import RULE_BASED_FEATURE_FIELDS


ID_COLUMN = 'studyAnonId'
TEXT_COLUMN = 'doctors_letters'
RULE_BASED_PREFIX = 'rule_based_baseline'
SOURCE_HASH_COLUMN = 'source_text_sha256'
RULE_CODE_HASH_COLUMN = 'rule_code_sha256'
RULE_BASED_CACHE_PATH = os.path.join(
    RESULTS_CACHE_DIR, 'rule_based_content_extraction.jsonl'
)


def source_text_sha256(report):
    """Hash the exact input text used for extraction, including its whitespace."""
    text = report if isinstance(report, str) else ''
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def rule_code_sha256():
    """Identify the extraction patterns, implementation, and eligibility rules."""
    rule_dir = Path(__file__).resolve().parent
    sources = (
        rule_dir / 'patterns.py',
        rule_dir / 'extraction.py',
        rule_dir.parent / 'evaluation' / 'eligibility.py',
    )
    digest = hashlib.sha256()
    for source in sources:
        digest.update(source.read_bytes())
    return digest.hexdigest()


def validated_study_ids(df):
    """Return string identifiers and reject ambiguous cache joins."""
    missing = [column for column in (ID_COLUMN, TEXT_COLUMN) if column not in df]
    if missing:
        raise ValueError(f"Input table is missing required columns: {', '.join(missing)}")
    if df[ID_COLUMN].isna().any():
        raise ValueError(f"Input table contains missing {ID_COLUMN} values.")
    ids = df[ID_COLUMN].astype(str)
    if ids.str.strip().eq('').any():
        raise ValueError(f"Input table contains empty {ID_COLUMN} values.")
    if ids.duplicated().any():
        raise ValueError(f"Input table contains duplicate {ID_COLUMN} values.")
    return ids


def load_rule_based_results(df):
    """Attach cached results in input order and reject stale or incomplete data."""
    ids = validated_study_ids(df)
    if not os.path.isfile(RULE_BASED_CACHE_PATH):
        raise FileNotFoundError(
            f"Rule-based results not found at {RULE_BASED_CACHE_PATH}. "
            "Run python rule_based_content_extraction.py first."
        )

    cached = pd.read_json(
        RULE_BASED_CACHE_PATH, orient='records', lines=True,
        dtype={ID_COLUMN: str},
    )
    result_columns = [f'{RULE_BASED_PREFIX}_{field}' for field in RULE_BASED_FEATURE_FIELDS]
    result_columns.extend(
        f'{RULE_BASED_PREFIX}_{suffix}'
        for suffix in ('match_summary', 'match_trace', 'eligible_class', 'reasons')
    )
    required = [ID_COLUMN, SOURCE_HASH_COLUMN, RULE_CODE_HASH_COLUMN, *result_columns]
    missing = [column for column in required if column not in cached]
    if missing:
        raise ValueError(
            f"Rule-based cache is missing columns: {', '.join(missing)}. "
            "Rerun python rule_based_content_extraction.py."
        )
    if cached[ID_COLUMN].isna().any() or cached[ID_COLUMN].duplicated().any():
        raise ValueError("Rule-based cache has missing or duplicate study identifiers.")

    cached = cached.set_index(ID_COLUMN)
    if not ids.isin(cached.index).all():
        raise ValueError(
            "Rule-based cache has no results for some input rows. "
            "Rerun python rule_based_content_extraction.py."
        )
    aligned = cached.loc[ids.to_list()]
    expected_hashes = df[TEXT_COLUMN].map(source_text_sha256).to_list()
    if aligned[SOURCE_HASH_COLUMN].to_list() != expected_hashes:
        raise ValueError(
            "Input reports changed after rule-based extraction. "
            "Rerun python rule_based_content_extraction.py."
        )
    if not aligned[RULE_CODE_HASH_COLUMN].eq(rule_code_sha256()).all():
        raise ValueError(
            "Rule-based extraction or eligibility rules changed after caching. "
            "Rerun python rule_based_content_extraction.py."
        )

    results = aligned[result_columns].copy()
    results.index = df.index
    return pd.concat([df.drop(columns=result_columns, errors='ignore'), results], axis=1)
