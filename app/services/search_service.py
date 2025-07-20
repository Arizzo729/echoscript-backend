# app/services/search_service.py
from typing import List, Dict
from sentence_transformers import SentenceTransformer, util
import torch
import re

# Load a transformer-based embedding model
_model = SentenceTransformer("all-MiniLM-L6-v2")

documents = [
    {"id": 1, "title": "How to use FastAPI", "content": "FastAPI is a modern web framework for Python."},
    {"id": 2, "title": "Introduction to Machine Learning", "content": "Machine learning enables systems to learn from data."},
    {"id": 3, "title": "Python Tips and Tricks", "content": "This article explores advanced features in Python."},
    {"id": 4, "title": "Deploying ML Models", "content": "You can deploy models using containers and cloud services."},
    {"id": 5, "title": "WhisperX Speech Transcription", "content": "WhisperX is used for accurate audio transcription."},
]

# Pre-compute embeddings for all documents
_texts = [f"{doc['title']} {doc['content']}" for doc in documents]
_doc_embeddings = _model.encode(_texts, convert_to_tensor=True, normalize_embeddings=True)

def search_documents(query: str, limit: int = 10) -> List[Dict]:
    """
    Perform semantic search using transformer embeddings.

    :param query: Search string
    :param limit: Number of results to return
    :return: List of matching documents
    """
    try:
        query_embedding = _model.encode(query, convert_to_tensor=True, normalize_embeddings=True)
        scores = util.cos_sim(query_embedding, _doc_embeddings)[0]
        top_results = torch.topk(scores, k=min(limit, len(documents)))

        results = []
        for idx in top_results.indices:
            doc = documents[idx]
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "score": float(scores[idx])
            })

        return results

    except Exception as e:
        return [{"error": str(e)}]