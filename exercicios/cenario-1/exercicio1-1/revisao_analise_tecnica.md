## Revisão Crítica — O que está errado ou fraco na análise

### 1. As estimativas de tokens são precisas demais para serem confiáveis

A análise apresenta números como "3.733.333 tokens" com uma falsa sensação de rigor. O problema está nas premissas:

**350 palavras por página para PDFs de logística é provavelmente subestimado.** PDFs técnicos de logística com tabelas de frete, fluxogramas e notas de rodapé podem ter facilmente 500–800 palavras por página quando você serializa as tabelas linha a linha — que é exatamente o que a própria análise recomenda fazer. Se cada linha de tabela vira um chunk com cabeçalhos repetidos ("Tabela de frete | Peso: 6–10 kg | Destino: Sul | Prazo SLA: 3 dias úteis | Valor: R$ 45,00"), o volume tokenizado explode. A estimativa de 350 palavras/página assume texto corrido, não a representação serializada recomendada. Há uma contradição interna aqui.

**A estimativa de 200 linhas × 8 colunas por planilha é um chute.** A análise reconhece isso implicitamente com "tamanho médio razoável", mas apresenta o número como se fosse derivado de algo. Planilhas de tarifas de frete com segmentações por CEP, tipo de carga, modal, peso e destino podem ter facilmente 5.000–20.000 linhas. Uma única planilha de tabela de frete rodoviário nacional pode ter mais tokens do que toda a estimativa das 50 planilhas combinadas.

**O que isso significa na prática:** o índice pode ser 3–5× maior do que estimado, o que afeta custo de embedding, custo de armazenamento no Azure AI Search e, principalmente, a latência de retrieval.

---

### 2. A meta de "> 85% de acurácia" é vaga até ser inútil

A análise usa essa métrica como se fosse uma garantia. Mas:

- **85% de acurácia em quê, exatamente?** Acurácia de recuperação do chunk certo? Acurácia factual da resposta final? Satisfação do atendente com a resposta? Esses números divergem radicalmente na prática.
- Projetos RAG em produção com documentação real, contraditória e mal estruturada raramente chegam a 85% de acurácia factual nas primeiras versões. Uma meta mais honesta para um MVP de 3 meses seria 65–75%, com plano de melhoria iterativa.
- A análise não menciona como essa acurácia será medida. Sem um golden dataset de perguntas e respostas esperadas validadas pela NovaTech, o número é inauferível.

---

### 3. O prazo de 3 meses ignora a complexidade política e organizacional

A análise foca quase inteiramente em desafios técnicos. Mas os maiores riscos de atraso em projetos RAG corporativos são não-técnicos:

- **Governança de dados:** Quem autoriza o acesso do pipeline ao SharePoint corporativo? Há dados sensíveis (salários, contratos com clientes, informações de fornecedores) misturados com a documentação operacional? A análise não menciona isso em nenhum momento.
- **Aprovação de TI e segurança:** Provisionar Azure AI Services e conectar ao tenant Microsoft 365 E3 requer aprovação de segurança da informação. Em empresas de médio porte, isso pode levar 4–8 semanas sozinho.
- **Resistência dos curadores de conteúdo:** As 3 áreas que atualizam a documentação (Operações, Compliance, Comercial) precisam adotar novos processos. A análise propõe triggers automáticos de re-ingestão, mas não considera que essas equipes podem resistir a ter seus documentos "processados por IA" sem controle.
- **Ausência de SLA de resposta do assistente:** A análise define o objetivo como "< 2 minutos" para o atendente, mas não define qual é o tempo aceitável de resposta do próprio assistente. Se a query decomposition + multi-step retrieval + reranking levar 8–12 segundos por pergunta, isso é aceitável num call center com cliente na linha?

---

### 4. A estratégia para documentos contraditórios é ingenuamente otimista

A análise propõe: "priorizar a versão mais recente" e "sinalizar ambiguidade ao atendente". Isso parece razoável na teoria, mas:

- **"Versão mais recente" não é sinônimo de "versão correta".** Se o departamento Comercial atualizou uma tabela de SLA com dados errados ontem, o assistente vai priorizar a versão errada sobre a versão correta de 3 meses atrás.
- **Sinalizar ambiguidade ao atendente é transferir o problema, não resolvê-lo.** O atendente que hoje já não sabe qual documento usar vai continuar sem saber — só que agora com uma mensagem do assistente dizendo "há conflito entre documentos". A análise não propõe nenhum processo para resolver as contradições antes da ingestão.
- O problema real é que a NovaTech não tem processo unificado de revisão — e o assistente de IA não vai criar esse processo. A análise deveria recomendar explicitamente que a resolução das contradições é um pré-requisito de qualidade de dados, não um problema a tratar em runtime.

---

