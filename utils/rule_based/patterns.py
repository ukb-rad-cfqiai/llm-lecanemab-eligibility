"""Fields and patterns used by the deterministic clinical letter extractor."""

import re


RULE_BASED_FEATURE_FIELDS = [
    'kognitive_stoerung_praesenz',
    'kognitive_stoerung_schweregrad',
    'kognitive_stoerung_aetiologie',
    'pathologische_amyloid_biomarker',
    'mini_mental_status_test_ergebnis',
    'krankengeschichte_schlaganfall',
    'krankengeschichte_epileptischer_anfall',
    'depression',
    'depression_diagnose_nennung_kontext',
    'depression_schweregrad',
    'depression_schweregrad_nennung_kontext',
    'depression_status',
    'MRT_gehirn_untersuchung_erhalten',
    'MRT_gehirn_befund_vorliegend',
    'MRT_haemorrhagie',
    'MRT_siderose',
    'MRT_ischaemie',
    'MRT_fazekas',
    'MRT_cerebrale_amyloidangiopathie',
    'MRT_erwaehnung_anderer_ursachen_fuer_demenz',
    'immunologische_erkrankung',
    'gerinnungsstoerung',
    'immunosuppression',
    'antikoagulation',
]

ANTICOAGULATION_PATTERNS = [
    ('Marcumar (Phenprocoumon)', r'\b(?:marcumar|phenprocoumon|phenprokumon)\b'),
    ('Warfarin', r'\bwarfarin\b'),
    ('Eliquis (Apixaban)', r'\b(?:eliquis|apixaban)\b'),
    ('Xarelto (Rivaroxaban)', r'\b(?:xarelto|rivaroxaban)\b'),
    ('Lixiana (Edoxaban)', r'\b(?:lixiana|edoxaban)\b'),
    ('Pradaxa (Dabigatran)', r'\b(?:pradaxa|dabigatran)\b'),
    ('Heparin', r'\bheparin(?:isierung)?\b'),
    ('Clexane (Enoxaparin)', r'\b(?:clexane|enoxaparin)\b'),
    ('Dalteparin', r'\b(?:fragmin|dalteparin)\b'),
    ('Nadroparin', r'\b(?:fraxiparin|nadroparin)\b'),
    ('Tinzaparin', r'\b(?:innohep|tinzaparin)\b'),
    ('Fondaparinux', r'\b(?:arixtra|fondaparinux)\b'),
    ('Argatroban', r'\bargatroban\b'),
    ('Bivalirudin', r'\bbivalirudin\b'),
    ('orale Antikoagulation', r'\b(?:doak|noak|oak|orale?\s+antikoagulation|antikoagulanzien|antikoagulantien)\b'),
]

IMMUNOSUPPRESSION_PATTERNS = [
    ('Methotrexat (MTX)', r'\b(?:methotrexat|mtx)\b'),
    ('Cortison', r'\b(?:corti(?:son|coid|kosteroid)|korti(?:son|koid|kosteroid))e?n?\b'),
    ('Prednisolon', r'\bprednisolon\b'),
    ('Methylprednisolon', r'\bmethylprednisolon\b'),
    ('Prednison', r'\bprednison\b'),
    ('Dexamethason', r'\bdexamethason\b'),
    ('Azathioprin (AZA)', r'\b(?:azathioprin|aza)\b'),
    ('Cyclosporin (CSA)', r'\b(?:cyclosporin|ciclosporin|csa)\b'),
    ('Tacrolimus', r'\btacrolimus\b'),
    ('Mycophenolatmofetil (MMF)', r'\b(?:mycophenolat|mycophenolatmofetil|mmf)\b'),
    ('Infliximab', r'\binfliximab\b'),
    ('Adalimumab', r'\badalimumab\b'),
    ('Etanercept', r'\betanercept\b'),
    ('Rituximab', r'\brituximab\b'),
    ('Cyclophosphamid (CTX)', r'\b(?:cyclophosphamid|ctx)\b'),
    ('Systemische Glukokortikoide', r'\bsystemische?\s+glukokortikoid(?:e|en)?\b'),
]

