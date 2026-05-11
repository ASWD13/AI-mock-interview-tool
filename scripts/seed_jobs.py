"""Seed ChromaDB with job embeddings from jobs_dataset.json."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chromadb
from ml.embeddings.embed_utils import generate_embeddings_batch


def get_chroma_client():
    """Get ChromaDB client — local persistent (no server needed)."""
    chroma_dir = os.path.join(os.path.dirname(__file__), "..", "chroma_data")
    os.makedirs(chroma_dir, exist_ok=True)
    return chromadb.PersistentClient(path=chroma_dir)


def seed_jobs():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "jobs_dataset.json")
    with open(data_path, "r") as f:
        jobs = json.load(f)

    print(f"Loading {len(jobs)} jobs...")
    client = get_chroma_client()
    collection = client.get_or_create_collection(name="jobs")

    documents, ids, metadatas = [], [], []
    for job in jobs:
        doc_text = f"{job['job_title']} at {job['company']}. Skills: {', '.join(job.get('required_skills', []))}. {job.get('description', '')}"
        documents.append(doc_text)
        ids.append(job["job_id"])
        metadatas.append({
            "job_title": job["job_title"],
            "company": job["company"],
            "location": job.get("location", "Remote"),
            "required_skills": ",".join(job.get("required_skills", [])),
            "experience_level": job.get("experience_level", "mid"),
        })

    print("Generating embeddings...")
    embeddings = generate_embeddings_batch(documents)

    print("Upserting to ChromaDB...")
    for i in range(0, len(ids), 50):
        kwargs = {"ids": ids[i:i+50], "documents": documents[i:i+50], "metadatas": metadatas[i:i+50]}
        batch_emb = embeddings[i:i+50] if embeddings and embeddings[0] else None
        if batch_emb and all(e for e in batch_emb):
            kwargs["embeddings"] = batch_emb
        collection.upsert(**kwargs)

    print(f"✅ Seeded {len(ids)} jobs into ChromaDB.")


if __name__ == "__main__":
    seed_jobs()
