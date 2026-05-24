"""
Pydantic data models for Healthcare Equity Bias Detection System.
Defines schemas for Bronze, Silver, and Gold layers of the medallion architecture.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List, Dict
from datetime import datetime
from enum import Enum
import uuid


class Race(str, Enum):
    WHITE = "white"
    BLACK = "black_or_african_american"
    HISPANIC = "hispanic_or_latino"
    ASIAN = "asian"
    NATIVE_AMERICAN = "american_indian_or_alaska_native"
    PACIFIC_ISLANDER = "native_hawaiian_or_pacific_islander"
    MULTIRACIAL = "multiracial"
    OTHER = "other"
    UNKNOWN = "unknown"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NONBINARY = "non_binary"
    TRANSGENDER_MALE = "transgender_male"
    TRANSGENDER_FEMALE = "transgender_female"
    OTHER = "other"
    UNKNOWN = "unknown"


class SexualOrientation(str, Enum):
    HETEROSEXUAL = "heterosexual"
    GAY = "gay"
    LESBIAN = "lesbian"
    BISEXUAL = "bisexual"
    QUEER = "queer"
    OTHER = "other"
    UNKNOWN = "unknown"
    DECLINE = "decline_to_state"


class InsuranceType(str, Enum):
    PRIVATE = "private"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
    UNINSURED = "uninsured"
    OTHER = "other"


class DecisionType(str, Enum):
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    REFERRAL = "referral"
    ADMISSION = "admission"
    DISCHARGE = "discharge"


class OutcomeType(str, Enum):
    RECOVERY = "recovery"
    READMISSION = "readmission"
    MORTALITY = "mortality"
    COMPLICATION = "complication"


class SeverityLevel(str, Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InterventionStatus(str, Enum):
    RECOMMENDED = "recommended"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DECLINED = "declined"


# ==================== BRONZE LAYER ====================
# Raw, unprocessed data as ingested

class RawPatientRecord(BaseModel):
    """Raw patient record from source system."""
    patient_id: str = Field(..., description="De-identified patient ID")
    age: int = Field(..., ge=0, le=120)
    race: Race
    gender: Gender
    sexual_orientation: SexualOrientation
    zip_code: str = Field(..., min_length=5, max_length=5)
    insurance_type: InsuranceType
    admission_date: datetime
    chief_complaint: str
    presenting_vitals: Dict[str, float] = Field(default_factory=dict)
    raw_labs: Dict[str, float] = Field(default_factory=dict)
    raw_notes: str = ""
    facility_id: str
    provider_id: str
    admission_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    class Config:
        use_enum_values = False


class RawTreatmentDecision(BaseModel):
    """Raw treatment decision from clinical system."""
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    admission_id: str
    decision_type: DecisionType
    decision_value: str = Field(..., description="What decision was made (e.g., drug name, procedure code)")
    clinical_indication: str
    decision_timestamp: datetime
    provider_id: str
    facility_id: str

    class Config:
        use_enum_values = False


class RawOutcome(BaseModel):
    """Raw outcome event from clinical system."""
    outcome_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    admission_id: str
    outcome_type: OutcomeType
    outcome_value: str
    outcome_date: datetime
    days_to_outcome: Optional[int] = None

    class Config:
        use_enum_values = False


# ==================== SILVER LAYER ====================
# Cleaned, normalized, feature-engineered data

class ProcessedPatientRecord(BaseModel):
    """Processed patient record with computed features."""
    patient_id: str
    age: int
    age_group: Literal["18-30", "31-45", "46-60", "61-75", "75+"]
    race: Race
    gender: Gender
    sexual_orientation: SexualOrientation
    zip_code: str
    ses_quintile: int = Field(..., ge=1, le=5, description="SES quintile derived from zip code")
    insurance_type: InsuranceType

    # Clinical severity scores
    sofa_score: Optional[float] = Field(None, ge=0, le=24, description="Sequential Organ Failure Assessment")
    cci_score: Optional[float] = Field(None, ge=0, description="Charlson Comorbidity Index")
    risk_tier: RiskTier

    # Data quality flags
    deidentified: bool = True
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = False


class ProcessedTreatmentDecision(BaseModel):
    """Normalized treatment decision."""
    decision_id: str
    patient_id: str
    admission_id: str
    decision_type: DecisionType
    decision_value: str
    decision_timestamp: datetime
    provider_id: str
    facility_id: str
    clinical_indication_severity: RiskTier = Field(default=RiskTier.MEDIUM)

    class Config:
        use_enum_values = False


class ProcessedOutcome(BaseModel):
    """Normalized outcome."""
    outcome_id: str
    patient_id: str
    admission_id: str
    outcome_type: OutcomeType
    outcome_date: datetime
    days_to_outcome: Optional[int] = None

    class Config:
        use_enum_values = False


# ==================== GOLD LAYER ====================
# Aggregated metrics, bias analysis, intervention tracking

class BiasMetric(BaseModel):
    """Computed bias metric for a specific scenario and demographic dimension."""
    metric_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_type: Literal["cardiac_catheterization", "pain_management", "mental_health_referral", "hospital_admission"]
    demographic_dimension: Literal["race", "gender", "sexual_orientation", "ses", "insurance"]
    reference_group: str = Field(..., description="Reference group for comparison (e.g., 'white')")
    comparison_group: str = Field(..., description="Group being compared (e.g., 'black_or_african_american')")

    # Statistical results
    metric_name: str = Field(..., description="e.g., 'disparate_impact_ratio', 'odds_ratio'")
    metric_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    p_value: float = Field(..., ge=0, le=1)
    is_significant: bool

    # Severity classification
    severity: SeverityLevel

    # Data context
    sample_size: int
    reference_group_rate: float = Field(..., ge=0, le=1, description="Treatment/outcome rate in reference group")
    comparison_group_rate: float = Field(..., ge=0, le=1, description="Treatment/outcome rate in comparison group")

    # Metadata
    calculation_date: datetime = Field(default_factory=datetime.utcnow)
    calculation_period: str = Field(default="monthly", description="e.g., 'monthly', 'quarterly'")

    class Config:
        use_enum_values = False


class InterventionRecord(BaseModel):
    """AI-generated and tracked intervention for a detected bias."""
    intervention_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_type: str
    bias_metric_id: str
    facility_id: str
    provider_id: Optional[str] = None

    # Intervention details
    intervention_type: str = Field(..., description="e.g., 'bias_alert', 'training', 'model_retrain'")
    intervention_description: str
    root_cause_analysis: str = Field(default="", description="AI-generated analysis of why bias exists")

    # Status tracking
    status: InterventionStatus = Field(default=InterventionStatus.RECOMMENDED)
    recommended_date: datetime = Field(default_factory=datetime.utcnow)
    implemented_date: Optional[datetime] = None

    # Effectiveness metrics
    pre_bias_score: float
    post_bias_score: Optional[float] = None
    is_effective: Optional[bool] = None

    # AI metadata
    ai_generated: bool = True
    ai_model: str = Field(default="claude-sonnet-4-6")
    ai_confidence: float = Field(default=0.8, ge=0, le=1)

    class Config:
        use_enum_values = False


class EquityReport(BaseModel):
    """Comprehensive equity report for a facility or time period."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    facility_id: Optional[str] = None
    reporting_period: str = Field(..., description="e.g., 'Q1_2024'")
    report_type: Literal["monthly", "quarterly", "annual"]

    # Summary metrics
    total_disparities_detected: int
    critical_disparities: int
    moderate_disparities: int

    # Interventions
    interventions_recommended: int
    interventions_implemented: int
    intervention_effectiveness_pct: float = Field(..., ge=0, le=100)

    # Narrative summary
    executive_summary: str
    key_findings: List[str]
    recommendations: List[str]

    # Regulatory compliance
    regulatory_framework: Literal["CMS", "Joint_Commission", "OCR", "NCQA"]
    compliance_status: Literal["compliant", "needs_improvement", "non_compliant"]

    # Metadata
    generated_date: datetime = Field(default_factory=datetime.utcnow)
    generated_by_ai: bool = True

    class Config:
        use_enum_values = False


