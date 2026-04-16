"""Runtime CSV sampling for characterization.

Aligned to `notebooks/charaterization_agent.ipynb`:
- BBC: groupby('category').head(2) and use `title` + `content[:500]`
- Taylor Swift: choose engagement column from [likeCount, likes, favorite_count, favorites],
  sort descending, take top 20, use `content`

Design:
- Returns `List[str]` (flexible downstream)
- Separate functions per persona, plus a dispatcher
- No caching across requests (pure runtime load)
- CSV paths configurable via env:
  - BBC_CSV_PATH (default: csv/bbc-news-data.csv)
  - TAYLOR_SWIFT_CSV_PATH (default: csv/TaylorSwift13.csv)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd


DEFAULT_BBC_CSV_PATH = "csv/bbc-news-data.csv"
DEFAULT_TAYLOR_SWIFT_CSV_PATH = "csv/TaylorSwift13.csv"


@dataclass(frozen=True)
class DataPaths:
    bbc_path: str = os.getenv("BBC_CSV_PATH", DEFAULT_BBC_CSV_PATH)
    taylor_swift_path: str = os.getenv("TAYLOR_SWIFT_CSV_PATH", DEFAULT_TAYLOR_SWIFT_CSV_PATH)


BBC_REQUIRED_COLUMNS = {"category", "title", "content"}
TS_REQUIRED_COLUMNS = {"content"}
TS_ENGAGEMENT_CANDIDATES = ["likeCount", "likes", "favorite_count", "favorites"]


def _assert_columns(df: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(list(required - set(df.columns)))
    if missing:
        raise ValueError(f"{label} CSV missing columns: {missing}. Found: {list(df.columns)}")


def get_bbc_samples(*, paths: DataPaths = DataPaths(), per_category: int = 2) -> List[str]:
    """Return BBC samples as a list of strings."""
    df = pd.read_csv(paths.bbc_path, sep="\t")
    _assert_columns(df, BBC_REQUIRED_COLUMNS, "BBC")

    # Match notebook behavior: groupby category and take first N rows from each group.
    samples_df = df.groupby("category").head(per_category)

    samples: List[str] = []
    for _, row in samples_df.iterrows():
        title = str(row["title"])
        content = str(row["content"])
        samples.append(f"{title}: {content}")
    return samples


def _pick_engagement_col(df: pd.DataFrame) -> Optional[str]:
    for col in TS_ENGAGEMENT_CANDIDATES:
        if col in df.columns:
            return col
    return None


def get_taylor_swift_samples(
    *,
    paths: DataPaths = DataPaths(),
    n: int = 20,
) -> List[str]:
    """Return Taylor Swift samples as a list of tweet content strings."""
    df = pd.read_csv(paths.taylor_swift_path, sep=",")
    _assert_columns(df, TS_REQUIRED_COLUMNS, "TaylorSwift")

    engagement_col = _pick_engagement_col(df)
    if engagement_col:
        df = df.sort_values(by=engagement_col, ascending=False)

    samples_df = df.head(n)
    return [str(x) for x in samples_df["content"].astype(str).tolist()]


def get_samples(
    *,
    persona: str,
    paths: DataPaths = DataPaths(),
) -> List[str]:
    """Persona dispatcher.

    Canonical personas:
    - bbc
    - taylor_swift
    """
    p = persona.strip().lower()
    if p == "bbc":
        return get_bbc_samples(paths=paths)
    if p in {"taylor_swift", "taylorswift", "taylor"}:
        return get_taylor_swift_samples(paths=paths)

    raise ValueError(f"Unknown persona: {persona}. Expected 'bbc' or 'taylor_swift'.")
