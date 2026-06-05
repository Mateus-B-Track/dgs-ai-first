I have all the content I need from the documents already in context. Let me now read the remaining uploaded files (system prompts v1 and v2) that aren't in the context window.Tenho todos os materiais necessários. Vou agora produzir a avaliação completa.

---

## Avaliação do Exercício 1.2

### Resumo

O participante produziu um entregável sólido e completo: dois system prompts bem estruturados, mapeamento de contexto estático/dinâmico com estimativa de tokens, três perguntas testadas com respostas documentadas e análise iterativa com melhorias concretas entre v1 e v2. A armadilha obrigatória foi corretamente identificada na v1 e mantida na v2. O principal gap está na profundidade da análise crítica — o participante identificou o problema da resposta à carga perigosa na v1, mas não documentou explicitamente esse raciocínio como análise própria antes de iterar.

---

### Scores por Dimensão

| Dimensão | Score | Justificativa |
|----------|-------|---------------|
| D1 — Domínio Conceitual | 3 | Demonstra compreensão clara de contexto estático vs dinâmico, orçamento de tokens, context rot e a lógica de chunking como unidade de contexto dinâmico. O risco de *context rot* com histórico crescente do Teams é identificado com precisão e relevância para o projeto. |
| D2 — Uso de Ferramentas | 3 | Há evidência explícita de uso do Claude como ambiente de teste real (modelo identificado: Claude Sonnet 4.6). A iteração v1 → v2 é concreta e verificável: a regra 3 foi desdobrada em duas regras distintas (3 e 4) para cobrir o caso de informação parcialmente presente, e a seção de instruções para chunks ganhou a cláusula de "Complemento". As respostas das duas rodadas estão documentadas. |
| D3 — Qualidade do Entregável | 3 | Todos os componentes exigidos estão presentes: system prompt v1, mapeamento estático/dinâmico com estimativa de tokens, respostas das 3 perguntas em ambas versões, e system prompt v2. O artefato é utilizável diretamente — outro membro do time conseguiria colocar em produção sem pedir esclarecimentos. |
| D4 — Pensamento Crítico | 2 | A armadilha da carga perigosa foi identificada corretamente (a resposta v1 já estava correta, mas o participante deveria ter documentado explicitamente *por que* considerou necessário iterar). A análise crítica entre v1 e v2 não está formalizada como um passo separado — o entregável vai direto do teste para a nova versão sem uma seção de "análise das falhas" explícita, como exige o enunciado (item 4 da tarefa). A melhoria é real, mas o raciocínio que a motivou não foi articulado. |
| D5 — Aplicabilidade ao Projeto | 3 | O system prompt referencia diretamente o contexto NovaTech/logística, os guardrails do Product Specialist foram todos incorporados, e o mapeamento de contexto usa dados reais do projeto (Teams como canal de histórico, tiers de cliente, multiplicadores regionais). O risco de context rot é endereçado com linguagem específica ao pipeline. |

**Score do exercício: 2.8**

---

### Verificação de Armadilhas

**Armadilha obrigatória — "prazo de devolução para carga perigosa":**

A resposta correta, conforme POL-001 seção 3.2, é que carga perigosa **não é elegível para devolução** — não existe prazo alternativo.

- **v1:** A resposta afirma corretamente que "cargas perigosas não podem ser devolvidas pelo processo padrão" e cita a exceção da POL-001. Há o alerta "não é possível afirmar que existe um prazo ou processo alternativo". A resposta está substancialmente correta, mas a formulação "não podem ser devolvidas pelo processo padrão" deixa margem para interpretar que existe um processo não-padrão — o que a documentação não prevê. Armadilha **parcialmente identificada** na v1.
- **v2:** A resposta usa a formulação mais precisa: "não são elegíveis para devolução conforme a política vigente", eliminando a ambiguidade. A armadilha foi **plenamente identificada** na v2.

A iteração que corrigiu esse ponto foi real e demonstra que o participante percebeu o problema. Não aplica corte de D4, pois a versão final está correta.

---

### Pontos Fortes

**1. Estrutura do system prompt é exemplar.** As seções Identidade, Regras, Ordem de Prioridade, Instruções para Chunks e Formato de Resposta cobrem exatamente o que um prompt de produção precisa. A regra de prioridade por número de revisão (PROC-042 vs versões anteriores) demonstra consciência direta do risco de mistura de versões do cenário NovaTech.

**2. Mapeamento de contexto estático/dinâmico com identificação de context rot.** A tabela com estimativa de tokens por componente é precisa e o risco de crescimento do histórico do Teams é identificado como vetor de degradação do orçamento de contexto — conceito aplicado corretamente ao projeto, não apenas citado.

**3. Iteração v1 → v2 resolve um problema real e não cosmético.** A regra 3 da v1 tratava ausência total de informação, mas não cobria o caso de informação *parcial* — exatamente o que ocorre na pergunta do frete para Manaus (multiplicador presente, valor base ausente). A v2 desdobra esse caso em uma regra própria (regra 4), e a resposta à mesma pergunta na v2 demonstra o comportamento esperado com o passo a passo para o atendente. Isso é iteração baseada em evidência de teste.

---

### Pontos de Melhoria

**1. Ausência de análise crítica formalizada (item 4 da tarefa).** O enunciado pede explicitamente: "Analise cada resposta: está correta? Citou a fonte? Respeitou os guardrails? Onde errou?" Esse passo não está documentado como seção separada no entregável — o participante passa direto dos resultados dos testes para o system prompt v2. Nas próximas entregas, a análise deve ser uma seção explícita com avaliação resposta a resposta, mostrando o raciocínio que motivou cada mudança.

**2. A formulação da resposta à carga perigosa na v1 poderia ter sido capturada como falha explícita.** A ambiguidade de "não podem ser devolvidas pelo processo padrão" vs "não são elegíveis para devolução" é uma distinção importante em contextos legais e operacionais. Documentar explicitamente esse gap na análise crítica teria demonstrado maior rigor — e é exatamente o tipo de armadilha semântica que sistemas RAG em produção precisam evitar.

**3. O mapeamento de contexto cita GPT-4o como modelo de referência para a janela de 128K.** O exercício foi executado no Claude (Sonnet 4.6, como evidenciado nas perguntas/respostas). O mapeamento deveria referenciar o modelo efetivamente utilizado, ou deixar o modelo como variável explícita — misturar referências de modelos diferentes em um entregável técnico é um gap de precisão.

---

### Classificação

**Aprovado com distinção (2.8)**

---

### Tópicos da Trilha para Reforço

Score ≥ 2.5 — nenhum tópico crítico para reforço obrigatório. Como desenvolvimento opcional, recomenda-se aprofundar **documentação de análise crítica iterativa**: o participante demonstra o pensamento, mas ainda não o registra formalmente como etapa do processo de engenharia de prompt, o que será exigido em exercícios mais avançados da trilha.