IMMUNOLOGICAL_DISEASE_PATTERNS = [
    ('Morbus Bechterew (M. Bechterew)', r'\b(?:morbus\s+bechterew|m\.\s*bechterew|spondylitis\s+ankylosans)\b'),
    ('Morbus Crohn (M. Crohn)', r'\b(?:morbus\s+crohn|m\.\s*crohn)\b'),
    ('Colitis ulcerosa (CU)', r'\b(?:colitis\s+ulcerosa|cu)\b'),
    ('Psoriasis-Arthritis (PsA)', r'\b(?:psoriasis[-\s]?arthritis|psa)\b'),
    ('Rheumatoide Arthritis (RA)', r'\b(?:rheumatoide\s+arthritis|chronische\s+polyarthritis|cP|ra)\b'),
    ('Systemischer Lupus erythematodes (SLE)', r'\b(?:systemischer\s+lupus|lupus\s+erythematodes|sle)\b'),
    ('Multiple Sklerose (MS)', r'\bmultiple\s+sklerose\b'),
    ('Sjoegren-Syndrom', r'\b(?:sjögren|sjoegren)[-\s]?syndrom\b'),
    ('Sklerodermie', r'\bsklerodermie\b'),
    ('Vaskulitis', r'\bvaskulitis\b'),
    ('Autoimmunhepatitis (AIH)', r'\b(?:autoimmunhepatitis|aih)\b'),
    ('Dermatomyositis', r'\bdermatomyositis\b'),
    ('Mischkollagenose', r'\bmischkollagenose\b'),
]

COAGULATION_DISORDER_PATTERNS = [
    ('Thrombophilie', r'\bthrombophilie\b'),
    ('Hämophilie A', r'\bh[äa]mophilie\s+a\b'),
    ('Hämophilie B', r'\bh[äa]mophilie\s+b\b'),
    ('Von-Willebrand-Syndrom (VWS)', r'\b(?:von[-\s]?willebrand|vws)\b'),
    ('Faktor-V-Leiden-Mutation (FVL)', r'\b(?:faktor[-\s]?v[-\s]?leiden|fvl)\b'),
    ('Protein-C-Mangel', r'\bprotein[-\s]?c[-\s]?mangel\b'),
    ('Antiphospholipid-Syndrom (APS)', r'\b(?:antiphospholipid[-\s]?syndrom|aps)\b'),
    ('Disseminierte intravasale Gerinnung (DIC)', r'\b(?:disseminierte\s+intravasale\s+gerinnung|dic)\b'),
]

THROMBOCYTE_DISORDER_PATTERNS = [
    ('Thrombozytopenie', r'\bthrombozytopenie\b'),
    ('Thrombozythaemie', r'\bthrombozyth[äa]mie\b'),
]

AETIOLOGY_PATTERNS = [
    ('Alzheimer-Krankheit', r'\balzheimer(?:[-\s]?(?:krankheit|demenz|typ))?\b|\balzheimertyp\b'),
    ('Lewy-Koerperchen Demenz', r'\blewy(?:[-\s]?k[öo]rperchen)?(?:[-\s]?demenz)?\b'),
    ('Lewy Body Krankheit (LBD)', r'\blewy\s+body\b|\blbd\b'),
    ('Frontotemporale Demenz (FTD)', r'\bfrontotemporal(?:e|er|en)?\s+demenz\b'),
    ('Parkinson-Krankheit', r'\bparkinson\b'),
    ('vaskulaere Demenz', r'\bvaskul[äa]re?\s+demenz\b'),
    ('cerebrale Mikroangiopathie', r'\b(?:cerebrale|zerebrale)?\s*mikroangiopathie\b'),
    ('Normaldruckhydrocephalus (NPH)', r'\b(?:normaldruckhydrocephalus|normaldruckhydrozephalus|nph)\b'),
    ('Tumor', r'\b(?:hirntumor|tumor|neoplasie|raumforderung)\b'),
]

COGNITIVE_DISORDER_PATTERNS = [
    ('kognitive Störung', r'\bkognitive?\s+(?:st[öo]rung|einschr[äa]nkung|defizit(?:e)?)\b'),
    ('Demenz', r'\bdemenz(?:iell|syndrom)?\b'),
    ('MCI', r'\b(?:mci|mild\s+cognitive\s+impairment)\b'),
    ('Alzheimer-Krankheit', r'\balzheimer\b'),
]

COGNITIVE_NO_DISORDER_PATTERNS = [
    ('keine kognitive Störung', r'\bkeine?\s+kognitive?\s+(?:st[öo]rung|einschr[äa]nkung|defizit(?:e)?)\b'),
    ('keine Demenz', r'\bkeine?\s+demenz\b'),
]

