
Você está me ajudando a realizar uma análise técnica de viabilidade para um projeto de assistente de IA com RAG (Retrieval-Augmented Generation).

Cenário da empresa:

A NovaTech é uma empresa de médio porte do setor de logística com 1.200 funcionários. Sua operação depende de um conjunto extenso de documentação interna: manuais de procedimento operacional, políticas de compliance, tabelas de SLA por tipo de cliente, regras de cálculo de frete, e normas de segurança de carga.

Hoje, essa documentação está espalhada em três fontes: um SharePoint corporativo com ~800 documentos (PDFs e Word), uma wiki interna no Confluence com ~400 páginas, e uma pasta de rede com planilhas de referência atualizadas mensalmente.

O problema: a equipe de atendimento ao cliente (45 pessoas) gasta em média 12 minutos por chamado buscando informações nessas fontes para responder dúvidas de clientes sobre prazos, regras de frete, políticas de devolução e procedimentos de reclamação. Isso gera atrasos, respostas inconsistentes e frustração tanto dos atendentes quanto dos clientes.

A NovaTech nos contratou para construir um assistente de IA que permita aos atendentes fazer perguntas em linguagem natural e receber respostas fundamentadas na documentação oficial da empresa, com indicação da fonte. O assistente será integrado ao ambiente Microsoft da NovaTech (Teams + SharePoint).

Informações adicionais:

Volume médio de 320 chamados/dia, dos quais ~60% envolvem consulta a documentação.
A documentação é atualizada mensalmente por 3 áreas diferentes (Operações, Compliance, Comercial), sem processo unificado de revisão.
Alguns documentos se contradizem entre versões.
A NovaTech já tem licenças Microsoft 365 E3 e está disposta a provisionar Azure AI Services.
Orçamento para 3 meses de discovery + desenvolvimento + go-live.
Meta: reduzir o tempo médio de busca de 12 para menos de 2 minutos por chamado.
Características técnicas das fontes de dados:

Os PDFs do SharePoint incluem documentos com tabelas complexas (tabelas de frete com 15+ colunas), fluxogramas embutidos como imagens, e alguns documentos escaneados (OCR necessário). A wiki do Confluence tem links internos entre páginas e usa macros customizadas. As planilhas têm fórmulas interdependentes.

Conceito de context engineering aplicado a RAG:

O contexto que o LLM recebe a cada pergunta é limitado pela janela de contexto do modelo. A qualidade da resposta depende de: quais chunks são selecionados (relevância), quantos chunks cabem no contexto (orçamento de atenção), onde ficam posicionados no prompt (informação no meio de contextos longos é "esquecida" — o efeito "lost in the middle"), e o que mais está no contexto competindo por atenção (system prompt, histórico de conversa, instruções).

Tarefa:

Com base em todo o contexto acima, produza uma análise técnica estruturada cobrindo os quatro pontos a seguir:

1. Análise por tipo de fonte
Para cada um dos quatro tipos de conteúdo abaixo, descreva: qual é o desafio específico para um pipeline de RAG, como esse desafio afeta a qualidade das respostas do assistente, e qual estratégia de tratamento você recomenda:

PDFs com tabelas complexas (15+ colunas)
PDFs escaneados (necessitam OCR)
Wiki do Confluence (links internos e macros customizadas)
Planilhas Excel com fórmulas interdependentes
2. Estimativa do tamanho da base em tokens
Calcule o tamanho aproximado da base de documentos em tokens considerando:

~800 documentos PDF com média de 10 páginas cada (estime uma média de palavras por página para PDFs de logística)
~400 páginas wiki com média de 1.500 palavras cada
~50 planilhas (estime um tamanho médio razoável)
Use a regra prática de ~0,75 palavras por token
Apresente os cálculos explicitamente, chegando a um total estimado.

3. Análise de orçamento de contexto
Dado que:

O GPT-4o tem janela de contexto de 128K tokens
O system prompt + instruções fixas consumirão aproximadamente 2K tokens
Cada chunk terá aproximadamente 500 tokens
Responda: quantos chunks cabem por query? O que isso significa para a estratégia de chunking e retrieval? O que acontece com perguntas que exigem cruzar informações de múltiplos domínios (ex: uma pergunta que envolve SLA + regras de frete ao mesmo tempo)?

4. Recomendação de estratégia de chunking
Proponha uma estratégia de chunking justificada pelo tipo de pergunta que os atendentes farão (perguntas curtas e diretas vs. perguntas contextuais) e pelo efeito "lost in the middle". Explique por que chunking fixo sem overlap pode ser problemático neste contexto específico.

Apresente a análise de forma estruturada, com seções claras para cada um dos quatro pontos. Seja específico — prefiro estimativas numéricas justificadas a afirmações genéricas.