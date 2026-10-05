"""Pydantic schemas for extracting structured findings from clinical letters."""

from enum import Enum
from typing import List, Union  # Union allows enum values and free-text entries in the same list.
from pydantic import BaseModel, Field

# ======================================================================================
# GENERIC BASE MODELS AND ENUMS
# ======================================================================================

class BaseExtraction(BaseModel):
    """A generic structure for fields that require a citation and justification."""
    Zitat_Nennung: str = Field(..., description="Das exakte Zitat aus dem Text, das die Extraktion stützt.")
    Begruendung_Extraktion: str = Field(..., description="Kurze und präzise Begründung für die getroffene Extraktionsentscheidung.")

class JaNeinFehltEnum(str, Enum):
    """A standardized Enum for 'yes', 'no', and 'missing' responses."""
    JA = "ja"
    NEIN = "nein"
    FEHLT = "fehlt"

# ======================================================================================
# GROUP 1: PROMPT 'prompt_diagnose_kognition.md'
# ======================================================================================

# --- Enums for Diagnosis and Cognition ---

class KognitiveStoerungSchweregradEnum(str, Enum):
    LEICHT = "leicht"
    MITTEL = "mittel"
    SCHWER = "schwer"
    FEHLT = "fehlt"
    KEINE_KOGNITIVE_STOERUNG = "keine_kognitive_stoerung"

class KognitiveStoerungAetiologieEnum(str, Enum):
    ALZHEIMER_KRANKHEIT = "Alzheimer-Krankheit"
    LEWY_KOERPERCHEN_DEMENZ = "Lewy-Koerperchen Demenz"
    LEWY_BODY_KRANKHEIT = "Lewy Body Krankheit (LBD)"
    FRONTOTEMPORALE_DEMENZ = "Frontotemporale Demenz (FTD)"
    PARKINSON_KRANKHEIT = "Parkinson-Krankheit"
    VASKULAERE_DEMENZ = "vaskulaere Demenz"
    CEREBRALE_MIKROANGIOPATHIE = "cerebrale Mikroangiopathie"
    MULTI_INFARKT_DEMENZ = "Multi-Infarkt Demenz"
    PROGRESSIVE_SUPRANUKLEAERE_BLICKPARESE = "Progressive supranukleaere Blickparese (PSP)"
    NORMALDRUCKHYDROCEPHALUS = "Normaldruckhydrocephalus (NPH)"
    KORTIKOBASALE_DEGENERATION = "Kortikobasale Degeneration (CBD)"
    HUNTINGTON_KRANKHEIT = "Huntington-Krankheit"
    CREUTZFELD_JACOB_KRANKHEIT = "Creutzfeld-Jacob Krankheit (CJD)"
    PRIMAER_PROGRESSIVE_APHASIE = "Primaer Progressive Aphasie (PPA)"
    WERNICKE_ENCEPHALOPAHTE = "Wernicke Encephalopathie"
    ENCEPHALITIS = "Encephalitis"
    TUMOR = "Tumor"
    CHOREA_HUNTINGTON = "Chorea Huntington"


# --- Pydantic Models for Diagnosis and Cognition Entries ---

class JaNeinFehltEntry(BaseExtraction):
    """A generic entry for any field using the JaNeinFehltEnum."""
    Extraktion: JaNeinFehltEnum

class KognitiveStoerungSchweregradEntry(BaseExtraction):
    Extraktion: KognitiveStoerungSchweregradEnum

class KognitiveStoerungAetiologieEntry(BaseExtraction):
    Extraktion: List[KognitiveStoerungAetiologieEnum] = Field(..., description="Liste der identifizierten Ätiologien für die kognitive Störung.")

class AmyloidBiomarkerEntry(JaNeinFehltEntry):
    pass

class MmseEntry(BaseExtraction):
    Extraktion: int = Field(..., description="Die reine Punktzahl des MMSE-Tests. -1, wenn kein Test erwähnt wird.")

# --- Main Pydantic Model for Diagnosis and Cognition ---

class DiagnoseKognitionAnalysis(BaseModel):
    kognitive_stoerung_praesenz: JaNeinFehltEntry
    kognitive_stoerung_schweregrad: KognitiveStoerungSchweregradEntry
    kognitive_stoerung_aetiologie: KognitiveStoerungAetiologieEntry
    pathologische_amyloid_biomarker: AmyloidBiomarkerEntry
    mini_mental_status_test_ergebnis: MmseEntry


# ======================================================================================
# GROUP 2: PROMPT 'prompt_komorbiditaeten_anamnese.md'
# ======================================================================================

# --- Enums for Comorbidities and Anamnesis ---

