# Laboratório 01 — Lab03 + Bônus

## 1. Introdução e hipóteses informais

Hipóteses iniciais: repositórios muito populares tendem a ser mais antigos, receber mais contribuições externas, publicar releases com frequência, ser atualizados recentemente, concentrar-se em poucas linguagens populares e apresentar alta proporção de issues fechadas.

## 2. Metodologia

Foi utilizada a API GraphQL do GitHub para coletar os 1.000 repositórios com maior número de estrelas. Para cada repositório, foram extraídas as métricas pedidas no enunciado e calculadas métricas derivadas, como idade do repositório, dias desde a última atualização e razão de issues fechadas. Os resultados numéricos foram sumarizados por mediana, enquanto a linguagem principal foi analisada por contagem.

Total de repositórios analisados: **1000**.

## 3. Resultados por questão de pesquisa

### RQ01
- Métrica: Repository age in years
- Mediana: **8.35**
- Média: 8.1494

### RQ02
- Métrica: Accepted pull requests
- Mediana: **746**
- Média: 3965.244

### RQ03
- Métrica: Total releases
- Mediana: **39.5**
- Média: 119.619

### RQ04
- Métrica: Days since last update
- Mediana: **0**
- Média: 0.013

### RQ06
- Métrica: Closed issues ratio
- Mediana: **0.88**
- Média: 0.8061

### RQ05 — Linguagens mais frequentes

- Python: 201 repositórios (20.1%)
- TypeScript: 160 repositórios (16.0%)
- JavaScript: 113 repositórios (11.3%)
- Unknown: 95 repositórios (9.5%)
- Go: 77 repositórios (7.7%)
- Rust: 55 repositórios (5.5%)
- C++: 46 repositórios (4.6%)
- Java: 46 repositórios (4.6%)
- C: 25 repositórios (2.5%)
- Jupyter Notebook: 23 repositórios (2.3%)

## 4. Discussão

A comparação entre hipóteses e resultados deve priorizar a mediana, pois a distribuição das métricas em repositórios populares costuma ser bastante assimétrica. Isso é especialmente relevante para pull requests aceitas e releases, já que poucos projetos muito grandes podem puxar a média para cima.

## 5. Bônus — RQ07

Para o bônus, os resultados de contribuição externa, releases e atualização foram agrupados por linguagem principal. A tabela gerada no arquivo `bonus_language_summary.csv` permite comparar se determinadas linguagens concentram projetos mais ativos.

- Python: 201 repos | mediana PRs aceitas = 620, mediana releases = 23, mediana dias desde atualização = 0
- TypeScript: 160 repos | mediana PRs aceitas = 2524, mediana releases = 157.5, mediana dias desde atualização = 0
- JavaScript: 113 repos | mediana PRs aceitas = 605, mediana releases = 36, mediana dias desde atualização = 0
- Unknown: 95 repos | mediana PRs aceitas = 129, mediana releases = 0, mediana dias desde atualização = 0
- Go: 77 repos | mediana PRs aceitas = 1690, mediana releases = 132, mediana dias desde atualização = 0
- Rust: 55 repos | mediana PRs aceitas = 2343, mediana releases = 74, mediana dias desde atualização = 0
- C++: 46 repos | mediana PRs aceitas = 983, mediana releases = 60, mediana dias desde atualização = 0
- Java: 46 repos | mediana PRs aceitas = 614, mediana releases = 42, mediana dias desde atualização = 0
- C: 25 repos | mediana PRs aceitas = 145, mediana releases = 39, mediana dias desde atualização = 0
- Jupyter Notebook: 23 repos | mediana PRs aceitas = 88, mediana releases = 0, mediana dias desde atualização = 0

## 6. Arquivos gerados

- `top_1000_repositories.csv`
- `top_1000_repositories.json`
- `rq_summary.csv`
- `language_counts.csv`
- `bonus_language_summary.csv`
- `top_languages.png`
- `bonus_prs_by_language.png`
- `bonus_releases_by_language.png`
- `bonus_updates_by_language.png`
