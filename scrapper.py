import os
import csv
import json
import time
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv

# -------------------------------------------------
# Config
# -------------------------------------------------
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_API_URL = "https://api.github.com/graphql"

if not GITHUB_TOKEN:
    raise RuntimeError("Missing GITHUB_TOKEN. Set it in your .env file.")

TRANSIENT_STATUS = {502, 503, 504}
SEARCH_PAGE_SIZE = 100
DETAIL_BATCH_SIZE = 10
BATCH_THROTTLE_SECONDS = 0.75

# -------------------------------------------------
# HTTP session
# -------------------------------------------------
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "lab01s02-repo-miner/1.0",
})

# -------------------------------------------------
# GraphQL queries
# -------------------------------------------------
SEARCH_TOP_REPOS_QUERY = """
query SearchTopRepos($first: Int!, $after: String) {
  search(
    query: "stars:>0 sort:stars-desc",
    type: REPOSITORY,
    first: $first,
    after: $after
  ) {
    nodes {
      ... on Repository {
        id
        nameWithOwner
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    repositoryCount
  }
}
"""

DETAILS_BY_IDS_QUERY = """
query RepoDetailsByIds($ids: [ID!]!) {
  nodes(ids: $ids) {
    ... on Repository {
      id
      nameWithOwner
      url
      createdAt
      updatedAt
      pushedAt
      stargazerCount
      primaryLanguage {
        name
      }
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
}
"""

# -------------------------------------------------
# Generic GraphQL runner with retry/backoff
# -------------------------------------------------
def run_query(
    query: str,
    variables: Optional[Dict[str, Any]] = None,
    max_retries: int = 6
) -> tuple[Dict[str, Any], Dict[str, str]]:
    payload = {"query": query, "variables": variables}

    for attempt in range(max_retries + 1):
        try:
            resp = session.post(
                GITHUB_API_URL,
                json=payload,
                timeout=(10, 60),
            )

            if resp.status_code in TRANSIENT_STATUS:
                raise requests.HTTPError(
                    f"Transient HTTP {resp.status_code}",
                    response=resp
                )

            resp.raise_for_status()
            data = resp.json()

            if "errors" in data:
                messages = "\n".join(
                    err.get("message", str(err))
                    for err in data["errors"]
                )
                raise RuntimeError(f"GraphQL errors:\n{messages}")

            return data, dict(resp.headers)

        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt == max_retries:
                raise RuntimeError(f"Network error after retries: {e}") from e

        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None

            if status not in TRANSIENT_STATUS or attempt == max_retries:
                try:
                    body = e.response.json()
                except Exception:
                    body = e.response.text if e.response is not None else None
                raise RuntimeError(f"HTTP error {status}: {body}") from e

        sleep_s = min(2 ** attempt, 30) + random.random()
        print(f"Retrying in {sleep_s:.1f}s...")
        time.sleep(sleep_s)

    raise RuntimeError("Unexpected retry exhaustion.")

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def chunked(values: List[Any], size: int) -> List[List[Any]]:
    return [values[i:i + size] for i in range(0, len(values), size)]


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def compute_age_years(created_at: Optional[str]) -> Optional[float]:
    dt = parse_iso_datetime(created_at)
    if not dt:
        return None
    now = datetime.now(timezone.utc)
    return round((now - dt).days / 365.25, 2)


def compute_days_since_update(updated_at: Optional[str]) -> Optional[int]:
    dt = parse_iso_datetime(updated_at)
    if not dt:
        return None
    now = datetime.now(timezone.utc)
    return (now - dt).days


def compute_closed_issues_ratio(closed_issues: int, total_issues: int) -> Optional[float]:
    if total_issues == 0:
        return None
    return round(closed_issues / total_issues, 4)


def normalize_repo(repo: Dict[str, Any]) -> Dict[str, Any]:
    issues_closed = repo["closedIssues"]["totalCount"]
    issues_total = repo["totalIssues"]["totalCount"]

    return {
        "id": repo["id"],
        "nameWithOwner": repo["nameWithOwner"],
        "url": repo["url"],
        "createdAt": repo["createdAt"],
        "updatedAt": repo["updatedAt"],
        "pushedAt": repo["pushedAt"],
        "stargazerCount": repo["stargazerCount"],
        "primaryLanguage": repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else None,
        "pullRequestsMerged": repo["mergedPRs"]["totalCount"],
        "releases": repo["releases"]["totalCount"],
        "issuesClosed": issues_closed,
        "issuesTotal": issues_total,
        "repoAgeYears": compute_age_years(repo["createdAt"]),
        "daysSinceLastUpdate": compute_days_since_update(repo["updatedAt"]),
        "closedIssuesRatio": compute_closed_issues_ratio(issues_closed, issues_total),
    }

