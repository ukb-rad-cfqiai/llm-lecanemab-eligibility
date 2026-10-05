"""Prompt steps and output schemas used in the extraction experiment."""

import os

from utils.data.models import (
    DiagnoseKognitionAnalysis,
    KomorbiditaetenAnamneseAnalysis,
    MrtBefundeAnalysis,
    SystemerkrankungenMedikationAnalysis,
)
from utils.data.paths import PROJECT_DIR


join = os.path.join
script_dir = PROJECT_DIR


prompt_steps_dict = {
    "komorbiditaeten_anamnese": {
        "prompt_txt_file": join(script_dir, 'prompts', 'prompt_komorbiditaeten_anamnese.md'),
        "pydantic_model": KomorbiditaetenAnamneseAnalysis,
        "classes_to_extract": [
            "krankengeschichte_schlaganfall", "krankengeschichte_epileptischer_anfall",
            "depression", "depression_diagnose_nennung_kontext", "depression_schweregrad", 
            "depression_schweregrad_nennung_kontext",  "depression_status"
        ]
    },   
    "diagnose_kognition": {
        "prompt_txt_file": join(script_dir, 'prompts', 'prompt_diagnose_kognition.md'),
        "pydantic_model": DiagnoseKognitionAnalysis,
        "classes_to_extract": [
            "kognitive_stoerung_praesenz", "kognitive_stoerung_schweregrad",
            "kognitive_stoerung_aetiologie",
            "pathologische_amyloid_biomarker", "mini_mental_status_test_ergebnis"
        ]
    },
    "mrt_befunde": {
        "prompt_txt_file": join(script_dir, 'prompts', 'prompt_mrt_befunde.md'),
        "pydantic_model": MrtBefundeAnalysis,
        "classes_to_extract": [
            "MRT_gehirn_untersuchung_erhalten", "MRT_gehirn_befund_vorliegend", "MRT_haemorrhagie", 
            "MRT_siderose", "MRT_ischaemie", "MRT_fazekas", "MRT_cerebrale_amyloidangiopathie",
            "MRT_erwaehnung_anderer_ursachen_fuer_demenz"
        ]
    },
    "systemerkrankungen_medikation": {
        "prompt_txt_file": join(script_dir, 'prompts', 'prompt_systemerkrankungen_medikation.md'),
        "pydantic_model": SystemerkrankungenMedikationAnalysis,
        "classes_to_extract": [
            "immunologische_erkrankung", "gerinnungsstoerung",
            "immunosuppression", "antikoagulation"
        ]
    }
}

PROMPT_STEP_NAMES = tuple(prompt_steps_dict)
