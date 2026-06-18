# Árvore de Skills — NovaTech Assistant

**Stack:** TypeScript · Azure Functions v4 · Azure AI Search · React · Vitest · pino · Zod  
**Time:** Tech Lead · 2 Devs · QA · Product Specialist · Delivery Manager

---

## Como ler esta árvore

As skills seguem três camadas hierárquicas. Cada Artifact skill herda implicitamente das camadas abaixo dela — um agente que executa `create-rag-endpoint`, por exemplo, precisa primeiro das Foundation skills (`typescript-conventions`, `error-handling`, `logging-conventions`, `validation-with-zod`) e das Domain skills (`azure-functions-v4`, `rag-pattern`).

```
Foundation  →  convenções globais, compartilhadas por todos
   └── Domain  →  padrões por camada, específicos de stack
         └── Artifact  →  receitas de geração, saída direta para o codebase
```

**Frequência:** ●●● Alta · ●●○ Média · ●○○ Baixa

---

## Camada 1 — Foundation

> Convenções globais. Lidas implicitamente a cada geração de código.

| Slug | Descrição | Frase-ativação | Cria | Consome | Freq. |
|---|---|---|---|---|---|
| `typescript-conventions` | Regras globais de TypeScript: tipagem estrita, módulos, nomenclatura, path aliases. | "como devemos tipar X?", "qual padrão de exports?", "strict mode" | Tech Lead | Todos os devs · Copilot · Claude | ●●● |
| `error-handling` | Estratégia de tratamento de erros: classes customizadas, pattern Result/Either, propagação em Azure Functions. | "como lançar erro aqui?", "exception vs Result", "error boundary" | Tech Lead | Devs · QA · Copilot · Claude | ●●● |
| `logging-conventions` | Padrões pino: níveis, campos estruturados obrigatórios (requestId, userId, duration), redação de PII. | "como logar aqui?", "qual nível usar?", "campos obrigatórios do log" | Tech Lead | Devs · Copilot · Claude | ●●● |
| `validation-with-zod` | Uso de Zod: definição de schemas, inferência de tipos, mensagens de erro padronizadas, integração com Azure Functions. | "como validar o body da request?", "schema Zod para X", "parse vs safeParse" | Tech Lead | Devs · Copilot · Claude | ●●● |
| `project-structure` | Organização de pastas, naming de arquivos, onde vive cada camada (functions/, services/, types/, ui/). | "onde criar esse arquivo?", "estrutura do projeto", "qual pasta para X?" | Tech Lead | Todos · Copilot · Claude | ●●○ |

---

## Camada 2 — Domain

> Padrões por camada, específicos de stack. Acionados quando o contexto da tarefa é identificado.

| Slug | Descrição | Frase-ativação | Cria | Consome | Freq. |
|---|---|---|---|---|---|
| `azure-functions-v4` | Anatomia de um endpoint Azure Functions v4: trigger HTTP, bindings, modelo de programação, `app.http()`, middlewares. | "como estruturar um endpoint?", "trigger http v4", "binding de output" | Tech Lead | Devs · Copilot · Claude | ●●● |
| `rag-pattern` | Fluxo padrão RAG do projeto: embed → search (Azure AI Search) → augment prompt → stream resposta. Contratos de entrada/saída. | "como funciona o fluxo RAG?", "busca semântica", "azure ai search query" | Tech Lead | Devs · QA · Copilot · Claude | ●●● |
| `integration-test-patterns` | Convenções Vitest para testes de integração: setup/teardown de Azure Functions, mocks de AI Search, asserções de resposta HTTP. | "como estruturar teste de integração?", "mock azure search", "vitest setup" | QA + Dev | QA · Devs · Copilot · Claude | ●●● |
| `react-component-patterns` | Organização de componentes React no painel web: estrutura de arquivos, props typing, composição, estado local vs contexto. | "como organizar esse componente?", "props interface", "padrão de composição React" | Tech Lead + Dev | Devs · Copilot · Claude | ●●○ |
| `technical-doc-conventions` | Padrões de documentação técnica: estrutura de ADR, seções obrigatórias de README de módulo, linguagem e estilo. | "como escrever esse ADR?", "template README de módulo", "seções obrigatórias da doc" | Tech Lead | Todos · Claude | ●●○ |
| `sdd-template` | Template SDD (Software Design Document / Spec): seções, critérios de aceite, formato de user stories, campos obrigatórios. | "template de spec", "SDD para feature X", "formato user story" | Product Specialist | Product · Delivery Mgr · Claude | ●●○ |

---

## Camada 3 — Artifact

> Receitas de geração. Produzem arquivos prontos para o codebase ou documentação entregável.

