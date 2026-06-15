# github.py
from os import getenv
import httpx
from fastapi import HTTPException

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


def get_headers():
    token = getenv("GITHUB_TOKEN")
    if not token:
        raise HTTPException(
            status_code=500, detail="Token do GitHub não configurado.")
    return {"Authorization": f"bearer {token}"}


def get_graphql_query():
    return """
    query userInfo($login: String!) {
      user(login: $login) {
        name login
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
          nodes { stargazers { totalCount } }
        }
        contributionsCollection { totalCommitContributions }
        pullRequests { totalCount }
        issues { totalCount }
        repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]) {
          totalCount
        }
      }
    }
    """


async def fetch_github_stats(username: str) -> dict:
    """Busca os dados brutos do GitHub e os organiza."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GITHUB_GRAPHQL_URL,
            json={"query": get_graphql_query(), "variables": {
                "login": username}},
            headers=get_headers(),
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502, detail="Erro ao se comunicar com o GitHub")

    data = response.json()
    if "errors" in data or not data.get("data") or not data["data"].get("user"):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user_data = data["data"]["user"]

    # Retorna apenas o que precisamos, já tratado
    return {
        "name": user_data["name"] or user_data["login"],
        "total_commits": user_data["contributionsCollection"]["totalCommitContributions"],
        "stars": sum(repo["stargazers"]["totalCount"] for repo in user_data["repositories"]["nodes"]),
        "total_prs": user_data.get("pullRequests", {}).get("totalCount", 0),
        "total_issues": user_data.get("issues", {}).get("totalCount", 0),
        "contributed_to": user_data.get("repositoriesContributedTo", {}).get("totalCount", 0)
    }