### 5. Query decomposition é apresentado como solução simples para um problema difícil

A análise recomenda query decomposition para perguntas multi-domínio como se fosse um componente trivial de implementar. Na prática:

- O classificador que detecta perguntas multi-domínio precisa ser treinado ou promovido — com exemplos reais da NovaTech. Quantos exemplos? Quem vai rotulá-los?
- A decomposição automática de queries frequentemente introduz erros: a sub-query gerada pelo LLM pode ser semanticamente diferente da intenção original.
- Multi-step retrieval com múltiplas chamadas ao LLM multiplica a latência. Se cada passo leva 2–3 segundos, uma pergunta com 3 domínios pode levar 8–12 segundos. Em contexto de call center, isso é muito tempo.
- A análise não considera um fallback: o que acontece quando a decomposição falha ou retorna sub-queries que não encontram nada relevante?

---

### 6. OCR com "fila de revisão humana" não está dimensionada

A análise propõe que chunks com confidence score < 0,85 entrem em fila de revisão humana. Mas:

- Qual a proporção estimada de chunks abaixo desse threshold? Se 30% dos PDFs escaneados têm qualidade ruim, e cada documento tem 10 páginas com 5 chunks por página, estamos falando potencialmente de centenas ou milhares de chunks aguardando revisão antes da indexação inicial.
- Quem faz essa revisão? Com que prazo? O cronograma de 3 meses tem buffer para isso?
- A análise não menciona que a ingestão inicial provavelmente não estará completa no go-live — o assistente vai ao ar com uma base parcial, o que pode gerar frustração dos atendentes se eles perceberem que o sistema "não sabe" coisas que estão nos documentos.

---

### 7. A integração com Microsoft Teams não é mencionada tecnicamente

A análise diz que o assistente "será integrado ao ambiente Microsoft da NovaTech (Teams + SharePoint)" mas dedica apenas uma linha ao assunto na seção de cronograma ("integração Microsoft Teams + interface do atendente"). Isso é uma omissão significativa:

- **Teams como canal de atendimento tem limitações sérias para RAG:** as mensagens têm limite de caracteres, rich text é limitado, citações de fonte são difíceis de formatar de forma utilizável.
- **Autenticação e controle de acesso:** O assistente deve responder igual para todos os 45 atendentes, ou deve respeitar permissões individuais de acesso aos documentos do SharePoint? Se um atendente não tem acesso a um documento, o assistente pode citar esse documento na resposta?
- A análise não menciona se será usado Azure Bot Framework, Power Virtual Agents, ou uma integração customizada via API do Teams — decisões que impactam fortemente o prazo.

---

### 8. O número "192 chamados/dia" e "30 horas-homem/dia" merece ceticismo

A análise calcula "~30 horas-homem por dia" de economia como se o assistente resolvesse 100% das consultas de documentação. Mas:

- O assistente vai errar. Com acurácia realista de 70–75% no MVP, em 30% dos casos o atendente ainda vai precisar buscar manualmente — levando talvez não 12 minutos, mas 6–8 minutos (já foi ao assistente, não encontrou, agora busca manualmente mais frustrado).
- A análise assume que "< 2 minutos com o assistente" é uma meta técnica. Mas se o atendente precisar verificar a resposta do assistente antes de passar ao cliente (o que é provável nas primeiras semanas), o tempo total pode não reduzir tanto.
- O ganho real de tempo provavelmente virá de forma gradual, não no dia 1 do go-live.

---

### O que a análise acerta e deve ser mantido

Para ser equilibrado: as recomendações técnicas de pipeline (Azure Document Intelligence para tabelas, serialização linha a linha, parent-child chunking, metadados por chunk, overlap de 10–15%) são sólidas e bem justificadas. O diagnóstico dos riscos por tipo de fonte é correto. A identificação do "lost in the middle" como problema real é pertinente.

O problema não é o que está lá — é o que falta, e a falsa precisão em algumas estimativas que pode criar expectativas irreais com o cliente.

---

### Recomendações para a próxima versão da análise

1. **Apresentar as estimativas de tokens como ranges**, não valores únicos: "entre 5M e 15M tokens dependendo da estratégia de serialização" é mais honesto que "4.960.000 tokens".
2. **Separar riscos técnicos de riscos organizacionais/políticos** — e tratar os segundos com o mesmo rigor.
3. **Definir o golden dataset de avaliação** como entregável do discovery, não como pressuposto.
4. **Colocar qualidade de dados (resolução de contradições) como pré-condição**, não como feature do sistema.
5. **Dimensionar a fila de revisão de OCR** com estimativa de volume e responsável nomeado.
6. **Incluir uma seção honesta sobre o que o sistema não vai conseguir fazer bem** no MVP de 3 meses — gerenciar expectativas é parte do trabalho de engenharia.