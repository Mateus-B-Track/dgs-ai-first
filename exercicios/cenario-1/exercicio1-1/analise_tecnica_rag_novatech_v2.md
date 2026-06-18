# Análise Técnica de Viabilidade — Assistente de IA com RAG
**Cliente:** NovaTech Logística
**Escopo:** Discovery + Desenvolvimento + Go-live (3 meses)
**Objetivo:** Reduzir tempo médio de busca por chamado de 12 min → < 2 min
**Versão:** 2.0 — incorpora revisão crítica da v1.0

> **Nota sobre esta versão:** A v1.0 desta análise foi submetida a revisão crítica interna. Esta versão corrige estimativas com falsa precisão, expande os riscos organizacionais (ausentes na v1.0), requalifica a meta de acurácia, detalha limitações do MVP e adiciona seções sobre governança de dados, integração técnica com Teams e dimensionamento da fila de OCR.

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

> **⚠ Atenção — dimensionamento da fila de revisão:** Se 30% dos PDFs escaneados tiverem qualidade abaixo do threshold, e considerando 800 documentos × 10 páginas × ~5 chunks/página, estamos falando de potencialmente **12.000 chunks aguardando revisão humana** antes da indexação inicial. Isso precisa ser dimensionado no planejamento: quem faz a revisão, com que prazo, e se o go-live pode ocorrer com a base parcialmente indexada. A alternativa é elevar o threshold para 0,75 e aceitar maior margem de erro nos chunks não revisados, documentando explicitamente essa decisão.

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

> **Nota metodológica:** As estimativas abaixo são apresentadas como **ranges**, não valores únicos. Estimativas pontuais criam falsa precisão. Os cenários pessimistas devem ser tratados como base para planejamento de infraestrutura; os otimistas como melhor caso.

### 2.1 PDFs do SharePoint (800 documentos)

| Variável | Cenário otimista | Cenário pessimista |
|---|---|---|
| Média de palavras/página (texto corrido) | 250 palavras | 350 palavras |
| Multiplicador de serialização de tabelas* | 1,0× | 2,5× |
| **Tokens estimados** | **≈ 2,7M tokens** | **≈ 9,3M tokens** |

> *O multiplicador de serialização é o fator mais crítico e mais negligenciado. A estratégia recomendada de serializar cada linha de tabela com cabeçalhos repetidos ("Tabela de frete | Peso: 6–10 kg | Destino: Sul | ...") pode facilmente triplicar o volume tokenizado em relação ao texto puro extraído. Uma tabela de frete com 15 colunas e 200 linhas que ocupa 2 páginas de PDF pode gerar 200 chunks de ~80 tokens cada = 16.000 tokens, contra ~600 tokens de extração linear. Isso é um aumento de 26×. O cenário pessimista assume que 30% dos documentos contêm tabelas significativas.

**Cálculo detalhado — cenário otimista:**
- 800 docs × 10 páginas × 250 palavras ÷ 0,75 = **≈ 2.667.000 tokens**

**Cálculo detalhado — cenário pessimista:**
- Texto corrido: 800 × 10 × 350 ÷ 0,75 = 3.733.333 tokens
- Acréscimo de serialização de tabelas (30% dos docs com fator 2,5×): + 5.600.000 tokens
- **Total pessimista: ≈ 9.333.000 tokens**

---

### 2.2 Wiki Confluence (400 páginas)

| Variável | Valor |
|---|---|
| Número de páginas | 400 |
| Média de palavras por página | 1.500 palavras (fornecido) |
| Total de palavras | 400 × 1.500 = **600.000 palavras** |
| Conversão (÷ 0,75) | 600.000 ÷ 0,75 = **≈ 800.000 tokens** |

> Esta estimativa é mais confiável pois não há ambiguidade de serialização. O range é estreito: **700K–900K tokens**.

---

### 2.3 Planilhas Excel (50 arquivos)

> **⚠ Maior incerteza desta seção.** A estimativa de "200 linhas × 8 colunas" é um chute explícito — planilhas de tarifas de frete com segmentações por CEP, tipo de carga, modal, peso e destino podem ter 5.000–20.000 linhas. Uma única planilha de tabela de frete rodoviário nacional pode superar toda a estimativa otimista das 50 planilhas combinadas.

| Variável | Cenário otimista | Cenário pessimista |
|---|---|---|
| Linhas por planilha (média) | 200 linhas | 2.000 linhas |
| Colunas por planilha (média) | 8 colunas | 12 colunas |
| Palavras por célula desnormalizada | 3 palavras | 5 palavras |
| **Tokens estimados** | **≈ 160.000 tokens** | **≈ 8.000.000 tokens** |

