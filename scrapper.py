import os
import csv
import json
import time
import random
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Iterable

import requests
from dotenv import load_dotenv

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

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
DEFAULT_OUTPUT_DIR = "lab01_outputs"
TOP_LANGUAGES_FOR_CHART = 15
MIN_REPOS_PER_LANGUAGE_FOR_BONUS = 5

# -------------------------------------------------
# HTTP session
# -------------------------------------------------
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "lab01-lab03-bonus-repo-miner/2.0",
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
    max_retries: int = 6,
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
                    response=resp,
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
def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


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
        "primaryLanguage": repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else "Unknown",
        "pullRequestsMerged": repo["mergedPRs"]["totalCount"],
        "releases": repo["releases"]["totalCount"],
        "issuesClosed": issues_closed,
        "issuesTotal": issues_total,
        "repoAgeYears": compute_age_years(repo["createdAt"]),
        "daysSinceLastUpdate": compute_days_since_update(repo["updatedAt"]),
        "closedIssuesRatio": compute_closed_issues_ratio(issues_closed, issues_total),
    }


def to_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    return int(value)


def to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    return float(value)


def median_or_none(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return round(statistics.median(clean), 4)


def safe_mean(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 4)


def load_existing_dataset(csv_path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "id": row["id"],
                "nameWithOwner": row["nameWithOwner"],
                "url": row["url"],
                "createdAt": row["createdAt"],
                "updatedAt": row["updatedAt"],
                "pushedAt": row["pushedAt"],
                "stargazerCount": to_int(row["stargazerCount"]),
                "primaryLanguage": row["primaryLanguage"] or "Unknown",
                "pullRequestsMerged": to_int(row["pullRequestsMerged"]),
                "releases": to_int(row["releases"]),
                "issuesClosed": to_int(row["issuesClosed"]),
                "issuesTotal": to_int(row["issuesTotal"]),
                "repoAgeYears": to_float(row["repoAgeYears"]),
                "daysSinceLastUpdate": to_int(row["daysSinceLastUpdate"]),
                "closedIssuesRatio": to_float(row["closedIssuesRatio"]),
            })
    return rows

# -------------------------------------------------
# Phase 1: paginate top repositories
# -------------------------------------------------
def get_top_repositories_paginated(
    total_repos: int = 1000,
    page_size: int = SEARCH_PAGE_SIZE,
) -> List[Dict[str, str]]:
    all_repos: List[Dict[str, str]] = []
    after = None

    while len(all_repos) < total_repos:
        remaining_needed = total_repos - len(all_repos)
        first = min(page_size, remaining_needed)

        data, _headers = run_query(
            SEARCH_TOP_REPOS_QUERY,
            {"first": first, "after": after},
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

        print(f"Collected {len(all_repos)}/{total_repos} repos")

        if not page_info["hasNextPage"]:
            break

        time.sleep(0.2)

    return all_repos[:total_repos]

# -------------------------------------------------
# Phase 2: adaptive batch fetching
# -------------------------------------------------
def fetch_batch(ids: List[str]) -> List[Dict[str, Any]]:
    data, _headers = run_query(DETAILS_BY_IDS_QUERY, {"ids": ids})
    nodes = data["data"]["nodes"]

    results = []
    for repo in nodes:
        if repo is None:
            continue
        results.append(normalize_repo(repo))

    print(f"   ↳ Batch success | size={len(ids)}")
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
    batch_size: int = DETAIL_BATCH_SIZE,
) -> List[Dict[str, Any]]:
    all_results: List[Dict[str, Any]] = []
    batches = chunked(repo_ids, batch_size)

    for index, batch in enumerate(batches, 1):
        print(f"Fetching batch {index}/{len(batches)} (size={len(batch)})...")
        batch_results = fetch_batch_with_fallback(batch)
        all_results.extend(batch_results)

    return all_results

# -------------------------------------------------
# Output: raw data
# -------------------------------------------------
def save_to_csv(data: List[Dict[str, Any]], filename: str) -> None:
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


