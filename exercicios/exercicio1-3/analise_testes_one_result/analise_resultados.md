# Análise dos Resultados — Pipeline RAG NovaTech

**Exercício 1.3 | Data: 05/06/2026**

---

## Contexto

O pipeline RAG foi testado com 5 perguntas representativas do cenário de atendimento da NovaTech. Os resultados foram comparados contra um gabarito de chunks esperados. Os testes foram executados em dois modos:

- **`search.py`** — retorna os 3 chunks mais similares por busca vetorial pura
- **`build_prompt.py`** — monta o prompt completo com system prompt + chunks recuperados

O modelo de embeddings utilizado foi `sentence-transformers/all-MiniLM-L6-v2` com ChromaDB como vector store local.

---

## Gabarito esperado

| # | Pergunta | Chunk esperado |
|---|---|---|
| 1 | "Qual o prazo de devolução?" | POL-001, seção 3.1 |
| 2 | "Cargas perigosas podem ser devolvidas?" | POL-001, seção 3.2 |
| 3 | "Qual o SLA do cliente Gold?" | SLA-2024 (tabela de prazos) |
| 4 | "Frete para 600kg para Manaus?" | PROC-042-v2, seção 2 |
| 5 | "Qual o multiplicador para o Sudeste?" | PROC-042-v2, seção 2 |

---

## Análise por pergunta

### Pergunta 1 — "Qual o prazo de devolução?"
**Gabarito:** POL-001, seção 3.1 | **Resultado: ❌ MISS**

**Top 3 retornados pelo search.py:**

| Rank | Arquivo | Seção | Distância |
|------|---------|-------|-----------|
| 1 | POL-001-politica-devolucao.md | 3.5. Custos de devolução | 0.7336 |
| 2 | FAQ-atendimento.md | Item 3 — Carga perigosa | 0.8589 |
| 3 | POL-001-politica-devolucao.md | 3.3. Procedimento de devolução | 0.8836 |

**Chunk correto (seção 3.1) não apareceu no top 3.** O build_prompt montou o prompt com os 3 chunks errados.

**Causa raiz:** A palavra "prazo" aparece na seção 3.5 no trecho *"prazo expirado (solicitação após 7 dias úteis)"*, tornando-a semanticamente próxima da query. O modelo de embedding associou "prazo de devolução" à seção de custos em vez da seção de prazo geral (3.1), onde o prazo de 7 dias úteis está definido como regra principal.

---

### Pergunta 2 — "Cargas perigosas podem ser devolvidas?"
**Gabarito:** POL-001, seção 3.2 | **Resultado: ⚠️ PARCIAL**

**Top 3 retornados pelo search.py:**

| Rank | Arquivo | Seção | Distância |
|------|---------|-------|-----------|
| 1 | FAQ-atendimento.md | Item 22 — Seguro de carga | 0.7437 |
| 2 | PROC-042-frete-especial-v1.md | 4. Condições especiais | 0.7651 |
| 3 | POL-001-politica-devolucao.md | **3.2. Exceções ao prazo geral** ✅ | 0.7888 |

**Com `n_results=3`:** o chunk correto está presente (3º lugar). O build_prompt incluiu os 3 chunks no prompt.

**Com `n_results=1`:** retornou apenas o FAQ Item 22 (seguro de carga) — completamente irrelevante para a pergunta de devolução.

**Causa raiz:** O termo "cargas perigosas" aparece em múltiplos documentos em contextos diferentes (seguro, frete, política de devolução). O modelo de embedding encontrou similaridade léxica mas não conseguiu discriminar a intenção (devolução) da mera ocorrência do termo. O chunk correto ficou em 3º com distância apenas 0.045 maior que o 1º — margem muito pequena que pode variar e causar instabilidade.

---

### Pergunta 3 — "Qual o SLA do cliente Gold?"
**Gabarito:** SLA-2024 (tabela de prazos) | **Resultado: ❌ MISS no build_prompt, ⚠️ PARCIAL no search**

**Top 3 retornados pelo search.py:**

