from app.services.evidence_retrieval_agent import EvidenceRetrievalAgent

# Manual retrieval smoke probe retained for backward compatibility.
retriever = EvidenceRetrievalAgent()

pattern = {
    "pattern_code": "anemia_pattern",
    "pattern_name": "Anemia Pattern",
    "evidence_for": ["Hemoglobin Low", "RBC Low"],
}

if __name__ == "__main__":
    print(retriever.retrieve_for_pattern(pattern, top_k=3))
