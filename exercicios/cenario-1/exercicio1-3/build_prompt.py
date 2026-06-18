import os

SYSTEM_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "exercicio1-2", "system-prompt-v2"
)


def _load_system_prompt() -> str:
    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def build_prompt(question: str, chunks: list[dict]) -> str:
    """
    Assembles the full prompt to send to the LLM.

    Structure:
      [SYSTEM PROMPT]           <- static, from system-prompt-v2
      [DOCUMENTATION CHUNKS]   <- dynamic, retrieved by search()
      [QUESTION]               <- dynamic, from the attendant

    Parameters:
      question : the attendant's question
      chunks   : list of dicts returned by search(), each containing
                 'text', 'filename', 'doc_title', 'section_title', 'distance'

    Returns:
      A single string ready to be sent as the user/human turn to the LLM,
      with the system prompt prepended as a clearly delimited block.
    """
    system_prompt = _load_system_prompt()

    chunks_block_lines = []
    for i, chunk in enumerate(chunks, 1):
        chunks_block_lines.append(
            f"--- Chunk {i} | Arquivo: {chunk['filename']} | Seção: {chunk['section_title']} ---"
        )
        chunks_block_lines.append(chunk["text"])
        chunks_block_lines.append("")

    chunks_block = "\n".join(chunks_block_lines).strip()

    prompt = (
        f"{system_prompt}\n\n"
        f"## DOCUMENTAÇÃO RECUPERADA\n\n"
        f"{chunks_block}\n\n"
        f"## PERGUNTA DO ATENDENTE\n\n"
        f"{question}"
    )

    return prompt


if __name__ == "__main__":
    from search import search

    question = input("Pergunta: ").strip()
    chunks = search(question, n_results=3)
    prompt = build_prompt(question, chunks)

    print("\n" + "=" * 60)
    print("PROMPT MONTADO:")
    print("=" * 60)
    print(prompt)
    print("=" * 60)
    print(f"\nTotal de caracteres: {len(prompt)}")
    print(f"Estimativa de tokens: ~{len(prompt) // 4}")