class ProviderAccountability(BaseModel):
    """Provider-level equity scorecard."""
    provider_id: str
    facility_id: str

    # Overall score
    equity_score: float = Field(..., ge=0, le=100, description="0-100 equity performance score")

    # Disparity metrics by scenario
    cardiac_catheterization_disparity: Optional[float] = None
    pain_management_disparity: Optional[float] = None
    mental_health_referral_disparity: Optional[float] = None
    hospital_admission_disparity: Optional[float] = None

    # Trend
    score_change_vs_prior_period: float = Field(default=0.0, description="Point change from prior period")

    # Actions
    required_interventions: List[str]

    # Last update
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = False


# ==================== API REQUEST/RESPONSE ====================

class BiasDetectionRequest(BaseModel):
    """Request to run bias detection analysis."""
    scenario_type: Literal["cardiac_catheterization", "pain_management", "mental_health_referral", "hospital_admission"]
    demographic_dimension: Literal["race", "gender", "sexual_orientation", "ses", "insurance"]
    start_date: datetime
    end_date: datetime
    facility_id: Optional[str] = None


class BiasDetectionResponse(BaseModel):
    """Response from bias detection analysis."""
    request_id: str
    status: Literal["completed", "in_progress", "failed"]
    metrics: List[BiasMetric]
    interventions: List[InterventionRecord]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class InterventionRecommendationRequest(BaseModel):
    """Request for AI-generated intervention recommendations."""
    bias_metric_id: str
    facility_context: Dict[str, str] = Field(default_factory=dict)
    prior_interventions: List[InterventionRecord] = Field(default_factory=list)


class InterventionRecommendationResponse(BaseModel):
    """Response with AI-generated interventions."""
    recommendation_id: str
    bias_metric_id: str
    interventions: List[InterventionRecord]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
