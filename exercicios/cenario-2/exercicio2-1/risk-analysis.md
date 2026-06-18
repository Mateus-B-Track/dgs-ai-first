Quatro riscos, ordenados por severidade de impacto. O diagrama abaixo mostra onde cada um incide na arquitetura:Detalhando cada risco com as ações concretas:

---

**R1 — `filesystem-rw` expondo segredos (crítico)**

O servidor MCP de filesystem não tem noção de "arquivo sensível" — ele obedece apenas ao `allowedDirectories`. Se `./src` contiver um `.env`, `config/secrets.yml` ou chave privada, qualquer agente com acesso ao servidor pode lê-los com um simples `read_file`. O risco é amplificado porque o mesmo servidor tem escrita, então um prompt injection poderia sobrescrever esses arquivos.

Mitigação acionável: criar um `.mcpignore` na raiz do projeto (o servidor filesystem da Anthropic o respeita) com padrões como `**/.env`, `**/*.pem`, `**/*.key`, `**/secrets.*`. Paralelamente, mover todos os segredos reais para um gerenciador externo (1Password Secrets, Doppler ou `direnv` com vault) — o repositório não deve conter segredos nem como variáveis de ambiente commitadas.

---

**R2 — escrita direta em `./src` sem revisão humana (alta)**

O `filesystem-rw` com acesso a `./src` permite que um agente escreva código e o "entregue" direto na fonte sem nenhuma revisão. Num fluxo normal de dev isso seria barrado por PR, mas o MCP bypassa esse controle completamente.

Mitigação acionável: restringir o `allowedDirectories` do servidor de escrita para incluir apenas `./drafts/` (pasta de rascunhos do agente) além de `./specs` e `./skills`. O código gerado vai para `./drafts/`, um dev faz a revisão e move para `./src` manualmente ou via PR. Adicionalmente, configurar um pre-commit hook com `lefthook` ou `husky` que bloqueia commits de arquivos de `./src` que não passaram por lint + tests — isso cria uma barreira mesmo se alguém mover o arquivo sem revisar.

---

**R3 — `git_show` expondo histórico com segredos (alta)**

O server `git` expõe `git_show` e `git_log`, que incluem o diff completo de cada commit. Se algum segredo foi commitado no passado (mesmo que deletado depois), ele ainda existe no histórico e pode ser lido por qualquer agente ou dev com acesso ao servidor.

Mitigação acionável: instalar `git-secrets` (da AWS Labs) e configurar `git secrets --register-aws` + padrões customizados para o projeto. Isso bloqueia commits futuros. Para o histórico existente, rodar `git log -p | grep -E "(API_KEY|SECRET|PASSWORD)"` para auditar o que já existe — e se houver vazamento, usar `git filter-repo` para reescrever o histórico antes de conectar o servidor MCP. No lado do servidor, considerar restringir as tools expostas apenas a `git_log`, `git_status` e `git_branch`, removendo `git_show` e `git_blame` se o caso de uso não exigir.

---

**R4 — `memory` persistindo dados sem política de tipos (média)**

O grafo do servidor `memory` é um JSONL que cresce indefinidamente e não tem nenhuma camada de controle sobre o que pode ser armazenado. Se um agente for instruído (ou manipulado via prompt injection no corpus) a criar uma entidade com uma observação contendo credenciais, chaves de API ou PII de usuários, esses dados ficam persistidos localmente — e o arquivo é legível por qualquer processo com acesso ao sistema de arquivos.

Mitigação acionável: definir uma "política de tipos" documentada para o grafo: o que pode e não pode ser uma entidade ou observação (decisões arquiteturais sim, credenciais nunca). Adicionar ao system prompt dos agentes uma instrução explícita como `Nunca armazene no memory server: senhas, tokens, chaves de API, CPFs ou dados pessoais de usuários`. Complementarmente, agendar uma rotina trimestral de `purge` que exporta o grafo, filtra entidades por uma lista de tipos permitidos, e reescreve o arquivo — mantendo o grafo enxuto e auditável.