| Slug | Descrição | Frase-ativação | Cria | Consome | Freq. |
|---|---|---|---|---|---|
| `create-rag-endpoint` | Receita completa para gerar um endpoint RAG: scaffold do arquivo, imports, handler, integração AI Search, resposta streaming. | "criar endpoint RAG para X", "novo endpoint com busca", "scaffold RAG function" | Tech Lead | Devs · Copilot · Claude | ●●● |
| `create-integration-test` | Receita para gerar teste de integração Vitest para um endpoint: arquivo, describe blocks, mocks de AI Search, casos feliz/triste. | "criar teste de integração para esse endpoint", "gerar test suite", "teste vitest para function" | QA + Dev | QA · Devs · Copilot · Claude | ●●● |
| `create-response-card` | Receita para gerar componente React de card de resposta: props interface, estrutura JSX, estados de loading/error, acessibilidade. | "criar card de resposta", "componente React para exibir resultado", "response card" | Dev + Tech Lead | Devs · Copilot · Claude | ●●○ |
| `create-feedback-form` | Receita para gerar componente React de formulário de feedback: campos, validação Zod client-side, submit handler, estados UX. | "criar formulário de feedback", "form de thumbs up/down", "componente feedback" | Dev | Devs · Copilot · Claude | ●●○ |
| `generate-endpoint-adr` | Receita para gerar ADR de um endpoint: contexto, decisão, consequências, alternativas descartadas — preenchido a partir de um briefing. | "escrever ADR para esse endpoint", "documentar decisão técnica", "gerar ADR" | Tech Lead | Tech Lead · Delivery Mgr · Claude | ●●○ |
| `generate-module-readme` | Receita para gerar README de módulo: visão geral, endpoints expostos, dependências, variáveis de ambiente, como rodar. | "gerar README para esse módulo", "documentar módulo X", "criar README" | Dev + Tech Lead | Todos · Claude | ●●○ |
| `generate-sdd` | Receita para gerar uma spec SDD completa a partir de notas do Product: seções, user stories, critérios de aceite, dependências técnicas. | "transformar notas em SDD", "criar spec da feature X", "gerar SDD" | Product Specialist | Product · Delivery Mgr · Tech Lead · Claude | ●○○ |

---

## Mapa de dependências

```
create-rag-endpoint
  ├── azure-functions-v4        (Domain)
  ├── rag-pattern               (Domain)
  ├── typescript-conventions    (Foundation)
  ├── error-handling            (Foundation)
  └── logging-conventions       (Foundation)

create-integration-test
  ├── integration-test-patterns (Domain)
  ├── rag-pattern               (Domain)
  └── typescript-conventions    (Foundation)

create-response-card / create-feedback-form
  ├── react-component-patterns  (Domain)
  ├── validation-with-zod       (Foundation)
  └── typescript-conventions    (Foundation)

generate-endpoint-adr / generate-module-readme
  └── technical-doc-conventions (Domain)

generate-sdd
  └── sdd-template              (Domain)
```

---

## Distribuição por papel

| Papel | Cria | Consome |
|---|---|---|
| Tech Lead | `typescript-conventions` · `error-handling` · `logging-conventions` · `validation-with-zod` · `project-structure` · `azure-functions-v4` · `rag-pattern` · `technical-doc-conventions` · `create-rag-endpoint` · `create-response-card` · `generate-endpoint-adr` · `generate-module-readme` | Todas |
| Dev | `integration-test-patterns` · `react-component-patterns` · `create-feedback-form` · `create-response-card` · `generate-module-readme` | Foundation + Domain + Artifacts de código |
| QA | `integration-test-patterns` · `create-integration-test` | `integration-test-patterns` · `rag-pattern` · `error-handling` |
| Product Specialist | `sdd-template` · `generate-sdd` | `sdd-template` · `generate-sdd` |
| Delivery Manager | — | `sdd-template` · `generate-sdd` · `generate-endpoint-adr` |

---

## Ordem de criação recomendada

Começar pelas Foundation, pois são pré-requisito de tudo. Com as cinco primeiras skills, o ciclo mais comum do time (criar um endpoint RAG com teste) fica totalmente coberto por agentes.

1. `typescript-conventions`
2. `error-handling`
3. `logging-conventions`
4. `validation-with-zod`
5. `azure-functions-v4`
6. `rag-pattern`
7. `create-rag-endpoint`
8. `integration-test-patterns`
9. `create-integration-test`
10. `react-component-patterns`
11. `create-response-card`
12. `create-feedback-form`
13. `technical-doc-conventions`
14. `generate-endpoint-adr`
15. `generate-module-readme`
16. `sdd-template`
17. `generate-sdd`
18. `project-structure`