MMSE_PATTERNS = [
    r'\b(?:mmse|mmst|mini[-\s]?mental(?:[-\s]?status)?(?:[-\s]?test)?)\b.{0,90}?\b([0-3]?\d)\s*(?:/|von)\s*30\s*(?:punkte?|pkt\.?|p\.?)?(?=\W|$)',
    r'\b([0-3]?\d)\s*(?:/|von)\s*30\s*(?:punkte?|pkt\.?|p\.?)?(?=\W|$).{0,90}?\b(?:mmse|mmst|mini[-\s]?mental)\b',
    r'\b(?:mmse|mmst|mini[-\s]?mental(?:[-\s]?status)?(?:[-\s]?test)?)\b.{0,90}?\b([0-2]?\d)\s*/\s*(?:28|29)\b',
    r'\b([0-2]?\d)\s*/\s*(?:28|29)\b.{0,90}?\b(?:mmse|mmst|mini[-\s]?mental)\b',
    r'\b(?:mmse|mmst|mini[-\s]?mental(?:[-\s]?status)?(?:[-\s]?test)?)\b.{0,40}?(?:[:=]|score|wert|ergebnis)\s*([0-3]?\d)\s*(?:punkte?|pkt\.?|p\.)\b',
    r'\b(?:mmse|mmst|mini[-\s]?mental(?:[-\s]?status)?(?:[-\s]?test)?)\s*[:=]\s*([0-3]?\d)(?:\s*[,.;)]|\s*$)',
]

MRT_TOKEN_PATTERN = r'(?:c\s*[-./]?\s*m\s*[-.]?\s*r\s*[-.]?\s*t|m\s*[-.]?\s*r\s*[-.]?\s*t|magnetresonanztomographie|kernspin(?:tomographie)?|sch[äa]del[-\s]?mrt|kopf[-\s]?mrt)'
MRT_BOUNDARY_PATTERN = rf'(?<![A-Za-zÄÖÜäöüß]){MRT_TOKEN_PATTERN}(?![A-Za-zÄÖÜäöüß])'

MRT_PATTERNS = [
    ('MRT', MRT_BOUNDARY_PATTERN),
]

MRT_NOT_DONE_PATTERNS = [
    ('MRT nicht durchgeführt', rf'\b(?:kein(?:e|en|er|es)?|ohne)\s+(?:(?:aktuell(?:e|es|en|er)?|vorliegend(?:e|es|en|er)?|durchgef[üu]hrt(?:e|es|en|er)?|angefertigt(?:e|es|en|er)?|verf[üu]gbar(?:e|es|en|er)?|zerebral(?:e|es|en|er)?|cerebral(?:e|es|en|er)?)\s+){{0,4}}{MRT_TOKEN_PATTERN}(?![A-Za-zÄÖÜäöüß])'),
    ('MRT ausstehend', rf'{MRT_BOUNDARY_PATTERN}.{{0,80}}\b(?:nicht\s+(?:durchgef[üu]hrt|erfolgt|angefertigt|vorliegend|verf[üu]gbar)|ausstehend|liegt\s+nicht\s+vor|befund\s+liegt\s+nicht\s+vor|kein(?:e[rsn]?)?\s+(?:befund|bericht)\s+(?:vorliegend|verf[üu]gbar))\b'),
]

MRI_EXCLUSION_PATTERNS = {
    'MRT_haemorrhagie': [
        ('Hämorrhagie', r'\b(?:h[äa]morrhagie|h[äa]morrhagisch(?:e|er|en|es)?|posth[äa]morrhagisch(?:e|er|en|es)?|posthaemorrhagisch(?:e|er|en|es)?|blutung(?:en)?|blutungsresid(?:uum|uen)|mikroblutung(?:en)?|microbleed(?:s)?)\b'),
    ],
    'MRT_siderose': [
        ('Siderose', r'\b(?:siderose|h[äa]mosiderin|haemosiderin)\b'),
    ],
    'MRT_ischaemie': [
        ('Ischämie', r'\b(?:isch[äa]mie|isch[äa]misch(?:e|er|en|es)?|postisch[äa]misch(?:e|er|en|es)?|infarkt(?:e|areal)?|lakun[äa]r|lakune(?:n)?)\b'),
    ],
    'MRT_fazekas': [
        ('Fazekas 3', r'\bfazekas\b.{0,20}\b(?:3|iii|grad\s*3|grad\s*iii)\b'),
    ],
    'MRT_cerebrale_amyloidangiopathie': [
        ('CAA', r'\b(?:cerebrale?\s+amyloidangiopathie|zerebrale?\s+amyloidangiopathie|amyloidangiopathie|caa)\b'),
    ],
}