# -------------------------------------------------
# Phase 1: paginate top repositories
# -------------------------------------------------
def get_top_repositories_paginated(
    total_repos: int = 1000,
    page_size: int = SEARCH_PAGE_SIZE
) -> List[Dict[str, str]]:
    all_repos: List[Dict[str, str]] = []
    after = None

    while len(all_repos) < total_repos:
        remaining_needed = total_repos - len(all_repos)
        first = min(page_size, remaining_needed)

        data, headers = run_query(
            SEARCH_TOP_REPOS_QUERY,
            {"first": first, "after": after}
        )

        search_data = data["data"]["search"]
        nodes = search_data["nodes"]

        for node in nodes:
            all_repos.append({
                "id": node["id"],
                "nameWithOwner": node["nameWithOwner"],
            })

        page_info = search_data["pageInfo"]
        after = page_info["endCursor"]

        print(
            f"Collected {len(all_repos)}/{total_repos} repos "
        )

        if not page_info["hasNextPage"]:
            break

        time.sleep(0.2)

    return all_repos[:total_repos]

# -------------------------------------------------
# Phase 2: adaptive batch fetching
# -------------------------------------------------
def fetch_batch(ids: List[str]) -> List[Dict[str, Any]]:
    data, headers = run_query(DETAILS_BY_IDS_QUERY, {"ids": ids})
    nodes = data["data"]["nodes"]

    results = []
    for repo in nodes:
        if repo is None:
            continue
        results.append(normalize_repo(repo))

    print(
        f"   ↳ Batch success | size={len(ids)} "
    )

    return results


def fetch_batch_with_fallback(ids: List[str], depth: int = 0) -> List[Dict[str, Any]]:
    indent = "  " * depth

    try:
        print(f"{indent}Trying batch of size {len(ids)}...")
        result = fetch_batch(ids)
        time.sleep(BATCH_THROTTLE_SECONDS)
        return result

    except Exception as e:
        print(f"{indent}Batch size {len(ids)} failed: {e}")

        if len(ids) == 1:
            print(f"{indent}Skipping repo id {ids[0]} after repeated failures.")
            return []

        mid = len(ids) // 2
        left_ids = ids[:mid]
        right_ids = ids[mid:]

        print(f"{indent}Splitting batch into {len(left_ids)} + {len(right_ids)}")
        left_result = fetch_batch_with_fallback(left_ids, depth + 1)
        right_result = fetch_batch_with_fallback(right_ids, depth + 1)
        return left_result + right_result


def fetch_repo_details_batched(
    repo_ids: List[str],
    batch_size: int = DETAIL_BATCH_SIZE
) -> List[Dict[str, Any]]:
    all_results: List[Dict[str, Any]] = []
    batches = chunked(repo_ids, batch_size)

    for index, batch in enumerate(batches, 1):
        print(f"Fetching batch {index}/{len(batches)} (size={len(batch)})...")
        batch_results = fetch_batch_with_fallback(batch)
        all_results.extend(batch_results)

    return all_results

# -------------------------------------------------
# Output
# -------------------------------------------------
def save_to_csv(data: List[Dict[str, Any]], filename: str = "top_1000_repositories.csv") -> None:
    if not data:
        raise RuntimeError("No data to save.")

    fieldnames = [
        "id",
        "nameWithOwner",
        "url",
        "createdAt",
        "updatedAt",
        "pushedAt",
        "stargazerCount",
        "primaryLanguage",
        "pullRequestsMerged",
        "releases",
        "issuesClosed",
        "issuesTotal",
        "repoAgeYears",
        "daysSinceLastUpdate",
        "closedIssuesRatio",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def save_to_json(data: List[Dict[str, Any]], filename: str = "top_1000_repositories.json") -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -------------------------------------------------
# Main
# -------------------------------------------------
def main():
    print("Step 1: fetching top 1000 repositories...")
    top_repos = get_top_repositories_paginated(total_repos=1000, page_size=SEARCH_PAGE_SIZE)
    print(f"Found {len(top_repos)} repositories.")

    repo_ids = [repo["id"] for repo in top_repos]

    print("Step 2: fetching repository metrics in batches...")
    results = fetch_repo_details_batched(repo_ids, batch_size=DETAIL_BATCH_SIZE)

    rank_map = {repo["id"]: idx for idx, repo in enumerate(top_repos)}
    results.sort(key=lambda repo: rank_map.get(repo["id"], 10**9))

    print("Step 3: saving files...")
    save_to_csv(results, "top_1000_repositories.csv")
    save_to_json(results, "top_1000_repositories.json")

    print("Done.")
    print(f"Saved {len(results)} repositories.")
    print("Generated:")
    print("- top_1000_repositories.csv")
    print("- top_1000_repositories.json")


if __name__ == "__main__":
    main()