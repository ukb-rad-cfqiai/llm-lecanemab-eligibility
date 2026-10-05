"""Extract structured findings from clinical letters with deterministic rules."""

import re

from .patterns import (
    ANTICOAGULATION_PATTERNS,
    IMMUNOSUPPRESSION_PATTERNS,
    IMMUNOLOGICAL_DISEASE_PATTERNS,
    COAGULATION_DISORDER_PATTERNS,
    THROMBOCYTE_DISORDER_PATTERNS,
    AETIOLOGY_PATTERNS,
    COGNITIVE_DISORDER_PATTERNS,
    COGNITIVE_NO_DISORDER_PATTERNS,
    MMSE_PATTERNS,
    MRT_PATTERNS,
    MRT_NOT_DONE_PATTERNS,
    MRI_EXCLUSION_PATTERNS,
    STROKE_PATTERNS,
    SEIZURE_PATTERNS,
    DEPRESSION_PATTERNS,
    SEVERE_DEPRESSION_PATTERNS,
    CURRENT_DEPRESSION_PATTERNS,
    REMITTED_DEPRESSION_PATTERNS,
    ABETA_42_PATTERN,
    ABETA_40_PATTERN,
    ABETA_RATIO_PATTERN,
    AMYLOID_POSITIVE_PATTERNS,
    AMYLOID_NEGATIVE_PATTERNS,
    AMYLOID_RATIO_MENTION_PATTERNS,
    NEGATION_RE,
    POST_CONCEPT_NEGATION_RE,
    FAMILY_CONTEXT_RE,
    MILD_SEVERITY_RE,
    SEVERE_SEVERITY_RE,
    QUESTIONNAIRE_CONTEXT_RE,
)


def normalize_text_for_regex(text):
    """Normalize whitespace and Unicode variants before regex matching."""
    if not isinstance(text, str):
        return ""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[\u00a0\u2007\u202f]', ' ', text)
    text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
    text = re.sub(r'[\u2010-\u2015\u2212]', '-', text)
    return text

def make_context(text, start, end, window=70):
    """Return a compact text window around a matched span."""
    snippet = text[max(0, start - window):min(len(text), end + window)]
    return re.sub(r'\s+', ' ', snippet).strip()

def is_negated(text, start, end, before_window=80, after_window=35):
    """Check for negation immediately before or after a match."""
    before = text[max(0, start - before_window):start]
    after = text[end:min(len(text), end + max(after_window, 110))]

    before_segment = re.split(r'[.;:\n]', before)[-1]
    after_segment = re.split(r'[.;:\n]', after)[0]
    after_negation_re = re.compile(
        r'^\W*(?:kein(?:e|en|er|es)?|nicht|negativ|ausgeschlossen|verneint|unauff[äa]llig)\b',
        flags=re.IGNORECASE,
    )

    return bool(
        NEGATION_RE.search(before_segment)
        or after_negation_re.search(after_segment)
        or POST_CONCEPT_NEGATION_RE.search(after_segment)
    )

def is_family_context(text, start, end, before_window=120, after_window=45):
    """Check whether a match refers to family history."""
    context = text[max(0, start - before_window):min(len(text), end + after_window)]
    return bool(FAMILY_CONTEXT_RE.search(context))

def is_questionnaire_context(text, start, end, before_window=120, after_window=60):
    """Check whether a match comes from questionnaire context."""
    context = text[max(0, start - before_window):min(len(text), end + after_window)]
    return bool(QUESTIONNAIRE_CONTEXT_RE.search(context))

def find_pattern_matches(text, patterns, skip_negated=True, first_per_label=True, skip_family=True):
    """Find labeled regex matches after contextual filtering."""
    text = normalize_text_for_regex(text)
    matches = []
    seen_labels = set()

    for label, pattern in patterns:
        if first_per_label and label in seen_labels:
            continue
        for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.DOTALL):
            if skip_negated and is_negated(text, match.start(), match.end()):
                continue
            if skip_family and is_family_context(text, match.start(), match.end()):
                continue
            matches.append({
                'label': label,
                'match': match.group(0),
                'context': make_context(text, match.start(), match.end()),
                'start': match.start(),
                'end': match.end(),
            })
            seen_labels.add(label)
            if first_per_label:
                break

    return matches