STROKE_PATTERNS = [
    ('Schlaganfall', r'\b(?:schlaganfall|apoplex|hirninfarkt|zerebralinfarkt|cerebralinfarkt|stroke)\b'),
]

SEIZURE_PATTERNS = [
    ('Epilepsie', r'\b(?:epilepsie|epileptische?r?\s+anfall|krampfanfall|zerebraler\s+anfall)\b'),
]

DEPRESSION_PATTERNS = [
    ('Depression', r'\b(?:depression|depressiv\w*\s+episode|depressivit[äa]t)\b'),
]

SEVERE_DEPRESSION_PATTERNS = [
    ('schwere Depression', r'\b(?:schwer(?:e|er|en|es)?|schwergradig(?:e|er|en|es)?|major)\b.{0,30}\b(?:depression|depressiv\w*\s+episode)\b'),
    ('schwere Depression', r'\b(?:depression|depressiv\w*\s+episode)\b.{0,30}\b(?:schwer(?:e|er|en|es)?|schwergradig(?:e|er|en|es)?)\b'),
]

CURRENT_DEPRESSION_PATTERNS = [
    ('aktuelle Depression', r'\b(?:aktuell|derzeit|gegenw[äa]rtig|bestehend|aktive?)\b.{0,50}\b(?:depression|depressiv\w*\s+episode)\b'),
    ('aktuelle Depression', r'\b(?:depression|depressiv\w*\s+episode)\b.{0,50}\b(?:aktuell|derzeit|gegenw[äa]rtig|bestehend|aktive?)\b'),
]

REMITTED_DEPRESSION_PATTERNS = [
    ('remittierte Depression', r'\b(?:remittiert|remission|z\.?\s*n\.?|zustand\s+nach)\b.{0,50}\b(?:depression|depressiv\w*\s+episode)\b'),
    ('remittierte Depression', r'\b(?:depression|depressiv\w*\s+episode)\b.{0,50}\b(?:remittiert|remission)\b'),
]

