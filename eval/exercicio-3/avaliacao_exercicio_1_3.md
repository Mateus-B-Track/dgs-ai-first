Tenho todos os materiais necessários para avaliar. Vou processar o entregável completo do participante com base nas skills de avaliação fornecidas nos documentos.

Os entregáveis do participante para o Exercício 1.3 são:
- **`ingest.py`** — pipeline de ingestão com ChromaDB + sentence-transformers
- **`search.py`** — busca vetorial
- **`build_prompt.py`** — montagem de prompt com system prompt v2
- **`analise_resultados.md`** — análise dos 5 testes com gabarito
- **`tarefa_4_problemas_e_correcoes.md`** — 4 problemas identificados com propostas de correção
- **`escolha_da_divisao_chunks.txt`** — justificativa da estratégia de chunking
- **Evidência do Copilot** — screenshots das duas imagens anexadas
- **Prompts e respostas** — para as perguntas 1 (cargas perigosas), 3 (SLA Gold), 4 (Frete Manaus) e 5 (Multiplicador Sudeste)

---

## Avaliação do Exercício 1.3

### Resumo

O participante entregou um pipeline RAG funcional e bem estruturado, com código limpo, justificativa de chunking elaborada, análise rigorosa de 5 testes contra gabarito e 4 problemas identificados com propostas de correção concretas e implementáveis. O ponto mais notável é a capacidade analítica: o participante não apenas registrou os resultados, mas diagnosticou causas raiz distintas para cada falha e propôs correções com código. O único gap real é a evidência de uso do Copilot, que está presente mas superficial nas capturas de tela fornecidas.

---

### Scores por Dimensão

| Dimensão | Score | Justificativa |
|----------|-------|---------------|
| **D1 — Domínio Conceitual** | **3** | Demonstra domínio real de RAG como sistema de engenharia de dados: explica *lost in the middle* na justificativa de chunking, distingue chunk para retrieval vs. chunk para geração (parent-child), entende por que distâncias >1.0 indicam falha de busca e não apenas baixo ranking, e articula a diferença entre similaridade léxica e intenção semântica. Conceitos aplicados com especificidade ao domínio NovaTech (PROC-042-v1 vs. v2, multiplicadores regionais, contexto de atendimento). |
| **D2 — Uso de Ferramentas** | **2** | Copilot evidenciado nas duas capturas de tela: prompt enviado ao Copilot para gerar `ingest.py` e `search.py` com especificações concretas (ChromaDB, all-MiniLM-L6-v2, collection 'novatech-docs'). Claude usado para gerar respostas com o prompt montado pelo pipeline. Porém, as capturas mostram apenas a geração inicial — não há evidência de ciclo gerar → avaliar → iterar com o Copilot (ex: prompt corrigido após erro, completion rejeitada). A evidência de iteração com o Copilot é ausente; a iteração visível foi com o Claude (system prompt v1→v2 no exercício 1.2, não aqui). |
| **D3 — Qualidade do Entregável** | **3** | Pipeline roda (ingest → search → build_prompt encadeados), código limpo e com docstrings. Chunking por seção markdown com overlap implementado. 5 testes documentados com pergunta, chunks retornados, arquivo/seção, distância e comparação com gabarito. Análise consolidada em tabela. 4 problemas identificados com causas raiz distintas e propostas de correção com código. O entregável é utilizável por outro membro do time sem esclarecimentos adicionais. |
| **D4 — Pensamento Crítico** | **3** | O participante vai além de registrar os resultados: identifica que o chunk correto para "cargas perigosas" ficou em 3º com margem de 0.045 e que isso é "instável o suficiente para variar entre execuções" — insight não-óbvio. Distingue entre falha do retrieval e comportamento correto do LLM ("os problemas são do pipeline, não do modelo"). Identifica que deletar a v1 seria incorreto porque ela tem validade legal para chamados históricos — nuance que a maioria perderia. Todas as análises são derivadas de evidência real (distâncias, rankings, textos dos chunks). |
| **D5 — Aplicabilidade ao Projeto** | **3** | Profundamente conectado ao NovaTech: usa os documentos reais (POL-001, PROC-042-v1/v2, SLA-2024, FAQ), referencia as seções específicas do gabarito, menciona o contexto de atendimento (320 chamados/dia implícitos na escolha de n_results), e a proposta de correção para controle de versão referencia a "vigência legal para chamados anteriores a 01/12/2023" — dado que só existe nos documentos do cenário. A proposta de chunking hierárquico para produção menciona as "~1.250 fontes heterogêneas" do projeto real. |

