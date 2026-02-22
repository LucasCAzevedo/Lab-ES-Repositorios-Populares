import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_URL = "https://api.github.com/graphql"


# -----------------------------------------
# Função para executar query
# -----------------------------------------
def run_query(query, variables=None):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    resp = requests.post(
        GITHUB_API_URL,
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=30,
    )

    resp.raise_for_status()
    data = resp.json()

    if "errors" in data:
        raise RuntimeError(data["errors"])

    return data


# -----------------------------------------
# FASE 1 — Buscar 100 mais estrelados
# -----------------------------------------
def get_top_repositories():
    query = """
    query {
      search(
        query: "stars:>0 sort:stars-desc",
        type: REPOSITORY,
        first: 100
      ) {
        nodes {
          ... on Repository {
            name
            owner { login }
          }
        }
      }
    }
    """

    data = run_query(query)
    return data["data"]["search"]["nodes"]


# -----------------------------------------
# FASE 2 — Buscar métricas detalhadas
# -----------------------------------------
def get_repository_details(owner, name):
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        nameWithOwner
        createdAt
        updatedAt
        stargazerCount

        primaryLanguage { name }

        mergedPRs: pullRequests(states: MERGED) {
          totalCount
        }

        releases {
          totalCount
        }

        closedIssues: issues(states: CLOSED) {
          totalCount
        }

        totalIssues: issues {
          totalCount
        }
      }
    }
    """

    variables = {"owner": owner, "name": name}
    data = run_query(query, variables)

    repo = data["data"]["repository"]

    return {
        "nameWithOwner": repo["nameWithOwner"],
        "createdAt": repo["createdAt"],
        "updatedAt": repo["updatedAt"],
        "stargazerCount": repo["stargazerCount"],
        "primaryLanguage": repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else None,
        "pullRequestsMerged": repo["mergedPRs"]["totalCount"],
        "releases": repo["releases"]["totalCount"],
        "issuesClosed": repo["closedIssues"]["totalCount"],
        "issuesTotal": repo["totalIssues"]["totalCount"],
    }


# -----------------------------------------
# Salvar JSON
# -----------------------------------------
def save_to_json(data, filename="top_100_repositories.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# -----------------------------------------
# MAIN
# -----------------------------------------
def main():
    print("🔍 Buscando os 100 repositórios mais estrelados...")
    top_repos = get_top_repositories()

    print(f"✅ {len(top_repos)} repositórios encontrados.")
    print("📊 Coletando métricas detalhadas...\n")

    results = []

    for index, repo in enumerate(top_repos, 1):
        owner = repo["owner"]["login"]
        name = repo["name"]

        print(f"{index:3d}/100 → {owner}/{name}")

        details = get_repository_details(owner, name)
        results.append(details)


    save_to_json(results)

    print("\n✅ Coleta finalizada.")
    print("📁 Dados salvos em top_100_repositories.json")


if __name__ == "__main__":
    main()