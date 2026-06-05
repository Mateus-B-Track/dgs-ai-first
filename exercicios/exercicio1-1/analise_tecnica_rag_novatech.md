# Análise Técnica de Viabilidade — Assistente de IA com RAG
**Cliente:** NovaTech Logística
**Escopo:** Discovery + Desenvolvimento + Go-live (3 meses)
**Objetivo:** Reduzir tempo médio de busca por chamado de 12 min → < 2 min

---

## Contexto do Projeto

A NovaTech é uma empresa de médio porte do setor de logística (1.200 funcionários) cuja equipe de atendimento ao cliente (45 pessoas) gasta em média **12 minutos por chamado** buscando informações em três fontes de documentação dispersas:

| Fonte | Volume | Formato |
|---|---|---|
| SharePoint corporativo | ~800 documentos | PDFs e Word |
| Wiki interna (Confluence) | ~400 páginas | HTML com macros |
| Pasta de rede | ~50 planilhas | Excel (.xlsx) |

**Volume operacional:** 320 chamados/dia, dos quais ~60% (≈ 192/dia) envolvem consulta a documentação.

**Infraestrutura disponível:** Microsoft 365 E3 + Azure AI Services (a provisionar).

---

## Seção 1 — Análise por Tipo de Fonte

### 1.1 PDFs com Tabelas Complexas (15+ colunas)
**Nível de risco: Alto**

**Desafio específico**

Tabelas com 15+ colunas extraídas como texto linear perdem completamente sua estrutura dimensional. Um chunk contendo `"destino, peso 1–5kg, peso 6–10kg, zona norte, zona sul…"` sem cabeçalhos repetidos é semanticamente opaco tanto para o retriever vetorial quanto para o LLM na geração. Fluxogramas embutidos como imagens são invisíveis para a maioria dos parsers de texto (PDFMiner, PyPDF2, pdfplumber), sendo silenciosamente descartados.

**Impacto na qualidade das respostas**

O assistente responderá perguntas como *"qual o frete para 8kg, destino Sul?"* com dados incorretos ou recusará a resposta por ausência de contexto estruturado. A taxa de erro em perguntas numéricas pode ultrapassar **40%** com chunking ingênuo sobre essas tabelas.

**Estratégia recomendada**

- Usar **Azure Document Intelligence (Layout model)** para extração estruturada — ele preserva a geometria da tabela, reconhece cabeçalhos de coluna e linhas de dados como entidades separadas.
- Serializar cada linha da tabela como um chunk autossuficiente em formato Markdown ou JSON com cabeçalhos repetidos, ex.:
  ```
  Tabela de frete | Peso: 6–10 kg | Destino: Sul | Prazo SLA: 3 dias úteis | Valor: R$ 45,00
  ```
- Para fluxogramas embutidos como imagem: gerar descrição textual via **GPT-4o Vision** como metadado enriquecido do chunk pai.

---

### 1.2 PDFs Escaneados (necessitam OCR)
**Nível de risco: Médio-alto**

**Desafio específico**

Documentos escaneados produzem texto com taxa de erro de caractere (CER) de **2–8%** em OCR padrão, chegando a **15–25%** em PDFs de baixa qualidade (< 150 DPI). Erros como `"prazo de 3 dias üteis"` ou `"R$4S,00"` são invisíveis para o pipeline de ingestão mas fatais para a precisão das respostas. Metadados estruturais como datas de vigência e números de versão — críticos para filtros temporais — ficam frequentemente ilegíveis.

**Impacto na qualidade das respostas**

Um documento de política desatualizado pode ser recuperado e citado pelo assistente como fonte vigente, caso sua data não seja legível. Erros numéricos em valores de frete ou prazos de SLA geram respostas incorretas que chegam ao cliente final.

**Estratégia recomendada**

Pipeline em dois estágios:
1. **Azure AI Vision OCR** com confidence score por token — chunks com score médio < 0,85 entram em fila de revisão humana antes da indexação.
2. Pré-processamento com LLM para **post-OCR correction** focado em passagens numéricas (valores monetários, prazos, códigos de produto).

Metadados obrigatórios em cada chunk: `confiança_ocr`, `data_documento`, `resolucao_dpi`. Esses campos habilitam filtros de retrieval que excluem automaticamente chunks de baixa qualidade.

---

### 1.3 Wiki do Confluence (links internos e macros customizadas)
**Nível de risco: Médio**

**Desafio específico**

Links internos entre páginas criam dependências de contexto invisíveis ao retriever: a Página A define "Cliente Nível 1", a Página B usa o termo sem redefini-lo. Um chunk de B recuperado isoladamente produzirá resposta incompleta ou incorreta. Macros customizadas (tabelas de status, painéis de tarefas, expanders) são exportadas como HTML não interpretado ou silenciosamente omitidas na extração de texto puro.

