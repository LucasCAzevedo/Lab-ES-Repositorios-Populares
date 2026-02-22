# 🚀 Lab-1-ES — Repositórios Populares do GitHub

> Coleta e análise das principais características dos 100 repositórios mais estrelados do GitHub usando a API GraphQL.

---

## 📋 Descrição
Este projeto realiza a extração automatizada de dados dos 100 repositórios mais populares do GitHub, coletando métricas como linguagem principal, número de estrelas, issues, pull requests e releases. Os dados são salvos em um arquivo JSON para análise posterior.

## 🛠️ Tecnologias Utilizadas
- Python 3.7+
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
	- O resultado será salvo em `top_100_repositories.json`.

## 📁 Estrutura do Projeto
```
├── scrapper.py           # Script principal de coleta
├── top_100_repositories.json  # Saída dos dados coletados
├── .env                  # Variáveis de ambiente (não versionado)
└── README.md             # Documentação
```

## 📝 Exemplo de Saída
```json
[
  {
	 "nameWithOwner": "torvalds/linux",
	 "createdAt": "2011-09-04T22:48:12Z",
	 "updatedAt": "2026-02-22T10:00:00Z",
	 "stargazerCount": 168000,
	 "primaryLanguage": "C",
	 "pullRequestsMerged": 12000,
	 "releases": 500,
	 "issuesClosed": 10000,
	 "issuesTotal": 12000
  },
  ...
]
```
---