Vou avaliar o entregável do participante analisando todos os artefatos fornecidos: o arquivo de arquitetura MCP (`novatech_mcp_architecture.md`), a análise de riscos (`risk-analysis.md`), e os prints das 3 sessões de evidência de execução.

---

## Avaliação do Exercício 2.1

### Resumo

O participante entregou um trabalho de qualidade alta, demonstrando domínio sólido de MCP com mapeamento correto de servers locais, aplicação concreta de least privilege com justificativas técnicas por server, e evidência real de execução nos três eixos exigidos (leitura de doc de negócio, recuperação de chunk via corpus, e histórico git). A análise de riscos vai além do pedido mínimo, identificando 4 riscos com mitigações acionáveis e específicas ao contexto local. O principal ponto de atenção é a ausência do arquivo `.mcp/mcp.json` como artefato explícito no entregável.

---

### Scores por Dimensão

| Dimensão                       | Score | Justificativa                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------------------ | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1 — Domínio Conceitual        | 3     | Distingue corretamente tools vs resources (filesystem expõe `read_file`/`write_file` como tools; filesystem-ro trata dados de negócio como read-only resources); nomeia os 4 reference servers locais corretos (filesystem, git, memory, e duas instâncias de filesystem); explica grafo JSONL do memory server com entidades/relações adequadas ao projeto. Conceito de least privilege aplicado com nuance: justificativa por server e não apenas por "boa prática genérica".                                                                                |
| D2 — Uso de Ferramentas        | 3     | Três sessões de evidência real e distintas: (1) listagem de `filesystem-ro` + leitura de `POL-001-politica-devolucao.md` com conteúdo real renderizado; (2) recuperação de chunk via `data/retrieval-corpus/chunks-novatech.md` mostrando input com path absoluto e output com chunk `POL-001-A` identificado; (3) `git_log` retornando commit real (`bbdd003a`, data 2026-06-09, autor `trilha@db1.local`). Os prints mostram o agente usando as tools MCP — não é simulação.                                                                                 |
| D3 — Qualidade do Entregável   | 2     | Mapeamento completo e coerente, análise de riscos bem estruturada com 4 riscos. O gap concreto: **o `.mcp/mcp.json` não foi entregue como artefato explícito** — o enunciado exige "o `.mcp/mcp.json` final" como entregável, e o arquivo está referenciado no texto mas não aparece nos artefatos. A tabela de resumo de least privilege é clara e utilizável, mas não substitui o arquivo de configuração.                                                                                                                                                   |
| D4 — Pensamento Crítico        | 3     | A análise de riscos demonstra julgamento próprio de alto nível: identifica que o `filesystem-rw` não tem noção de "arquivo sensível" (não é só "alguém pode hackear"); propõe mitigação com `.mcpignore` específico; reconhece que `git_show` expõe histórico completo incluindo segredos já deletados (risco não óbvio); propõe restringir `git_show`/`git_blame` se o caso de uso não exigir. R2 (escrita direta em `./src` sem revisão) aponta um risco arquitetural real que vai além do escopo pedido — propõe pasta `./drafts/` como buffer de revisão.  |
| D5 — Aplicabilidade ao Projeto | 3     | Referencia explicitamente `docs/novatech/` e `data/retrieval-corpus/` com os paths corretos do Starter Repo (Anexo D); os documentos lidos na evidência (`POL-001`, `FAQ-atendimento.md`, `PROC-042`) são exatamente os do Anexo A; o chunk recuperado (`POL-001-A`) é coerente com o mapa de cobertura do Anexo B; o commit do git (`starter repo — estrutura + dados semeados dos Anexos A e B`) referencia o contexto do cenário. O memory server é configurado para guardar ADRs e linguagem ubíqua — conectando diretamente com as decisões do cenário 1. |

**Score do exercício: 2.8**

---

### Verificação de Artefatos Machine-Readable

Este exercício não exige AGENTS.md ou skill — o artefato principal é o `.mcp/mcp.json`. A tabela de mapeamento entregue é clara e um técnico conseguiria usar para escrever o JSON, mas o arquivo em si está ausente como entregável explícito. O texto do `novatech_mcp_architecture.md` é prescritivo (não narrativo): especifica ports, `allowedDirectories`, tools por server, e quem consome — o que é positivo. Se o `.mcp/mcp.json` estivesse presente e sintaticamente correto, o D3 seria 3.

---

### Pontos Fortes

1. **Separação de instâncias filesystem** — criar `filesystem-rw` e `filesystem-ro` como servidores separados (em vez de uma instância com permissões mistas) é uma decisão de segurança não trivial e demonstra compreensão real de como o servidor filesystem da Anthropic funciona.

2. **Evidência de execução nos três eixos com qualidade**: o print do chunk recuperado vai além de "mostrar que funcionou" — o agente identifica `POL-001-A` como chunk primário E aponta `POL-001-D` como complementar, demonstrando que o retrieval foi semântico, não apenas por filename.

3. **Análise de riscos com mitigações acionáveis e específicas**: os 4 riscos têm comandos concretos (`git secrets --register-aws`, `git filter-repo`, estrutura de `.mcpignore`), não apenas recomendações vagas de "usar boas práticas de segurança".

---

### Pontos de Melhoria

1. **Entregar o `.mcp/mcp.json` como arquivo** — o enunciado é explícito: "escreva o `.mcp/mcp.json` do projeto". O mapeamento em prosa é excelente como documentação, mas o arquivo de configuração precisa existir como artefato independente, sintaticamente correto, para ser usado diretamente. Sugestão: gerar o JSON a partir do mapeamento e incluí-lo como bloco de código ou arquivo separado.

2. **Documentar a iteração com Claude** — o enunciado pede uso do Claude (chat) para o mapeamento. O entregável apresenta o resultado final mas não mostra o processo: qual prompt foi usado, se houve refinamento entre v1 e v2 do mapeamento. Mesmo um parágrafo descrevendo "o primeiro mapeamento sugeria X, refinei para Y por razão Z" fortaleceria o D2 e evidenciaria o uso real da ferramenta.

3. **Endereçar o server `everything`** — o enunciado menciona `everything` na lista de reference servers disponíveis, mas o participante optou por não usá-lo sem justificar a omissão. Uma nota explícita ("avaliamos `everything` mas não há necessidade no projeto pois...") mostraria que a decisão foi deliberada, não uma lacuna.

---

### Classificação

**Aprovado com distinção (2.8)**

---

### Tópicos da Trilha para Reforço

Score acima de 2.5 — nenhum tópico crítico para reforço. Recomendação opcional: revisar as convenções de entregáveis do Anexo C para garantir que artefatos machine-readable (JSON, YAML) sejam sempre incluídos como arquivos, não apenas referenciados em prosa.