| Rank | Arquivo | Seção | Distância |
|------|---------|-------|-----------|
| 1 | SLA-2024-tabela-sla-clientes.md | 5. Medição e reportes | 0.9017 |
| 2 | FAQ-atendimento.md | Item 41 — SLA resposta vs resolução | 0.9024 |
| 3 | FAQ-atendimento.md | Item 15 — Tier Platinum | 0.9149 |

O **FAQ Item 41** (rank 2) contém a resposta correta: *"Gold tem 2h de resposta e 24h de resolução"*. Porém o build_prompt usou apenas **1 chunk** — o 1º colocado, que é a seção de Medição e Reportes, sem os valores de SLA por tier.

O chunk do gabarito (tabela de prazos por tier) não chegou ao top 3. Ele foi provavelmente ofuscado pela seção 5 (que também menciona "Gold" e "SLA") e pelo FAQ.

**Causa raiz (dupla):**
1. `build_prompt` configurado com `n_results=1`, descartando o chunk do FAQ Item 41 que continha a resposta.
2. A seção com a tabela SLA completa (com os valores por tier) não foi recuperada porque o título da seção não contém os termos "Gold", "prazo" ou os valores numéricos — o embedding priorizou seções que mencionam "Gold" textualmente.

---

### Pergunta 4 — "Frete para 600kg para Manaus?"
**Gabarito:** PROC-042-v2, seção 2 | **Resultado: ❌ MISS**

**Top 3 retornados pelo search.py:**

| Rank | Arquivo | Seção | Distância |
|------|---------|-------|-----------|
| 1 | PROC-042-frete-especial-v1.md | 1. Objetivo | 1.0516 |
| 2 | PROC-042-v2-frete-especial-revisado.md | 4. Condições especiais | 1.069 |
| 3 | PROC-042-v2-frete-especial-revisado.md | 1. Objetivo | 1.0809 |

O build_prompt usou apenas o chunk 1 (PROC-042-v1 seção 1 — Objetivo), que não contém nenhum multiplicador nem dado sobre regiões.

**Distâncias acima de 1.0** indicam baixa similaridade semântica — a busca falhou de forma significativa.

**Causa raiz:** O documento usa "Região Norte" como unidade geográfica; a pergunta usa "Manaus" (cidade). O modelo `all-MiniLM-L6-v2` não infere que Manaus pertence à Região Norte. Não há nenhuma ocorrência de "Manaus" nos documentos indexados. Além disso, a seção 2 (tabela de multiplicadores regionais) não foi recuperada porque a query não contém termos como "multiplicador" ou "tabela regional".

---

### Pergunta 5 — "Qual o multiplicador para o Sudeste?"
**Gabarito:** PROC-042-v2, seção 2 | **Resultado: ❌ MISS + versão errada**

**Top 3 retornados pelo search.py:**

| Rank | Arquivo | Seção | Distância |
|------|---------|-------|-----------|
| 1 | POL-001-politica-devolucao.md | 3.4. Devoluções parciais | 0.9392 |
| 2 | FAQ-atendimento.md | Item 8 — Como funciona o frete especial | 0.9776 |
| 3 | PROC-042-frete-especial-**v1**.md | 2.1. Multiplicadores regionais | 0.9874 |

O build_prompt usou apenas **1 chunk** — o 1º colocado (POL-001 seção 3.4, sobre devoluções parciais), completamente irrelevante.

O chunk do gabarito (PROC-042-**v2** seção 2) não apareceu no top 3. O 3º colocado é a versão **v1** (com Sudeste = 1.0), não a v2 (com Sudeste = 1.1 — valor atualizado).

**Causa raiz (dupla):**
1. `build_prompt` com `n_results=1` descarta os chunks de frete em favor de um chunk de devolução com distância ligeiramente menor.
2. O modelo de embedding não diferenciou v1 de v2 semanticamente — ambas têm texto quase idêntico, mas os valores numéricos diferem. Sem metadados de versão no critério de busca, a v1 pode ranquear antes da v2.

---

## Resumo consolidado

