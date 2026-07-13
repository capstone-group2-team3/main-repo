export type Sex = "male" | "female";
export type LabStatus = "normal" | "low" | "high" | "critical" | "unknown" | string;
export type SeverityLabel = "Routine" | "Urgent" | "Critical";

export interface SeverityResult {
  label: SeverityLabel;
  confidence: number;
  source: string;
}

export interface TemplateTest {
  name?: string;
  test_name?: string;
  unit?: string;
  required?: boolean;
  description?: string;
  reference_low?: number | null;
  reference_high?: number | null;
  critical_low?: number | null;
  critical_high?: number | null;
}

export interface PanelTemplate {
  name?: string;
  panel_name?: string;
  display_name?: string;
  tests?: TemplateTest[];
  suggested_symptoms?: string[];
  educational_disclaimer?: string;
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
  critical_low?: number | null;
  critical_high?: number | null;
  reference_range?: string;
  evidence?: string;
}

export interface AbnormalFinding extends LabResult {
  test?: string;
  evidence?: string;
}

export interface ClinicalPattern {
  pattern_code?: string;
  pattern?: string;
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
  retrieved_sources?: Array<RetrievedSource | string>;
}

export interface RetrievedSource {
  title?: string;
  snippet?: string;
  similarity_score?: number | string;
  source_id?: string;
  id?: string;
  pattern_code?: string;
}

export interface ClinicalWarning {
  severity?: string;
  text?: string;
  warning?: string;
  associated_item?: string;
}

export interface ReportInfo {
  generated?: boolean;
  markdown_path?: string;
  html_path?: string;
  pdf_path?: string;
  markdown_download_url?: string;
  html_download_url?: string;
  pdf_download_url?: string;
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
  clinical_warnings?: Array<ClinicalWarning | string>;
  clinical_patterns?: Array<ClinicalPattern | string>;
  patterns?: Array<ClinicalPattern | string>;
  pattern_results?: Array<ClinicalPattern | string>;
  retrieved_sources?: Array<RetrievedSource | string>;
  missing_required_labs?: string[];
  severity?: SeverityResult;
  safety_notice?: string;
  generated_at?: string;
  report_file_path?: string;
  report?: ReportInfo;
  report_format_version?: string;
  [key: string]: unknown;
}
