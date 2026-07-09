export type Sex = "male" | "female";
export type LabStatus = "normal" | "low" | "high" | "critical" | "unknown" | string;

export interface TemplateTest {
  name?: string;
  test_name?: string;
  unit?: string;
  required?: boolean;
  description?: string;
}

export interface PanelTemplate {
  name?: string;
  panel_name?: string;
  display_name?: string;
  tests?: TemplateTest[];
  suggested_symptoms?: string[];
}

export interface TemplateOption {
  name: string;
  display_name: string;
}

export interface LabInput {
  name: string;
  value: number;
  unit: string;
}

export interface AnalyzePayload {
  age: number;
  sex: Sex;
  selected_panel: string;
  symptoms: string[];
  clinical_notes: string;
  labs: LabInput[];
}

export interface LabResult {
  name?: string;
  test_name?: string;
  value?: number | string;
  unit?: string;
  status?: LabStatus;
  reference_low?: number;
  reference_high?: number;
  reference_range?: string;
}

export interface AbnormalFinding extends LabResult {
  test?: string;
  evidence?: string;
}

export interface ClinicalPattern {
  name?: string;
  pattern_name?: string;
  rank?: number;
  score?: number | string;
  confidence?: string;
  confidence_level?: string;
  evidence_for?: string[];
  supporting_findings?: string[];
  missing_evidence?: string[];
  warnings?: string[];
}

export interface RetrievedSource {
  title?: string;
  snippet?: string;
  similarity_score?: number | string;
  source_id?: string;
  id?: string;
}

export interface PatientSummary {
  age?: number;
  sex?: string;
  selected_panel?: string;
  symptoms?: string[];
  clinical_notes?: string;
}

export interface AnalyzeResponse {
  report_case_id?: string;
  case_id?: string;
  id?: string;
  received?: PatientSummary;
  patient_summary?: PatientSummary;
  lab_results?: LabResult[];
  labs?: LabResult[];
  findings?: LabResult[];
  abnormal_findings?: Array<AbnormalFinding | string>;
  clinical_warnings?: string[];
  clinical_patterns?: Array<ClinicalPattern | string>;
  patterns?: Array<ClinicalPattern | string>;
  pattern_results?: Array<ClinicalPattern | string>;
  retrieved_sources?: Array<RetrievedSource | string>;
  missing_required_labs?: string[];
  safety_notice?: string;
  [key: string]: unknown;
}
