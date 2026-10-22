"""Domain logic for calculating top languages from repository language data.

Adheres to Single Responsibility Principle (SRP): pure business calculations
for aggregating repository language byte counts, applying exclusions, and computing percentages.
"""

from typing import Optional


class LanguagesCalculator:
    """Calculates top languages aggregated across repositories."""

    DEFAULT_FALLBACK_COLOR = "#858585"

    @classmethod
    def calculate_top_languages(
        cls,
        repo_nodes: list[dict],
        exclude_languages: Optional[set[str]] = None,
        exclude_repos: Optional[set[str]] = None,
        top_n: int = 5,
    ) -> list[dict]:
        """Aggregate language usage across repositories, computing percentages and returning top N."""
        if not repo_nodes:
            return []

        clean_exclude_langs = {lang.strip().lower() for lang in exclude_languages} if exclude_languages else set()
        clean_exclude_repos = {repo.strip().lower() for repo in exclude_repos} if exclude_repos else set()

        langs_data: dict[str, dict] = {}
        total_size = 0

        for repo in repo_nodes:
            repo_name = repo.get("name", "").strip().lower()
            if repo_name in clean_exclude_repos or repo.get("isFork", False):
                continue

            edges = repo.get("languages", {}).get("edges", [])
            for edge in edges:
                size = edge.get("size", 0)
                node = edge.get("node", {})
                name = node.get("name", "")
                if not name or size <= 0:
                    continue

                if name.lower() in clean_exclude_langs:
                    continue

                color = node.get("color") or cls.DEFAULT_FALLBACK_COLOR

                if name not in langs_data:
                    langs_data[name] = {
                        "name": name,
                        "color": color,
                        "size": 0,
                    }

                langs_data[name]["size"] += size
                total_size += size

        if total_size <= 0:
            return []

        sorted_langs = sorted(langs_data.values(), key=lambda x: x["size"], reverse=True)

        result = []
        for item in sorted_langs[:top_n]:
            percent = round((item["size"] / total_size) * 100, 2)
            result.append({
                "name": item["name"],
                "color": item["color"],
                "size": item["size"],
                "percent": percent,
            })

        return result


def calculate_top_languages(
    repo_nodes: list[dict],
    exclude_languages: Optional[set[str]] = None,
    exclude_repos: Optional[set[str]] = None,
    top_n: int = 5,
) -> list[dict]:
    """Functional shortcut for LanguagesCalculator.calculate_top_languages."""
    return LanguagesCalculator.calculate_top_languages(
        repo_nodes=repo_nodes,
        exclude_languages=exclude_languages,
        exclude_repos=exclude_repos,
        top_n=top_n,
    )