Estimativa: **~30% das páginas** do Confluence da NovaTech dependem de contexto definido em outra página.

**Impacto na qualidade das respostas**

Termos técnicos internos (siglas de área, códigos de SLA, tipos de cliente, categorias de carga) ficarão sem definição no contexto, causando respostas genéricas ou factualmente equivocadas para perguntas que envolvam esses termos.

**Estratégia recomendada**

- Usar **Confluence REST API v2** para exportação com resolução de links: incluir título + primeiro parágrafo da página vinculada como metadado contextual do chunk de origem.
- Construir um **grafo de dependência entre páginas** para identificar "páginas âncora" que devem ser recuperadas conjuntamente com as páginas que as referenciam.
- Macros: parsear o HTML exportado e converter painéis de status em texto estruturado; ignorar macros puramente visuais (calendários, roadmaps).
- Construir e manter um **glossário centralizado** de termos internos da NovaTech como documento de alta prioridade no índice.

---

### 1.4 Planilhas Excel com Fórmulas Interdependentes
**Nível de risco: Médio**

**Desafio específico**

Fórmulas como `=VLOOKUP(A2,TabelaClientes,3,FALSE)` são texto sem semântica para o LLM. O valor computado depende de células em outras abas — e potencialmente outros arquivos —, tornando os dados estáticos na exportação. As planilhas são atualizadas mensalmente por 3 áreas distintas (Operações, Compliance, Comercial), criando risco de desatualização se o pipeline de ingestão não for automatizado.

**Impacto na qualidade das respostas**

Se a planilha de SLA for indexada com valores de uma data e o atendente consultar 3 semanas depois (pós-atualização mensal), as respostas estarão desatualizadas. Planilhas com múltiplas abas interdependentes podem produzir chunks contraditórios entre si dentro do mesmo índice.

**Estratégia recomendada**

- **Nunca indexar fórmulas** — apenas valores calculados exportados via `openpyxl` com avaliação completa das fórmulas antes da extração.
- **Desnormalizar as abas** em tabelas planas antes do chunking — cada linha deve ser autossuficiente com todas as colunas relevantes.
- Configurar **trigger de re-ingestão automática** no SharePoint via Power Automate para qualquer arquivo `.xlsx` modificado, com versionamento de chunks por hash do conteúdo para detectar mudanças reais vs. salvamentos sem alteração.
- Metadado obrigatório: `data_atualizacao`, `area_responsavel`, `versao_hash`.

---

## Seção 2 — Estimativa do Tamanho da Base em Tokens

### 2.1 PDFs do SharePoint (800 documentos)

| Variável | Valor |
|---|---|
| Número de documentos | 800 |
| Média de páginas por documento | 10 páginas |
| Total de páginas | **8.000 páginas** |
| Média de palavras por página* | 350 palavras |
| Total de palavras | 8.000 × 350 = **2.800.000 palavras** |
| Conversão (÷ 0,75 palavras/token) | 2.800.000 ÷ 0,75 = **≈ 3.733.333 tokens** |

> *Justificativa: PDFs técnicos de logística têm ~250–300 palavras de texto corrido por página, mais ~80–100 palavras adicionais em tabelas e legendas. Estimativa conservadora de 350 palavras/página.

---

### 2.2 Wiki Confluence (400 páginas)

| Variável | Valor |
|---|---|
| Número de páginas | 400 |
| Média de palavras por página | 1.500 palavras (fornecido) |
| Total de palavras | 400 × 1.500 = **600.000 palavras** |
| Conversão (÷ 0,75) | 600.000 ÷ 0,75 = **≈ 800.000 tokens** |

---

### 2.3 Planilhas Excel (50 arquivos)

| Variável | Valor |
|---|---|
| Número de planilhas | 50 |
| Tamanho médio estimado | 200 linhas × 8 colunas = 1.600 células |
| Média de palavras por célula (após desnormalização) | 4 palavras |
| Total de palavras | 50 × 1.600 × 4 = **320.000 palavras** |
| Conversão (÷ 0,75) | 320.000 ÷ 0,75 = **≈ 426.667 tokens** |

> Justificativa: planilhas de referência de logística (SLA, frete, tarifas) são densas mas não gigantescas. Células contêm valores numéricos, unidades, categorias e descrições curtas — média de 4 palavras/célula após desnormalização é razoável.

---

### 2.4 Total Consolidado

| Fonte | Tokens estimados | % do total |
|---|---|---|
| PDFs (SharePoint) | 3.733.333 | 75,3% |
| Wiki (Confluence) | 800.000 | 16,1% |
| Planilhas (Excel) | 426.667 | 8,6% |
| **Total** | **≈ 4.960.000 tokens** | **100%** |