def values_from_matches(matches):
    """Return unique labels in match order."""
    values = []
    for match in matches:
        label = match['label']
        if label not in values:
            values.append(label)
    return values

def dedupe_matches_by_label(matches):
    """Keep only the first match for each label."""
    deduped = []
    seen = set()
    for match in matches:
        label = match['label']
        if label in seen:
            continue
        deduped.append(match)
        seen.add(label)
    return deduped

def remove_matches_inside_absence(matches, absence_matches):
    """Discard matches contained in explicit absence spans."""
    filtered = []
    for match in matches:
        inside_absence = any(
            absence['start'] <= match['start'] and match['end'] <= absence['end']
            for absence in absence_matches
        )
        if not inside_absence:
            filtered.append(match)
    return filtered

def without_questionnaire_context(report, matches):
    """Remove matches attributed to questionnaire text."""
    filtered = []
    for match in matches:
        start = match.get('start')
        end = match.get('end')
        if start is None or end is None:
            start = report.find(match.get('match', ''))
            end = start + len(match.get('match', '')) if start >= 0 else start
        if start >= 0 and is_questionnaire_context(report, start, end):
            continue
        filtered.append(match)
    return filtered

def summarize_rule_based_trace(trace):
    """Summarize matched labels and counts for each feature."""
    summary = {}
    for field, matches in trace.items():
        labels = values_from_matches(matches)
        summary[field] = {
            'matched_labels': labels,
            'match_count': len(matches),
        }
    return summary

def extract_medication_section(report):
    """Extract medication sections from a clinical report."""
    report = normalize_text_for_regex(report)
    if not report:
        return ""

    start_re = re.compile(
        r'(?im)^\s*(?:aktuelle\s+|derzeitige\s+|dauer\s*)?'
        r'(?:medikation|medikamente|arzneimittel(?:therapie)?)\b\s*:?',
    )
    starts = list(start_re.finditer(report))
    if not starts:
        starts = list(re.finditer(
            r'(?i)(?:aktuelle\s+|derzeitige\s+|dauer\s*)?'
            r'(?:medikation|medikamente|arzneimittel(?:therapie)?)\s*:',
            report,
        ))

    if not starts:
        return ""

    sections = []
    heading_re = re.compile(r'(?m)^\s*[A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9 /().,-]{2,60}:\s*$')
    for start_match in starts:
        start = start_match.start()
        search_from = min(len(report), start_match.end() + 20)
        next_heading = heading_re.search(report, search_from)
        end = next_heading.start() if next_heading else min(len(report), start + 1500)
        sections.append(report[start:end])

    return "\n".join(sections)

def extract_medication_term_matches(report, medication_text, patterns):
    """Match medication terms in sections and the full report."""
    medication_matches = find_pattern_matches(
        medication_text,
        patterns,
        skip_family=False,
    )
    report_matches = find_pattern_matches(report, patterns)
    return dedupe_matches_by_label(medication_matches + report_matches)

def extract_anticoagulation_matches(report, medication_text):
    """Find anticoagulant mentions in medication text and the report."""
    return extract_medication_term_matches(report, medication_text, ANTICOAGULATION_PATTERNS)

def extract_coagulation_disorder_matches(report):
    """Find coagulation disorders and classify platelet severity."""
    matches = find_pattern_matches(report, COAGULATION_DISORDER_PATTERNS)

    for disorder_name, pattern in THROMBOCYTE_DISORDER_PATTERNS:
        for match in re.finditer(pattern, report, flags=re.IGNORECASE | re.DOTALL):
            if is_negated(report, match.start(), match.end()):
                continue
            if is_family_context(report, match.start(), match.end()):
                continue

            context = make_context(report, match.start(), match.end(), window=55)
            if disorder_name == 'Thrombozytopenie':
                label = 'Thrombozytopenie (leicht)' if MILD_SEVERITY_RE.search(context) else 'Thrombozytopenie (schwer)'
            else:
                label = 'Thrombozythaemie (leicht)' if MILD_SEVERITY_RE.search(context) else 'Thrombozythämie (schwer)'

            if SEVERE_SEVERITY_RE.search(context):
                label = 'Thrombozytopenie (schwer)' if disorder_name == 'Thrombozytopenie' else 'Thrombozythämie (schwer)'

            matches.append({
                'label': label,
                'match': match.group(0),
                'context': context,
            })

    return dedupe_matches_by_label(matches)

