# Code Review — `feedback-handler.ts`

Revisor: GitHub Copilot (senior code review)
Data: 2026-06-20
Arquivo revisado: `feedback-handler.ts`

---

## Resumo

Foram identificados **6 problemas**, distribuídos entre violações do AGENTS.md, problemas de segurança e bugs potenciais. Nenhum trecho do código está em conformidade com os padrões definidos para o projeto.

---

## Problemas Encontrados

---

### [1] `require` dinâmico dentro do handler

**Classificação:** Violação do AGENTS.md

**Regra violada:** _"Imports estáticos no topo (nunca require dinâmico)"_

**Trecho problemático:**

```typescript
const { CosmosClient } = require("@azure/cosmos");
```

O `require` dinâmico dentro do corpo da função viola diretamente a regra de imports do projeto. Além de ser incompatível com TypeScript strict/ESM, impede que bundlers realizem tree-shaking e dificulta a análise estática de dependências.

**Correção:**

```typescript
// topo do arquivo
import { CosmosClient } from "@azure/cosmos";
```

---

### [2] `console.log` em vez de `pino`

**Classificação:** Violação do AGENTS.md

**Regra violada:** _"pino para logging (nunca console.log)"_

**Trecho problemático:**

```typescript
console.log("Feedback recebido:", JSON.stringify(feedback));
```

O uso de `console.log` é explicitamente proibido. O logger estruturado `pino` deve ser utilizado em seu lugar, pois oferece níveis de log, serialização segura e integração com sistemas de observabilidade.

**Correção:**

```typescript
import pino from "pino";
const logger = pino();

// no handler:
logger.info(
  { queryId: feedback.queryId, rating: feedback.rating },
  "Feedback recebido",
);
```

---

### [3] Dado pessoal (`attendantEmail`) exposto no log

**Classificação:** Violação do AGENTS.md + Problema de segurança

**Regra violada:** _"Nunca logar dados pessoais (e-mail, nome)"_

**Trecho problemático:**

```typescript
console.log("Feedback recebido:", JSON.stringify(feedback));
```

O objeto `feedback` contém `attendantEmail`. Ao serializar o objeto inteiro no log, o e-mail do atendente é exposto. Isso viola a regra de privacidade do AGENTS.md e pode infringir a LGPD dependendo do contexto de uso.

**Correção:** Logar apenas os campos não-sensíveis, como demonstrado no item [2] acima (`queryId`, `rating`). Nunca incluir `attendantEmail` ou qualquer PII no payload de log.

---

### [4] Ausência de validação com Zod

**Classificação:** Violação do AGENTS.md + Bug potencial

**Regra violada:** _"Zod para validação de input"_

**Trecho problemático:**

```typescript
const body = await request.json() as any;

const feedback = {
  queryId: body.queryId,
  rating: body.rating,
  comment: body.comment,
  attendantEmail: body.attendantEmail,
  ...
};
```

O corpo da requisição é tratado como `any` e consumido diretamente sem nenhuma validação. Campos obrigatórios podem estar ausentes ou com tipos incorretos, causando gravação de dados inválidos no Cosmos DB silenciosamente.

**Correção:**

```typescript
import { z } from "zod";

const FeedbackSchema = z.object({
  queryId: z.string().uuid(),
  rating: z.number().int().min(1).max(5),
  comment: z.string().optional(),
  attendantEmail: z.string().email(),
});

const parsed = FeedbackSchema.safeParse(await request.json());
if (!parsed.success) {
  return { status: 400, body: JSON.stringify(parsed.error.flatten()) };
}
const feedback = { ...parsed.data, timestamp: new Date().toISOString() };
```

---

### [5] Cast `as any` quebra o TypeScript strict mode

**Classificação:** Violação do AGENTS.md

**Regra violada:** _"TypeScript strict mode"_

**Trecho problemático:**

```typescript
const body = (await request.json()) as any;
```

O cast para `any` desabilita toda a verificação de tipos do TypeScript, anulando os benefícios do strict mode. Em conjunto com a ausência de Zod (item [4]), isso cria uma superfície de entrada completamente sem tipagem.

**Correção:** Resolvido como consequência da adoção do Zod (item [4]). Após o parse do schema, `parsed.data` é fortemente tipado automaticamente.

---

### [6] `COSMOS_CONNECTION_STRING` pode ser `undefined`

**Classificação:** Bug potencial + Problema de segurança

**Trecho problemático:**

```typescript
const client = new CosmosClient(process.env.COSMOS_CONNECTION_STRING);
```

`process.env.COSMOS_CONNECTION_STRING` é do tipo `string | undefined`. Passar `undefined` para o construtor do `CosmosClient` pode causar comportamento imprevisível em runtime. Adicionalmente, a connection string nunca deve ser logada ou exposta em stack traces.

**Correção:** Validar a variável de ambiente na inicialização do módulo (fora do handler), falhando explicitamente com uma mensagem clara se estiver ausente:

```typescript
const connectionString = process.env.COSMOS_CONNECTION_STRING;
if (!connectionString) {
  throw new Error(
    "Variável de ambiente COSMOS_CONNECTION_STRING não configurada.",
  );
}
const client = new CosmosClient(connectionString);
```

---

## Tabela Consolidada

| #   | Trecho                               | Classificação                      | Severidade |
| --- | ------------------------------------ | ---------------------------------- | ---------- |
| 1   | `require('@azure/cosmos')` dinâmico  | Violação AGENTS.md                 | Alta       |
| 2   | `console.log(...)`                   | Violação AGENTS.md                 | Alta       |
| 3   | `attendantEmail` no log              | Violação AGENTS.md + Segurança     | Alta       |
| 4   | Sem validação Zod                    | Violação AGENTS.md + Bug potencial | Alta       |
| 5   | Cast `as any`                        | Violação AGENTS.md                 | Média      |
| 6   | `COSMOS_CONNECTION_STRING` sem guard | Bug potencial + Segurança          | Média      |

---

## Conclusão

O código não pode ser aprovado no estado atual. **Todos os 6 problemas devem ser corrigidos** antes do merge. Os itens [1], [2], [3] e [4] são bloqueadores diretos por violarem regras explícitas do AGENTS.md. Recomenda-se refatorar o handler aplicando Zod na entrada, pino no logging, imports estáticos e guard de variável de ambiente.
