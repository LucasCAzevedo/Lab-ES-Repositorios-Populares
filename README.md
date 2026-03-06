# 🚀 Lab-1-ES — Repositórios Populares do GitHub

> Coleta e análise das principais características dos **1.000 repositórios mais estrelados** do GitHub usando a API GraphQL, com exportação para CSV e JSON.

---

## 📋 Descrição
Este projeto realiza a extração automatizada dos **1.000 repositórios mais populares** do GitHub, coletando métricas detalhadas e derivadas, como:
- Linguagem principal
- Número de estrelas
- Issues (abertas/fechadas)
- Pull requests merged
- Releases
- Idade do repositório (anos)
- Dias desde última atualização
- Percentual de issues fechadas

O sistema utiliza paginação GraphQL, busca em batches adaptativos e exporta os dados para **CSV** e **JSON** para análise posterior.

## 🛠️ Tecnologias Utilizadas
- Python 3.8+
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [requests](https://pypi.org/project/requests/)

## ⚡ Como Usar
1. **Clone o repositório:**
	```bash
	git clone https://github.com/seu-usuario/Lab-ES-Repositorios-Populares.git
	cd Lab-ES-Repositorios-Populares
	```

2. **Instale as dependências:**
	```bash
	pip install -r requirements.txt
	```

3. **Configure o token do GitHub:**
	- Crie um arquivo `.env` na raiz do projeto com o conteúdo:
	  ```env
	  GITHUB_TOKEN=seu_token_aqui
	  ```
	- Gere um token [aqui](https://github.com/settings/tokens) com permissão de leitura pública.

4. **Execute o scrapper:**
	```bash
	python scrapper.py
	```

5. **Saída:**
	- Dados detalhados em `top_1000_repositories.json`
	- Exportação tabular em `top_1000_repositories.csv`

## 📁 Estrutura do Projeto
```
├── scrapper.py                  # Script principal de coleta e análise
├── top_1000_repositories.json   # Dados brutos coletados (JSON)
├── top_1000_repositories.csv    # Dados tabulares (CSV)
├── .env                         # Variáveis de ambiente (não versionado)
└── README.md                    # Documentação
```

## 📝 Exemplos de Saída

### JSON
```json
[
	{
		"id": "MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
		"nameWithOwner": "torvalds/linux",
		"url": "https://github.com/torvalds/linux",
		"createdAt": "2011-09-04T22:48:12Z",
		"updatedAt": "2026-02-22T10:00:00Z",
		"pushedAt": "2026-02-22T10:00:00Z",
		"stargazerCount": 168000,
		"primaryLanguage": "C",
		"pullRequestsMerged": 12000,
		"releases": 500,
		"issuesClosed": 10000,
		"issuesTotal": 12000,
		"repoAgeYears": 14.5,
		"daysSinceLastUpdate": 8,
		"closedIssuesRatio": 0.8333
	},
	...
]
```

### CSV
```
id,nameWithOwner,url,createdAt,updatedAt,pushedAt,stargazerCount,primaryLanguage,pullRequestsMerged,releases,issuesClosed,issuesTotal,repoAgeYears,daysSinceLastUpdate,closedIssuesRatio
MDEwOlJlcG9zaXRvcnkxMjk2MjY5,torvalds/linux,https://github.com/torvalds/linux,2011-09-04T22:48:12Z,2026-02-22T10:00:00Z,2026-02-22T10:00:00Z,168000,C,12000,500,10000,12000,14.5,8,0.8333
...
```
---