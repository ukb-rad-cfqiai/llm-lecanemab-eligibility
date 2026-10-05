"""Shared eligibility rules for LLM and rule-based extractions."""

import ast
import re

import numpy as np
import pandas as pd


# --- Configurable Whitelists ---
ALLOWED_AETIOLOGIES = ['vaskulaere Demenz', 'cerebrale Mikroangiopathie']
ALLOWED_IMMUNOLOGICAL_DISEASES = []
ALLOWED_COAGULATION_DISORDERS = ['Thrombozytopenie (leicht)', 'Thrombozythaemie (leicht)']
ALLOWED_IMMUNOSUPPRESSANTS = ['Denosumab', 'Denusomab', 'Aducanumab', 'Lecanemab', 'Trontinemab', 'Donanemab']
ALLOWED_ANTICOAGULTS = ['Tromcardin']

def fix_and_normalize_string(text: str) -> str:
    """Normalize text for comparisons against allowed values."""
    if not isinstance(text, str): return ""
    try:
        repaired_text = text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        repaired_text = text
    return re.sub(r'[^a-z0-9]', '', repaired_text.lower())

def parse_list_from_string(value):
    """Parse a stored Python list literal or return an empty list."""
    if isinstance(value, (list, tuple)): return list(value)
    if isinstance(value, str):
        try:
            parsed_value = ast.literal_eval(value)
            if isinstance(parsed_value, (list, tuple)): return list(parsed_value)
        except (ValueError, SyntaxError, TypeError): return []
    return []

def is_missing_value(value):
    """Check scalar missing values without treating containers as missing."""
    if isinstance(value, (list, tuple, dict)):
        return False
    if isinstance(value, np.ndarray):
        return False
    return pd.isna(value)

