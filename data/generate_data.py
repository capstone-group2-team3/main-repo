import json
import random

routines = [
    "Age: {age}, Sex: {sex}, Panel: CBC. Abnormal: None. Symptoms: None. Top pattern: None.",
    "Age: {age}, Sex: {sex}, Panel: Comprehensive. Abnormal: Cholesterol High. Symptoms: mild fatigue. Top pattern: Lipid Dysregulation.",
    "Age: {age}, Sex: {sex}, Panel: Metabolic. Abnormal: Glucose High, HbA1c High. Symptoms: increased thirst, polyuria. Top pattern: Diabetes Management.",
    "Age: {age}, Sex: {sex}, Panel: Thyroid. Abnormal: TSH Slightly High. Symptoms: mild weight gain, dry skin. Top pattern: Subclinical Hypothyroidism.",
    "Age: {age}, Sex: {sex}, Panel: CBC. Abnormal: Platelets Normal. Symptoms: routine checkup. Top pattern: None.",
    "Age: {age}, Sex: {sex}, Panel: Liver. Abnormal: ALT Mildly Elevated. Symptoms: none. Top pattern: Fatty Liver Screening."
]

urgents = [
    "Age: {age}, Sex: {sex}, Panel: Metabolic. Abnormal: Potassium High, Creatinine High. Symptoms: muscle weakness, nausea, decreased urination. Top pattern: Renal Insufficiency.",
    "Age: {age}, Sex: {sex}, Panel: CBC. Abnormal: WBC High ({wbc_val}). Symptoms: high fever, localized pain, chills, productive cough. Top pattern: Acute Infection.",
    "Age: {age}, Sex: {sex}, Panel: CBC. Abnormal: Leukocytosis detected. Symptoms: fever, body aches, painful urination. Top pattern: Urinary Tract Infection.",
    "Age: {age}, Sex: {sex}, Panel: Liver. Abnormal: ALT High, AST High. Symptoms: severe abdominal pain, jaundice, nausea. Top pattern: Hepatic Stress.",
    "Age: {age}, Sex: {sex}, Panel: Metabolic. Abnormal: Sodium Low. Symptoms: confusion, headache, mild vomiting. Top pattern: Electrolyte Imbalance."
]

criticals = [
    "Age: {age}, Sex: {sex}, Panel: CBC. Abnormal: Hemoglobin Critical Low ({hb_val}). Symptoms: severe dizziness, shortness of breath, syncope. Top pattern: Severe Anemia.",
    "Age: {age}, Sex: {sex}, Panel: Unknown. Abnormal: None. Symptoms: severe chest pain, radiating jaw pain, sweating, pressure in chest. Top pattern: Suspected Myocardial Infarction.",
    "Age: {age}, Sex: {sex}, Panel: Cardiac. Abnormal: Troponin High ({trop_val}). Symptoms: crushing chest pain, dyspnea, left arm numbness. Top pattern: Acute Coronary Syndrome.",
    "Age: {age}, Sex: {sex}, Panel: CBC. Abnormal: Platelets Critical Low ({plt_val}). Symptoms: active bleeding, severe bruising, epistaxis. Top pattern: Severe Thrombocytopenia."
]

def generate_dataset(num_samples):
    dataset = []
    sex_options = ["Male", "Female", "Unknown"]
    
    for _ in range(num_samples):
        age = random.randint(1, 90)
        sex = random.choice(sex_options)
        label = random.choice(["Routine", "Urgent", "Critical"])
        
        if label == "Routine":
            text = random.choice(routines).format(age=age, sex=sex)
        elif label == "Urgent":
            wbc_val = round(random.uniform(15.0, 24.0), 1)
            text = random.choice(urgents).format(age=age, sex=sex, wbc_val=wbc_val)
        else:
            hb_val = round(random.uniform(3.5, 6.8), 1)
            trop_val = round(random.uniform(1.5, 10.0), 2)
            plt_val = random.randint(10, 45)
            text = random.choice(criticals).format(
                age=age, sex=sex, hb_val=hb_val, trop_val=trop_val, plt_val=plt_val
            )
            
        dataset.append({"text": text, "label": label})
    return dataset

train_data = generate_dataset(1000)
val_data = generate_dataset(200)

with open("data/severity_training_data.jsonl", "w", encoding="utf-8") as f:
    for item in train_data:
        f.write(json.dumps(item) + "\n")

with open("data/severity_val_data.jsonl", "w", encoding="utf-8") as f:
    for item in val_data:
        f.write(json.dumps(item) + "\n")

print("Successfully generated 1000 training samples and 200 validation samples!")