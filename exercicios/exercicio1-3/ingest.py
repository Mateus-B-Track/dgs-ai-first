import os
import re
import chromadb
from sentence_transformers import SentenceTransformer

DOCS_FOLDER = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "specifics")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "novatech-docs"


def load_markdown_files(folder: str) -> list[dict]:
    """Reads all .md files from the given folder."""
    documents = []
    for filename in os.listdir(folder):
        if filename.endswith(".md"):
            filepath = os.path.join(folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            documents.append({"filename": filename, "content": content})
    return documents


def split_into_chunks(document: dict) -> list[dict]:
    """
    Splits markdown content into chunks by section headers (## and ###).
    Each chunk retains the section title as part of its text and as metadata.
    Preserves the top-level title (# heading) as a fallback title prefix.
    """
    filename = document["filename"]
    content = document["content"]

    # Extract top-level document title if present
    doc_title_match = re.match(r"^#\s+(.+)", content, re.MULTILINE)
    doc_title = doc_title_match.group(1).strip() if doc_title_match else filename

    # Split on ## or ### headers, keeping the delimiter
    parts = re.split(r"(?m)(?=^#{2,3}\s+)", content)

    chunks = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Check if this part starts with a ## or ### header
        header_match = re.match(r"^(#{2,3})\s+(.+)", part)
        if header_match:
            section_title = header_match.group(2).strip()
        else:
            # Content before any ## heading (intro / document header)
            section_title = doc_title

        # Skip chunks that are only a header with no body text
        body = part[len(header_match.group(0)):].strip() if header_match else part
        if not body:
            continue

        chunks.append(
            {
                "text": part,          # full chunk text including the section header
                "filename": filename,
                "doc_title": doc_title,
                "section_title": section_title,
            }
        )

    return chunks


def generate_chunk_id(filename: str, section_title: str, index: int) -> str:
    """Creates a deterministic, URL-safe ID for a chunk."""
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", filename)
    safe_section = re.sub(r"[^a-zA-Z0-9_-]", "_", section_title)
    return f"{safe_name}__{safe_section}__{index}"


def ingest():
    print(f"Loading documents from: {os.path.abspath(DOCS_FOLDER)}")
    documents = load_markdown_files(DOCS_FOLDER)
    print(f"  Found {len(documents)} file(s): {[d['filename'] for d in documents]}")

    all_chunks = []
    for doc in documents:
        chunks = split_into_chunks(doc)
        print(f"  {doc['filename']} → {len(chunks)} chunk(s)")
        all_chunks.extend(chunks)

    print(f"\nTotal chunks to index: {len(all_chunks)}")

    # Generate embeddings
    print("\nLoading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    texts = [chunk["text"] for chunk in all_chunks]
    print("Generating embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    # Store in ChromaDB
    print("\nConnecting to ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Drop collection if it already exists to allow re-ingestion
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
        print(f"  Existing collection '{COLLECTION_NAME}' deleted.")

    collection = client.create_collection(COLLECTION_NAME)
    print(f"  Collection '{COLLECTION_NAME}' created.")

    ids = [
        generate_chunk_id(chunk["filename"], chunk["section_title"], i)
        for i, chunk in enumerate(all_chunks)
    ]
    metadatas = [
        {
            "filename": chunk["filename"],
            "doc_title": chunk["doc_title"],
            "section_title": chunk["section_title"],
        }
        for chunk in all_chunks
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    print(f"\nDone! {len(all_chunks)} chunks stored in collection '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    ingest()
