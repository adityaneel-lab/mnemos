
import uuid
import chromadb

from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction,
)

# Persistent local vector database
client = chromadb.PersistentClient(
    path="./chroma_db"
)

# Local embedding model
embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name="user_memories",
    embedding_function=embedding_function,
    metadata={"hnsw:space": "cosine"},
)


def save_memory(
    text: str,
    user_id: str = "default",
    category: str = "general",
):
    """Save a memory, avoiding close semantic duplicates."""

    text = text.strip()

    if not text:
        return

    # Search existing memories for a close match
    existing = collection.query(
        query_texts=[text],
        n_results=1,
        where={"user_id": user_id},
    )

    if existing["ids"] and existing["ids"][0]:
        distance = existing["distances"][0][0]

        # Update an existing memory if it is very similar
        if distance < 0.15:
            memory_id = existing["ids"][0][0]

            collection.update(
                ids=[memory_id],
                documents=[text],
                metadatas=[{
                    "user_id": user_id,
                    "category": category,
                }],
            )
            return

    memory_id = str(uuid.uuid4())

    collection.add(
        ids=[memory_id],
        documents=[text],
        metadatas=[{
            "user_id": user_id,
            "category": category,
        }],
    )


def search_memories(
    query: str,
    user_id: str = "default",
    limit: int = 5,
):
    total = collection.count()

    if total == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(limit, total),
        where={"user_id": user_id},
        include=["documents", "distances", "metadatas"],
    )

    memories = []

    if results["documents"] and results["documents"][0]:
        for document, distance, metadata in zip(
            results["documents"][0],
            results["distances"][0],
            results["metadatas"][0],
        ):
            memories.append({
                "text": document,
                "distance": distance,
                "category": metadata.get("category", "general"),
            })

    return memories


def filter_relevant_memories(
    memories: list,
    max_distance: float = 0.60,
):
    relevant_memories = []

    for memory in memories:
        if memory["distance"] <= max_distance:
            relevant_memories.append(memory)

    return relevant_memories


def get_all_memories(user_id: str = "default"):
    """Return all memories belonging to one user."""

    results = collection.get(
        where={"user_id": user_id},
        include=["documents", "metadatas"],
    )

    return [
        {
            "id": memory_id,
            "text": text,
            "category": metadata.get("category", "general"),
        }
        for memory_id, text, metadata in zip(
            results["ids"],
            results["documents"],
            results["metadatas"],
        )
    ]


def delete_memory(memory_id: str, user_id: str = "default"):
    """Delete a memory only if it belongs to this user."""

    result = collection.get(
        ids=[memory_id],
        where={"user_id": user_id},
    )

    if result["ids"]:
        collection.delete(ids=[memory_id])
        return True

    return False