AMYLOID_LOW_POSITIVE_TERMS_PATTERN = r'(?:positiv|pathologisch|erniedrigt|vermindert|reduziert|vereinbar|hinweisend|auff[äa]llig|abnorm)'
AMYLOID_PET_POSITIVE_TERMS_PATTERN = r'(?:positiv|pathologisch|erh[öo]ht|vermehrt|vereinbar|hinweisend|auff[äa]llig|abnorm)'
AMYLOID_NEGATIVE_TERMS_PATTERN = r'(?:negativ|unauff[äa]llig|normal|normwertig|nicht\s+pathologisch|nicht\s+auff[äa]llig|nicht\s+erniedrigt|im\s+normbereich|ohne\s+pathologischen?\s+befund)'
ABETA_PREFIX_PATTERN = r'(?:a\s*(?:β|ß|beta)?|abeta|amyloid[-\s]?(?:β|beta)|beta[-\s]?amyloid)'
ABETA_42_PATTERN = rf'(?:{ABETA_PREFIX_PATTERN}\s*(?:1[-\s]?)?42)'
ABETA_40_PATTERN = rf'(?:{ABETA_PREFIX_PATTERN}\s*(?:1[-\s]?)?40|(?:1[-\s]?)?40)'
ABETA_RATIO_PATTERN = rf'(?:{ABETA_42_PATTERN}\s*(?:/|zu|:|-)\s*{ABETA_40_PATTERN}|(?:42|1[-\s]?42)\s*(?:/|zu|:|-)\s*(?:40|1[-\s]?40))'
AMYLOID_PET_PATTERN = r'(?:amyloid[-\s]?pet|amyloid.{0,20}\bpet\b|\bpet\b.{0,20}\bamyloid)'
CSF_PATTERN = r'(?:liquor|csf|cerebrospinal(?:e|er|en|es)?\s+fluid|nervenwasser)'
AMYLOID_POSITIVE_PATTERNS = [
    ('pathologisches CSF-Aß42', rf'\b{CSF_PATTERN}\b.{{0,120}}\b{ABETA_42_PATTERN}\b.{{0,90}}\b{AMYLOID_LOW_POSITIVE_TERMS_PATTERN}\b'),
    ('pathologisches CSF-Aß42', rf'\b{ABETA_42_PATTERN}\b.{{0,90}}\b{AMYLOID_LOW_POSITIVE_TERMS_PATTERN}\b'),
    ('pathologisches CSF-Aß42', rf'\b{AMYLOID_LOW_POSITIVE_TERMS_PATTERN}\b.{{0,90}}\b{ABETA_42_PATTERN}\b'),
    ('pathologischer Amyloid-PET', rf'\b{AMYLOID_PET_PATTERN}\b.{{0,90}}\b{AMYLOID_PET_POSITIVE_TERMS_PATTERN}\b'),
    ('pathologischer Amyloid-PET', rf'\b{AMYLOID_PET_POSITIVE_TERMS_PATTERN}\b.{{0,90}}\b{AMYLOID_PET_PATTERN}\b'),
    ('pathologischer Amyloid-Biomarker', r'\b(?:amyloid|aβ|abeta|beta[-\s]?amyloid|liquor)\b.{0,90}\b(?:positiv|pathologisch|erniedrigt|erh[öo]ht|vereinbar|hinweisend)\b'),
    ('pathologischer Amyloid-Biomarker', r'\b(?:positiv|pathologisch)\b.{0,90}\b(?:amyloid|aβ|abeta|beta[-\s]?amyloid)\b'),
    ('pathologischer Amyloid-Quotient', r'\b(?:amyloid[-\s]?(?:quotient|ratio)|amyloidquotient|amyloidratio|a\s*(?:β|ß|beta)[-\s]*(?:42|1[-\s]?42)\s*(?:/|zu|:|-)?\s*(?:a\s*(?:β|ß|beta)[-\s]*)?(?:40|1[-\s]?40))\b.{0,90}\b(?:positiv|pathologisch|grenzwertig|auff[äa]llig|erniedrigt|abnorm)\b'),
    ('pathologischer Amyloid-Quotient', r'\b(?:positiv|pathologisch|grenzwertig|auff[äa]llig|erniedrigt|abnorm)\b.{0,90}\b(?:amyloid[-\s]?(?:quotient|ratio)|amyloidquotient|amyloidratio|a\s*(?:β|ß|beta)[-\s]*(?:42|1[-\s]?42)\s*(?:/|zu|:|-)?\s*(?:a\s*(?:β|ß|beta)[-\s]*)?(?:40|1[-\s]?40))\b'),
    ('pathologischer Amyloid-Quotient', r'\b(?:amyloid\s*beta|amyloid|a\s*(?:β|ß|beta))\b.{0,50}\b(?:42|1[-\s]?42)\s*(?:/|zu|:|-)?\s*(?:40|1[-\s]?40)\b.{0,90}\b(?:positiv|pathologisch|grenzwertig|auff[äa]llig|erniedrigt|abnorm)\b'),
    ('pathologische Amyloid-Ablagerungen', r'\b(?:auff[äa]llige?|pathologische?)\b.{0,90}\b(?:amyloid[-\s]?(?:ablagerungen|marker|quotient|ratio)|amyloidablagerungen)\b'),
]

AMYLOID_NEGATIVE_PATTERNS = [
    ('negatives CSF-Aß42', rf'\b{CSF_PATTERN}\b.{{0,120}}\b{ABETA_42_PATTERN}\b.{{0,90}}\b{AMYLOID_NEGATIVE_TERMS_PATTERN}\b'),
    ('negatives CSF-Aß42', rf'\b{ABETA_42_PATTERN}\b.{{0,90}}\b{AMYLOID_NEGATIVE_TERMS_PATTERN}\b'),
    ('negatives CSF-Aß42', rf'\b{AMYLOID_NEGATIVE_TERMS_PATTERN}\b.{{0,90}}\b{ABETA_42_PATTERN}\b'),
    ('negatives Amyloid-PET', rf'\b{AMYLOID_PET_PATTERN}\b.{{0,90}}\b{AMYLOID_NEGATIVE_TERMS_PATTERN}\b'),
    ('negatives Amyloid-PET', rf'\b{AMYLOID_NEGATIVE_TERMS_PATTERN}\b.{{0,90}}\b{AMYLOID_PET_PATTERN}\b'),
    ('negativer Amyloid-Biomarker', r'\b(?:amyloid|aβ|abeta|beta[-\s]?amyloid|liquor)\b.{0,90}\b(?:negativ|unauff[äa]llig|normal|nicht\s+pathologisch)\b'),
    ('negativer Amyloid-Biomarker', r'\b(?:kein(?:e|en|er|es)?|ohne)\b.{0,40}\b(?:pathologischen?\s+)?(?:amyloid|aβ|abeta|beta[-\s]?amyloid)\b'),
    ('negativer Amyloid-Quotient', r'\b(?:amyloid[-\s]?(?:quotient|ratio)|amyloidquotient|amyloidratio)\b.{0,90}\b(?:negativ|unauff[äa]llig|normal|nicht\s+pathologisch)\b'),
    ('negativer Amyloid-Quotient', r'\b(?:negativ|unauff[äa]llig|normal|nicht\s+pathologisch)\b.{0,90}\b(?:amyloid[-\s]?(?:quotient|ratio)|amyloidquotient|amyloidratio)\b'),
]

