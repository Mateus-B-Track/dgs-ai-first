# Tasks — Query Endpoint

> Gerado a partir de `plan.md` via Spec Driven Development.  
> Stack: TypeScript strict · Azure Functions v4 · Zod · pino · Vitest

---

## QE-001 — Setup do endpoint com validação de input

**Descrição**  
Criar a estrutura de diretórios do feature e implementar o handler HTTP da Azure Function com validação de input via Zod. Esta é a base para todas as tasks subsequentes.

**Arquivos a criar**
- `src/functions/query/handler.ts`
- `src/functions/query/validator.ts`

**Critérios de aceite**
- `POST /api/query` com body `{ question: string }` retorna `200` com body provisório `{ status: "ok" }`.
- `POST /api/query` com `question` ausente ou não-string retorna `400` com `{ error: string }` descrevendo o campo inválido.
- `POST /api/query` com `question: ""` (string vazia) retorna `400`.
- `POST /api/query` com `question` excedendo 2 000 caracteres retorna `400`.
- O schema Zod está em `validator.ts` e é exportado como `QueryInputSchema` + tipo inferido `QueryInput`.
- Nenhuma chamada a `console.log` — logging usa instância `pino` importada de um módulo `src/lib/logger.ts`.
- Testes unitários em Vitest cobrem: input válido, campo ausente, string vazia, string acima do limite.

**Dependências**  
Nenhuma.

**Estimativa** `P` (até 2 h)

---

## QE-002 — Logger compartilhado (pino)

**Descrição**  
Criar o módulo `src/lib/logger.ts` que exporta uma instância configurada de `pino` para ser usada em toda a aplicação.

**Arquivos a criar**
- `src/lib/logger.ts`

**Critérios de aceite**
- Exporta `logger` como instância singleton de `pino`.
- Em ambiente `NODE_ENV=production`, o nível mínimo é `info`; em outros ambientes, `debug`.
- O logger inclui o campo fixo `service: "query-endpoint"` em todos os registros.
- Módulo importável sem efeitos colaterais (não inicia I/O ao importar).
- Teste unitário verifica que o objeto exportado possui os métodos `info`, `warn`, `error`, `debug`.

**Dependências**  
Nenhuma.

**Estimativa** `P` (até 2 h)

---

## QE-003 — Serviço de embedding (Azure OpenAI)

**Descrição**  
Implementar `src/services/search.ts` — função `generateEmbedding(question: string): Promise<number[]>` que converte a pergunta em vetor usando a API de embeddings do Azure OpenAI.

**Arquivos a criar**
- `src/services/search.ts` (função `generateEmbedding`)

**Critérios de aceite**
- Função aceita `string` e retorna `Promise<number[]>`.
- Lê as variáveis de ambiente `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` — lança `Error` com mensagem descritiva se alguma estiver ausente ao inicializar o módulo.
- Implementa retry com exponential backoff: máximo 3 tentativas, delay inicial de 500 ms, fator 2.
- Em caso de falha após todas as tentativas, lança erro tipado `EmbeddingError` com `cause` original.
- Usa `logger` (nunca `console.log`); registra `debug` antes da chamada e `info` com latência após sucesso.
- Testes unitários com mock da API cobrem: sucesso na 1ª tentativa, sucesso na 3ª tentativa (após 2 falhas), falha após 3 tentativas.

**Dependências**  
QE-002

**Estimativa** `M` (2–4 h)

---

## QE-004 — Serviço de busca vetorial (Azure AI Search)

**Descrição**  
Implementar `searchChunks(embedding: number[]): Promise<Chunk[]>` em `src/services/search.ts` — busca os top-5 chunks no índice do Azure AI Search usando o vetor gerado.

**Arquivos a criar / editar**
- `src/services/search.ts` (adicionar `searchChunks` e tipo `Chunk`)

**Critérios de aceite**
- Tipo `Chunk` exportado com campos: `id: string`, `content: string`, `source_document: string`, `vigencia: string | null`.
- Função retorna exatamente os N resultados definidos pela constante `TOP_K = 5` (configurável via env `SEARCH_TOP_K`, padrão 5).
- Lê variáveis `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_API_KEY`, `AZURE_SEARCH_INDEX_NAME` — lança `Error` descritivo se ausentes.
- Implementa retry com exponential backoff (mesma política de QE-003).
- Lança `SearchError` tipado em caso de falha permanente.
- Usa `logger`; registra quantidade de chunks retornados em nível `debug`.
- Testes unitários com mock do SDK cobrem: retorno de 5 chunks, retorno de 0 chunks, falha de rede.

