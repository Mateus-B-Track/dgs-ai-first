# Tarefa 4 — Problemas Identificados e Propostas de Correção

**Exercício 1.3 | Desenvolvedor | Data: 05/06/2026**

---

## Base de análise

Esta análise combina três fontes de evidência:
1. **Saída do `search.py`** — top 3 chunks retornados por busca vetorial pura para cada pergunta
2. **Saída do `build_prompt.py`** — prompt montado e enviado ao LLM (com configuração `n_results=1` ou `n_results=3`)
3. **Respostas do Claude** — avaliação qualitativa de correção, citação de fonte e aderência aos guardrails

---

## Avaliação das respostas do Claude

| # | Pergunta | Chunks enviados ao Claude | Resposta correta? | Citou fonte? | Respeitou guardrails? |
|---|---|---|---|---|---|
| 1 | Cargas perigosas podem ser devolvidas? | FAQ seguro (irrelevante) + PROC-042-v1 seção 4 (irrelevante) + POL-001 seção 3.2 ✅ | ✅ Sim — "NÃO são elegíveis" | ✅ POL-001, seção 3.2 | ✅ Completo |
| 2 | Cargas perigosas podem ser devolvidas? (reteste) | Idem pergunta 1 | ✅ Sim | ✅ POL-001, seção 3.2 | ✅ Completo |
| 3 | Qual o SLA do cliente Gold? | SLA seção 5 (medição, sem valores) + FAQ Item 41 ✅ + FAQ Item 15 (Platinum, irrelevante) | ⚠️ Parcial — valores corretos (2h/24h), mas extraídos do FAQ informal, não da tabela oficial SLA-2024 | ✅ FAQ Item 41 | ✅ Alertou sobre incidentes críticos e SLA não-pausado |
| 4 | Frete para 600kg para Manaus? | PROC-042-v1 seção 1 (apenas objetivo, sem tabela) | ✅ Sim — declarou corretamente "não encontrei os multiplicadores" e orientou escalar | ✅ Citou o que tinha disponível | ✅ Não inventou valores; recomendou supervisor |
| 5 | Qual o multiplicador para o Sudeste? | POL-001 seção 3.4 (irrelevante) + FAQ Item 8 + PROC-042-**v1** seção 2.1 (tabela desatualizada) | ⚠️ Parcial — respondeu 1.0 (valor da v1) mas alertou sobre conflito de versões | ✅ PROC-042-v1, seção 2.1 (correto sobre o chunk disponível) | ✅ Alertou conflito antes de repassar |

**Observação geral:** O LLM (Claude) se comportou de forma exemplar em todos os testes — nunca inventou informação ausente, sempre citou fontes, e ativou os guardrails de alerta quando detectou conflito ou lacuna. **Os problemas identificados são do pipeline de retrieval, não do modelo de linguagem.**

---

## Problema 1 — `build_prompt.py` configurado com `n_results=1`

### Descrição

O `build_prompt.py` passa `n_results=1` ao chamar o `search.py`, usando apenas o chunk mais similar para montar o prompt. Como a busca semântica com `all-MiniLM-L6-v2` não é perfeita, o chunk mais similar frequentemente **não é o chunk correto**.

### Evidência

Nos testes de `build_prompt`, 3 dos 5 casos usaram apenas 1 chunk:
- **Pergunta 3 (SLA Gold):** chunk enviado = SLA seção 5 (medição), sem os valores de SLA por tier. O chunk correto estava em 2º lugar no `search.py` (FAQ Item 41) e foi descartado.
- **Pergunta 4 (Frete Manaus):** chunk enviado = PROC-042-v1 seção 1 (objetivo), sem nenhuma tabela de multiplicadores.
- **Pergunta 5 (Multiplicador Sudeste):** chunk enviado = POL-001 seção 3.4 (devoluções parciais), completamente irrelevante.

Nos testes com Claude (perguntas 1 e 2), o prompt foi montado com 3 chunks — e o Claude conseguiu identificar e usar o chunk correto mesmo com 2 chunks irrelevantes no contexto.

### Impacto

Com `n_results=1`, a taxa de acerto cai para **0/5**. Com `n_results=3`, o Claude demonstrou capacidade de filtrar ruído e responder corretamente nos casos em que o chunk correto estava presente.

### Correção proposta

Alterar o `build_prompt.py` para usar `n_results=3`, alinhado ao comportamento já implementado no `search.py`. Opcionalmente, adicionar um filtro de threshold para descartar chunks com distância acima de um limite (ex: 1.2), em vez de usar um número fixo de chunks.

