# 🚀 Lab-1-ES — Repositórios Populares do GitHub

> Coleta **e análise** das principais características dos repositórios mais populares do GitHub usando a API GraphQL.

---

## 📋 Descrição
Este projeto realiza a extração automatizada de dados de repositórios populares do GitHub e também executa a etapa de análise solicitada no laboratório, incluindo as estatísticas principais e o bônus por linguagem.

O script atualizado permite:
- coletar os dados via API GraphQL do GitHub;
- salvar os dados em CSV e JSON;
- gerar os resultados das questões analíticas do laboratório;
- gerar os arquivos do bônus por linguagem;
- opcionalmente gerar gráficos em `.png` quando `matplotlib` estiver instalado.

---

## 🛠️ Tecnologias Utilizadas
- Python 3.8+
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [requests](https://pypi.org/project/requests/)
- [matplotlib](https://pypi.org/project/matplotlib/) *(opcional, apenas para gráficos)*

---

## 📦 Instalação
1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/Lab-ES-Repositorios-Populares.git
   cd Lab-ES-Repositorios-Populares
   ```

2. **Instale as dependências:**
   ```bash
   pip install requests python-dotenv
   ```

3. **Opcional: instale o matplotlib para gerar gráficos:**
   ```bash
   pip install matplotlib
   ```

4. **Configure o token do GitHub:**
   Crie um arquivo `.env` na raiz do projeto com o conteúdo:
   ```env
   GITHUB_TOKEN=seu_token_aqui
   ```

   Gere um token em GitHub Settings > Developer settings > Personal access tokens com permissão de leitura para dados públicos.

---

## ▶️ Como executar
O script atualizado é o **`scrapper.py`**.

### 1. Coletar dados e gerar a análise completa
Esse comando faz a coleta na API do GitHub e já executa a análise do laboratório e do bônus:

```bash
python scrapper.py collect --total 1000 --output-dir outputs
```

### 2. Gerar apenas a análise a partir de um CSV já existente
Se você já coletou os dados antes, pode rodar somente a etapa analítica:

```bash
python scrapper.py analyze --csv outputs/top_1000_repositories.csv --output-dir outputs
```

---

## 📁 Arquivos gerados
Após a execução, os principais arquivos gerados serão:

- `top_1000_repositories.csv` → base coletada
- `top_1000_repositories.json` → base em JSON
- `rq_summary.csv` → resumo das questões principais
- `language_counts.csv` → contagem por linguagem
- `bonus_language_summary.csv` → métricas do bônus por linguagem
- `report_lab03_bonus.md` → relatório resumido em Markdown
- arquivos `.png` → gráficos, se `matplotlib` estiver disponível

---

## ⚠️ Observação sobre gráficos
Se aparecer a mensagem abaixo:

```text
matplotlib is not available; skipping charts.
```

isso significa apenas que o script executou normalmente, mas **não gerou os gráficos**.

As análises principais continuam sendo produzidas. Para habilitar os gráficos, instale:

```bash
pip install matplotlib
```

---

## 📁 Estrutura esperada do projeto
```text
├── scrapper.py
├── README.md
├── .env
└── outputs/
```

---

## 📝 Exemplo de uso rápido
```bash
pip install requests python-dotenv matplotlib
python scrapper.py collect --total 1000 --output-dir outputs
```

---

## ✅ Resultado esperado
Ao final, você terá:
- os dados coletados dos repositórios;
- os arquivos de resposta da etapa analítica;
- o bônus consolidado por linguagem;
- os gráficos, caso `matplotlib` esteja instalado.
