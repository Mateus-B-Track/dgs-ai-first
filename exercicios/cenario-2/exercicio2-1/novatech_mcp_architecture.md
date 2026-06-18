Aqui está o mapeamento completo, servidor por servidor:

---

**`filesystem-rw`** — leitura e escrita em código/specs/skills

Este é o único servidor com permissão de escrita. Ele expõe `read_file`, `write_file`, `create_file`, `delete_file` e `list_dir`, restrito às pastas `./src`, `./specs` e `./skills`. É consumido por devs (via editor/CLI) e pelo agente de código (geração, refatoração, atualização de skills). Nunca deve ter acesso à `./docs` ou `./data` — uma escrita acidental no corpus ou na documentação seria difícil de rastrear.

---

**`filesystem-ro`** — leitura de documentação e corpus

Instância separada do mesmo servidor `@modelcontextprotocol/server-filesystem`, mas configurada com `--read-only` e escopo restrito a `./docs/novatech` e `./data/retrieval-corpus`. Expõe apenas `read_file` e `list_dir`. Consumido pelo agente RAG (injeção de contexto) e pelo agente de código (referência de regras de negócio). A separação física do servidor evita que um bug de configuração conceda escrita acidentalmente.

---

**`git`** — histórico e branches do repositório local

Usa `@modelcontextprotocol/server-git` apontando para o repositório local. Expõe `git_log`, `git_diff`, `git_status`, `git_branch`, `git_show` e `git_blame`. Sem operações de escrita (`commit`, `push`, `checkout` destrutivo). Consumido principalmente por devs para rastrear contexto histórico e por agentes que precisam entender o que mudou em um arquivo antes de propor edições.

---

**`memory`** — grafo persistente de decisões e linguagem ubíqua

Usa `@modelcontextprotocol/server-memory` com backend em JSONL local. Expõe `create_entities`, `add_observations`, `create_relations`, `search_nodes`, `open_nodes` e `read_graph`. O grafo deve conter entidades como decisões arquiteturais (ADRs), termos do domínio (linguagem ubíqua), personas e invariantes de negócio. Consumido por todos os agentes para manter coerência entre sessões — sem isso cada nova janela de contexto começa do zero.

---

**Resumo de least privilege aplicado:**

| Servidor        | Permissão     | Pastas                                       |
| --------------- | ------------- | -------------------------------------------- |
| `filesystem-rw` | r/w           | `./src`, `./specs`, `./skills`               |
| `filesystem-ro` | r             | `./docs/novatech`, `./data/retrieval-corpus` |
| `git`           | r (histórico) | repo local                                   |
| `memory`        | r/w (grafo)   | `knowledge-graph.jsonl`                      |

Dois pontos práticos para a configuração: rode cada servidor em uma porta diferente no `claude_desktop_config.json` e defina `allowedDirectories` explicitamente em cada instância — o servidor filesystem respeita essa lista e recusa qualquer path fora dela, o que é a principal barreira de contenção.