class DepressionSchweregradEnum(str, Enum):
    KEINE_DEPRESSION = "keine_depression"
    FEHLT = "fehlt"
    LEICHT = "leicht"
    MITTEL = "mittel"
    SCHWER = "schwer"

class DepressionStatus(str, Enum):
    KEINE_DEPRESSION = "keine_depression"
    FEHLT = "fehlt"
    AKTUELL = "aktuell"
    REMITTIERT = "remittiert"

class DepressionDiagnoseNennungKontextEnum(str, Enum):
    EXPLIZITE_AERZTLICHE_NENNUNG_DER_DIAGNOSE = "Explizite aerztliche Nennung einer gesicherten Diagnose"
    SYMPTOMBESCHREIBUNG = "Symptombeschreibung"
    BEHANDLUNG_MEDIKAMENTOES = "Behandlung (Medikamentoes)"
    BEHANDLUNG_PSYCHOTHERAPIE = "Behandlung (Psychotherapie)"
    NPIQ = "Neuropsychiatrisches Interview (NPI-Q)"
    PHQ = "Patient Health Questionaire (PHQ)"
    ANDERE = "Anderer Kontext"

class DepressionSchweregradNennungKontextEnum(str, Enum):
    NPIQ = "Neuropsychiatrisches Interview (NPI-Q)"
    PHQ = "Patient Health Questionaire (PHQ)"
    ANDERE = "Anderer Kontext"

# --- Pydantic Models for Comorbidities and Anamnesis Entries ---

class DepressionDiagnoseNennungKontextEntry(BaseExtraction):
    Extraktion: List[DepressionDiagnoseNennungKontextEnum] = Field(..., description="Liste der identifizierten Kontexte für die Nennung einer Depression.")

class DepressionSchweregradNennungKontextEntry(BaseExtraction):
    Extraktion: List[DepressionSchweregradNennungKontextEnum] = Field(..., description="Liste der identifizierten Kontexte für die Nennung einer Depression.")


class DepressionSchweregradEntry(BaseExtraction):
    Extraktion: DepressionSchweregradEnum

class DepressionStatusEntry(BaseExtraction):
    Extraktion: DepressionStatus


# --- Main Pydantic Model for Comorbidities and Anamnesis ---

class KomorbiditaetenAnamneseAnalysis(BaseModel):
    krankengeschichte_schlaganfall: JaNeinFehltEntry
    krankengeschichte_epileptischer_anfall: JaNeinFehltEntry
    depression: JaNeinFehltEntry
    depression_diagnose_nennung_kontext: DepressionDiagnoseNennungKontextEntry
    depression_schweregrad: DepressionSchweregradEntry
    depression_schweregrad_nennung_kontext: DepressionSchweregradNennungKontextEntry
    depression_status: DepressionStatusEntry


# ======================================================================================
# GROUP 3: PROMPT 'prompt_mrt_befunde.md'
# ======================================================================================

# --- Main Pydantic Model for MRI Findings ---

class MrtBefundeAnalysis(BaseModel):
    MRT_gehirn_untersuchung_erhalten: JaNeinFehltEntry
    MRT_gehirn_befund_vorliegend: JaNeinFehltEntry
    MRT_haemorrhagie: JaNeinFehltEntry
    MRT_siderose: JaNeinFehltEntry
    MRT_ischaemie: JaNeinFehltEntry
    MRT_fazekas: JaNeinFehltEntry
    MRT_cerebrale_amyloidangiopathie: JaNeinFehltEntry
    MRT_erwaehnung_anderer_ursachen_fuer_demenz: JaNeinFehltEntry


# ======================================================================================
# GROUP 4: PROMPT 'prompt_systemerkrankungen_medikation.md'
# ======================================================================================

# --- Enums for Systemic Conditions and Medications ---

class ImmunologischeErkrankungEnum(str, Enum):
    MORBUS_BECHTEREW = "Morbus Bechterew (M. Bechterew)"
    MORBUS_CROHN = "Morbus Crohn (M. Crohn)"
    COLITIS_ULCEROSA = "Colitis ulcerosa (CU)"
    PSORIASIS_ARTHRITIS = "Psoriasis-Arthritis (PsA)"
    RHEUMATOIDE_ARTHRITIS = "Rheumatoide Arthritis (RA)"
    SAPHO_SYNDROM = "SAPHO-Syndrom"
    SYSTEMISCHER_LUPUS_ERYTHEMATODES = "Systemischer Lupus erythematodes (SLE)"
    MULTIPLE_SKLEROSE = "Multiple Sklerose (MS)"
    SJOEGREN_SYNDROM = "Sjoegren-Syndrom"
    SKLERODERMIE = "Sklerodermie"
    VASKULITIS = "Vaskulitis"
    AUTOIMMUNHEPATITIS = "Autoimmunhepatitis (AIH)"
    CHRONISCHE_POLYARTHRITIS = "Chronische Polyarthritis (cP)"
    DERMATOMYOSITIS = "Dermatomyositis"
    MISCHKOLLAGENOSE = "Mischkollagenose"