def classify_patient_eligibility(row, model_prefix):
    """Apply the shared eligibility rules to prefixed extraction fields."""
    reasons_not_eligible = []
    reasons_potentially_eligible = []

    norm_allowed_aetiologies = {fix_and_normalize_string(s) for s in ALLOWED_AETIOLOGIES}
    norm_alzheimer = fix_and_normalize_string('Alzheimer-Krankheit')
    norm_allowed_immuno = {fix_and_normalize_string(s) for s in ALLOWED_IMMUNOLOGICAL_DISEASES}
    norm_allowed_coagulation = {fix_and_normalize_string(s) for s in ALLOWED_COAGULATION_DISORDERS}
    norm_allowed_immunosupp = {fix_and_normalize_string(s) for s in ALLOWED_IMMUNOSUPPRESSANTS}
    norm_allowed_anticoag = {fix_and_normalize_string(s) for s in ALLOWED_ANTICOAGULTS}
    
    def get_value(field_name):
        """Read one prefixed field, returning None for missing values."""
        col = f"{model_prefix}_{field_name}"
        if col not in row:
            return None
        value = row[col]
        return None if is_missing_value(value) else value

    # LOGIC 1: Depression
    if get_value('depression_status') == 'aktuell' and get_value('depression_schweregrad') == 'schwer':
        severity_context = parse_list_from_string(get_value('depression_schweregrad_nennung_kontext'))
        weak_contexts_enum = ["Neuropsychiatrisches Interview (NPI-Q)", "Patient Health Questionaire (PHQ)"]
        is_severity_context_weak = severity_context and all(item in weak_contexts_enum for item in severity_context)
        
        if is_severity_context_weak:
            reasons_potentially_eligible.append("Depression: Aktuelle schwere Episode (schwacher Kontext)")
        else:
            reasons_not_eligible.append("Depression: Aktuelle schwere Episode (starker Kontext)")

    # LOGIC 2: Not Eligible
    aetiologie_list = parse_list_from_string(get_value('kognitive_stoerung_aetiologie'))
    if aetiologie_list:
        bad = [a for a in aetiologie_list if fix_and_normalize_string(a) != norm_alzheimer and fix_and_normalize_string(a) not in norm_allowed_aetiologies]
        if bad: reasons_not_eligible.append(f"Ätiologie: Unzulässig ({bad})")

    def check_disallowed(field, allowed, label):
        """Add an ineligibility reason for values outside an allowed set."""
        items = parse_list_from_string(get_value(field))
        bad = [i for i in items if fix_and_normalize_string(i) not in allowed]
        if bad: reasons_not_eligible.append(f"{label}: Unzulässig ({bad})")

    check_disallowed('immunologische_erkrankung', norm_allowed_immuno, "Immunerkrankung")
    check_disallowed('gerinnungsstoerung', norm_allowed_coagulation, "Gerinnungsstörung")
    check_disallowed('immunosuppression', norm_allowed_immunosupp, "Immunsuppression")
    check_disallowed('antikoagulation', norm_allowed_anticoag, "Antikoagulation")

    if get_value('kognitive_stoerung_praesenz') == 'nein': reasons_not_eligible.append("Kognition: Störung verneint")
    if get_value('kognitive_stoerung_schweregrad') in ['mittel', 'schwer']: reasons_not_eligible.append(f"Kognition: Schweregrad '{get_value('kognitive_stoerung_schweregrad')}'")
    if get_value('pathologische_amyloid_biomarker') == 'nein': reasons_not_eligible.append("Amyloid: Negativ")
    
    mmse = get_value('mini_mental_status_test_ergebnis')
    if isinstance(mmse, (int, float)) and mmse != -1 and mmse < 22: reasons_not_eligible.append(f"MMSE: Score {mmse} (< 22)")
    
    mrt_map = {'MRT_haemorrhagie': 'Hämorrhagie', 'MRT_siderose': 'Siderose', 'MRT_ischaemie': 'Ischämie', 'MRT_fazekas': 'Fazekas 3', 'MRT_cerebrale_amyloidangiopathie': 'CAA'}
    for k, v in mrt_map.items():
        if get_value(k) == 'ja': reasons_not_eligible.append(f"MRT: {v}")
    
    if get_value('krankengeschichte_schlaganfall') == 'ja': reasons_not_eligible.append("Historie: Schlaganfall")
    if get_value('krankengeschichte_epileptischer_anfall') == 'ja': reasons_not_eligible.append("Historie: Epilepsie")

    if reasons_not_eligible:
        return {'class': 'not eligible', 'reasons': sorted(list(set(reasons_not_eligible)))}

    # LOGIC 3: Potentially Eligible
    missing_map = {
        'kognitive_stoerung_praesenz': "Kognition: Präsenz fehlt",
        'kognitive_stoerung_schweregrad': "Kognition: Schweregrad fehlt",
        'pathologische_amyloid_biomarker': "Amyloid: Status fehlt",
    }
    for k, v in missing_map.items():
        if get_value(k) in ['fehlt', 'nein', -1]: reasons_potentially_eligible.append(v)

    mrt_status = get_value('MRT_gehirn_untersuchung_erhalten')
    if mrt_status == 'fehlt':
        reasons_potentially_eligible.append("MRT: Fehlt")
    elif mrt_status == 'nein':
        reasons_potentially_eligible.append("MRT: Nicht erhalten")
    
    if not aetiologie_list: reasons_potentially_eligible.append("Ätiologie: Fehlt")
    elif not any(fix_and_normalize_string(a) == norm_alzheimer for a in aetiologie_list): reasons_potentially_eligible.append("Ätiologie: Alzheimer nicht genannt")
    if get_value('mini_mental_status_test_ergebnis') == -1: reasons_potentially_eligible.append("MMSE: Fehlt")

    if reasons_potentially_eligible:
        return {'class': 'potentially eligible', 'reasons': sorted(list(set(reasons_potentially_eligible)))}

    return {'class': 'eligible', 'reasons': ["Alle Kriterien erfüllt."]}