**A base total equivale a aproximadamente 5 milhões de tokens brutos.**

> Com ~5M tokens brutos, a base completa não cabe em nenhuma janela de contexto disponível atualmente — nem mesmo modelos com 1M tokens de contexto poderiam processar isso de forma prática por query. Isso confirma a necessidade de **retrieval semântico eficiente como etapa central da arquitetura**, não como componente opcional.

> **Implicação para indexação:** Com chunks de 500 tokens, o índice vetorial terá ~10.000 chunks — volume perfeitamente gerenciável para Azure AI Search no tier Standard S1, sem necessidade de tiers mais caros.

---

## Seção 3 — Análise de Orçamento de Contexto

### 3.1 Parâmetros Base

| Parâmetro | Valor |
|---|---|
| Janela de contexto do GPT-4o | 128.000 tokens |
| System prompt + instruções fixas | ~2.000 tokens |
| Histórico de conversa (estimado) | ~3.000 tokens |
| Buffer para resposta gerada | ~4.000 tokens |
| **Disponível para chunks** | **≈ 119.000 tokens** |
| Tamanho de cada chunk | 500 tokens |
| **Máximo teórico de chunks por query** | **~238 chunks** |

### 3.2 Recomendação Prática: 20–25 Chunks

Apesar do máximo teórico de ~238 chunks, a recomendação é limitar a **20–25 chunks por query** (10.000–12.500 tokens de contexto de recuperação). Os motivos são:

1. **Efeito "lost in the middle":** Chunks posicionados nas regiões centrais do contexto recebem menor atenção do modelo na geração. Com mais de 25 chunks, a probabilidade de chunks críticos caírem na zona de baixa atenção aumenta significativamente.
2. **Qualidade vs. quantidade:** 20 chunks altamente relevantes produzem respostas melhores do que 100 chunks misturados com ruído semântico.
3. **Custo de inferência:** Contextos maiores têm custo proporcional em tokens de entrada — 238 chunks por query inviabiliza economicamente 192 chamados/dia.

### 3.3 Efeito "Lost in the Middle"

```
[Chunk 1: Alta atenção] [Ch 2] [Ch 3: ↓atenção] [Ch 4: ↓↓] ... [Ch N-1] [Chunk N: Alta atenção]
```

Os chunks nas posições centrais do contexto recebem menos "atenção" do modelo. **Implicação prática:** usar reranking com cross-encoder após o retrieval vetorial para garantir que os chunks mais relevantes ocupem as posições privilegiadas (início e fim do bloco de contexto).

### 3.4 Perguntas Multi-domínio (ex: SLA + frete simultâneos)

Perguntas como *"qual o prazo para cliente Nível 2 com carga de 12 kg para o Norte?"* exigem chunks de pelo menos 3 domínios distintos simultaneamente:
- Tabela de SLA por tipo de cliente
- Tabela de frete por peso e destino
- Definição de "Cliente Nível 2" (possivelmente no Confluence)

Com um retriever de similaridade semântica padrão (single-query), a busca tende a retornar chunks de apenas 1–2 domínios — o mais semanticamente próximo da query. **Solução: query decomposition.**

**Pipeline recomendado para perguntas multi-domínio:**
1. Classificador detecta que a pergunta cruza múltiplos domínios.
2. LLM decompõe a pergunta em 2–3 sub-queries independentes.
3. Retrieval paralelo para cada sub-query.
4. Fusão dos resultados com deduplicação antes da geração.
5. LLM gera resposta sintetizando os múltiplos domínios.

---

## Seção 4 — Recomendação de Estratégia de Chunking

### 4.1 Dois Perfis de Pergunta, Necessidades Opostas

A equipe de atendimento da NovaTech faz dois tipos predominantes de pergunta:

| Tipo | Exemplo | Necessidade |
|---|---|---|
| **Direta** | "Qual o prazo para cliente Padrão?" | Chunk pequeno (200–350 tokens): a resposta está em 1–2 linhas de uma tabela |
| **Contextual** | "Como funciona o processo de reclamação para avaria de carga?" | Chunk médio (400–600 tokens): exige contexto de procedimento multi-etapa |

Com chunking fixo de 500 tokens sem distinção de tipo de conteúdo, perdemos precisão nos dois casos: chunks grandes demais para perguntas diretas diluem o sinal semântico; chunks pequenos demais para perguntas contextuais fragmentam o raciocínio.

### 4.2 Por que Chunking Fixo sem Overlap é Problemático

Com documentos de procedimento multi-etapa, um chunk pode terminar no meio de uma instrução:

