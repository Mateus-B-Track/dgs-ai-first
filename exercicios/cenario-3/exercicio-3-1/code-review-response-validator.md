# Code Review — `response-validator.ts`

**Módulo:** `src/services/response-validator.ts`  
**Revisor:** GitHub Copilot  
**Data:** 2026-06-20

---

## Resumo

O módulo valida structured outputs do assistente RAG com dois guardrails: rejeitar respostas sem `source_document` e bloquear afirmações de que devolução de carga perigosa é possível. A análise identificou **5 problemas** de severidade variada.

---

## Problema 1 — `FALLBACK_RESPONSE` viola o próprio schema

**Severidade:** Alta  
**Local:** Linhas 18-24

```ts
const FALLBACK_RESPONSE: RagResponse = {
  answer: "Não foi possível gerar uma resposta confiável...",
  source_document: "", // ← min(1) exige pelo menos 1 caractere
  confidence_score: 0,
};
```

**Risco:** `source_document: ""` não passa na validação do `RagResponseSchema` (que exige `.min(1)`). Isso significa que o tipo `RagResponse` é satisfeito apenas pelo `z.infer`, mas se qualquer consumidor downstream re-validar o objeto com o schema, ele será rejeitado. Além disso, o guardrail de `source_document.trim()` na linha 43 rejeita exatamente esse cenário — o fallback seria rejeitado pela própria função se re-processado.

**Correção proposta:** Separar o tipo do fallback ou usar um discriminated union que distinga respostas válidas de fallbacks:

```ts
// Opção 1: tipo dedicado para fallback
export type FallbackResponse = {
  answer: string;
  source_document: "";
  confidence_score: 0;
};

export type ValidatedResponse = RagResponse | FallbackResponse;

// Opção 2 (mais simples): definir source_document como string sem min(1) no schema,
// e confiar no guardrail funcional da linha 43 para rejeitar strings vazias/espaços.
export const RagResponseSchema = z
  .object({
    answer: z.string().min(1, "answer não pode ser vazia"),
    source_document: z.string(), // sem min(1), validação feita no guardrail
    confidence_score: z.number().min(0).max(1),
  })
  .strict();
```

---

## Problema 2 — `RETURN_PATTERN` não cobre sinônimos relevantes

**Severidade:** Média  
**Local:** Linha 26

```ts
const RETURN_PATTERN = /devolu[çc][ãa]o|devolver|devolvida/i;
```

**Risco:** O regex não captura variações comuns que um LLM pode gerar:

| Variação                    | Capturada?                                                               |
| --------------------------- | ------------------------------------------------------------------------ |
| "devolução"                 | ✅                                                                       |
| "devolver"                  | ✅                                                                       |
| "devolvida"                 | ✅                                                                       |
| "devolvido"                 | ❌                                                                       |
| "devolvidas"                | ❌ (parcialmente — match por "devolvida" funciona, mas "devolvidos" não) |
| "retorno" / "retornar"      | ❌                                                                       |
| "logística reversa"         | ❌                                                                       |
| "enviar de volta"           | ❌                                                                       |
| "restituir" / "restituição" | ❌                                                                       |

Conforme a [POL-001](../docs/novatech/POL-001-politica-devolucao.md), o contexto usa termos como "devolução", "frete reverso" e "coleta reversa". Um LLM pode parafrasear com qualquer um desses sinônimos.

**Correção proposta:**

```ts
const RETURN_PATTERN =
  /devolu[çc][ãa]o|devolv(?:er|id[oa]s?)|retorn(?:o|ar)|reversa|enviar\s+de\s+volta|restitu(?:ir|i[çc][ãa]o)/i;
```

---

## Problema 3 — Guardrail de negativa é facilmente burlado por frases ambíguas

**Severidade:** Alta  
**Local:** Linhas 27 e 47-53

```ts
const NEGATION_PATTERN = /\bnão\b|impossível|proibido|vedado|não é possível/i;
```

**Risco:** A presença de qualquer negativa na resposta inteira desativa o guardrail, mesmo que a negativa se refira a outra parte da frase. Exemplos perigosos:

