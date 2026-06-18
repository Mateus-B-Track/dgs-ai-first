## Avaliação do Exercício 2.2

### Resumo

O participante entregou os três artefatos exigidos com qualidade notavelmente alta: um `tasks.md` com decomposição SDD exemplar, evidência concreta de uso do Copilot com prompt específico e resposta documentada, e uma revisão crítica que vai além do mínimo exigido ao identificar três problemas reais — incluindo um erro de API do Zod v4 que exige conhecimento técnico genuíno para detectar. A conexão com as decisões do cenário 1 é explícita e consistente. O único ponto de atenção é que a revisão crítica foi produzida como documento separado, sugerindo que parte dela pode ter sido elaborada fora do fluxo natural com o Copilot, mas os problemas identificados são tecnicamente sólidos e verificáveis.

---

### Scores por Dimensão

| Dimensão                       | Score | Justificativa                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------------------ | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1 — Domínio Conceitual        | 3     | Demonstra compreensão precisa de SDD: tasks com ID, critérios verificáveis, dependências explícitas e estimativa P/M/G. O `tasks.md` reflete o conceito de "atomicidade" corretamente — QE-002 (logger) é separado de QE-001 porque é uma dependência independente testável. A revisão crítica demonstra conhecimento de semver (`^` vs `~`), breaking changes entre Zod v3 e v4, e OWASP A01. |
| D2 — Uso de Ferramentas        | 3     | Evidência real de uso: print do Copilot em produção, prompt detalhado preservado no histórico, e resposta do Copilot documentada com a observação sobre `src/shared/logger.ts` (o agente raciocinou sobre o Anexo C e corrigiu o caminho de `src/lib/` para `src/shared/`). Isso evidencia iteração real — o Copilot avaliou o contexto do repositório e tomou uma decisão estrutural.         |
| D3 — Qualidade do Entregável   | 3     | `tasks.md` com 10 tasks, cada uma com arquivos a criar, critérios verificáveis concretos (ex: "retorna 400 para question excedendo 2.000 caracteres"), dependências e estimativa. Revisão crítica com código antes/depois para os 3 problemas. Tabela de resumo de dependências. Artefatos utilizáveis diretamente por outro membro do time sem esclarecimentos.                               |
| D4 — Pensamento Crítico        | 3     | A revisão vai além dos 2 problemas exigidos e encontra um terceiro. O problema 1 (Zod v4 vs v3) é particularmente forte: identifica que o `package.json` usa `^3.23.0` mas o código gerado usa a API do v4, explica o mecanismo de semver que causa o problema, e propõe fixar a versão como prevenção. Isso é análise técnica real, não checklist de code review.                             |
| D5 — Aplicabilidade ao Projeto | 3     | ADR-0002 citada explicitamente no QE-006 (context budget: 4K system + 8K chunks). ADR-0003 citada no QE-005 (vigência de documentos contraditórios). Stack do cenário 1 respeitada (TypeScript, Azure Functions v4, Azure AI Search, GPT-4o). Paths seguem o Anexo C. O histórico do Copilot mostra o agente referenciando `src/shared/logger.ts` como definido no Anexo C.                    |

**Score do exercício: 3.0**

---

### Verificação de Artefatos Machine-Readable

O `tasks.md` é prescritivo e acionável. Exemplos do que está bem:

- **QE-003:** "Implementa retry com exponential backoff: máximo 3 tentativas, delay inicial de 500 ms, fator 2. Em caso de falha após todas as tentativas, lança erro tipado `EmbeddingError` com `cause` original." — um agente consegue implementar isso sem ambiguidade.
- **QE-005:** "Chunks com `vigencia` não-nulo são ordenados do mais recente ao mais antigo antes dos chunks sem `vigencia`. Chunks sem `vigencia` mantêm a ordem relativa original (estável). A função não descarta nenhum chunk — apenas reordena." — especificação de comportamento de borda completa.
- **QE-006:** Limite de budget em tokens com estimativa de conversão (1 token ≈ 4 chars) — acionável por um LLM.

Não há seções narrativas vagas. O único ponto cosmético é que o critério de aceite de QE-001 usa limite de 2.000 caracteres enquanto o prompt ao Copilot usou 500 — inconsistência menor que não impacta a qualidade estrutural.

---

### Pontos Fortes

1. **Decomposição SDD exemplar:** A separação de QE-005 (rankChunks) como task independente demonstra entendimento real de atomicidade — é uma função pura testável isoladamente, derivada diretamente da ADR-0003, e reutilizável por QE-006 e QE-008.

2. **Evidência de uso real e documentada:** O histórico preserva o prompt completo, a observação do Copilot sobre o conflito de paths (`src/lib/logger.ts` vs `src/shared/logger.ts`), e a revisão crítica com código antes/depois. A cadeia completa está auditável.

3. **Revisão crítica tecnicamente densa:** O problema 1 (API do Zod v4) é um erro real que o Copilot genuinamente gera — o modelo de linguagem foi treinado com código Zod v3 e v4 misturados. Identificar isso, explicar o mecanismo e propor fixação de versão demonstra julgamento de desenvolvedor sênior, não apenas leitura de documentação.

---

### Pontos de Melhoria

1. **Inconsistência no limite do `question`:** O `tasks.md` (QE-001) define limite de 2.000 caracteres, mas o prompt ao Copilot solicitou `max 500`. O código gerado usou 500. O critério de aceite deveria ser derivado do `plan.md` (que não especifica) ou de uma decisão explícita — vale criar uma constante nomeada (`MAX_QUESTION_LENGTH`) e registrar o valor escolhido como comentário ou ADR leve.

2. **QE-002 e QE-001 com dependência circular no `tasks.md`:** QE-001 especifica "logging usa instância `pino` importada de `src/lib/logger.ts`" como critério de aceite, mas QE-002 (que cria esse logger) está listado como sem dependências e paralelo a QE-001. Na prática, QE-001 depende de QE-002 para compilar. Sugestão: ou remover o critério de pino do QE-001 (deixando para QE-009 integrar) ou declarar QE-002 como dependência de QE-001.

3. **Ausência de task para variáveis de ambiente:** O `tasks.md` menciona leitura de env vars em QE-003, QE-004 e QE-007, mas não há task para criar o `.env.example` com as variáveis necessárias para desenvolvimento local. Isso é um entregável concreto e testável que poderia ser QE-000 ou parte de QE-001, e evitaria que um desenvolvedor entrando no projeto precise caçar as variáveis em múltiplos arquivos.

---

### Classificação

**Aprovado com distinção (3.0)**

---

### Tópicos da Trilha para Reforço

Não aplicável — score 3.0.