AMYLOID_RATIO_MENTION_PATTERNS = [
    ('Amyloid-Quotient erwähnt', r'\b(?:amyloid[-\s]?(?:quotient|ratio)|amyloidquotient|amyloidratio)\b'),
    ('Amyloid-Quotient erwähnt', r'\b(?:quotient)\b.{0,40}\b(?:a\s*(?:β|ß|beta))?\s*(?:42|41|1[-\s]?42)\s*(?:/|zu|:|-)?\s*(?:a\s*(?:β|ß|beta))?\s*(?:40|1[-\s]?40)\b'),
    ('Amyloid-Quotient erwähnt', r'\b(?:amyloid\s*beta|amyloid|a\s*(?:β|ß|beta))\b.{0,40}\b(?:42|41|1[-\s]?42)\s*(?:/|zu|:|-)?\s*(?:a\s*(?:β|ß|beta))?\s*(?:40|1[-\s]?40)\b.{0,40}\b(?:quotient|ratio)?\b'),
    ('Amyloid-Quotient erwähnt', r'\b(?:a\s*(?:β|ß|beta))\b.{0,30}\b(?:42\s*40|4240)\b.{0,40}\b(?:quotient|ratio)\b'),
]

NEGATION_RE = re.compile(
    r'\b(?:kein(?:e|en|er|es)?|ohne|nicht|negativ|ausgeschlossen|verneint|'
    r'unauff[äa]llig|kein\s+hinweis|keinen\s+hinweis|ohne\s+hinweis)\b',
    flags=re.IGNORECASE,
)

POST_CONCEPT_NEGATION_RE = re.compile(
    r'\b(?:ausgeschlossen|auszuschlie[ßs]en|nicht\s+nachweisbar|nicht\s+belegt|'
    r'findet\s+sich\s+nicht|finden\s+sich\s+nicht|zeigt\s+sich\s+nicht|'
    r'kein\s+nachweis|kein\s+hinweis|keine\s+hinweise|ohne\s+nachweis|'
    r'ohne\s+hinweis|unauff[äa]llig)\b',
    flags=re.IGNORECASE,
)

FAMILY_CONTEXT_RE = re.compile(
    r'\b(?:familienanamnese|familienanamnestisch|famili[äa]r|familie|'
    r'mutter|vater|eltern|tochter|sohn|bruder|schwester|gro[ßs]mutter|'
    r'gro[ßs]vater|oma|opa|tante|onkel|cousine|cousin)\b',
    flags=re.IGNORECASE,
)

MILD_SEVERITY_RE = re.compile(
    r'\b(?:leicht(?:gradig)?(?:e|er|en|es)?|mild(?:e|er|en|es)?|gering(?:gradig)?(?:e|er|en|es)?|diskret(?:e|er|en|es)?)\b',
    flags=re.IGNORECASE,
)

SEVERE_SEVERITY_RE = re.compile(
    r'\b(?:schwer(?:gradig)?(?:e|er|en|es)?|hochgradig(?:e|er|en|es)?|ausgepr[äa]gt(?:e|er|en|es)?|massiv(?:e|er|en|es)?|deutlich(?:e|er|en|es)?|relevant(?:e|er|en|es)?)\b',
    flags=re.IGNORECASE,
)

QUESTIONNAIRE_CONTEXT_RE = re.compile(
    r'\b(?:npi[-\s]?q|neuropsychiatrisches\s+interview|gds|geriatrische\s+depressionsskala|fragebogen|skala)\b',
    flags=re.IGNORECASE,
)
