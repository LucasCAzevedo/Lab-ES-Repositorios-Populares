import os
import requests

from dotenv import load_dotenv

load_dotenv()  

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

query = """
query TopStarredRepos {
  search(
    query: "stars:>0 sort:stars-desc",
    type: REPOSITORY,
    first: 100
  ) {
    repositoryCount
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount
        url
        description
        primaryLanguage {
          name
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
  rateLimit {
    remaining
    resetAt
    cost
  }
}
"""

resp = requests.post(
    "https://api.github.com/graphql",
    json={"query": query},
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    },
    timeout=30,
)

try:
    resp.raise_for_status()
except requests.HTTPError as e:
    try:
        info = resp.json()
    except Exception:  
        info = resp.text
    raise RuntimeError(f"GitHub API request failed: {resp.status_code} - {info}") from e

data = resp.json()

if "errors" in data:
    raise RuntimeError(data["errors"])

repos = data["data"]["search"]["nodes"]

for i, repo in enumerate(repos, 1):
    print(f"{i:3d}. {repo['nameWithOwner']} - ⭐ {repo['stargazerCount']:,}")
