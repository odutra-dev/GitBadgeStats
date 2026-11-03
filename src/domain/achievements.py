"""GitHub Achievements domain models and calculations.

Adheres to Single Responsibility Principle (SRP): handles achievement definitions,
tier milestones, profile badge parsing, and progress status calculation.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TierTarget:
    """Milestone target for an achievement tier."""
    label: str
    target: int
    multiplier: str = "x1"


@dataclass(frozen=True)
class AchievementDefinition:
    """Definition and milestones for a GitHub achievement."""
    id: str
    name: str
    description: str
    unit: str
    tiers: list[TierTarget]

    @property
    def max_target(self) -> int:
        return self.tiers[-1].target if self.tiers else 1


ACHIEVEMENT_DEFINITIONS: dict[str, AchievementDefinition] = {
    "pull-shark": AchievementDefinition(
        id="pull-shark",
        name="Pull Shark",
        description="Opened pull requests that have been merged.",
        unit="merged PRs",
        tiers=[
            TierTarget(label="Default", target=2, multiplier="x1"),
            TierTarget(label="Bronze", target=16, multiplier="x2"),
            TierTarget(label="Silver", target=128, multiplier="x3"),
            TierTarget(label="Gold", target=1024, multiplier="x4"),
        ],
    ),
    "starstruck": AchievementDefinition(
        id="starstruck",
        name="Starstruck",
        description="Created a repository that has many stars.",
        unit="stars",
        tiers=[
            TierTarget(label="Default", target=16, multiplier="x1"),
            TierTarget(label="Bronze", target=128, multiplier="x2"),
            TierTarget(label="Silver", target=512, multiplier="x3"),
            TierTarget(label="Gold", target=4096, multiplier="x4"),
        ],
    ),
    "galaxy-brain": AchievementDefinition(
        id="galaxy-brain",
        name="Galaxy Brain",
        description="Answered discussions and got answers accepted.",
        unit="accepted answers",
        tiers=[
            TierTarget(label="Default", target=2, multiplier="x1"),
            TierTarget(label="Bronze", target=8, multiplier="x2"),
            TierTarget(label="Silver", target=16, multiplier="x3"),
            TierTarget(label="Gold", target=32, multiplier="x4"),
        ],
    ),
    "pair-extraordinaire": AchievementDefinition(
        id="pair-extraordinaire",
        name="Pair Extraordinaire",
        description="Co-authored commits on merged pull requests.",
        unit="co-authored PRs",
        tiers=[
            TierTarget(label="Default", target=1, multiplier="x1"),
            TierTarget(label="Bronze", target=10, multiplier="x2"),
            TierTarget(label="Silver", target=24, multiplier="x3"),
            TierTarget(label="Gold", target=48, multiplier="x4"),
        ],
    ),
    "quickdraw": AchievementDefinition(
        id="quickdraw",
        name="Quickdraw",
        description="Closed an issue or pull request within 5 minutes.",
        unit="closes",
        tiers=[
            TierTarget(label="Default", target=1, multiplier="x1"),
        ],
    ),
    "yolo": AchievementDefinition(
        id="yolo",
        name="YOLO",
        description="Merged a pull request without code review.",
        unit="merges",
        tiers=[
            TierTarget(label="Default", target=1, multiplier="x1"),
        ],
    ),
    "public-sponsor": AchievementDefinition(
        id="public-sponsor",
        name="Public Sponsor",
        description="Sponsored open source contributors via GitHub Sponsors.",
        unit="sponsorships",
        tiers=[
            TierTarget(label="Default", target=1, multiplier="x1"),
        ],
    ),
}

ORDERED_ACHIEVEMENT_IDS = [
    "pull-shark",
    "starstruck",
    "galaxy-brain",
    "pair-extraordinaire",
    "quickdraw",
    "yolo",
    "public-sponsor",
]

TIER_ORDER = {"default": 1, "bronze": 2, "silver": 3, "gold": 4}
TIER_LABELS = {
    "default": "Default",
    "bronze": "Bronze",
    "silver": "Silver",
    "gold": "Gold",
}
TIER_MULTIPLIERS = {
    "default": "x1",
    "bronze": "x2",
    "silver": "x3",
    "gold": "x4",
}


@dataclass
class UserAchievement:
    """Calculated achievement state for a user."""
    id: str
    name: str
    unlocked: bool
    tier: str  # "locked", "default", "bronze", "silver", "gold"
    tier_label: str  # "Locked", "Default", "Bronze", "Silver", "Gold"
    multiplier: str  # "", "x1", "x2", "x3", "x4"
    current_value: int
    target_value: int
    progress_percentage: float
    badge_url: Optional[str] = None


def normalize_achievement_id(raw_id: str) -> Optional[str]:
    """Normalize raw id / slug to canonical achievement id."""
    slug = raw_id.strip().lower().replace("_", "-")
    # Handle known variations
    if "pull-shark" in slug or "pullshark" in slug:
        return "pull-shark"
    if "starstruck" in slug or "star-struck" in slug:
        return "starstruck"
    if "galaxy-brain" in slug or "galaxybrain" in slug:
        return "galaxy-brain"
    if "pair-extraordinaire" in slug or "pairextraordinaire" in slug:
        return "pair-extraordinaire"
    if "quickdraw" in slug or "quick-draw" in slug:
        return "quickdraw"
    if "yolo" in slug:
        return "yolo"
    if "sponsor" in slug:
        return "public-sponsor"
    return slug if slug in ACHIEVEMENT_DEFINITIONS else None


def parse_profile_achievements(html: str) -> dict[str, dict]:
    """Parse official achievement badges from a GitHub profile or achievements HTML page."""
    detected: dict[str, dict] = {}
    if not html:
        return detected

    # Pattern matches achievement image tags on GitHub profiles
    # e.g.: <img src=".../pull-shark-silver-0643f87ac9fd.png" alt="Achievement: Pull Shark" ... />
    img_matches = re.finditer(
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]*alt=["\']Achievement:\s*([^"\']+)["\']',
        html,
        re.IGNORECASE,
    )
    for match in img_matches:
        src = match.group(1)
        alt_name = match.group(2).strip()

        ach_id = normalize_achievement_id(alt_name)
        if not ach_id:
            ach_id = normalize_achievement_id(src)
        if not ach_id:
            continue

        # Extract tier from image src
        tier = "default"
        src_lower = src.lower()
        if "gold" in src_lower:
            tier = "gold"
        elif "silver" in src_lower:
            tier = "silver"
        elif "bronze" in src_lower:
            tier = "bronze"

        # Check if already present and keep highest tier if duplicates occur
        if ach_id in detected:
            existing_rank = TIER_ORDER.get(detected[ach_id]["tier"], 0)
            new_rank = TIER_ORDER.get(tier, 0)
            if new_rank <= existing_rank:
                continue

        detected[ach_id] = {
            "id": ach_id,
            "name": alt_name,
            "tier": tier,
            "src": src,
        }

    # Also check hovercard / detail links if img regex missed any
    hovercard_matches = re.finditer(
        r'data-hovercard-url=["\']/users/[^/]+/achievements/([^/?]+)/detail',
        html,
        re.IGNORECASE,
    )
    for match in hovercard_matches:
        raw_slug = match.group(1)
        ach_id = normalize_achievement_id(raw_slug)
        if ach_id and ach_id not in detected:
            detected[ach_id] = {
                "id": ach_id,
                "name": ACHIEVEMENT_DEFINITIONS[ach_id].name,
                "tier": "default",
                "src": None,
            }

    return detected


def build_user_achievements(
    official_badges: dict[str, dict],
    metric_counts: Optional[dict[str, int]] = None,
) -> list[UserAchievement]:
    """Build unified achievement list combining official badges and known counts."""
    metric_counts = metric_counts or {}
    results: list[UserAchievement] = []

    for ach_id in ORDERED_ACHIEVEMENT_IDS:
        definition = ACHIEVEMENT_DEFINITIONS[ach_id]
        official = official_badges.get(ach_id)
        raw_count = metric_counts.get(ach_id, 0)

        # Determine tier
        if official:
            unlocked = True
            tier = official.get("tier", "default").lower()
            if tier not in TIER_ORDER:
                tier = "default"

            # Official badge gives a minimum baseline count
            tier_target = next(
                (t.target for t in definition.tiers if t.label.lower() == tier),
                definition.tiers[0].target,
            )
            count = max(raw_count, tier_target)
        elif raw_count > 0:
            # Check if count unlocks at least the default tier
            unlocked = raw_count >= definition.tiers[0].target
            tier = "locked"
            for t in reversed(definition.tiers):
                if raw_count >= t.target:
                    tier = t.label.lower()
                    break
            count = raw_count
        else:
            unlocked = False
            tier = "locked"
            count = 0

        # Calculate next target & progress
        if tier == "locked":
            tier_label = "Locked"
            multiplier = ""
            target_value = definition.tiers[0].target
            progress = min(100.0, (count / target_value) * 100.0) if target_value > 0 else 0.0
        else:
            tier_label = TIER_LABELS.get(tier, "Default")
            multiplier = TIER_MULTIPLIERS.get(tier, "x1")
            # Next tier target
            current_tier_index = next(
                (i for i, t in enumerate(definition.tiers) if t.label.lower() == tier),
                0,
            )
            if current_tier_index + 1 < len(definition.tiers):
                target_value = definition.tiers[current_tier_index + 1].target
            else:
                target_value = definition.tiers[-1].target

            progress = min(100.0, (count / target_value) * 100.0) if target_value > 0 else 100.0

        results.append(
            UserAchievement(
                id=ach_id,
                name=definition.name,
                unlocked=unlocked,
                tier=tier,
                tier_label=tier_label,
                multiplier=multiplier,
                current_value=count,
                target_value=target_value,
                progress_percentage=round(progress, 1),
                badge_url=official.get("src") if official else None,
            )
        )

    return results