```
...acione o operador responsável. Em seguida,
[CORTE DE CHUNK]
preencha o formulário F-07 com...
```

O segundo chunk não tem contexto suficiente para ser recuperado na query original — o retriever não sabe que ele é continuação do procedimento. **Estimativa:** ~15–20% das informações críticas da NovaTech estão em posições de fronteira de chunk com chunking fixo de 500 tokens, gerando perdas sistemáticas de informação.

### 4.3 Estratégia Recomendada: Chunking Hierárquico com Overlap Adaptativo

#### Passo 1 — Segmentação semântica primária
Usar a **estrutura natural do documento** (títulos H1/H2, seções, breaks de tabela, separadores de procedimento) como fronteiras de chunk, não tamanho fixo em tokens. Isso preserva unidades de significado completas.

#### Passo 2 — Overlap de 10–15% entre chunks adjacentes
~50–70 tokens de sobreposição — as últimas 2–3 frases do chunk anterior são repetidas no início do próximo.
- **Custo:** +15% de espaço de índice (de ~10.000 para ~11.500 chunks)
- **Benefício:** elimina o problema de fronteira de chunk estimado em 15–20% das perdas de informação

#### Passo 3 — Chunks pai–filho (parent-child chunking)
- **Chunk filho (200 tokens):** indexado para retrieval vetorial — alta precisão semântica.
- **Chunk pai (500–800 tokens):** retornado ao LLM na geração — contexto suficiente para resposta completa.

Isso combina alta precisão de retrieval com contexto de qualidade para geração.

#### Passo 4 — Metadados obrigatórios em cada chunk

| Metadado | Descrição | Para que serve |
|---|---|---|
| `fonte` | SharePoint / Confluence / Excel | Filtro por tipo de fonte |
| `nome_documento` | Nome e caminho do arquivo original | Citação da fonte na resposta |
| `data_atualizacao` | Data da última modificação | Priorizar versão mais recente |
| `area_responsavel` | Operações / Compliance / Comercial | Filtro por domínio |
| `confianca_ocr` | Score de confiança (0–1) | Excluir chunks de baixa qualidade |
| `versao_hash` | Hash do conteúdo do chunk | Detectar mudanças reais vs. salvamentos |

Esses metadados habilitam **filtros de retrieval** que aumentam a precisão sem aumentar o número de chunks retornados ao contexto.

#### Passo 5 — Tratamento especial para documentos contraditórios

Dado que a NovaTech tem documentos em versões conflitantes entre as três áreas (Operações, Compliance, Comercial), o sistema deve:
- Adicionar metadado de versão + data de vigência em cada chunk.
- Configurar o system prompt para priorizar explicitamente a versão mais recente quando houver múltiplos chunks do mesmo tópico com datas diferentes.
- Sinalizar ao atendente quando houver ambiguidade entre versões, ao invés de silenciosamente escolher uma.

---

## Síntese Executiva e Riscos

### Impacto esperado na meta de negócio
Com retrieval em < 2 segundos (vs. busca manual atual de 12 minutos) e acurácia de resposta > 85% (meta conservadora com a estratégia acima), a redução de tempo por chamado alcança o objetivo de < 2 minutos. Sobre os 192 chamados/dia que envolvem documentação, isso representa uma economia de **~30 horas-homem por dia** na equipe de atendimento.

### Principais riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Baixa qualidade na extração de tabelas de frete | Alta | Alto | Azure Document Intelligence + serialização linha a linha |
| Documentos contraditórios entre versões | Alta | Médio | Metadado de versão + prompt de priorização |
| OCR com baixa acurácia em PDFs escaneados | Média | Alto | Confidence scoring + fila de revisão humana |
| Re-ingestão manual após atualizações mensais | Alta | Médio | Power Automate trigger automático |
| Perguntas multi-domínio sem cobertura completa | Média | Médio | Query decomposition + multi-step retrieval |

### Recomendação de alocação do cronograma (3 meses)

> O principal risco de atraso está no **pipeline de ingestão**, não no RAG em si. A geração com GPT-4o é a parte tecnicamente mais simples do projeto. Transformar tabelas de frete escaneadas em chunks semânticos precisos é onde projetos similares tipicamente atrasam.

- **50–60% do tempo de discovery:** pipeline de ingestão (parsing, OCR, serialização de tabelas, desnormalização de planilhas)
- **20–30%:** camada de retrieval (embeddings, índice vetorial, reranking, query decomposition)
- **10–20%:** integração Microsoft Teams + interface do atendente + avaliação de qualidade

---

*Documento gerado como análise técnica de viabilidade. Estimativas numéricas baseadas em parâmetros fornecidos pelo cliente e benchmarks de mercado para projetos RAG em logística.*