def parse_decimal_number(value):
    """Parse a decimal value using either comma or period."""
    try:
        return float(value.replace(',', '.'))
    except (AttributeError, ValueError):
        return None

def parse_laboratory_number(value):
    """Parse a laboratory value with optional thousands separators."""
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if re.fullmatch(r'[1-9]\d{0,2}\.\d{3}(?:,\d+)?', cleaned):
        cleaned = cleaned.replace('.', '').replace(',', '.')
    else:
        cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None

def amyloid_match_modality(match):
    """Identify the biomarker modality of an amyloid match."""
    label = match.get('label', '')
    if 'PET' in label:
        return 'pet'
    if 'CSF-Aß42' in label:
        return 'csf_abeta42'
    if 'Quotient' in label:
        return 'ratio'
    return 'generic'

def extract_amyloid_status(report):
    """Determine amyloid status from textual and numeric evidence."""
    amyloid_positive = find_pattern_matches(report, AMYLOID_POSITIVE_PATTERNS)
    amyloid_negative = find_pattern_matches(report, AMYLOID_NEGATIVE_PATTERNS, skip_negated=False)

    numeric_matches = []
    ratio_numeric_patterns = [
        r'\b(?:amyloid[-\s]?(?:quotient|ratio)|amyloidquotient|amyloidratio|quotient\s+a\s*(?:β|ß|beta)?\s*(?:1[-\s]?)?42\s*/\s*(?:a\s*(?:β|ß|beta)?\s*)?(?:1[-\s]?)?40|a\s*(?:β|ß|beta)?\s*(?:1[-\s]?)?42\s*/\s*(?:a\s*(?:β|ß|beta)?\s*)?(?:1[-\s]?)?40)\b.{0,35}?([01][,.]\d{2,3})',
        r'\b([01][,.]\d{2,3})\b.{0,35}\b(?:amyloid[-\s]?(?:quotient|ratio)|amyloidquotient|amyloidratio|a\s*(?:β|ß|beta)?\s*(?:1[-\s]?)?42\s*/\s*(?:a\s*(?:β|ß|beta)?\s*)?(?:1[-\s]?)?40)\b',
    ]
    for pattern in ratio_numeric_patterns:
        for match in re.finditer(pattern, report, flags=re.IGNORECASE | re.DOTALL):
            value = parse_decimal_number(match.group(1))
            if value is None:
                continue
            is_positive = value <= 0.095
            numeric_matches.append({
                'label': 'Amyloid-Quotient numerisch pathologisch' if is_positive else 'Amyloid-Quotient numerisch negativ',
                'match': match.group(0),
                'context': make_context(report, match.start(), match.end()),
                'value': value,
                'positive': is_positive,
                'modality': 'ratio',
                'start': match.start(),
                'end': match.end(),
            })

    abeta42_numeric_value_pattern = r'([1-9]\d{0,3}(?:[,.]\d+)?|0(?:[,.]\d+)?)'
    abeta42_numeric_patterns = [
        rf'\b{ABETA_42_PATTERN}\b(?!\s*(?:/|zu|:|-)\s*{ABETA_40_PATTERN})[^\d]{{0,40}}\b{abeta42_numeric_value_pattern}\b',
        rf'\b{abeta42_numeric_value_pattern}\b[^\d]{{0,40}}\b{ABETA_42_PATTERN}\b(?!\s*(?:/|zu|:|-)\s*{ABETA_40_PATTERN})',
    ]
    abeta42_ratio_context_re = re.compile(
        rf'(?:{ABETA_RATIO_PATTERN}|amyloid[-\s]?(?:quotient|ratio)|amyloidquotient|amyloidratio|\bquotient\b|\bratio\b)',
        flags=re.IGNORECASE,
    )
    for pattern in abeta42_numeric_patterns:
        for match in re.finditer(pattern, report, flags=re.IGNORECASE | re.DOTALL):
            context = make_context(report, match.start(), match.end(), window=60)
            if abeta42_ratio_context_re.search(match.group(0)):
                continue
            value = parse_laboratory_number(match.group(1))
            if value is None:
                continue
            is_positive = 0 <= value < 630
            numeric_matches.append({
                'label': 'CSF-Aß42 numerisch pathologisch' if is_positive else 'CSF-Aß42 numerisch negativ',
                'match': match.group(0),
                'context': context,
                'value': value,
                'positive': is_positive,
                'modality': 'csf_abeta42',
                'start': match.start(),
                'end': match.end(),
            })

    amyloid_numeric_context_re = re.compile(
        r'(?:amyloid[-\s]?(?:quotient|ratio)|amyloidquotient|amyloidratio|quotient|ratio|(?:1[-\s]?)?42\s*/\s*(?:1[-\s]?)?40)',
        flags=re.IGNORECASE,
    )
    for match in re.finditer(r'\b([01][,.]\d{2,3})\b', report, flags=re.IGNORECASE):
        context = make_context(report, match.start(), match.end(), window=80)
        if not amyloid_numeric_context_re.search(context):
            continue
        value = parse_decimal_number(match.group(1))
        if value is None:
            continue
        is_positive = value <= 0.095
        numeric_matches.append({
            'label': 'Amyloid-Quotient numerisch pathologisch' if is_positive else 'Amyloid-Quotient numerisch negativ',
            'match': match.group(0),
            'context': context,
            'value': value,
            'positive': is_positive,
            'modality': 'ratio',
            'start': match.start(),
            'end': match.end(),
        })

    if numeric_matches:
        numeric_matches.sort(key=lambda item: item.get('start', 10**9))
        positive_numeric_matches = [item for item in numeric_matches if item.get('positive')]
        if positive_numeric_matches:
            return 'ja', positive_numeric_matches

    if amyloid_positive:
        negative_numeric_modalities = {
            item.get('modality') for item in numeric_matches if not item.get('positive')
        }
        independent_positive_matches = [
            item for item in amyloid_positive
            if amyloid_match_modality(item) in {'pet', 'generic'}
            or amyloid_match_modality(item) not in negative_numeric_modalities
        ]
        if independent_positive_matches:
            return 'ja', independent_positive_matches

    if numeric_matches:
        return 'nein', numeric_matches

    if amyloid_positive:
        return 'ja', amyloid_positive
    if amyloid_negative:
        return 'nein', amyloid_negative

    amyloid_ratio = find_pattern_matches(report, AMYLOID_RATIO_MENTION_PATTERNS)
    if amyloid_ratio:
        return 'ja', amyloid_ratio

    return 'fehlt', []

