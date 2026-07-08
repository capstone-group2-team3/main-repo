import json
import os
import difflib  # Used for fuzzy matching as required by the task

# Global collections to store processed data for efficient access
REVERSE_LAB_ALIASES = {}
KNOWN_SYMPTOMS = set()

def load_normalizer_data():
    """
    Loads aliases and symptom lists once during startup.
    Builds the reverse mapping for lab names and a set for known symptoms.
    """
    global REVERSE_LAB_ALIASES, KNOWN_SYMPTOMS
    
    # 1. Load lab aliases and build the reverse mapping
    aliases_path = "data/lab_name_aliases.json"
    if os.path.exists(aliases_path):
        try:
            with open(aliases_path, "r", encoding="utf-8") as f:
                original_aliases = json.load(f)
                for standard_name, aliases_list in original_aliases.items():
                    for alias in aliases_list:
                        # Map every alias to the standard name for O(1) lookup
                        REVERSE_LAB_ALIASES[alias.lower().strip()] = standard_name
            print("Lab aliases successfully mapped.")
        except Exception as e:
            print(f"Error loading lab aliases: {e}")

    # 2. Load suggested_symptoms from panel_templates.json for normalization
    templates_path = "data/panel_templates.json"
    if os.path.exists(templates_path):
        try:
            with open(templates_path, "r", encoding="utf-8") as f:
                templates = json.load(f)
                for panel in templates.values():
                    # Collect all symptoms to use as a reference for normalization
                    for sym in panel.get("suggested_symptoms", []):
                        KNOWN_SYMPTOMS.add(sym.lower().strip())
            print("Known symptoms loaded for fuzzy matching.")
        except Exception as e:
            print(f"Error loading templates for symptoms: {e}")

# Trigger loading process immediately
load_normalizer_data()

def normalize_lab_name(name: str) -> str:
    """
    Standardizes a lab test name.
    Matches the input against the reverse dictionary.
    """
    if not name: 
        return ""
    
    clean_name = name.lower().strip()
    
    # Return standard name if match found
    if clean_name in REVERSE_LAB_ALIASES:
        return REVERSE_LAB_ALIASES[clean_name]
    
    # Log warning for unknown labs
    print(f"WARNING: Unknown lab name encountered - '{name}'.")
    return name.strip()

def normalize_symptom(text: str) -> str:
    """
    Standardizes a clinical symptom name using exact or fuzzy matching
    against the list of known symptoms from the templates.
    """
    if not text: 
        return ""
        
    clean_text = text.lower().strip()
    
    # 1. Attempt Exact Match
    if clean_text in KNOWN_SYMPTOMS:
        return clean_text
        
    # 2. Attempt Fuzzy Match (as requested in the task description)
    # n=1: return the single best match, cutoff=0.7: 70% similarity threshold
    matches = difflib.get_close_matches(clean_text, list(KNOWN_SYMPTOMS), n=1, cutoff=0.7)
    
    if matches:
        return matches[0]
        
    # If no match found, return the cleaned original text
    return clean_text

if __name__ == "__main__":
    print(normalize_lab_name("Hgb"))  
    print(normalize_symptom("fatige")) 