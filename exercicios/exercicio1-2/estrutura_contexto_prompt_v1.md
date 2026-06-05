## Mapeamento de Contexto Estático/Dinâmico

| Parte | Tipo | Estimativa de Tokens |
|---|---|---|
| System prompt completo | Estático | ~450 tokens |
| Metadados do cliente (tier, ID) | Dinâmico | ~50 tokens |
| Chunks recuperados (3 × ~500) | Dinâmico | ~1.500 tokens |
| Pergunta do atendente | Dinâmico | ~30 tokens |
| Histórico da conversa no Teams | Dinâmico, crescente | 0 → até ~5.000 tokens |

**Orçamento total típico por query:** ~2.000–2.500 tokens — bem dentro da janela de 128K tokens do GPT-4o.

> **Risco — Context Rot:** conversas longas no Teams acumulam histórico de forma crescente.
> A partir de determinado ponto, o histórico começa a competir com os chunks pelo orçamento disponível,
> podendo forçar o truncamento de chunks relevantes ou da própria pergunta.
> Esse é o efeito de *context rot* que precisa ser endereçado na estratégia de gerenciamento de contexto do pipeline.