def extract_mmse(report):
    """Extract the last valid MMSE score and its supporting matches."""
    report = normalize_text_for_regex(report)
    matches = []
    for pattern in MMSE_PATTERNS:
        for match in re.finditer(pattern, report, flags=re.IGNORECASE | re.DOTALL):
            if is_negated(report, match.start(), match.end()):
                continue
            try:
                score = int(match.group(1))
            except (TypeError, ValueError):
                continue
            if 0 <= score <= 30:
                matches.append({
                    'label': str(score),
                    'match': match.group(0),
                    'context': make_context(report, match.start(), match.end()),
                    'score': score,
                    'start': match.start(),
                })

    if not matches:
        return -1, []

    matches.sort(key=lambda item: item['start'])
    return matches[-1]['score'], matches

def get_cognitive_severity(report):
    """Determine the strongest stated cognitive impairment severity."""
    severe = find_pattern_matches(report, [
        ('schwer', r'\b(?:schwere?|schwergradige?)\b.{0,35}\b(?:demenz|alzheimer|kognitive?\s+st[öo]rung|kognitive?\s+einschr[äa]nkung)\b'),
        ('schwer', r'\b(?:demenz|alzheimer|kognitive?\s+st[öo]rung|kognitive?\s+einschr[äa]nkung)\b.{0,35}\b(?:schwer|schwergradig)\b'),
    ])
    if severe:
        return 'schwer', severe

    moderate = find_pattern_matches(report, [
        ('mittel', r'\b(?:mittelgradige?|moderate?|mittelschwere?)\b.{0,35}\b(?:demenz|alzheimer|kognitive?\s+st[öo]rung|kognitive?\s+einschr[äa]nkung)\b'),
        ('mittel', r'\b(?:demenz|alzheimer|kognitive?\s+st[öo]rung|kognitive?\s+einschr[äa]nkung)\b.{0,35}\b(?:mittelgradig|moderat|mittelschwer)\b'),
    ])
    if moderate:
        return 'mittel', moderate

    mild = find_pattern_matches(report, [
        ('leicht', r'\b(?:leichte?|leichtgradige?)\b.{0,35}\b(?:demenz|alzheimer|kognitive?\s+st[öo]rung|kognitive?\s+einschr[äa]nkung)\b'),
        ('leicht', r'\b(?:demenz|alzheimer|kognitive?\s+st[öo]rung|kognitive?\s+einschr[äa]nkung)\b.{0,35}\b(?:leicht|leichtgradig)\b'),
        ('leicht', r'\b(?:beginnend(?:e|er|en)?|fr[üu]h(?:e|er|en)?|prodromal(?:e|er|en)?|incipient)\b.{0,35}\b(?:demenz|alzheimer|kognitive?\s+st[öo]rung|kognitive?\s+einschr[äa]nkung)\b'),
        ('leicht', r'\b(?:demenz|alzheimer|kognitive?\s+st[öo]rung|kognitive?\s+einschr[äa]nkung)\b.{0,35}\b(?:beginnend|fr[üu]h|prodromal|incipient)\b'),
        ('leicht', r'\b(?:mci|mild\s+cognitive\s+impairment)\b'),
    ])
    if mild:
        return 'leicht', mild

    return 'fehlt', []