```python
# Antes (build_prompt.py)
chunks = search(question, n_results=1)

# Depois
chunks = search(question, n_results=3)
# Opcional: filtrar por qualidade
chunks = [c for c in chunks if c['distance'] < 1.2]
```

---

## Problema 2 — Vocabulário geográfico não coberto pelos documentos (gap semântico estrutural)

### Descrição

A pergunta "Frete para 600kg para Manaus?" falhou completamente na recuperação. Os documentos usam **"Região Norte"** como unidade geográfica; a pergunta usa **"Manaus"** (cidade específica). O modelo `all-MiniLM-L6-v2` não possui o conhecimento geográfico necessário para inferir que Manaus pertence à Região Norte. O resultado foi que os chunks retornados tiveram distâncias >1.0 — confirmando falha de busca, não apenas baixo ranking.

### Evidência

Top 3 retornados pelo `search.py` para "Frete para 600kg para Manaus?":

| Rank | Seção | Distância |
|------|-------|-----------|
| 1 | PROC-042-v1, seção 1 — Objetivo | 1.0516 |
| 2 | PROC-042-v2, seção 4 — Condições especiais | 1.0690 |
| 3 | PROC-042-v2, seção 1 — Objetivo | 1.0809 |

A seção com a tabela de multiplicadores (seção 2) não apareceu em nenhum dos resultados. O Claude respondeu corretamente que não tinha informação suficiente — o que é o comportamento ideal do guardrail — mas o usuário ficou sem a resposta.

### Impacto

Qualquer pergunta com nome de cidade, estado ou ponto de referência geográfico retornará resultados irrelevantes. Isso afeta diretamente o domínio de logística, onde clientes frequentemente perguntam por destino específico ("frete para Recife", "entrega em Campinas").

### Correção proposta

Implementar uma etapa de **query expansion** antes da busca vetorial: um dicionário estático que normaliza termos geográficos para os valores usados nos documentos antes de gerar o embedding da query.

```python
REGIAO_MAP = {
    "manaus": "Região Norte",
    "belém": "Região Norte",
    "fortaleza": "Região Nordeste",
    "recife": "Região Nordeste",
    "salvador": "Região Nordeste",
    "são paulo": "Região Sudeste",
    "rio de janeiro": "Região Sudeste",
    "belo horizonte": "Região Sudeste",
    "curitiba": "Região Sul",
    "porto alegre": "Região Sul",
    "brasília": "Região Centro-Oeste",
    "goiânia": "Região Centro-Oeste",
}

def expand_query(question: str) -> str:
    q = question.lower()
    for city, region in REGIAO_MAP.items():
        if city in q:
            q = q.replace(city, f"{city} ({region})")
    return q
```

Chamada no `search.py`:
```python
expanded = expand_query(question)
embedding = model.encode(expanded)
```

---

## Problema 3 — Chunk correto enterrado por ruído semântico (termos multi-contextuais)

### Descrição

Para a pergunta "Cargas perigosas podem ser devolvidas?", o chunk correto (POL-001, seção 3.2) ficou em **3º lugar** (distância 0.79), atrás de:
1. FAQ Item 22 — seguro de carga (menciona "cargas perigosas" no contexto de percentual de seguro, distância 0.74)
2. PROC-042-v1, seção 4 — condições de frete (menciona "cargas perigosas" no contexto de peso, distância 0.77)

O modelo de embedding detectou presença do termo "cargas perigosas" mas não discriminou a intenção (devolução vs. seguro vs. frete). A margem entre o 1º e o 3º lugar é de apenas 0.045 — instável o suficiente para variar entre execuções.

### Impacto

Com `n_results=1`, o resultado é completamente errado. Com `n_results=3`, o Claude conseguiu recuperar, mas isso é uma dependência frágil: se o LLM for menos capaz de filtrar ruído, ou se o chunk correto cair para 4º lugar em outra execução, a resposta estará errada.

### Correção proposta

Adicionar **metadados de categoria** nos chunks durante a ingestão, e usar filtros de metadados no momento da busca quando a intenção puder ser inferida a partir de palavras-chave na pergunta.

