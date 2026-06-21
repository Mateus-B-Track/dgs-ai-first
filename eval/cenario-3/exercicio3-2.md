## Avaliação do Exercício 3.2 — Revisão crítica de código gerado por IA

**Papel:** Desenvolvedor
**Data:** 2026-06-20

### Resumo

O participante entregou os quatro artefatos exigidos: revisão própria feita antes da IA, revisão assistida por IA (via Copilot), comparação honesta entre as duas, e código reescrito aderente ao AGENTS.md. Todas as quatro armadilhas obrigatórias foram identificadas na análise própria, o que demonstra julgamento independente real. O ponto de atenção é o uso do **GitHub Copilot** para a etapa de segunda revisão quando o enunciado exigia explicitamente o **Claude** — o procedimento correto seria Copilot para reescrita e Claude para revisão independente.

---

### Scores por Dimensão

| Dimensão                       | Score | Justificativa                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| ------------------------------ | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1 — Domínio Conceitual        | 3     | Demonstra domínio das regras do AGENTS.md e compreende o racional por trás de cada uma (ex: explica que `console.log` deve ser substituído por `pino` pelo suporte a níveis de log e serialização segura; cita LGPD ao justificar por que `attendantEmail` não deve ser logado). A revisão não é mecânica — conecta cada problema à consequência técnica ou de segurança.                                                                                                                                                                                         |
| D2 — Uso de Ferramentas        | 2     | Há evidência clara de geração e uso de ferramenta: revisão própria documentada, revisão do Copilot detalhada com 6 problemas, comparação, e código reescrito. No entanto, o enunciado determina explicitamente **Claude** para a etapa de segunda revisão e **Copilot** para reescrita; o participante inverteu (usou Copilot para revisar, não documentou uso de Claude). Ferramenta produz análise de qualidade, mas protocolo do exercício não foi seguido.                                                                                                    |
| D3 — Qualidade do Entregável   | 3     | Código reescrito (`handler.ts`) é funcional e aderente ao AGENTS.md: imports estáticos no topo, Zod com `safeParse`, `pino` sem PII nos logs (apenas `queryId` e `rating`), guard de variável de ambiente com `throw` explícito, tratamento de erros nas operações de I/O, status `201` para criação via POST. Todos os quatro artefatos exigidos foram entregues e são utilizáveis. Nenhum guardrail deveria apenas logar — e de fato o código bloqueia adequadamente com retornos de erro estruturados.                                                         |
| D4 — Pensamento Crítico        | 3     | Revisão própria feita antes do Claude/Copilot é substantiva: identifica os 4 problemas obrigatórios (armadilhas do exercício) mais 2 adicionais (ausência de tratamento de erros em I/O e semântica REST incorreta — status 200 em vez de 201). A comparação é honesta sobre o que cada revisão encontrou e não encontrou, reconhecendo explicitamente que o Copilot capturou um ponto que a revisão própria perdeu (guard da variável de ambiente). Não há sinal de cópia ou dependência prévia da IA.                                                           |
| D5 — Aplicabilidade ao Projeto | 2     | Conectado ao projeto: referencia o AGENTS.md como guia central, usa o contexto real da NovaTech (Cosmos DB, banco `novatech`, container `feedbacks`, Azure Functions), e posiciona corretamente o módulo em `/src/functions/feedback/handler.ts` conforme o Anexo C. Porém, não conecta explicitamente às decisões dos cenários anteriores — não referencia as ADRs do cenário 1 nem os guardrails formalizados pelo Product Specialist no cenário 2 como origem das convenções aplicadas. Para score 3, esperava-se esse elo com artefatos anteriores da trilha. |

**Score do exercício: 2.6**

---

### Verificação de Armadilhas

| Armadilha (obrigatória)                     | Identificado na revisão própria? | Observação                                                                                           |
| ------------------------------------------- | -------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `as any` sem validação Zod                  | ✅ Sim                           | Identificado como "body recebido como any, sem validação real da estrutura". D4 não penalizado.      |
| `console.log` em vez de pino                | ✅ Sim                           | Identificado diretamente com referência à regra do AGENTS.md.                                        |
| `require` dinâmico (import dentro do corpo) | ✅ Sim                           | Identificado como "importado dinamicamente dentro do código com require(...)".                       |
| `attendantEmail` (PII) logado               | ✅ Sim                           | Identificado com menção explícita à violação de segurança do AGENTS.md. Critério D4 ≤ 1 não ativado. |

Todas as 4 armadilhas obrigatórias foram identificadas na análise própria, antes do uso da ferramenta de IA.

---

### Pontos Fortes

1. **Revisão própria genuinamente independente:** os 4 problemas mínimos exigidos foram identificados sem auxílio de IA, e a revisão ainda extrapolou com 2 pontos adicionais (tratamento de erros e semântica REST), demonstrando competência técnica real.
2. **Comparação honesta e equilibrada:** o participante reconhece explicitamente o que cada revisão encontrou e perdeu, incluindo um ponto capturado pelo Copilot e não pela revisão própria (guard de `COSMOS_CONNECTION_STRING`) — o que é raro e demonstra maturidade crítica.
3. **Código reescrito de alta qualidade:** o `handler.ts` final aplica corretamente Zod, pino, imports estáticos, guard de env var e tratamento de erros em I/O — cobrindo inclusive pontos que iam além do mínimo exigido pelo exercício.

---

### Pontos de Melhoria

1. **Ferramenta errada na etapa 2:** o exercício exige Claude para a segunda revisão independente e Copilot para reescrita. Usar Copilot para revisar reduz a triangulação entre ferramentas distintas (LLMs com diferentes vieses). Refazer o passo 2 com Claude permitiria uma comparação mais rica — e é um requisito explícito da tarefa.
2. **Ancoragem nos artefatos dos cenários anteriores:** a revisão e o código reescrito não referenciam as ADRs (cenário 1) nem os guardrails de produto formalizados pelo Product Specialist (cenário 2) como origem das convenções adotadas. Uma nota como "conforme ADR-0003, usamos Zod para validação de contratos externos" fortaleceria a rastreabilidade técnica.
3. **Armazenamento de PII no Cosmos:** o campo `attendantEmail` é validado e persistido no Cosmos DB sem discussão sobre implicações de LGPD além do logging. O participante demonstrou ciência do problema no log — seria valioso documentar a decisão de armazenar (se intencional) ou propor pseudonimização/hashing como melhoria.

---

### Classificação

**Aprovado com distinção** (score 2.6 — faixa 2.5–3.0)

### Tópicos da Trilha para Reforço

Nenhum tópico crítico para reforço obrigatório. Como aprimoramento opcional:

- **Revisão Crítica de Outputs de IA:** praticar triangulação entre ferramentas diferentes (Claude vs Copilot) para explorar divergências entre modelos com vieses distintos.
- **Rastreabilidade de decisões:** hábito de referenciar ADRs e artefatos de fases anteriores ao justificar escolhas técnicas.
