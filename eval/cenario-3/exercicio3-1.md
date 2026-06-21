## Avaliação do Exercício 3.1 — Structured output e verificações determinísticas

**Papel:** Desenvolvedor
**Data:** 2026-06-20

### Resumo

O participante entregou os três artefatos exigidos: schema Zod, módulo `response-validator.ts` inicial (gerado com Copilot), code review documentado com 5 problemas identificados e um `response-validator-corrigido.ts` com todas as correções aplicadas. A qualidade técnica é alta — o problema mais sutil do guardrail 2 (negação facilmente burlável por frases como "Não há restrição para devolução") foi identificado e corrigido com abordagem conservadora. O único ponto de atenção é que o code review está atribuído ao "GitHub Copilot" quando o exercício exigia explicitamente o uso do **Claude** para essa etapa.

---

### Scores por Dimensão

| Dimensão                       | Score | Justificativa                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------------------ | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1 — Domínio Conceitual        | 3     | Demonstra compreensão precisa de structured output (Zod + safeParse + `.strict()`) e distingue explicitamente o que o prompt faz probabilisticamente do que o código garante deterministicamente. O Problema 3 do code review ("regex não captura semântica") evidencia que o participante sabe onde a abordagem determinística tem limites e como endereçá-los (judge de segunda camada ou lógica conservadora).                                                                                                                                                                                              |
| D2 — Uso de Ferramentas        | 2     | Há evidência clara de geração com Copilot (`response-validator.ts`) e de revisão analítica (5 problemas com localização por linha, exemplos de frases perigosas e correções concretas). No entanto, o code review está atribuído a "Revisor: GitHub Copilot", quando o enunciado exige explicitamente **Claude** para essa etapa. Ferramenta errada para o passo certo — a análise existe, mas o uso não segue o protocolo do exercício.                                                                                                                                                                       |
| D3 — Qualidade do Entregável   | 3     | Três artefatos entregues e funcionais. Schema válido com `.strict()`, tipo correto para confidence_score (0–1), todos os campos obrigatórios. Os dois guardrails **bloqueiam** (retornam FALLBACK_RESPONSE), não apenas logam. A versão corrigida resolve os problemas de Alta severidade: fallback tipado separadamente com `FallbackResponse`, regex de devolução expandido com sinônimos (retorno, reversa, restituição), lógica do guardrail 2 invertida para abordagem conservadora, `.trim()` aplicado no schema. Código compilável e aderente ao padrão do projeto.                                     |
| D4 — Pensamento Crítico        | 3     | Identifica 5 problemas reais, dois de Alta severidade. O mais sofisticado é o Problema 3: demonstra com exemplos concretos que `NEGATION_PATTERN` é burlável por frases como "Não há restrição para devolução de carga perigosa" ou "Não recomendamos, mas a devolução pode ser solicitada" — e explica corretamente por que a solução via regex é insuficiente para capturar semântica, propondo inversão da lógica ou judge de segunda camada. O Problema 1 (fallback que viola o próprio schema) é uma armadilha sutil de tipagem que exige raciocínio sobre o contrato entre consumidores downstream.      |
| D5 — Aplicabilidade ao Projeto | 2     | Conectado ao projeto: usa `../shared/logger.js` da estrutura do repositório, posiciona o módulo em `/src/services/response-validator.ts` conforme o Anexo C, e cita a [POL-001](../../docs/novatech/POL-001-politica-devolucao.md) com link ao justificar os sinônimos de devolução ("frete reverso", "coleta reversa"). Porém, não referencia explicitamente o AGENTS.md como fonte das convenções de logger e Zod, nem cita os guardrails formalizados pelo Product Specialist no cenário 2 como origem das regras implementadas. Para score 3, esperava-se ancoragem nos artefatos dos cenários anteriores. |

**Score do exercício: 2.6**

---

### Verificação de Armadilhas

Este exercício não contém armadilhas pré-plantadas no sentido estrito (código com violações intencionais para detectar), mas o enunciado indica dois problemas esperados como exemplos de análise crítica:

| Armadilha / Problema esperado                          | Identificado?                                                                                             | Observação                                                                       |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Schema aceita campos extras?                           | ✅ Sim — o próprio schema já usa `.strict()` e o Problema 5 do code review confirma que isso está correto | O participante confirma a ausência do problema, o que também é análise válida    |
| Regex de "carga perigosa + devolução" cobre variações? | ✅ Sim — Problema 2, com tabela de variações não cobertas e correção                                      | Identificação precisa com expansão para sinônimos do domínio                     |
| Guardrail burlável por negativa superficial            | ✅ Sim — Problema 3, com exemplos de frases perigosas que passariam pelo filtro original                  | Identificação além do que o enunciado sugeriu, com proposta de abordagem correta |

---

### Pontos Fortes

1. **Guardrail 2 corrigido com abordagem conservadora:** A inversão da lógica ("sempre bloquear quando ambos os padrões coexistem, independente de negativa") é a solução correta para o limite semântico do regex. O participante justifica a decisão com exemplos de risco real.
2. **Problema 1 (fallback vs schema) demonstra domínio de TypeScript/Zod:** Identificar que `FALLBACK_RESPONSE: RagResponse = { source_document: "" }` viola `.min(1)` e que consumidores downstream podem re-validar é uma análise de nível sênior sobre contratos de tipo.
3. **Código final completo e aderente ao padrão:** A versão corrigida usa `pino` via `logger`, Zod com `.strict()` e `.trim()`, `Object.freeze` para imutabilidade do fallback, e `FallbackResponse` como tipo discriminado — todos os elementos da identidade técnica do projeto.

---

### Pontos de Melhoria

1. **Usar a ferramenta certa para cada etapa:** O enunciado exige Claude para o code review. Usar Copilot para ambas as etapas perde o propósito pedagógico de comparar dois instrumentos com perfis distintos de análise. Em avaliações futuras, entregar evidência de ambas as ferramentas separadamente.
2. **Ancorar nas decisões dos cenários anteriores:** O AGENTS.md (construído no cenário 2) é a fonte das regras de `pino`, Zod e imports estáticos aplicadas no código. Citá-lo explicitamente no code review transforma uma boa prática isolada em governança rastreável. Da mesma forma, os guardrails implementados vêm das regras formalizadas pelo Product Specialist — referenciar essa origem fortalece a D5.
3. **Discutir o ponto de HITL explicitamente:** O exercício menciona HITL como conceito da fase. A abordagem conservadora do guardrail 2 (redirecionar ao supervisor) implicitamente cria um ponto de human-in-the-loop, mas o participante não nomeia isso. Uma frase explicitando "esta decisão cria um HITL para o caso de carga perigosa" demonstraria domínio conceitual mais completo.

---

### Classificação

**Aprovado com distinção** (score 2.6 — faixa 2.5–3.0)

### Tópicos da Trilha para Reforço

Nenhum reforço obrigatório. O participante domina os dois tópicos do cenário. Recomendação opcional: aprofundar o padrão de **ferramentas em cadeia** (Claude + Copilot como instrumentos complementares) para extrair o máximo do protocolo de geração + revisão crítica com perspectivas distintas.
