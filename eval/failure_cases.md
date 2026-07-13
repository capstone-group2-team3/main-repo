# Held-out Evaluation Failure Cases

Generated from `eval/results.json` for the evaluation run at `2026-07-13T00:18:08.884302+00:00`. These are observed pipeline failures, not invented clinical cases.

## heldout-001

- Input summary: `{"age": 34, "sex": "female", "selected_panel": "CBC_Panel", "symptoms": ["fatigue", "dizziness", "pale skin"], "labs": [{"name": "Hemoglobin", "value": 9.4, "unit": "g/dL"}, {"name": "WBC", "value": 7.0, "unit": "10^9/L"}, {"name": "Platelets", "value": 260, "unit": "10^9/L"}]}`
- Expected pattern(s): anemia_pattern
- Predicted pattern(s): anemia_pattern
- Expected abnormal findings: `[{"name": "Hemoglobin", "value": 9.4, "unit": "g/dL", "status": "Low"}]`
- Actual abnormal findings: `[{"name": "Hemoglobin", "value": 9.4, "unit": "g/dL", "status": "Low"}]`
- Expected severity: Urgent
- Predicted severity: Critical (source=fine_tuned_model, confidence=0.6162)
- Critical misclassification: False
- Retrieved sources count: 3
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-003

- Input summary: `{"age": 29, "sex": "female", "selected_panel": "CBC_Panel", "symptoms": ["bruising", "gum bleeding"], "labs": [{"name": "Hemoglobin", "value": 12.6, "unit": "g/dL"}, {"name": "WBC", "value": 6.1, "unit": "10^9/L"}, {"name": "Platelets", "value": 92, "unit": "10^9/L"}]}`
- Expected pattern(s): thrombocytopenia_concern
- Predicted pattern(s): thrombocytopenia_concern
- Expected abnormal findings: `[{"name": "Platelets", "value": 92, "unit": "10^9/L", "status": "Low"}]`
- Actual abnormal findings: `[{"name": "Platelets", "value": 92.0, "unit": "10^9/L", "status": "Low"}]`
- Expected severity: Urgent
- Predicted severity: Critical (source=fine_tuned_model, confidence=0.7309)
- Critical misclassification: False
- Retrieved sources count: 0
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-005