def default_rule_based_features():
    """Return default values for every rule-based feature."""
    return {
        'kognitive_stoerung_praesenz': 'fehlt',
        'kognitive_stoerung_schweregrad': 'fehlt',
        'kognitive_stoerung_aetiologie': [],
        'pathologische_amyloid_biomarker': 'fehlt',
        'mini_mental_status_test_ergebnis': -1,
        'krankengeschichte_schlaganfall': 'fehlt',
        'krankengeschichte_epileptischer_anfall': 'fehlt',
        'depression': 'fehlt',
        'depression_diagnose_nennung_kontext': [],
        'depression_schweregrad': 'fehlt',
        'depression_schweregrad_nennung_kontext': [],
        'depression_status': 'fehlt',
        'MRT_gehirn_untersuchung_erhalten': 'fehlt',
        'MRT_gehirn_befund_vorliegend': 'fehlt',
        'MRT_haemorrhagie': 'fehlt',
        'MRT_siderose': 'fehlt',
        'MRT_ischaemie': 'fehlt',
        'MRT_fazekas': 'fehlt',
        'MRT_cerebrale_amyloidangiopathie': 'fehlt',
        'MRT_erwaehnung_anderer_ursachen_fuer_demenz': 'fehlt',
        'immunologische_erkrankung': [],
        'gerinnungsstoerung': [],
        'immunosuppression': [],
        'antikoagulation': [],
    }

