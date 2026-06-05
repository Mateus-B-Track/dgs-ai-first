# Avaliação — Exercício 1.1 · Desenvolvedor · Cenário 1

**Programa:** Trilha de Certificação AI First — DGS / DB1 Global Software
**Exercício:** 1.1 — Análise de viabilidade técnica com fundamentos de LLM e engenharia de contexto

---

## Resumo

Entregável de alto nível técnico que supera amplamente o esperado para o exercício. O participante produziu análise profunda, específica ao domínio NovaTech, com estimativas apresentadas como ranges com justificativa metodológica explícita — sinal claro de pensamento crítico. A iteração v1→v2 está documentada com nota explicativa detalhando o que foi corrigido, evidenciando o ciclo gerar→avaliar→iterar. O entregável é imediatamente acionável por qualquer membro do time sem necessidade de esclarecimentos.

---

## Scores por Dimensão

| Dimensão | Score | Justificativa |
|----------|:-----:|---------------|
| D1 — Domínio Conceitual | 3 | Domínio profundo e nuançado em todos os tópicos. Tokens/context window: cálculo detalhado com cenários otimistas e pessimistas, multiplicador de serialização explicado com exemplo concreto (tabela 15 col × 200 linhas = 26× o texto linear). Lost in the middle: corretamente identificado e aplicado à recomendação de 20–25 chunks (não apenas citado como conceito). RAG: desafios distintos por tipo de fonte, não tratamento genérico. Identifica corretamente que "mais contexto não é melhor" — contraintuitivo e não-óbvio para iniciantes. |
| D2 — Uso de Ferramentas | 3 | Iteração v1→v2 documentada explicitamente: a nota no início da v2.0 lista 5 categorias concretas de melhorias incorporadas (estimativas com falsa precisão, riscos organizacionais ausentes, meta de acurácia requalificada, limitações do MVP, governança, integração Teams, dimensionamento fila OCR). As mudanças são estruturais e verificáveis — não cosméticas. O ciclo gerar→avaliar→iterar é visível e substancial. |
| D3 — Qualidade do Entregável | 3 | Completo, correto e diretamente acionável. Cobre todos os pontos do enunciado e vai além: seções de governança de dados, integração Teams, síntese executiva com riscos priorizados. Tabelas de risco com probabilidade e impacto. Limitações explícitas do MVP. Recomendação de cronograma com percentuais por fase. Outro engenheiro poderia usar como base para a proposta técnica sem pedir esclarecimentos. |
| D4 — Pensamento Crítico | 3 | Múltiplos exemplos de análise não-óbvia e autônoma. Identifica que "versão mais recente ≠ versão correta" — uma armadilha lógica que sistemas RAG tipicamente ignoram. Contesta a meta de acurácia > 85% da v1 como "vaga e otimista demais" e propõe 65–75% com golden dataset. Quantifica o risco do multiplicador de serialização (26×) que a maioria ignora. Reconhece que query decomposition tem custo de latência que pode ser inaceitável em call center — não aceita a técnica acriticamente. |
| D5 — Aplicabilidade ao Projeto | 3 | Profundamente enraizado no contexto NovaTech. Referencia dados específicos do enunciado: 320 chamados/dia, 192 com consulta documental, 45 atendentes, 12 min por chamado, 3 áreas responsáveis, Microsoft 365 E3, Azure. Exemplos de perguntas com dados da NovaTech ("qual o frete para 8kg, destino Sul?"). Análise de adoção com projeção temporal realista (semanas 1–4 vs. meses 2–3). |

**Score do exercício: 3,0**

---

## Classificação

**Aprovado com distinção** — Score: 3,0 · Faixa: 2,5–3,0

---

## Verificação de Armadilhas

O exercício 1.1 não possui armadilha intencional definida na skill do papel. A armadilha obrigatória (POL-001 — pergunta sobre prazo de devolução para carga perigosa) está no exercício 1.2. Status: N/A.

---

## Pontos Fortes

- Estimativas como ranges com justificativa metodológica explícita — elimina falsa precisão e demonstra maturidade técnica além do esperado no exercício.
- Multiplicador de serialização de tabelas quantificado (fator 26×) — insight técnico não-óbvio que afeta diretamente o dimensionamento de infraestrutura.
- Seções sobre riscos organizacionais, governança de dados e integração Teams mostram visão de engenharia de sistemas, não apenas de pipeline de ML.
- Limitações explícitas do MVP — postura de engenharia responsável que raramente aparece neste nível de exercício.

---

## Pontos de Melhoria

- A estratégia de chunking hierárquico pai–filho é recomendada, mas não há estimativa do impacto no custo de embedding — útil quantificar (ex: +X% de tokens na ingestão inicial).
- O histórico de iteração com o Claude não está anexado ao documento — o enunciado pede explicitamente o histórico de interação, não apenas a nota sobre o que mudou.
- A seção de perguntas multi-domínio menciona a necessidade de classificador, mas não estima o esforço de desenvolvimento separadamente do resto do pipeline.

---

## Tópicos da Trilha para Reforço

Score 3,0 — nenhum tópico da trilha requer reforço neste exercício. Recomenda-se aplicar o mesmo rigor de estimativas em ranges e análise de custos nos exercícios 1.2 e 1.3.
