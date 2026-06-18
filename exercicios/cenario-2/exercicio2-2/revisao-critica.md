# Revisão Crítica — Query Endpoint (QE-001)

> Exercício 2.2 — Desenvolvedor · Fase de Estruturação  
> Código revisado: `src/functions/query/handler.ts`, `src/functions/query/validator.ts`, `src/functions/query/response-builder.ts`

---

## Problema 1 — API obsoleta do Zod v4 em `validator.ts`

**Arquivo:** `src/functions/query/validator.ts`  
**Severidade:** 🔴 Erro de compilação (bloqueia build)

### Código com problema

```typescript
export const QueryInputSchema = z.object({
  question: z
    .string({
      required_error: "question is required", // ❌ propriedade não existe no Zod v4
      invalid_type_error: "question must be a string", // ❌ propriedade não existe no Zod v4
    })
    .min(3, "question must be at least 3 characters")
    .max(500, "question must be at most 500 characters"),
});
```

### Diagnóstico

O `package.json` declara `zod: "^3.23.0"`, mas o erro de tipo reportado pelo TypeScript é característico da **Zod v4**, que quebrou a API do construtor `z.string()`: os parâmetros `required_error` e `invalid_type_error` foram removidos. O tipo aceito agora é `{ error?: string | $ZodErrorMap; message?: string }`.

O erro de compilação é:

```
No overload matches this call.
  Object literal may only specify known properties, and 'required_error' does not exist
  in type '{ error?: string | $ZodErrorMap<...> | undefined; message?: string | undefined; }'.
ts(2769)
```

### Ajuste necessário

Substituir as propriedades obsoletas pela propriedade `error` (Zod v4) ou remover o objeto e confiar nas mensagens dos refinamentos:

```typescript
question: z
  .string({ error: "question must be a string" })
  .min(3, "question must be at least 3 characters")
  .max(500, "question must be at most 500 characters"),
```

> **Lição:** ao usar `^` no semver, uma major release do Zod (3 → 4) pode ser instalada automaticamente. Em projetos de produção, fixar `"zod": "3.23.x"` ou `"~3.23.0"` evita breaking changes inesperados.

---

## Problema 2 — `authLevel: 'anonymous'` expõe o endpoint sem autenticação

**Arquivo:** `src/functions/query/handler.ts` (linhas 50–56)  
**Severidade:** 🔴 Risco de segurança (OWASP A01 — Broken Access Control)

### Código com problema

```typescript
app.http("query", {
  methods: ["POST"],
  authLevel: "anonymous", // ❌ sem autenticação
  route: "query",
  handler: queryHandler,
});
```

### Diagnóstico

`authLevel: 'anonymous'` significa que qualquer cliente na internet pode chamar `POST /api/query` sem nenhuma credencial. Em produção, isso expõe o endpoint a:

- **Abuso de custo**: cada requisição consome tokens do Azure OpenAI (GPT-4o) — um atacante pode gerar custo irrestrito.
- **Extração de dados**: o endpoint retorna informações da base documental da NovaTech sem qualquer controle de acesso.

### Ajuste necessário

A decisão de autenticação deve ser registrada como ADR, mas as opções imediatas são:

1. **`authLevel: 'function'`** — exige `x-functions-key` header ou query param. Mínimo aceitável para staging.
2. **Proxy via API Gateway** — a arquitetura do projeto prevê o API Gateway da NovaTech como camada de autenticação OAuth2/PKCE. Nesse caso, o `authLevel` pode ficar como `'anonymous'` **somente se** a Function não for exposta diretamente na internet (apenas acessível pelo Gateway via VNet ou IP restriction).

---

## Problema 3 — `ZodError` não tratada no `response-builder.ts`

**Arquivo:** `src/functions/query/response-builder.ts`  
**Arquivo impactado:** `src/functions/query/handler.ts` (QE-009)  
**Severidade:** 🟡 Bug latente (falha silenciosa em produção)

### Código com problema

```typescript
export function buildResponse(answer: string, chunks: Chunk[]): QueryOutput {
  const source_documents = [
    ...new Set(chunks.map((c) => c.source_document)),
  ].sort();
  return QueryOutputSchema.parse({ answer, source_documents }); // ❌ lança ZodError não tipada
}
```

### Diagnóstico

`QueryOutputSchema.parse()` lança uma `ZodError` genérica se `answer` for uma string vazia (o que pode acontecer se o LLM retornar uma resposta em branco). Essa exceção:

1. **Não é capturada pelo handler** — subirá como erro não tratado, resultando em `500` sem log estruturado e sem `detail` útil para diagnóstico.
2. **Não é um erro tipado** — o plano (QE-009) prevê `EmbeddingError`, `SearchError` e `CompletionError` como erros tipados com `cause`. `ZodError` de output não segue esse padrão.

### Ajuste necessário

Criar um `ResponseBuildError` tipado e usar `safeParse` internamente:

```typescript
export class ResponseBuildError extends Error {
  constructor(
    message: string,
    public readonly cause?: unknown,
  ) {
    super(message);
    this.name = "ResponseBuildError";
  }
}

export function buildResponse(answer: string, chunks: Chunk[]): QueryOutput {
  const source_documents = [
    ...new Set(chunks.map((c) => c.source_document)),
  ].sort();
  const result = QueryOutputSchema.safeParse({ answer, source_documents });
  if (!result.success) {
    throw new ResponseBuildError(
      `Invalid response shape: ${result.error.issues.map((i) => i.message).join("; ")}`,
      result.error,
    );
  }
  return result.data;
}
```

O handler (QE-009) deve então capturar `ResponseBuildError` e retornar `500` com log em nível `error`, sem expor o `detail` ao cliente.

---

## Resumo

| #   | Arquivo               | Problema                                                  | Severidade            | Impacto imediato                                 |
| --- | --------------------- | --------------------------------------------------------- | --------------------- | ------------------------------------------------ |
| 1   | `validator.ts`        | `required_error`/`invalid_type_error` obsoletos no Zod v4 | 🔴 Erro de compilação | Build quebrado                                   |
| 2   | `handler.ts`          | `authLevel: 'anonymous'` sem proteção                     | 🔴 Segurança          | Endpoint público sem autenticação                |
| 3   | `response-builder.ts` | `ZodError` não tratada no output                          | 🟡 Bug latente        | 500 sem log estruturado quando LLM retorna vazio |