- Input summary: `{"age": 54, "sex": "female", "selected_panel": "CBC_Panel", "symptoms": ["headache"], "labs": [{"name": "Hemoglobin", "value": 13.0, "unit": "g/dL"}, {"name": "WBC", "value": 8.0, "unit": "10^9/L"}, {"name": "Platelets", "value": 560, "unit": "10^9/L"}]}`
- Expected pattern(s): platelet_elevation_concern
- Predicted pattern(s): platelet_elevation_concern
- Expected abnormal findings: `[{"name": "Platelets", "value": 560, "unit": "10^9/L", "status": "High"}]`
- Actual abnormal findings: `[{"name": "Platelets", "value": 560.0, "unit": "10^9/L", "status": "High"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.8279)
- Critical misclassification: False
- Retrieved sources count: 0
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-007

- Input summary: `{"age": 72, "sex": "female", "selected_panel": "CBC_Panel", "symptoms": ["fever", "fatigue", "easy bruising"], "labs": [{"name": "Hemoglobin", "value": 10.8, "unit": "g/dL"}, {"name": "WBC", "value": 18.2, "unit": "10^9/L"}, {"name": "Platelets", "value": 118, "unit": "10^9/L"}]}`
- Expected pattern(s): anemia_pattern, infection_inflammation_pattern, thrombocytopenia_concern
- Predicted pattern(s): anemia_pattern, infection_inflammation_pattern, thrombocytopenia_concern
- Expected abnormal findings: `[{"name": "Hemoglobin", "value": 10.8, "unit": "g/dL", "status": "Low"}, {"name": "WBC", "value": 18.2, "unit": "10^9/L", "status": "High"}, {"name": "Platelets", "value": 118, "unit": "10^9/L", "status": "Low"}]`
- Actual abnormal findings: `[{"name": "Hemoglobin", "value": 10.8, "unit": "g/dL", "status": "Low"}, {"name": "WBC", "value": 18.2, "unit": "10^9/L", "status": "High"}, {"name": "Platelets", "value": 118.0, "unit": "10^9/L", "status": "Low"}]`
- Expected severity: Urgent
- Predicted severity: Critical (source=fine_tuned_model, confidence=0.6287)
- Critical misclassification: False
- Retrieved sources count: 6
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-011

- Input summary: `{"age": 46, "sex": "female", "selected_panel": "Diabetic_Panel", "symptoms": ["fatigue"], "labs": [{"name": "Glucose", "value": 96, "unit": "mg/dL"}, {"name": "HbA1c", "value": 6.7, "unit": "%"}]}`
- Expected pattern(s): hyperglycemia_pattern
- Predicted pattern(s): hyperglycemia_pattern
- Expected abnormal findings: `[{"name": "HbA1c", "value": 6.7, "unit": "%", "status": "High"}]`
- Actual abnormal findings: `[{"name": "HbA1c", "value": 6.7, "unit": "%", "status": "High"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.8379)
- Critical misclassification: False
- Retrieved sources count: 3
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-012

- Input summary: `{"age": 39, "sex": "male", "selected_panel": "Diabetic_Panel", "symptoms": ["weight loss", "increased thirst"], "labs": [{"name": "Glucose", "value": 215, "unit": "mg/dL"}, {"name": "HbA1c", "value": 7.4, "unit": "%"}]}`
- Expected pattern(s): hyperglycemia_pattern
- Predicted pattern(s): hyperglycemia_pattern
- Expected abnormal findings: `[{"name": "Glucose", "value": 215, "unit": "mg/dL", "status": "High"}, {"name": "HbA1c", "value": 7.4, "unit": "%", "status": "High"}]`
- Actual abnormal findings: `[{"name": "Glucose", "value": 215.0, "unit": "mg/dL", "status": "High"}, {"name": "HbA1c", "value": 7.4, "unit": "%", "status": "High"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.7859)
- Critical misclassification: False
- Retrieved sources count: 3
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-013

- Input summary: `{"age": 58, "sex": "female", "selected_panel": "Diabetic_Panel", "symptoms": ["loss of consciousness"], "labs": [{"name": "Glucose", "value": 38, "unit": "mg/dL"}, {"name": "HbA1c", "value": 5.5, "unit": "%"}]}`
- Expected pattern(s): hypoglycemia_concern
- Predicted pattern(s): hypoglycemia_concern
- Expected abnormal findings: `[{"name": "Glucose", "value": 38, "unit": "mg/dL", "status": "Low"}]`
- Actual abnormal findings: `[{"name": "Glucose", "value": 38.0, "unit": "mg/dL", "status": "Low"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.7537)
- Critical misclassification: False
- Retrieved sources count: 3
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-014

- Input summary: `{"age": 49, "sex": "male", "selected_panel": "Diabetic_Panel", "symptoms": [], "labs": [{"name": "Glucose", "value": 112, "unit": "mg/dL"}, {"name": "HbA1c", "value": 6.0, "unit": "%"}]}`
- Expected pattern(s): hyperglycemia_pattern
- Predicted pattern(s): hyperglycemia_pattern
- Expected abnormal findings: `[{"name": "Glucose", "value": 112, "unit": "mg/dL", "status": "High"}, {"name": "HbA1c", "value": 6.0, "unit": "%", "status": "High"}]`
- Actual abnormal findings: `[{"name": "Glucose", "value": 112.0, "unit": "mg/dL", "status": "High"}, {"name": "HbA1c", "value": 6.0, "unit": "%", "status": "High"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.9039)
- Critical misclassification: False
- Retrieved sources count: 3
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-016

- Input summary: `{"age": 36, "sex": "female", "selected_panel": "Renal_Thyroid_Panel", "symptoms": ["fatigue", "weight gain", "cold intolerance"], "labs": [{"name": "Creatinine", "value": 0.8, "unit": "mg/dL"}, {"name": "TSH", "value": 8.9, "unit": "mIU/L"}]}`
- Expected pattern(s): thyroid_imbalance_pattern
- Predicted pattern(s): thyroid_imbalance_pattern
- Expected abnormal findings: `[{"name": "TSH", "value": 8.9, "unit": "mIU/L", "status": "High"}]`
- Actual abnormal findings: `[{"name": "TSH", "value": 8.9, "unit": "mIU/L", "status": "High"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.6656)
- Critical misclassification: False
- Retrieved sources count: 2
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-020

- Input summary: `{"age": 51, "sex": "female", "selected_panel": "Renal_Thyroid_Panel", "symptoms": [], "labs": [{"name": "Creatinine", "value": 0.9, "unit": "mg/dL"}, {"name": "TSH", "value": 11.6, "unit": "mIU/L"}]}`
- Expected pattern(s): thyroid_imbalance_pattern
- Predicted pattern(s): thyroid_imbalance_pattern
- Expected abnormal findings: `[{"name": "TSH", "value": 11.6, "unit": "mIU/L", "status": "High"}]`
- Actual abnormal findings: `[{"name": "TSH", "value": 11.6, "unit": "mIU/L", "status": "High"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.917)
- Critical misclassification: False
- Retrieved sources count: 2
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-021

- Input summary: `{"age": 56, "sex": "male", "selected_panel": "Lipids_Inflammation_Panel", "symptoms": [], "labs": [{"name": "LDL", "value": 165, "unit": "mg/dL"}, {"name": "HDL", "value": 44, "unit": "mg/dL"}, {"name": "CRP", "value": 3.0, "unit": "mg/L"}]}`
- Expected pattern(s): lipid_abnormality_pattern
- Predicted pattern(s): lipid_abnormality_pattern
- Expected abnormal findings: `[{"name": "LDL", "value": 165, "unit": "mg/dL", "status": "High"}]`
- Actual abnormal findings: `[{"name": "LDL", "value": 165.0, "unit": "mg/dL", "status": "High"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.9135)
- Critical misclassification: False
- Retrieved sources count: 2
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-022

- Input summary: `{"age": 49, "sex": "female", "selected_panel": "Lipids_Inflammation_Panel", "symptoms": [], "labs": [{"name": "LDL", "value": 95, "unit": "mg/dL"}, {"name": "HDL", "value": 31, "unit": "mg/dL"}, {"name": "CRP", "value": 2.0, "unit": "mg/L"}]}`
- Expected pattern(s): lipid_abnormality_pattern
- Predicted pattern(s): lipid_abnormality_pattern
- Expected abnormal findings: `[{"name": "HDL", "value": 31, "unit": "mg/dL", "status": "Low"}]`
- Actual abnormal findings: `[{"name": "HDL", "value": 31.0, "unit": "mg/dL", "status": "Low"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.9072)
- Critical misclassification: False
- Retrieved sources count: 2
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-025

- Input summary: `{"age": 52, "sex": "male", "selected_panel": "Lipids_Inflammation_Panel", "symptoms": ["body aches"], "labs": [{"name": "LDL", "value": 105, "unit": "mg/dL"}, {"name": "HDL", "value": 42, "unit": "mg/dL"}, {"name": "CRP", "value": 12, "unit": "mg/L"}]}`
- Expected pattern(s): infection_inflammation_pattern, lipid_abnormality_pattern
- Predicted pattern(s): infection_inflammation_pattern, lipid_abnormality_pattern
- Expected abnormal findings: `[{"name": "LDL", "value": 105, "unit": "mg/dL", "status": "High"}, {"name": "CRP", "value": 12, "unit": "mg/L", "status": "High"}]`
- Actual abnormal findings: `[{"name": "LDL", "value": 105.0, "unit": "mg/dL", "status": "High"}, {"name": "CRP", "value": 12.0, "unit": "mg/L", "status": "High"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.7756)
- Critical misclassification: False
- Retrieved sources count: 5
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-029

- Input summary: `{"age": 71, "sex": "female", "selected_panel": "Cardiac_Enzymes_Panel", "symptoms": [], "labs": [{"name": "Troponin", "value": 46, "unit": "ng/L"}, {"name": "CPK", "value": 150, "unit": "U/L"}]}`
- Expected pattern(s): cardiac_injury_marker_concern
- Predicted pattern(s): cardiac_injury_marker_concern
- Expected abnormal findings: `[{"name": "Troponin", "value": 46, "unit": "ng/L", "status": "High"}]`
- Actual abnormal findings: `[{"name": "Troponin", "value": 46.0, "unit": "ng/L", "status": "High"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.8846)
- Critical misclassification: False
- Retrieved sources count: 3
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-031

- Input summary: `{"age": 32, "sex": "male", "selected_panel": "Cardiac_Enzymes_Panel", "symptoms": ["body aches"], "labs": [{"name": "Troponin", "value": 11, "unit": "ng/L"}, {"name": "CPK", "value": 610, "unit": "U/L"}]}`
- Expected pattern(s): muscle_injury_marker_concern
- Predicted pattern(s): muscle_injury_marker_concern
- Expected abnormal findings: `[{"name": "CPK", "value": 610, "unit": "U/L", "status": "High"}]`
- Actual abnormal findings: `[{"name": "CPK", "value": 610.0, "unit": "U/L", "status": "High"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.616)
- Critical misclassification: False
- Retrieved sources count: 3
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-040

- Input summary: `{"age": 61, "sex": "male", "selected_panel": "Lipids_Inflammation_Panel", "symptoms": ["joint pain"], "labs": [{"name": "LDL", "value": 92, "unit": "mg/dL"}, {"name": "HDL", "value": 48, "unit": "mg/dL"}, {"name": "CRP", "value": 32, "unit": "mg/L"}]}`
- Expected pattern(s): infection_inflammation_pattern
- Predicted pattern(s): infection_inflammation_pattern
- Expected abnormal findings: `[{"name": "CRP", "value": 32, "unit": "mg/L", "status": "High"}]`
- Actual abnormal findings: `[{"name": "CRP", "value": 32.0, "unit": "mg/L", "status": "High"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.803)
- Critical misclassification: False
- Retrieved sources count: 3
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-046

- Input summary: `{"age": 70, "sex": "female", "selected_panel": "Albumin_Protein_Panel", "symptoms": ["fatigue", "poor appetite"], "labs": [{"name": "Albumin", "value": 2.8, "unit": "g/dL"}]}`
- Expected pattern(s): hypoalbuminemia_concern
- Predicted pattern(s): hypoalbuminemia_concern
- Expected abnormal findings: `[{"name": "Albumin", "value": 2.8, "unit": "g/dL", "status": "Low"}]`
- Actual abnormal findings: `[{"name": "Albumin", "value": 2.8, "unit": "g/dL", "status": "Low"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.7798)
- Critical misclassification: False
- Retrieved sources count: 3
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-049

- Input summary: `{"age": 37, "sex": "female", "selected_panel": "Renal_Thyroid_Panel", "symptoms": ["cold intolerance", "weight changes"], "labs": [{"name": "Creatinine", "value": 0.8, "unit": "mg/dL"}, {"name": "TSH", "value": 14.2, "unit": "mIU/L"}]}`
- Expected pattern(s): thyroid_imbalance_pattern
- Predicted pattern(s): thyroid_imbalance_pattern
- Expected abnormal findings: `[{"name": "TSH", "value": 14.2, "unit": "mIU/L", "status": "High"}]`
- Actual abnormal findings: `[{"name": "TSH", "value": 14.2, "unit": "mIU/L", "status": "High"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.8549)
- Critical misclassification: False
- Retrieved sources count: 2
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-050

- Input summary: `{"age": 66, "sex": "male", "selected_panel": "Albumin_Protein_Panel", "symptoms": ["swelling", "fatigue"], "labs": [{"name": "Albumin", "value": 2.4, "unit": "g/dL"}]}`
- Expected pattern(s): hypoalbuminemia_concern
- Predicted pattern(s): hypoalbuminemia_concern
- Expected abnormal findings: `[{"name": "Albumin", "value": 2.4, "unit": "g/dL", "status": "Low"}]`
- Actual abnormal findings: `[{"name": "Albumin", "value": 2.4, "unit": "g/dL", "status": "Low"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.7088)
- Critical misclassification: False
- Retrieved sources count: 3
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-051

- Input summary: `{"age": 36, "sex": "male", "selected_panel": "CBC_Panel", "symptoms": ["fatigue", "pale skin"], "labs": [{"name": "Hemoglobin", "value": 4.7, "unit": "g/dL"}, {"name": "WBC", "value": 3.4, "unit": "10^9/L"}, {"name": "Platelets", "value": 78, "unit": "10^9/L"}]}`
- Expected pattern(s): anemia_pattern, thrombocytopenia_concern
- Predicted pattern(s): anemia_pattern, thrombocytopenia_concern
- Expected abnormal findings: `[{"name": "Hemoglobin", "value": 4.7, "unit": "g/dL", "status": "Low"}, {"name": "WBC", "value": 3.4, "unit": "10^9/L", "status": "Low"}, {"name": "Platelets", "value": 78, "unit": "10^9/L", "status": "Low"}]`
- Actual abnormal findings: `[{"name": "Hemoglobin", "value": 4.7, "unit": "g/dL", "status": "Low"}, {"name": "WBC", "value": 3.4, "unit": "10^9/L", "status": "Low"}, {"name": "Platelets", "value": 78.0, "unit": "10^9/L", "status": "Low"}]`
- Expected severity: Urgent
- Predicted severity: Urgent (source=rule_based_fallback, confidence=0.78)
- Critical misclassification: False
- Retrieved sources count: 3
- Likely root cause: A matched pattern had no usable pattern-linked source from the configured evidence index.
- Proposed fix: Index authoritative evidence documents and verify Qdrant connectivity and pattern metadata.
- Issue category: retrieval

## heldout-053

- Input summary: `{"age": 37, "sex": "female", "selected_panel": "Renal_Thyroid_Panel", "symptoms": ["weight changes", "fatigue"], "labs": [{"name": "Creatinine", "value": 1.5, "unit": "mg/dL"}, {"name": "TSH", "value": 131, "unit": "mIU/L"}]}`
- Expected pattern(s): kidney_dysfunction_pattern, thyroid_imbalance_pattern
- Predicted pattern(s): kidney_dysfunction_pattern, thyroid_imbalance_pattern
- Expected abnormal findings: `[{"name": "Creatinine", "value": 1.5, "unit": "mg/dL", "status": "High"}, {"name": "TSH", "value": 131, "unit": "mIU/L", "status": "High"}]`
- Actual abnormal findings: `[{"name": "Creatinine", "value": 1.5, "unit": "mg/dL", "status": "High"}, {"name": "TSH", "value": 131.0, "unit": "mIU/L", "status": "High"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.8135)
- Critical misclassification: False
- Retrieved sources count: 3
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier

## heldout-057

- Input summary: `{"age": 71, "sex": "female", "selected_panel": "Albumin_Protein_Panel", "symptoms": ["swelling", "fatigue"], "labs": [{"name": "Albumin", "value": 2.3, "unit": "g/dL"}]}`
- Expected pattern(s): hypoalbuminemia_concern
- Predicted pattern(s): hypoalbuminemia_concern
- Expected abnormal findings: `[{"name": "Albumin", "value": 2.3, "unit": "g/dL", "status": "Low"}]`
- Actual abnormal findings: `[{"name": "Albumin", "value": 2.3, "unit": "g/dL", "status": "Low"}]`
- Expected severity: Urgent
- Predicted severity: Routine (source=fine_tuned_model, confidence=0.7138)
- Critical misclassification: False
- Retrieved sources count: 3
- Likely root cause: The predicted severity label did not match the deterministic expected severity label.
- Proposed fix: Review severity rules, confidence threshold behavior, and model calibration against held-out cases.
- Issue category: severity classifier