| Frase                                                                      | Contém negativa?         | Guardrail ativa? | Correto?              |
| -------------------------------------------------------------------------- | ------------------------ | ---------------- | --------------------- |
| "A devolução de carga perigosa é permitida."                               | ❌                       | ✅ Bloqueia      | ✅                    |
| "Não há restrição para devolução de carga perigosa."                       | ✅ ("Não")               | ❌ Passa         | ❌ **Perigoso**       |
| "Não recomendamos, mas a devolução de carga perigosa pode ser solicitada." | ✅ ("Não")               | ❌ Passa         | ❌ **Perigoso**       |
| "A devolução de carga perigosa não é impossível."                          | ✅ ("não", "impossível") | ❌ Passa         | ❌ **Dupla negativa** |

O problema fundamental: **regex não captura semântica**. A simples presença do token "não" em qualquer lugar do texto não garante que a resposta esteja negando a possibilidade de devolução.

**Correção proposta:** Inverter a lógica — em vez de verificar se há negativa, bloquear **sempre** que "carga perigosa" + termos de devolução aparecerem juntos, independentemente de negativa. A resposta correta para carga perigosa é redirecionar ao setor de Gestão de Riscos (ramal 4500), não afirmar ou negar devolução:

```ts
// Guardrail conservador: QUALQUER menção de devolução + carga perigosa → fallback
if (
  DANGEROUS_CARGO_PATTERN.test(response.answer) &&
  RETURN_PATTERN.test(response.answer)
) {
  logger.warn(
    "Guardrail ativado: resposta menciona devolução e carga perigosa simultaneamente",
  );
  return FALLBACK_RESPONSE;
}
```

Se for necessário permitir respostas que expliquem corretamente a impossibilidade, a validação semântica deve ser feita por um segundo LLM (judge) e não por regex.

---

## Problema 4 — `source_document` com apenas espaços/whitespace passa pelo schema

**Severidade:** Baixa  
**Local:** Linhas 7 e 43

```ts
source_document: z.string().min(1, "source_document não pode ser vazio"),
```

**Risco:** `" "` (string com espaços) passa no `.min(1)` do Zod. O guardrail da linha 43 (`source_document.trim()`) cobre esse caso corretamente para a função `validateResponse`, mas o **schema exportado** (`RagResponseSchema`) é reutilizável por outros módulos que podem não chamar `validateResponse`. Qualquer consumidor que confie apenas no schema aceitará `source_document: "   "`.

**Correção proposta:** Aplicar `.trim()` diretamente no schema:

```ts
source_document: z
  .string()
  .trim()
  .min(1, "source_document não pode ser vazio"),
```

Isso garante que o schema exportado já normalize e rejeite strings vazias/whitespace, tornando a validação da linha 43 redundante (pode ser removida ou mantida como defesa em profundidade).

---

## Problema 5 — Schema já usa `.strict()` (sem problema), mas `FALLBACK_RESPONSE` é `as const` implícito

**Severidade:** Informativa

O schema já aplica `.strict()` corretamente — campos extras serão rejeitados. Esse ponto do checklist está adequado.

Porém, `FALLBACK_RESPONSE` é tipada como `RagResponse` mutável. Se outro módulo importar e modificar o objeto, todas as referências serão afetadas (singleton mutável).

**Correção proposta:**

```ts
const FALLBACK_RESPONSE: Readonly<RagResponse> = Object.freeze({
  answer:
    "Não foi possível gerar uma resposta confiável. Por favor, consulte um supervisor.",
  source_document: "",
  confidence_score: 0,
});
```

Ou usar `as const satisfies RagResponse` (se o tipo do fallback for separado conforme Problema 1).

---

## Resumo das ações

| #   | Problema                                      | Severidade | Ação                                                         |
| --- | --------------------------------------------- | ---------- | ------------------------------------------------------------ |
| 1   | Fallback viola o próprio schema               | Alta       | Separar tipo ou relaxar schema delegando ao guardrail        |
| 2   | Regex de devolução incompleto                 | Média      | Expandir `RETURN_PATTERN` com sinônimos                      |
| 3   | Detecção de negativa não é robusta            | Alta       | Inverter lógica — bloquear sempre que ambos termos coexistam |
| 4   | `source_document` whitespace aceito no schema | Baixa      | Usar `.trim()` no Zod                                        |
| 5   | Fallback mutável                              | Info       | `Object.freeze` ou `Readonly`                                |
