import os
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "novatech-docs"

_model = None


def _get_model() -> SentenceTransformer:
    """Lazy-loads the embedding model (singleton)."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def search(question: str, n_results: int = 3) -> list[dict]:
    """
    Searches the ChromaDB collection for the N most similar chunks.

    Returns a list of dicts with:
      - text: full chunk text
      - filename: source document filename
      - section_title: markdown section title
      - doc_title: top-level document title
      - distance: cosine distance score (lower = more similar)
    """
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(COLLECTION_NAME)

    model = _get_model()
    query_embedding = model.encode(question).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for text, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(
            {
                "text": text,
                "filename": metadata["filename"],
                "doc_title": metadata["doc_title"],
                "section_title": metadata["section_title"],
                "distance": round(distance, 4),
            }
        )

    return chunks


if __name__ == "__main__":
    question = input("Pergunta: ").strip()
    results = search(question)

    print(f"\nTop {len(results)} chunk(s) para: '{question}'\n")
    for i, chunk in enumerate(results, 1):
        print(f"--- Resultado {i} ---")
        print(f"Arquivo : {chunk['filename']}")
        print(f"Seção   : {chunk['section_title']}")
        print(f"Distância: {chunk['distance']}")
        print(f"Texto:\n{chunk['text']}\n")