class GerinnungsstoerungEnum(str, Enum):
    THROMBOPHILIE = "Thrombophilie"
    HAEMOPHILIE_A = "Hämophilie A"
    HAEMOPHILIE_B = "Hämophilie B"
    VON_WILLEBRAND_SYNDROM = "Von-Willebrand-Syndrom (VWS)"
    THROMBOZYTOPENIE_LEICHT = "Thrombozytopenie (leicht)"
    THROMBOZYTOPENIE_SCHWER = "Thrombozytopenie (schwer)"
    THROMBOZYTHAEMIE_LEICHT = "Thrombozythämie (leicht)"
    THROMBOZYTHAEMIE_SCHWER = "Thrombozythämie (schwer)"
    FAKTOR_V_LEIDEN_MUTATION = "Faktor-V-Leiden-Mutation (FVL)"
    PROTEIN_C_MANGEL = "Protein-C-Mangel"
    ANTIPHOSPHOLIPID_SYNDROM = "Antiphospholipid-Syndrom (APS)"
    DISSEMINIERTE_INTRAVASALE_GERINNUNG = "Disseminierte intravasale Gerinnung (DIC)"

class ImmunsuppressiveMedikationEnum(str, Enum):
    METHOTREXAT = "Methotrexat (MTX)"
    CORTISON = "Cortison"
    PREDNISOLON = "Prednisolon"
    METHYLPREDISOLON = "Methylpredisolon"
    PREDNISON = "Prednison"
    DEXAMETHASON = "Dexamethason"
    AZATHIOPRIN = "Azathioprin (AZA)"
    CYCLOSPORIN = "Cyclosporin (CSA)"
    TACROLIMUS = "Tacrolimus"
    MYCOPHENOLATMOFETIL = "Mycophenolatmofetil (MMF)"
    INFLIXIMAB = "Infliximab"
    ADALIMUMAB = "Adalimumab"
    ETANERCEPT = "Etanercept"
    RITUXIMAB = "Rituximab"
    CYCLOPHOSPHAMID = "Cyclophosphamid (CTX)"
    ORALE_GLUKOKORTIKOIDE = "Orale Glukokortikoide"
    SYSTEMISCHE_GLUKOKORTIKOIDE = "Systemische Glukokortikoide"

class AntikoagulativeMedikationEnum(str, Enum):
    MARCUMAR = "Marcumar (Phenprocoumon)"
    ELIQUIS = "Eliquis (Apixaban)"
    XARELTO = "Xarelto (Rivaroxaban)"
    LIXIANA = "Lixiana (Edoxaban)"
    PRADAXA = "Pradaxa (Dabigatran)"
    HEPARIN = "Heparin"
    CLEXANE = "Clexane (Enoxaparin)"
    WARFARIN = "Warfarin"

# --- Pydantic Models for Systemic Conditions and Medications Entries ---

class ImmunologischeErkrankungEntry(BaseExtraction):
    Extraktion: List[Union[ImmunologischeErkrankungEnum, str]] = Field(..., description="Liste der identifizierten immunologischen Erkrankungen.")

class GerinnungsstoerungEntry(BaseExtraction):
    Extraktion: List[Union[GerinnungsstoerungEnum, str]] = Field(..., description="Liste der identifizierten Gerinnungsstörungen.")

class ImmunsuppressionEntry(BaseExtraction):
    
    Extraktion: List[Union[ImmunsuppressiveMedikationEnum, str]] = Field(..., description="Liste der identifizierten immunsuppressiven Medikationen, inklusive spezifischer -mab Medikamente.")

class AntikoagulationEntry(BaseExtraction):
    Extraktion: List[AntikoagulativeMedikationEnum] = Field(..., description="Liste der identifizierten antikoagulativen Medikationen.")

# --- Main Pydantic Model for Systemic Conditions and Medications ---

class SystemerkrankungenMedikationAnalysis(BaseModel):
    immunologische_erkrankung: ImmunologischeErkrankungEntry
    gerinnungsstoerung: GerinnungsstoerungEntry
    immunosuppression: ImmunsuppressionEntry
    antikoagulation: AntikoagulationEntry