**Dependências**  
QE-002, QE-003

**Estimativa** `M` (2–4 h)

---

## QE-005 — Ordenação por vigência de documentos contraditórios

**Descrição**  
Implementar a lógica de priorização de chunks (ADR-0003): quando há chunks de documentos com o campo `vigencia` preenchido, os mais recentes devem ter maior peso na ordenação final entregue ao prompt-builder.

**Arquivos a criar**
- `src/services/search.ts` (adicionar `rankChunks(chunks: Chunk[]): Chunk[]`)

**Critérios de aceite**
- Função pura `rankChunks` exportada separadamente — não tem efeitos colaterais.
- Chunks com `vigencia` não-nulo são ordenados do mais recente ao mais antigo antes dos chunks sem `vigencia`.
- Chunks sem `vigencia` mantêm a ordem relativa original (estável).
- A função não descarta nenhum chunk — apenas reordena.
- Testes unitários cobrem: todos com vigência, nenhum com vigência, mistura de ambos, vigências com mesmo valor.

**Dependências**  
QE-004

**Estimativa** `P` (até 2 h)

---

## QE-006 — Prompt builder

**Descrição**  
Implementar `src/services/prompt-builder.ts` — monta o array de mensagens para o GPT-4o respeitando o context budget definido no ADR-0002 (~4 K tokens para system prompt + ~8 K para chunks).

**Arquivos a criar**
- `src/services/prompt-builder.ts`

**Critérios de aceite**
- Exporta `buildPrompt(chunks: Chunk[], question: string): Message[]` onde `Message = { role: "system" | "user"; content: string }`.
- Lê o system prompt de `prompts/system-prompt.md` em tempo de inicialização do módulo; lança `Error` descritivo se o arquivo não existir.
- O conteúdo dos chunks é concatenado até o limite de `CHUNK_BUDGET_TOKENS = 8192` tokens (estimativa por caracteres: 1 token ≈ 4 chars); chunks além do budget são descartados com log `warn`.
- O system prompt é truncado a `SYSTEM_BUDGET_TOKENS = 4096` tokens se necessário, com log `warn`.
- Retorna exatamente dois elementos no array: `[{ role: "system", ... }, { role: "user", ... }]`.
- A mensagem `user` inclui os chunks formatados como lista numerada seguida da pergunta.
- Testes unitários cobrem: montagem normal, truncamento de chunks, truncagem de system prompt, arquivo ausente.

**Dependências**  
QE-002, QE-005

**Estimativa** `M` (2–4 h)

---

## QE-007 — Serviço de completion (GPT-4o)

**Descrição**  
Implementar `src/services/completion.ts` — envia o array de mensagens ao GPT-4o via Azure OpenAI e retorna a resposta em texto.

**Arquivos a criar**
- `src/services/completion.ts`

**Critérios de aceite**
- Exporta `getCompletion(messages: Message[]): Promise<string>`.
- Lê variáveis `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_CHAT_DEPLOYMENT` — lança `Error` descritivo se ausentes.
- Implementa retry com exponential backoff (mesma política de QE-003).
- Em caso de falha permanente, lança `CompletionError` tipado com `cause` original.
- Registra latência da chamada em nível `info`; registra tentativas de retry em nível `warn`.
- Testes unitários com mock cobrem: resposta bem-sucedida, sucesso após retry, falha após 3 tentativas.

**Dependências**  
QE-002, QE-006

**Estimativa** `M` (2–4 h)

---

## QE-008 — Response builder e schema de output

**Descrição**  
Implementar `src/functions/query/response-builder.ts` — monta e valida a resposta final da API usando Zod antes de retorná-la ao cliente.

**Arquivos a criar**
- `src/functions/query/response-builder.ts`

**Critérios de aceite**
- Exporta `QueryOutputSchema` (Zod) e tipo inferido `QueryOutput` com campos:
  - `answer: string` — resposta do modelo.
  - `source_documents: string[]` — lista deduplicada dos `source_document` dos chunks usados.