def extract_rule_based_features(report):
    """Extract structured features and supporting matches from a report."""
    report = normalize_text_for_regex(report)
    medication_text = extract_medication_section(report)
    features = default_rule_based_features()
    trace = {}

    def set_trace(field, matches):
        """Store supporting matches for a feature when present."""
        if matches:
            trace[field] = matches

    no_cognition = find_pattern_matches(report, COGNITIVE_NO_DISORDER_PATTERNS, skip_negated=False)
    cognition = find_pattern_matches(report, COGNITIVE_DISORDER_PATTERNS)
    if no_cognition:
        features['kognitive_stoerung_praesenz'] = 'nein'
        set_trace('kognitive_stoerung_praesenz', no_cognition)
    elif cognition:
        features['kognitive_stoerung_praesenz'] = 'ja'
        set_trace('kognitive_stoerung_praesenz', cognition)

    severity, severity_matches = get_cognitive_severity(report)
    features['kognitive_stoerung_schweregrad'] = severity
    set_trace('kognitive_stoerung_schweregrad', severity_matches)

    aetiology_matches = find_pattern_matches(report, AETIOLOGY_PATTERNS)
    features['kognitive_stoerung_aetiologie'] = values_from_matches(aetiology_matches)
    set_trace('kognitive_stoerung_aetiologie', aetiology_matches)

    amyloid_status, amyloid_matches = extract_amyloid_status(report)
    features['pathologische_amyloid_biomarker'] = amyloid_status
    set_trace('pathologische_amyloid_biomarker', amyloid_matches)

    mmse, mmse_matches = extract_mmse(report)
    features['mini_mental_status_test_ergebnis'] = mmse
    set_trace('mini_mental_status_test_ergebnis', mmse_matches)

    mrt_not_done = find_pattern_matches(report, MRT_NOT_DONE_PATTERNS, skip_negated=False)
    mrt_present = find_pattern_matches(report, MRT_PATTERNS, skip_negated=False, first_per_label=False)
    mrt_present = remove_matches_inside_absence(mrt_present, mrt_not_done)
    if mrt_present:
        features['MRT_gehirn_untersuchung_erhalten'] = 'ja'
        features['MRT_gehirn_befund_vorliegend'] = 'ja'
        set_trace('MRT_gehirn_untersuchung_erhalten', mrt_present)
    elif mrt_not_done:
        features['MRT_gehirn_untersuchung_erhalten'] = 'nein'
        features['MRT_gehirn_befund_vorliegend'] = 'nein'
        set_trace('MRT_gehirn_untersuchung_erhalten', mrt_not_done)

    for field, patterns in MRI_EXCLUSION_PATTERNS.items():
        matches = find_pattern_matches(report, patterns)
        if matches:
            features[field] = 'ja'
            set_trace(field, matches)

    stroke_matches = find_pattern_matches(report, STROKE_PATTERNS)
    if stroke_matches:
        features['krankengeschichte_schlaganfall'] = 'ja'
        set_trace('krankengeschichte_schlaganfall', stroke_matches)

    seizure_matches = find_pattern_matches(report, SEIZURE_PATTERNS)
    if seizure_matches:
        features['krankengeschichte_epileptischer_anfall'] = 'ja'
        set_trace('krankengeschichte_epileptischer_anfall', seizure_matches)

    depression_matches = without_questionnaire_context(report, find_pattern_matches(report, DEPRESSION_PATTERNS))
    if depression_matches:
        features['depression'] = 'ja'
        features['depression_diagnose_nennung_kontext'] = ['Explizite aerztliche Nennung einer gesicherten Diagnose']
        set_trace('depression', depression_matches)

    severe_depression = without_questionnaire_context(report, find_pattern_matches(report, SEVERE_DEPRESSION_PATTERNS))
    if severe_depression:
        features['depression_schweregrad'] = 'schwer'
        features['depression_schweregrad_nennung_kontext'] = ['Anderer Kontext']
        set_trace('depression_schweregrad', severe_depression)

    current_depression = without_questionnaire_context(report, find_pattern_matches(report, CURRENT_DEPRESSION_PATTERNS))
    remitted_depression = without_questionnaire_context(
        report,
        find_pattern_matches(report, REMITTED_DEPRESSION_PATTERNS, skip_negated=False)
    )
    if current_depression:
        features['depression_status'] = 'aktuell'
        set_trace('depression_status', current_depression)
    elif remitted_depression:
        features['depression_status'] = 'remittiert'
        set_trace('depression_status', remitted_depression)
    elif depression_matches:
        features['depression_status'] = 'aktuell'

    immunological_matches = find_pattern_matches(report, IMMUNOLOGICAL_DISEASE_PATTERNS)
    features['immunologische_erkrankung'] = values_from_matches(immunological_matches)
    set_trace('immunologische_erkrankung', immunological_matches)

    coagulation_matches = extract_coagulation_disorder_matches(report)
    features['gerinnungsstoerung'] = values_from_matches(coagulation_matches)
    set_trace('gerinnungsstoerung', coagulation_matches)

    immunosuppression_matches = extract_medication_term_matches(report, medication_text, IMMUNOSUPPRESSION_PATTERNS)
    features['immunosuppression'] = values_from_matches(immunosuppression_matches)
    set_trace('immunosuppression', immunosuppression_matches)

    anticoagulation_matches = extract_anticoagulation_matches(report, medication_text)
    features['antikoagulation'] = values_from_matches(anticoagulation_matches)
    set_trace('antikoagulation', anticoagulation_matches)

    return features, trace