**Recomendação:** Antes de fechar o escopo técnico, auditar as 5 maiores planilhas para calibrar esta estimativa. Se uma única planilha de frete tiver 10.000 linhas × 15 colunas, o plano de infraestrutura precisa ser revisto.

---

### 2.4 Total Consolidado

| Fonte | Cenário otimista | Cenário pessimista |
|---|---|---|
| PDFs (SharePoint) | ~2,7M tokens | ~9,3M tokens |
| Wiki (Confluence) | ~0,7M tokens | ~0,9M tokens |
| Planilhas (Excel) | ~0,2M tokens | ~8,0M tokens |
| **Total** | **~3,6M tokens** | **~18,2M tokens** |

**A base indexada deve ser planejada para um range de 3,6M a 18M tokens brutos.**

Com chunks de 500 tokens, isso representa entre **7.200 e 36.000 chunks** no índice vetorial. O Azure AI Search Standard S1 suporta confortavelmente até 1M chunks — ambos os cenários são tecnicamente viáveis nesse tier. O impacto real do tamanho da base é no **custo de embedding na ingestão inicial** (cobrado por token pela OpenAI) e no **tempo do pipeline de ingestão**, não no retrieval em si.

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

Com um retriever de similaridade semântica padrão (single-query), a busca tende a retornar chunks de apenas 1–2 domínios — o mais semanticamente próximo da query. **Solução proposta: query decomposition.** Mas essa solução tem custos que precisam ser considerados antes de adotá-la:

**Pipeline recomendado para perguntas multi-domínio:**
1. Classificador detecta que a pergunta cruza múltiplos domínios.
2. LLM decompõe a pergunta em 2–3 sub-queries independentes.
3. Retrieval paralelo para cada sub-query.
4. Fusão dos resultados com deduplicação antes da geração.
5. LLM gera resposta sintetizando os múltiplos domínios.

**Limitações e custos reais desta abordagem:**

- **Latência acumulada:** cada passo de decomposição + retrieval + síntese adiciona 2–4 segundos. Uma pergunta com 3 domínios pode levar 8–12 segundos de ponta a ponta. Em contexto de call center com cliente na linha, isso pode ser inaceitável. Definir SLA de resposta do assistente (ex: < 5 segundos em P95) é um requisito que precisa ser capturado no discovery.
- **O classificador precisa ser treinado com exemplos reais:** não existe um classificador genérico de "perguntas multi-domínio de logística". Será necessário coletar e rotular 50–100 perguntas reais dos atendentes durante o discovery. Quem faz essa rotulação?
- **A decomposição automática pode introduzir erros:** o LLM pode decompor a pergunta de forma que as sub-queries não cubram a intenção original. É necessário um fallback: se a decomposição falhar ou as sub-queries não retornarem resultados relevantes, o sistema deve cair de volta para single-query com aviso de incerteza.
- **Custo adicional:** cada pergunta multi-domínio consome 3–5× mais tokens de API do que uma pergunta simples, impactando o custo operacional mensal.

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

#### Passo 5 — Tratamento de documentos contraditórios

Dado que a NovaTech tem documentos em versões conflitantes entre as três áreas (Operações, Compliance, Comercial), é necessário distinguir o que pode ser tratado em runtime do que precisa ser resolvido antes da ingestão.

**O que o sistema pode fazer em runtime:**
- Adicionar metadado de versão + data de vigência em cada chunk.
- Configurar o system prompt para priorizar explicitamente a versão mais recente quando houver múltiplos chunks do mesmo tópico com datas diferentes.
- Sinalizar ao atendente quando houver ambiguidade entre versões, ao invés de silenciosamente escolher uma.

**O que o sistema não pode resolver — e precisa ser tratado antes:**

> **⚠ Pré-condição crítica:** "Versão mais recente" não é sinônimo de "versão correta". Se o departamento Comercial atualizou uma tabela de SLA com dados errados ontem, o assistente vai priorizar a versão errada sobre a versão correta de 3 meses atrás. Nenhuma lógica de runtime resolve isso.
>
> A **resolução das contradições entre documentos é uma pré-condição de qualidade de dados**, não uma feature do sistema. Recomendamos fortemente que a NovaTech conduza, como entregável do discovery, um processo de auditoria e harmonização da documentação conflitante pelas três áreas responsáveis. O assistente pode expor e sinalizar conflitos, mas não pode resolvê-los — isso requer decisão humana e autoridade sobre o conteúdo.

---

## Seção 5 — Governança de Dados e Riscos Organizacionais

> Esta seção estava ausente na v1.0. A experiência em projetos RAG corporativos mostra que os maiores riscos de atraso e fracasso são organizacionais, não técnicos. O pipeline de ingestão pode ser perfeito e o projeto ainda falhar por falta de governança.