| # | Pergunta | Search (top 3) | Build_prompt | Status |
|---|---|---|---|---|
| 1 | Prazo de devolução | ❌ Chunk correto ausente | ❌ Chunks errados | MISS completo |
| 2 | Cargas perigosas | ⚠️ Correto em 3º | ⚠️ Incluído com 3 chunks / errado com 1 | Parcial / Instável |
| 3 | SLA Gold | ⚠️ Resposta no 2º (FAQ) | ❌ Usou só 1 chunk errado | MISS no build_prompt |
| 4 | Frete Manaus | ❌ Seção correta ausente, dist >1.0 | ❌ Chunk objetivo sem dados | MISS completo |
| 5 | Multiplicador Sudeste | ❌ v1 em 3º, v2 ausente | ❌ Chunk de devolução irrelevante | MISS completo |

**Taxa de acerto: 0/5 respostas corretas com configuração `n_results=1`**

---

## Problemas identificados

### Problema 1 — `build_prompt` configurado com `n_results=1` (crítico)

Em 3 dos 5 casos (testes 3, 4 e 5), o chunk correto ou um chunk útil existia no top 3 do `search.py`, mas foi descartado porque o `build_prompt` usou apenas 1 resultado. Com um único chunk, a margem de erro da busca semântica é intoleravelmente alta.

**Correção:** Alterar o `build_prompt.py` para usar `n_results=3`, alinhado ao comportamento já implementado no `search.py`. Se houver preocupação com o tamanho do contexto, implementar um threshold de distância (ex.: descartar chunks com distância > 1.2) em vez de limitar a 1.

---

### Problema 2 — Vocabulário geográfico não coberto pelos documentos (estrutural)

A query "Manaus" não encontra correspondência semântica com "Região Norte" nos documentos. O modelo `all-MiniLM-L6-v2` não possui o conhecimento geográfico necessário para essa inferência. As distâncias >1.0 no teste 4 confirmam falha de recuperação, não apenas baixo ranking.

**Correção:** Implementar uma etapa de *query expansion* antes da busca vetorial: mapear cidades para regiões usando um dicionário estático (ex.: `{"Manaus": "Região Norte", "São Paulo": "Região Sudeste", ...}`). Alternativamente, enriquecer os metadados dos chunks do PROC-042 com os estados e cidades cobertos por cada região, e usar filtragem por metadados como critério secundário.

---

### Problema 3 — Ambiguidade semântica por termos multi-contextuais

Termos como "cargas perigosas" e "prazo" aparecem em múltiplos documentos com intenções diferentes. O modelo de embedding detecta presença do termo mas não discrimina o contexto de uso. Isso explica o Rank 1 de FAQ Item 22 (seguro) para a pergunta sobre devolução de cargas perigosas.

**Correção:** Adicionar metadados de categoria nos chunks durante o ingestion (ex.: `categoria: "politica_devolucao"`, `categoria: "frete"`, `categoria: "seguro"`). Usar filtros por metadados para restringir o espaço de busca quando a intenção da pergunta puder ser inferida.

---

### Problema 4 — Ausência de controle de versão na recuperação

Para o teste 5, o modelo recuperou PROC-042-v1 (valores desatualizados) em vez de PROC-042-v2 (valores vigentes). Ambas as versões têm texto semanticamente quase idêntico, portanto o embedding não diferencia. Isso pode levar um atendente a passar valores errados ao cliente.

**Correção:** Durante o ingestion, adicionar metadado `versao` e `data_vigencia` em cada chunk. No momento da busca, aplicar filtro para priorizar a versão mais recente de documentos com o mesmo número base (PROC-042). Se ambas devem estar indexadas por razões de auditoria, o sistema prompt já instrui a usar a versão mais recente — mas o retriever precisa trazê-la.

---

## Conclusão

O pipeline demonstrou capacidade de recuperar chunks relevantes em buscas abertas, mas falhou em casos que exigem:
- Correspondência de vocabulário indireto (cidades → regiões)
- Discriminação de intenção quando um termo aparece em múltiplos contextos
- Controle de versão de documentos

O problema mais imediato e de correção mais simples é o `n_results=1` no `build_prompt`. Os demais problemas requerem melhorias na estratégia de chunking, metadados e/ou query expansion.