def save_to_json(data: List[Dict[str, Any]], filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -------------------------------------------------
# Lab03 + Bonus analysis
# -------------------------------------------------
def write_csv(rows: List[Dict[str, Any]], filename: str, fieldnames: List[str]) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_rq_summary(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "RQ": "RQ01",
            "metric": "repoAgeYears",
            "description": "Repository age in years",
            "median": median_or_none(row["repoAgeYears"] for row in data),
            "mean": safe_mean(row["repoAgeYears"] for row in data),
        },
        {
            "RQ": "RQ02",
            "metric": "pullRequestsMerged",
            "description": "Accepted pull requests",
            "median": median_or_none(row["pullRequestsMerged"] for row in data),
            "mean": safe_mean(row["pullRequestsMerged"] for row in data),
        },
        {
            "RQ": "RQ03",
            "metric": "releases",
            "description": "Total releases",
            "median": median_or_none(row["releases"] for row in data),
            "mean": safe_mean(row["releases"] for row in data),
        },
        {
            "RQ": "RQ04",
            "metric": "daysSinceLastUpdate",
            "description": "Days since last update",
            "median": median_or_none(row["daysSinceLastUpdate"] for row in data),
            "mean": safe_mean(row["daysSinceLastUpdate"] for row in data),
        },
        {
            "RQ": "RQ06",
            "metric": "closedIssuesRatio",
            "description": "Closed issues ratio",
            "median": median_or_none(row["closedIssuesRatio"] for row in data),
            "mean": safe_mean(row["closedIssuesRatio"] for row in data),
        },
    ]