**Score do exercício: 2.8**

---

### Verificação de Armadilhas

O exercício 1.3 não define armadilhas internas formais na rubrica (as armadilhas obrigatórias estão no 1.2 — pergunta sobre carga perigosa com devolução). Contudo, há dois elementos que funcionam como armadilhas implícitas no contexto do exercício:

**Armadilha implícita 1 — Usar LangChain sem entender o que está abstraído:** O participante não usou LangChain; implementou o pipeline manualmente com ChromaDB + sentence-transformers direto. A rubrica diz "se usou LangChain sem entender o que está abstraído → D1 ≤ 2". O participante evitou essa armadilha e demonstrou entendimento das camadas. ✅ Identificada/evitada.

**Armadilha implícita 2 — Aceitar resultados do retrieval sem análise crítica:** O participante identificou que o `build_prompt` estava com `n_results=1` (bug que causou 0/5 acertos) e propôs correção com código. Não aceitou os resultados como suficientes. ✅ Identificada.

---

### Pontos Fortes

**1. Diagnóstico causal rigoroso:** Para cada um dos 5 testes que falharam, o participante identificou a causa raiz específica — não apenas "o chunk errado foi retornado", mas *por que* (sobreposição léxica em "prazo" na seção 3.5, falta de mapeamento geográfico para "Manaus", embeddings quase idênticos entre v1 e v2). Isso demonstra compreensão real do funcionamento de busca semântica.

**2. Separação entre problemas do retrieval e do LLM:** A conclusão de que "o LLM não é o ponto fraco" é tecnicamente correta e demonstra maturidade: o Claude seguiu os guardrails em todos os testes, inclusive declarando "não encontrei" quando os chunks eram insuficientes — e o participante usou isso como evidência para isolar o problema no retrieval.

**3. Proposta de chunking escalável:** A justificativa de chunking vai além do PoC — propõe parent-child chunks com overlap dinâmico para produção, com análise de custo/benefício. Demonstra que o participante pensa o sistema em escala, não apenas para os 5 documentos do exercício.

---

### Pontos de Melhoria

**1. Evidência de iteração com o Copilot:** As capturas mostram o prompt inicial enviado ao Copilot, mas não há registro de ciclos de refinamento — por exemplo, uma completion que o participante rejeitou e corrigiu, ou um prompt reformulado após o código gerado não funcionar. Para D2 = 3, seria necessário mostrar o ciclo gerar → avaliar → iterar. Sugestão: documentar pelo menos um caso em que o Copilot gerou algo incorreto e como o participante corrigiu.

**2. Teste de n_results=3 vs. n_results=1 documentado sistematicamente:** A análise de `build_prompt` mistura testes com `n_results=1` e `n_results=3` sem deixar claro em qual configuração cada teste foi executado no início do documento. A tabela consolidada em `analise_resultados.md` ajuda, mas a inconsistência de configuração entre testes reduz a clareza do diagnóstico. Sugestão: normalizar todos os testes com a mesma configuração (ou documentar explicitamente a configuração usada em cada teste).

**3. Gabarito do Anexo B não confrontado explicitamente para todos os testes:** A análise menciona o gabarito na introdução e tabela de resumo, mas nas análises individuais de alguns testes (especialmente o 4 e o 5) a comparação com o Anexo B poderia ser mais explícita. Para a pergunta 4 (Manaus), o gabarito esperava PROC-042-v2 seção 2 — o participante identificou isso, mas seria mais forte afirmar explicitamente "o Anexo B esperava X, o pipeline retornou Y". Isso é um ponto menor de clareza documental, não de conteúdo.

---

### Classificação

**✅ Aprovado com distinção (2.8)**

---

### Tópicos da Trilha para Reforço

Score acima de 2.5 — nenhum reforço obrigatório. O único gap (D2 = 2) está na documentação do processo de uso do Copilot, não na competência técnica. Recomendação opcional: revisar boas práticas de documentação de prompt engineering com ferramentas de desenvolvimento (como registrar prompts enviados, completions recebidas e decisões de aceitar/rejeitar), útil para exercícios de evidência em avaliações futuras.