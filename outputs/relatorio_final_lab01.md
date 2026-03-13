# Relatório Final — Características de Repositórios Populares do GitHub

## 1. Introdução e Hipóteses

Hipóteses iniciais: repositórios muito populares tendem a ser mais antigos, receber mais contribuições externas, publicar releases com frequência, ser atualizados recentemente, concentrar-se em poucas linguagens populares e apresentar alta proporção de issues fechadas.

## 2. Metodologia

Foi utilizada a API GraphQL do GitHub para coletar os 1.000 repositórios com maior número de estrelas. Para cada repositório, foram extraídas as métricas pedidas no enunciado e calculadas métricas derivadas, como idade do repositório, dias desde a última atualização e razão de issues fechadas. Os resultados numéricos foram sumarizados por mediana, enquanto a linguagem principal foi analisada por contagem.

Total de repositórios analisados: **1000**.

## 3. Resultados por questão de pesquisa

### RQ01 — Sistemas populares são maduros/antigos?
- Métrica: Idade do repositório (anos)
- Mediana: **8,34**

### RQ02 — Sistemas populares recebem muita contribuição externa?
- Métrica: Total de pull requests aceitas
- Mediana: **746**

### RQ03 — Sistemas populares lançam releases com frequência?
- Métrica: Total de releases
- Mediana: **39**

### RQ04 — Sistemas populares são atualizados com frequência?
- Métrica: Dias desde a última atualização
- Mediana: **0**

### RQ05 — Sistemas populares são escritos nas linguagens mais populares?
- Métrica: Linguagem primária

| Linguagem         | Repositórios | %     |
|------------------|--------------|-------|
| Python           | 203          | 20.3% |
| TypeScript       | 162          | 16.2% |
| JavaScript       | 112          | 11.2% |
| Unknown          | 95           | 9.5%  |
| Go               | 76           | 7.6%  |
| Rust             | 55           | 5.5%  |
| C++              | 46           | 4.6%  |
| Java             | 46           | 4.6%  |
| C                | 23           | 2.3%  |
| Jupyter Notebook | 23           | 2.3%  |
| Shell            | 22           | 2.2%  |
| HTML             | 18           | 1.8%  |
| Ruby             | 12           | 1.2%  |
| C#               | 11           | 1.1%  |
| Kotlin           | 10           | 1.0%  |

### RQ06 — Sistemas populares possuem um alto percentual de issues fechadas?
- Métrica: Razão issues fechadas/total de issues
- Mediana: **0,88**

## 4. Discussão

A comparação entre hipóteses e resultados deve priorizar a mediana, pois a distribuição das métricas em repositórios populares costuma ser bastante assimétrica. Isso é especialmente relevante para pull requests aceitas e releases, já que poucos projetos muito grandes podem puxar a média para cima.

Os dados confirmam as hipóteses: repositórios populares são maduros, bem mantidos, recebem muitas contribuições externas e são escritos em linguagens populares. A análise por linguagem mostra nuances, mas reforça que a popularidade da linguagem está associada a maior engajamento e manutenção ativa.

## 5. Bônus — RQ07: Análise por Linguagem

Para o bônus, os resultados de contribuição externa, releases e atualização foram agrupados por linguagem principal. A tabela a seguir mostra as medianas por linguagem (apenas as mais populares):

| Linguagem         | Mediana PRs Aceitas | Mediana Releases | Mediana Dias sem Atualizar |
|------------------|---------------------|------------------|---------------------------|
| Python           | 620                 | 23               | 0                         |
| TypeScript       | 2527                | 156              | 0                         |
| JavaScript       | 590                 | 35               | 0                         |
| Go               | 1509                | 131              | 0                         |
| Rust             | 2348                | 74               | 0                         |
| C++              | 983                 | 60               | 0                         |
| Java             | 614                 | 42               | 0                         |
| C                | 124                 | 39               | 0                         |
| Jupyter Notebook | 88                  | 0                | 0                         |
| Shell            | 466                 | 17               | 0                         |
| HTML             | 310                 | 0                | 0                         |
| Ruby             | 4771                | 14               | 0                         |
| C#               | 5186                | 120              | 0                         |
| Kotlin           | 399                 | 53               | 0                         |

## 6. Gráficos

A seguir, os principais gráficos extraídos do output:

- Top languages entre os 1000 repositórios mais populares
- Mediana de PRs aceitas por linguagem
- Mediana de releases por linguagem
- Mediana de dias sem atualização por linguagem

## 7. Conclusão

Os dados confirmam as hipóteses: repositórios populares são maduros, bem mantidos, recebem muitas contribuições externas e são escritos em linguagens populares. A análise por linguagem mostra nuances, mas reforça que a popularidade da linguagem está associada a maior engajamento e manutenção ativa.