### 5.1 Acesso e Segurança dos Dados

**Questões que precisam ser respondidas no discovery, antes de qualquer desenvolvimento:**

- Há dados sensíveis (salários, contratos com clientes nomeados, informações de fornecedores, dados pessoais) misturados com a documentação operacional no SharePoint? O assistente potencialmente indexará tudo que o pipeline conseguir acessar.
- O acesso ao SharePoint corporativo pelo pipeline de ingestão requer aprovação formal de TI e Segurança da Informação — em empresas de médio porte, esse processo pode levar **4–8 semanas**. Isso precisa iniciar no primeiro dia do projeto.
- O assistente deve respeitar permissões individuais de acesso? Se um atendente não tem acesso a um documento no SharePoint, o assistente pode citar esse documento em uma resposta a ele? Essa decisão tem implicações técnicas (arquitetura de retrieval com filtros por usuário) e de compliance que precisam ser definidas com TI e jurídico.
- A NovaTech tem políticas de retenção de dados que afetam quais documentos podem ser indexados e por quanto tempo?

### 5.2 Resistência Organizacional e Change Management

- As 3 áreas que mantêm a documentação (Operações, Compliance, Comercial) precisarão adotar novos processos: triggers automáticos de re-ingestão, padrões mínimos de formatação de documentos, processo de resolução de contradições. Isso requer patrocínio executivo, não apenas acordo técnico.
- Os 45 atendentes precisarão de treinamento e período de adaptação. Nas primeiras semanas, a tendência é verificar manualmente as respostas do assistente — o que pode não reduzir o tempo por chamado inicialmente. O ganho de produtividade provavelmente será gradual, não imediato no go-live.
- Há risco de rejeição se o assistente der respostas erradas nas primeiras semanas. Um plano de comunicação e gerenciamento de expectativas é tão importante quanto a arquitetura técnica.

### 5.3 Processo de Resolução de Contradições como Pré-condição

Conforme detalhado na Seção 4 (Passo 5), a resolução das contradições entre documentos das três áreas é **pré-condição para qualidade aceitável**, não feature do sistema. Recomendamos que o contrato de discovery inclua explicitamente a NovaTech como responsável por entregar uma base documental harmonizada até o início da fase de desenvolvimento. Sem isso, o sistema vai ao ar sinalizando contradições constantemente, o que corrói a confiança dos atendentes.

---

## Seção 6 — Integração Técnica com Microsoft Teams

> Esta seção estava ausente na v1.0. A integração com Teams não é trivial e tem implicações que afetam prazo e arquitetura.

### 6.1 Decisão de Arquitetura de Canal

Há três abordagens para integração com Teams, com trade-offs significativos:

| Abordagem | Vantagens | Desvantagens |
|---|---|---|
| **Azure Bot Framework + Teams** | Controle total, suporte a rich cards, citação de fontes formatada | Maior complexidade de desenvolvimento, requer expertise em Bot Framework |
| **Power Virtual Agents (Copilot Studio)** | Low-code, integração nativa com M365 E3 | Limitações de customização, difícil integrar pipeline RAG customizado |
| **API customizada + Teams Webhook** | Flexibilidade total | Sem UI nativa do Teams, experiência degradada para o atendente |

**Recomendação:** Azure Bot Framework para controle sobre a experiência do atendente e capacidade de exibir citações de fonte com links clicáveis. Mas isso precisa de uma decisão explícita no discovery — não é um detalhe de implementação.

### 6.2 Limitações do Teams como Canal para RAG

- Mensagens no Teams têm limite de formatação — respostas longas com múltiplas citações de fonte precisam ser truncadas ou paginadas.
- O histórico de conversa do Teams não é automaticamente disponível para o pipeline RAG — é necessário implementar gerenciamento de sessão explícito.
- **SLA de resposta:** o assistente precisa responder em < 5 segundos para não parecer "travado" na interface do Teams. Isso é um requisito de arquitetura, não só de UX.

### 6.3 Autenticação e Permissões

A integração Teams + SharePoint via Azure Bot Framework usa OAuth 2.0 com o Azure AD da NovaTech. Isso significa que o pipeline pode, em tese, ser configurado para respeitar as permissões individuais de cada atendente no SharePoint — mas isso adiciona complexidade considerável. A decisão entre "um único service account com acesso total" vs. "permissões individuais espelhadas" precisa ser tomada no discovery com TI e compliance.

---

## Síntese Executiva e Riscos

### Impacto esperado na meta de negócio

