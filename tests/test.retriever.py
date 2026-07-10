from app.services.evidence_retrieval_agent import EvidenceRetrievalAgent

# Test
retriever = EvidenceRetrievalAgent()

pattern = {
    "pattern_code": "anemia_pattern",
    "pattern_name": "Anemia Pattern",
    "evidence_for": ["Hemoglobin Low", "RBC Low"]
}

results = retriever.retrieve_for_pattern(pattern, top_k=3)
print(results)