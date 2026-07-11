# Held-out Evaluation Failure Cases

Generated from `eval/results.json` for the evaluation run at `2026-07-11T12:36:48.646081+00:00`. These are observed pipeline failures, not invented clinical cases.

## heldout-003

- Input summary: `{"age": 29, "sex": "female", "selected_panel": "CBC_Panel", "symptoms": ["bruising", "gum bleeding"], "labs": [{"name": "Hemoglobin", "value": 12.6, "unit": "g/dL"}, {"name": "WBC", "value": 6.1, "unit": "10^9/L"}, {"name": "Platelets", "value": 92, "unit": "10^9/L"}]}`
- Expected pattern(s): thrombocytopenia_concern
- Predicted pattern(s): thrombocytopenia_concern
- Expected abnormal findings: `[{"name": "Platelets", "value": 92, "unit": "10^9/L", "status": "Low"}]`
- Actual abnormal findings: `[{"name": "Platelets", "value": 92.0, "unit": "10^9/L", "status": "Low"}]`
- Retrieved sources count: 0
- Likely root cause: A matched pattern had no usable pattern-linked source from the configured evidence index.
- Proposed fix: Index authoritative evidence documents and verify Qdrant connectivity and pattern metadata.
- Issue category: retrieval

## heldout-005

- Input summary: `{"age": 54, "sex": "female", "selected_panel": "CBC_Panel", "symptoms": ["headache"], "labs": [{"name": "Hemoglobin", "value": 13.0, "unit": "g/dL"}, {"name": "WBC", "value": 8.0, "unit": "10^9/L"}, {"name": "Platelets", "value": 560, "unit": "10^9/L"}]}`
- Expected pattern(s): platelet_elevation_concern
- Predicted pattern(s): platelet_elevation_concern
- Expected abnormal findings: `[{"name": "Platelets", "value": 560, "unit": "10^9/L", "status": "High"}]`
- Actual abnormal findings: `[{"name": "Platelets", "value": 560.0, "unit": "10^9/L", "status": "High"}]`
- Retrieved sources count: 0
- Likely root cause: A matched pattern had no usable pattern-linked source from the configured evidence index.
- Proposed fix: Index authoritative evidence documents and verify Qdrant connectivity and pattern metadata.
- Issue category: retrieval

## heldout-007

- Input summary: `{"age": 72, "sex": "female", "selected_panel": "CBC_Panel", "symptoms": ["fever", "fatigue", "easy bruising"], "labs": [{"name": "Hemoglobin", "value": 10.8, "unit": "g/dL"}, {"name": "WBC", "value": 18.2, "unit": "10^9/L"}, {"name": "Platelets", "value": 118, "unit": "10^9/L"}]}`
- Expected pattern(s): anemia_pattern, infection_inflammation_pattern, thrombocytopenia_concern
- Predicted pattern(s): anemia_pattern, infection_inflammation_pattern, thrombocytopenia_concern
- Expected abnormal findings: `[{"name": "Hemoglobin", "value": 10.8, "unit": "g/dL", "status": "Low"}, {"name": "WBC", "value": 18.2, "unit": "10^9/L", "status": "High"}, {"name": "Platelets", "value": 118, "unit": "10^9/L", "status": "Low"}]`
- Actual abnormal findings: `[{"name": "Hemoglobin", "value": 10.8, "unit": "g/dL", "status": "Low"}, {"name": "WBC", "value": 18.2, "unit": "10^9/L", "status": "High"}, {"name": "Platelets", "value": 118.0, "unit": "10^9/L", "status": "Low"}]`
- Retrieved sources count: 6
- Likely root cause: A matched pattern had no usable pattern-linked source from the configured evidence index.
- Proposed fix: Index authoritative evidence documents and verify Qdrant connectivity and pattern metadata.
- Issue category: retrieval

## heldout-051

- Input summary: `{"age": 36, "sex": "male", "selected_panel": "CBC_Panel", "symptoms": ["fatigue", "pale skin"], "labs": [{"name": "Hemoglobin", "value": 4.7, "unit": "g/dL"}, {"name": "WBC", "value": 3.4, "unit": "10^9/L"}, {"name": "Platelets", "value": 78, "unit": "10^9/L"}]}`
- Expected pattern(s): anemia_pattern, thrombocytopenia_concern
- Predicted pattern(s): anemia_pattern, thrombocytopenia_concern
- Expected abnormal findings: `[{"name": "Hemoglobin", "value": 4.7, "unit": "g/dL", "status": "Low"}, {"name": "WBC", "value": 3.4, "unit": "10^9/L", "status": "Low"}, {"name": "Platelets", "value": 78, "unit": "10^9/L", "status": "Low"}]`
- Actual abnormal findings: `[{"name": "Hemoglobin", "value": 4.7, "unit": "g/dL", "status": "Low"}, {"name": "WBC", "value": 3.4, "unit": "10^9/L", "status": "Low"}, {"name": "Platelets", "value": 78.0, "unit": "10^9/L", "status": "Low"}]`
- Retrieved sources count: 3
- Likely root cause: A matched pattern had no usable pattern-linked source from the configured evidence index.
- Proposed fix: Index authoritative evidence documents and verify Qdrant connectivity and pattern metadata.
- Issue category: retrieval
