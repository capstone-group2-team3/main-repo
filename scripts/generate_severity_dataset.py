import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import random
from pathlib import Path

# Import custom services
from app.services.lab_normalizer import LabNormalizer
from app.services.clinical_pattern_scorer import ClinicalPatternScorer
from app.services.lab_analysis_agent import LabAnalysisAgent 

def build_severity_input_text(case: dict, abnormal_labs: list, top_pattern_name: str) -> str:
    """
    Format case data into a single descriptive text string for the model.
    """
    age = case.get("age", "Unknown")
    sex = case.get("sex", "Unknown")
    panel = case.get("panel", "Unknown")
    
    symptoms_str = ", ".join(case.get("symptoms", [])) if case.get("symptoms") else "None"
    
    if abnormal_labs:
        abnormal_labs_str = ", ".join([f"{lab['test_name']} {lab['status']}" for lab in abnormal_labs])
    else:
        abnormal_labs_str = "None"
        
    text = (f"Age: {age}, Sex: {sex}, Panel: {panel}. "
            f"Abnormal: {abnormal_labs_str}. "
            f"Symptoms: {symptoms_str}. "
            f"Top pattern: {top_pattern_name}.")
    
    return text

def determine_severity(abnormal_labs: list, top_pattern_code: str, patterns_data: dict) -> str:
    """
    Apply T31 labeling schema rules to determine severity level.
    """
    # 1. Hard Override Rule (Critical Safety Net)
    for lab in abnormal_labs:
        if lab.get("status") == "Critical":
            return "Critical"
            
    # 2. Base Levels from Schema
    if top_pattern_code and top_pattern_code in patterns_data:
        return patterns_data[top_pattern_code].get("default_severity", "Routine")
        
    return "Routine"

def main():
    print("Starting Dataset Generation (T32)...")
    
    # 1. Initialize classes
    normalizer = LabNormalizer()
    scorer = ClinicalPatternScorer(normalizer=normalizer)
    patterns_data = scorer._load_json()
    
    # تعريف الكلاس تبعك
    lab_agent = LabAnalysisAgent(normalizer=normalizer)
    
    # File paths
    input_cases_file = Path("data/synthetic_cases.jsonl")
    train_file = Path("data/severity_training_data.jsonl")
    val_file = Path("data/severity_val_data.jsonl")
    heldout_file = Path("data/eval/heldout.jsonl")
    
    # Ensure input file exists
    if not input_cases_file.exists():
        print(f"Error: {input_cases_file} not found. Please ensure T6 cases are generated.")
        return

    processed_cases = []
    
    # 2. Process cases
    with open(input_cases_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            case = json.loads(line)
            
            # ----------------- التعديل الذكي لقراءة الداتا -----------------
            raw_labs = []
            lab_results_data = case.get("lab_results", [])
            
            if isinstance(lab_results_data, dict):
                # إذا كانت الداتا محفوظة كقاموس
                for test_name, details in lab_results_data.items():
                    if isinstance(details, dict):
                        raw_labs.append({
                            "name": test_name,
                            "value": details.get("value", 0),
                            "unit": details.get("unit", "")
                        })
                    else:
                        raw_labs.append({
                            "name": test_name,
                            "value": details,
                            "unit": ""
                        })
            elif isinstance(lab_results_data, list):
                # إذا كانت الداتا محفوظة كقائمة
                for lab in lab_results_data:
                    if isinstance(lab, dict):
                        raw_labs.append({
                            "name": lab.get("test_name", lab.get("name", "")),
                            "value": lab.get("value", 0),
                            "unit": lab.get("unit", "")
                        })
            # ---------------------------------------------------------------
            
            # استدعاء دالة analyze_labs من كودك
            analyzed_data = lab_agent.analyze_labs(case.get("panel", ""), raw_labs)
            
            evaluated_labs = []
            for res in analyzed_data:
                evaluated_labs.append({
                    "test_name": res["test_name"],
                    "value": res["value"],
                    "status": res["status"]
                })
            
            # Extract abnormal labs
            abnormal_labs = [lab for lab in evaluated_labs if lab["status"] not in ["Normal", "Unknown"]]
            
            # Call T11 (Clinical Pattern Scorer)
            top_patterns = scorer.score_patterns(
                selected_panel=case.get("panel", ""),
                lab_results=evaluated_labs,
                symptoms=case.get("symptoms", [])
            )
            
            top_pattern_name = top_patterns[0]["pattern_name"] if top_patterns else "None"
            top_pattern_code = top_patterns[0]["pattern_code"] if top_patterns else ""
            
            # Build input text and assign severity label
            input_text = build_severity_input_text(case, abnormal_labs, top_pattern_name)
            severity_label = determine_severity(abnormal_labs, top_pattern_code, patterns_data)
            
            processed_cases.append({
                "text": input_text,
                "label": severity_label
            })

    # 3. Data Splitting
    random.shuffle(processed_cases)
    total_cases = len(processed_cases)
    
    # Reserve 20% for Heldout (Evaluation)
    heldout_count = int(total_cases * 0.2)
    heldout_data = processed_cases[:heldout_count]
    remaining_data = processed_cases[heldout_count:]
    
    # Split remaining data: 80% Train, 20% Validation
    val_count = int(len(remaining_data) * 0.2)
    val_data = remaining_data[:val_count]
    train_data = remaining_data[val_count:]
    
    # 4. Save output files
    Path("data/eval").mkdir(parents=True, exist_ok=True)
    
    def save_jsonl(data: list, filepath: Path):
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
                
    save_jsonl(train_data, train_file)
    save_jsonl(val_data, val_file)
    save_jsonl(heldout_data, heldout_file)
    
    print(f"Done! Generated {len(train_data)} train, {len(val_data)} val, and {len(heldout_data)} heldout cases.")

if __name__ == "__main__":
    main()