def build_language_counts(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts = Counter(row["primaryLanguage"] or "Unknown" for row in data)
    total = len(data)
    rows = []
    for language, count in counts.most_common():
        rows.append({
            "language": language,
            "repositories": count,
            "percentage": round((count / total) * 100, 2) if total else 0.0,
        })
    return rows


def build_bonus_summary(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in data:
        grouped[row["primaryLanguage"] or "Unknown"].append(row)

    rows = []
    for language, repos in grouped.items():
        if len(repos) < MIN_REPOS_PER_LANGUAGE_FOR_BONUS:
            continue
        rows.append({
            "language": language,
            "repositories": len(repos),
            "medianPullRequestsMerged": median_or_none(r["pullRequestsMerged"] for r in repos),
            "medianReleases": median_or_none(r["releases"] for r in repos),
            "medianDaysSinceLastUpdate": median_or_none(r["daysSinceLastUpdate"] for r in repos),
            "meanPullRequestsMerged": safe_mean(r["pullRequestsMerged"] for r in repos),
            "meanReleases": safe_mean(r["releases"] for r in repos),
            "meanDaysSinceLastUpdate": safe_mean(r["daysSinceLastUpdate"] for r in repos),
        })

    rows.sort(key=lambda r: (-r["repositories"], str(r["language"])))
    return rows


def generate_markdown_report(
    output_dir: str,
    data: List[Dict[str, Any]],
    rq_summary: List[Dict[str, Any]],
    language_counts: List[Dict[str, Any]],
    bonus_summary: List[Dict[str, Any]],
) -> None:
    report_path = os.path.join(output_dir, "report_lab03_bonus.md")
    total = len(data)
    top_langs = language_counts[:10]
    bonus_top = bonus_summary[:10]

    def fmt(v: Any) -> str:
        if v is None:
            return "N/A"
        if isinstance(v, float):
            return f"{v:.4f}".rstrip("0").rstrip(".")
        return str(v)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Laboratório 01 — Lab03 + Bônus\n\n")
        f.write("## 1. Introdução e hipóteses informais\n\n")
        f.write(
            "Hipóteses iniciais: repositórios muito populares tendem a ser mais antigos, "
            "receber mais contribuições externas, publicar releases com frequência, "
            "ser atualizados recentemente, concentrar-se em poucas linguagens populares "
            "e apresentar alta proporção de issues fechadas.\n\n"
        )
        f.write("## 2. Metodologia\n\n")
        f.write(
            "Foi utilizada a API GraphQL do GitHub para coletar os 1.000 repositórios com maior número de estrelas. "
            "Para cada repositório, foram extraídas as métricas pedidas no enunciado e calculadas métricas derivadas, "
            "como idade do repositório, dias desde a última atualização e razão de issues fechadas. "
            "Os resultados numéricos foram sumarizados por mediana, enquanto a linguagem principal foi analisada por contagem.\n\n"
        )
        f.write(f"Total de repositórios analisados: **{total}**.\n\n")
        f.write("## 3. Resultados por questão de pesquisa\n\n")
        for row in rq_summary:
            f.write(f"### {row['RQ']}\n")
            f.write(f"- Métrica: {row['description']}\n")
            f.write(f"- Mediana: **{fmt(row['median'])}**\n")
            f.write(f"- Média: {fmt(row['mean'])}\n\n")

        f.write("### RQ05 — Linguagens mais frequentes\n\n")
        for row in top_langs:
            f.write(f"- {row['language']}: {row['repositories']} repositórios ({row['percentage']}%)\n")
        f.write("\n")

        f.write("## 4. Discussão\n\n")
        f.write(
            "A comparação entre hipóteses e resultados deve priorizar a mediana, pois a distribuição das métricas em repositórios populares "
            "costuma ser bastante assimétrica. Isso é especialmente relevante para pull requests aceitas e releases, já que poucos projetos muito grandes "
            "podem puxar a média para cima.\n\n"
        )

        f.write("## 5. Bônus — RQ07\n\n")
        f.write(
            "Para o bônus, os resultados de contribuição externa, releases e atualização foram agrupados por linguagem principal. "
            "A tabela gerada no arquivo `bonus_language_summary.csv` permite comparar se determinadas linguagens concentram projetos mais ativos.\n\n"
        )
        for row in bonus_top:
            f.write(
                f"- {row['language']}: {row['repositories']} repos | "
                f"mediana PRs aceitas = {fmt(row['medianPullRequestsMerged'])}, "
                f"mediana releases = {fmt(row['medianReleases'])}, "
                f"mediana dias desde atualização = {fmt(row['medianDaysSinceLastUpdate'])}\n"
            )
        f.write("\n")

        f.write("## 6. Arquivos gerados\n\n")
        f.write("- `top_1000_repositories.csv`\n")
        f.write("- `top_1000_repositories.json`\n")
        f.write("- `rq_summary.csv`\n")
        f.write("- `language_counts.csv`\n")
        f.write("- `bonus_language_summary.csv`\n")
        if plt is not None:
            f.write("- `top_languages.png`\n")
            f.write("- `bonus_prs_by_language.png`\n")
            f.write("- `bonus_releases_by_language.png`\n")
            f.write("- `bonus_updates_by_language.png`\n")


def plot_bar(labels: List[str], values: List[float], title: str, xlabel: str, ylabel: str, filename: str) -> None:
    if plt is None or not labels:
        return

    plt.figure(figsize=(12, 6))
    plt.bar(labels, values)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()


def generate_charts(output_dir: str, language_counts: List[Dict[str, Any]], bonus_summary: List[Dict[str, Any]]) -> None:
    if plt is None:
        print("matplotlib is not available; skipping charts.")
        return

    top_langs = language_counts[:TOP_LANGUAGES_FOR_CHART]
    plot_bar(
        [row["language"] for row in top_langs],
        [row["repositories"] for row in top_langs],
        "Top languages among the 1000 most starred repositories",
        "Primary language",
        "Repositories",
        os.path.join(output_dir, "top_languages.png"),
    )

    bonus_top = bonus_summary[:TOP_LANGUAGES_FOR_CHART]
    plot_bar(
        [row["language"] for row in bonus_top],
        [row["medianPullRequestsMerged"] or 0 for row in bonus_top],
        "Bonus (RQ07): median accepted PRs by language",
        "Primary language",
        "Median merged PRs",
        os.path.join(output_dir, "bonus_prs_by_language.png"),
    )
    plot_bar(
        [row["language"] for row in bonus_top],
        [row["medianReleases"] or 0 for row in bonus_top],
        "Bonus (RQ07): median releases by language",
        "Primary language",
        "Median releases",
        os.path.join(output_dir, "bonus_releases_by_language.png"),
    )
    plot_bar(
        [row["language"] for row in bonus_top],
        [row["medianDaysSinceLastUpdate"] or 0 for row in bonus_top],
        "Bonus (RQ07): median days since last update by language",
        "Primary language",
        "Median days since update",
        os.path.join(output_dir, "bonus_updates_by_language.png"),
    )


def run_lab03_and_bonus(data: List[Dict[str, Any]], output_dir: str) -> None:
    ensure_dir(output_dir)

    rq_summary = build_rq_summary(data)
    language_counts = build_language_counts(data)
    bonus_summary = build_bonus_summary(data)

    write_csv(
        rq_summary,
        os.path.join(output_dir, "rq_summary.csv"),
        ["RQ", "metric", "description", "median", "mean"],
    )
    write_csv(
        language_counts,
        os.path.join(output_dir, "language_counts.csv"),
        ["language", "repositories", "percentage"],
    )
    write_csv(
        bonus_summary,
        os.path.join(output_dir, "bonus_language_summary.csv"),
        [
            "language",
            "repositories",
            "medianPullRequestsMerged",
            "medianReleases",
            "medianDaysSinceLastUpdate",
            "meanPullRequestsMerged",
            "meanReleases",
            "meanDaysSinceLastUpdate",
        ],
    )

    generate_markdown_report(output_dir, data, rq_summary, language_counts, bonus_summary)
    generate_charts(output_dir, language_counts, bonus_summary)

    print("Lab03 summaries and bonus outputs generated successfully.")

# -------------------------------------------------
# Main
# -------------------------------------------------
def collect_and_analyze(total_repos: int = 1000, output_dir: str = DEFAULT_OUTPUT_DIR) -> None:
    ensure_dir(output_dir)

    print("Step 1: fetching top repositories...")
    top_repos = get_top_repositories_paginated(total_repos=total_repos, page_size=SEARCH_PAGE_SIZE)
    print(f"Found {len(top_repos)} repositories.")

    repo_ids = [repo["id"] for repo in top_repos]

    print("Step 2: fetching repository metrics in batches...")
    results = fetch_repo_details_batched(repo_ids, batch_size=DETAIL_BATCH_SIZE)

    rank_map = {repo["id"]: idx for idx, repo in enumerate(top_repos)}
    results.sort(key=lambda repo: rank_map.get(repo["id"], 10**9))

    csv_path = os.path.join(output_dir, "top_1000_repositories.csv")
    json_path = os.path.join(output_dir, "top_1000_repositories.json")

    print("Step 3: saving raw dataset...")
    save_to_csv(results, csv_path)
    save_to_json(results, json_path)

    print("Step 4: generating Lab03 summaries and bonus analysis...")
    run_lab03_and_bonus(results, output_dir)

    print("Done.")
    print(f"Saved {len(results)} repositories into {output_dir}")


def analyze_existing_csv(csv_path: str, output_dir: Optional[str] = None) -> None:
    if output_dir is None:
        output_dir = os.path.dirname(csv_path) or DEFAULT_OUTPUT_DIR
    ensure_dir(output_dir)

    print(f"Loading dataset from {csv_path}...")
    data = load_existing_dataset(csv_path)
    print(f"Loaded {len(data)} repositories.")

    run_lab03_and_bonus(data, output_dir)
    print(f"Analysis completed in {output_dir}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect top GitHub repositories and generate Lab03 + bonus outputs."
    )
    sub = parser.add_subparsers(dest="command")

    collect_cmd = sub.add_parser("collect", help="Collect raw data from GitHub and run analysis.")
    collect_cmd.add_argument("--total", type=int, default=1000, help="Number of repositories to collect.")
    collect_cmd.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory for generated files.")

    analyze_cmd = sub.add_parser("analyze", help="Run Lab03 + bonus analysis from an existing CSV.")
    analyze_cmd.add_argument("--csv", required=True, help="Path to top_1000_repositories.csv")
    analyze_cmd.add_argument("--output-dir", default=None, help="Directory for generated files.")

    args = parser.parse_args()

    if args.command == "collect":
        collect_and_analyze(total_repos=args.total, output_dir=args.output_dir)
    elif args.command == "analyze":
        analyze_existing_csv(csv_path=args.csv, output_dir=args.output_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