- Exporta `buildResponse(answer: string, chunks: Chunk[]): QueryOutput`.
- `source_documents` não contém duplicatas e está ordenado alfabeticamente.
- Se a validação Zod falhar internamente, lança `ResponseBuildError` com detalhes.
- Testes unitários cobrem: lista com duplicatas, lista vazia, resposta com string em branco (deve lançar erro).

**Dependências**  
QE-001, QE-005

**Estimativa** `P` (até 2 h)

---

## QE-009 — Integração do handler (orquestração fim a fim)

**Descrição**  
Conectar todos os serviços no `handler.ts`: validar input → gerar embedding → buscar chunks → ranquear → montar prompt → obter completion → construir resposta.

**Arquivos a editar**
- `src/functions/query/handler.ts`

**Critérios de aceite**
- O handler usa `QueryInputSchema` de `validator.ts` para validar o body.
- O fluxo completo é executado na ordem: `generateEmbedding` → `searchChunks` → `rankChunks` → `buildPrompt` → `getCompletion` → `buildResponse`.
- Erros tipados (`EmbeddingError`, `SearchError`, `CompletionError`) são capturados e retornam `503` com `{ error: "service_unavailable", detail: string }`.
- Erros de validação retornam `400` com `{ error: "validation_error", detail: string }`.
- Erros inesperados retornam `500` com `{ error: "internal_error" }` — o `detail` original **não** é exposto ao cliente, apenas logado em nível `error`.
- O request ID é injetado no contexto do logger para correlação de logs.
- Teste de integração (ainda com mocks dos serviços Azure) cobre o fluxo happy path e os três cenários de erro acima.

**Dependências**  
QE-001, QE-003, QE-004, QE-005, QE-006, QE-007, QE-008

**Estimativa** `M` (2–4 h)

---

## QE-010 — Testes de integração end-to-end (ambiente de staging)

**Descrição**  
Criar suite de testes de integração que exercita o endpoint real contra os serviços Azure de staging (Azure AI Search populado + Azure OpenAI).

**Arquivos a criar**
- `tests/integration/query.integration.test.ts`

**Critérios de aceite**
- Testes marcados com `@integration` para serem excluídos do CI padrão e rodarem apenas com flag `--run-integration`.
- Happy path: `POST /api/query` com pergunta válida retorna `200`, `answer` não-vazio e `source_documents` com ao menos um item.
- Erro de input: `POST /api/query` sem `question` retorna `400`.
- O teste registra latência total e falha se exceder 10 segundos.
- Variáveis de ambiente necessárias para integração estão documentadas em `.env.integration.example`.

**Dependências**  
QE-009

**Estimativa** `G` (4–8 h)

---

## Resumo de dependências

```
QE-002 ──────────────────────────────────────────┐
QE-001 ──────────────────────────────────────────┤
QE-003 (depende QE-002) ──────────────────────── ┤
QE-004 (depende QE-002, QE-003) ─────────────── ┤
QE-005 (depende QE-004) ──────────────────────── ┤
QE-006 (depende QE-002, QE-005) ─────────────── ┤
QE-007 (depende QE-002, QE-006) ─────────────── ┤
QE-008 (depende QE-001, QE-005) ─────────────── ┤
QE-009 (depende QE-001..QE-008) ─────────────── ┤
QE-010 (depende QE-009) ─────────────────────────┘
```

| ID     | Descrição resumida              | Tamanho | Pode começar em paralelo com |
|--------|---------------------------------|---------|-------------------------------|
| QE-001 | Setup endpoint + Zod validator  | P       | QE-002                        |
| QE-002 | Logger pino                     | P       | QE-001                        |
| QE-003 | Serviço de embedding            | M       | QE-004 (após QE-002)          |
| QE-004 | Busca vetorial AI Search        | M       | QE-005 (após QE-003)          |
| QE-005 | Ordenação por vigência          | P       | QE-006, QE-008                |
| QE-006 | Prompt builder                  | M       | QE-007                        |
| QE-007 | Serviço de completion GPT-4o    | M       | —                             |
| QE-008 | Response builder + schema saída | P       | —                             |
| QE-009 | Integração handler fim a fim    | M       | QE-010                        |
| QE-010 | Testes integração e2e staging   | G       | —                             |