```python
# Mapeamento de intenção → categoria de documento
INTENT_FILTER = {
    "devolução": "politica_devolucao",
    "devolver": "politica_devolucao",
    "reembolso": "politica_devolucao",
    "frete": "calculo_frete",
    "multiplicador": "calculo_frete",
    "sla": "sla_clientes",
    "prazo de resposta": "sla_clientes",
    "seguro": "faq",
}

def infer_category_filter(question: str):
    q = question.lower()
    for keyword, category in INTENT_FILTER.items():
        if keyword in q:
            return {"categoria": {"$eq": category}}
    return None  # sem filtro se intenção não for clara

# Na busca:
where_filter = infer_category_filter(question)
results = collection.query(
    query_embeddings=[embedding],
    n_results=3,
    where=where_filter  # None = sem filtro
)
```

E durante a ingestão (`ingest.py`), cada chunk recebe o metadado `categoria` baseado no documento de origem:

```python
CATEGORIA_POR_ARQUIVO = {
    "POL-001-politica-devolucao.md": "politica_devolucao",
    "PROC-042-frete-especial-v1.md": "calculo_frete",
    "PROC-042-v2-frete-especial-revisado.md": "calculo_frete",
    "SLA-2024-tabela-sla-clientes.md": "sla_clientes",
    "FAQ-atendimento.md": "faq",
}
```

---

## Problema 4 — Ausência de controle de versão na recuperação (risco de dados desatualizados)

### Descrição

Para "Qual o multiplicador para o Sudeste?", o `search.py` retornou PROC-042-**v1** (Sudeste = 1.0) em vez de PROC-042-**v2** (Sudeste = 1.1). Ambas as versões têm texto semanticamente quase idêntico — o embedding não as diferencia. O Claude, ao receber apenas a v1, respondeu 1.0 e alertou sobre o conflito, mas o atendente ficaria sem o valor correto.

Agravante: a PROC-042-v1 ainda tem **validade legal para chamados anteriores a 01/12/2023** (conforme a seção 5 de disposições transitórias da v2). Logo, simplesmente deletar a v1 do índice seria incorreto — ela precisa existir para consultas históricas.

### Impacto

Um atendente que consulta o multiplicador para um chamado novo receberá 1.0 (desatualizado) em vez de 1.1 (vigente), potencialmente causando cobrança incorreta ao cliente.

### Correção proposta

Durante a ingestão, adicionar metadados de versão e vigência em cada chunk. Na busca padrão (chamados novos), filtrar para recuperar apenas a versão vigente:

```python
# ingest.py — metadados por arquivo
VERSION_META = {
    "PROC-042-frete-especial-v1.md": {
        "doc_base": "PROC-042",
        "doc_version": "v1",
        "vigente_para_novos": False,
        "vigencia": "chamados anteriores a 01/12/2023"
    },
    "PROC-042-v2-frete-especial-revisado.md": {
        "doc_base": "PROC-042",
        "doc_version": "v2",
        "vigente_para_novos": True,
        "vigencia": "chamados a partir de 01/12/2023"
    },
}

# search.py — busca padrão usa apenas versão vigente
results = collection.query(
    query_embeddings=[embedding],
    n_results=3,
    where={"vigente_para_novos": {"$eq": True}}
)

# Para consultas históricas, o atendente pode passar o parâmetro:
results = collection.query(
    query_embeddings=[embedding],
    n_results=3
    # sem filtro = busca todas as versões
)
```

---

## Resumo dos problemas e correções

| # | Problema | Impacto | Complexidade da correção | Prioridade |
|---|---|---|---|---|
| 1 | `n_results=1` no build_prompt | 0/5 respostas corretas no pipeline padrão | Baixa — mudança de 1 linha | 🔴 Crítica |
| 2 | Vocabulário geográfico (Manaus ≠ Região Norte) | Falha total em queries por cidade/estado | Média — dicionário estático | 🟠 Alta |
| 3 | Ruído semântico por termos multi-contextuais | Chunk errado no top 1 em cenários com termos compartilhados | Média — metadados + filtros | 🟠 Alta |
| 4 | Sem controle de versão na recuperação | Valor desatualizado repassado ao cliente | Média — metadados de versão | 🟠 Alta |

---

## Conclusão

O sistema demonstrou que o **LLM não é o ponto fraco** do pipeline. Em todos os testes, o Claude seguiu rigorosamente os guardrails: nunca inventou valores, sempre citou fontes, alertou sobre conflitos e escalou quando os dados eram insuficientes. A qualidade da resposta final dependeu exclusivamente de **quais chunks chegaram ao LLM** — confirmando que RAG é, antes de tudo, um problema de engenharia de dados e retrieval.

As quatro correções propostas atacam a raiz dos problemas identificados e podem ser implementadas incrementalmente, sem reescrever a arquitetura do pipeline.