Com retrieval em < 5 segundos e acurácia realista de **65–75% no MVP** (ver nota abaixo), o impacto operacional dependerá fortemente do comportamento dos atendentes nas primeiras semanas. O cálculo direto de "30 horas-homem/dia economizadas" assume 100% de adoção e 0% de verificação manual — ambas premissas irreais para um MVP.

**Projeção mais honesta:**
- Semanas 1–4 pós go-live: atendentes verificam ~70% das respostas manualmente. Economia real: ~3–5 min/chamado (vs. meta de 10 min de redução).
- Meses 2–3: com calibração do sistema e confiança crescente, verificação cai para ~30%. Economia: ~7–8 min/chamado.
- Meta de < 2 min por chamado é alcançável, mas provavelmente em 6 meses, não no go-live.

> **Nota sobre acurácia:** A v1.0 usava "> 85% de acurácia" como meta. Esse número é vago e provavelmente otimista demais para um MVP de 3 meses com documentação contraditória e não padronizada. **65–75% de acurácia factual verificada** é uma meta mais realista e honesta para o primeiro go-live, com plano de melhoria iterativa. Mais importante: a acurácia precisa ser definida e medida — isso requer um **golden dataset** de 50–100 pares de pergunta/resposta esperada validados pela NovaTech, construído durante o discovery.

### Principais riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Baixa qualidade na extração de tabelas de frete | Alta | Alto | Azure Document Intelligence + serialização linha a linha |
| Documentos contraditórios sem resolução prévia | Alta | Alto | Auditoria documental como pré-condição contratual do discovery |
| Aprovação de TI/segurança atrasando acesso ao SharePoint | Alta | Alto | Iniciar processo de aprovação no dia 1 do projeto |
| OCR com volume de revisão humana subestimado | Média | Alto | Auditar amostra de PDFs escaneados na primeira semana |
| Query decomposition adicionando latência inaceitável | Média | Médio | Definir SLA de resposta (< 5s) como requisito, não suposição |
| Re-ingestão manual após atualizações mensais | Alta | Médio | Power Automate trigger automático |
| Resistência dos atendentes nas primeiras semanas | Média | Médio | Plano de change management + período de adoção guiada |
| Permissões individuais de acesso ao SharePoint | Média | Médio | Decisão arquitetural explícita no discovery com TI |
| Volume real das planilhas Excel muito maior que estimado | Média | Baixo | Auditar as 5 maiores planilhas antes de fechar escopo |

### O que o MVP de 3 meses não vai conseguir fazer bem

Ser explícito sobre as limitações do MVP é parte do trabalho de engenharia responsável:

- **Perguntas que exigem raciocínio numérico complexo** (ex: "calcule o custo total de frete para 3 remessas com pesos diferentes para destinos diferentes") — o assistente pode buscar as tabelas, mas não é uma calculadora confiável.
- **Perguntas sobre documentos muito recentes** — se um documento foi atualizado há menos de 24h e o trigger de re-ingestão ainda não rodou, o assistente responderá com a versão anterior sem saber que há uma mais recente.
- **Perguntas que dependem de contexto não-documentado** (decisões tomadas em reuniões, exceções negociadas verbalmente com clientes específicos) — o sistema só sabe o que está nos documentos indexados.
- **Alta confiabilidade em documentos com OCR de baixa qualidade** — chunks com score < 0,85 que não passaram por revisão humana serão sinalizados como incertos, mas ainda assim podem ser recuperados e usados na geração.

### Recomendação de alocação do cronograma (3 meses)

> O principal risco de atraso está no **pipeline de ingestão** e nas **aprovações organizacionais**, não no RAG em si. A geração com GPT-4o é a parte tecnicamente mais simples do projeto. Transformar tabelas de frete escaneadas em chunks semânticos precisos, e obter aprovações de TI e segurança, é onde projetos similares tipicamente atrasam.

| Fase | % do tempo | Entregas principais |
|---|---|---|
| Pipeline de ingestão | 40–50% | Parsing, OCR, serialização de tabelas, desnormalização de planilhas, golden dataset |
| Camada de retrieval | 20–25% | Embeddings, índice vetorial, reranking, query decomposition com fallback |
| Integração e interface | 15–20% | Azure Bot Framework + Teams, autenticação, formatação de citações |
| Avaliação e calibração | 10–15% | Testes com atendentes reais, ajuste de prompts, plano de melhoria pós go-live |

> **Aprovações organizacionais (TI, segurança, compliance) não estão no cronograma técnico acima — precisam correr em paralelo desde o dia 1, ou vão atrasar todas as outras fases.**

---

*Documento v2.0 — análise técnica de viabilidade com revisão crítica incorporada. Estimativas numéricas apresentadas como ranges onde há incerteza material. Riscos organizacionais tratados com o mesmo rigor que os riscos técnicos.*
