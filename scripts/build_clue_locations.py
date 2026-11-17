#!/usr/bin/env python3
"""Build a clue-location TSV with each location's clue tier.

The tooling's ``clue-locations.json`` lists clue step locations, each with a
``targetSource`` pointing at the RuneLite clue-scroll source line that defines
it, but no tier. RuneLite has no tier field either: the tier is part of the
clue item's gameval name (``TRAIL_CLUE_HARD_…``, ``TRAIL_ELITE_SEXTANT_…``).
This script finds the RuneLite clue entry around each ``targetSource`` line
and reads the tiers from the item names in it.

Fallbacks, in order:

- ``BeginnerMapClue`` entries are beginner tier.
- ``HotColdLocation`` entries carry their tier as the enum's first argument.
- ``MusicClue`` entries share one tile, which every music clue tier uses.
- A ``CoordinateClue`` entry without an item id takes the tier of the
  ``// <Tier>`` section comment above it.

Entries with no tier, such as the X Marks the Spot quest clues
(``CLUEQUEST_*``), are left out and listed on stderr. A clue whose item ids
span several tiers gives one row per tier. The tile written is the tooling's
target, which may be a few tiles from RuneLite's when the tooling moved it to
a walkable tile.

Usage::

    python3 scripts/build_clue_locations.py --runelite-ref <sha> --out clue-locations.tsv
    python3 scripts/build_clue_locations.py --runelite-dir <clues dir> --out clue-locations.tsv
"""

import argparse
import json
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOCATIONS = REPO_ROOT / "src/test/resources/scenarios/clue-locations.json"
RAW_CLUES_URL = ("https://raw.githubusercontent.com/runelite/runelite/{ref}/runelite-client/src/main/"
                 "java/net/runelite/client/plugins/cluescrolls/clues/{path}")
CLUE_FILES = {
    "AnagramClue.java": "AnagramClue.java",
    "BeginnerMapClue.java": "BeginnerMapClue.java",
    "CipherClue.java": "CipherClue.java",
    "CoordinateClue.java": "CoordinateClue.java",
    "CrypticClue.java": "CrypticClue.java",
    "EmoteClue.java": "EmoteClue.java",
    "FairyRingClue.java": "FairyRingClue.java",
    "HotColdClue.java": "HotColdClue.java",
    "HotColdLocation.java": "hotcold/HotColdLocation.java",
    "MapClue.java": "MapClue.java",
    "MusicClue.java": "MusicClue.java",
}
TIERS = ["BEGINNER", "EASY", "MEDIUM", "HARD", "ELITE", "MASTER"]
ITEM_TIER = re.compile(r"ItemID\.TRAIL_(?:CLUE_)?(" + "|".join(TIERS) + r")")
HOT_COLD_TIER = re.compile(r"^\s*[A-Z0-9_]+\((BEGINNER|MASTER),")
SECTION_TIER = re.compile(r"^\s*//\s*(" + "|".join(t.title() for t in TIERS) + r")\s*$")
ENTRY_START = re.compile(r"builder\(\)|new \w+Clue\(|^\s*[A-Z0-9_]+\((?:BEGINNER|MASTER),")


def fetch_runelite(ref, cache_dir):
    """Downloads the clue sources at ``ref`` into ``cache_dir`` once; returns the directory."""
    target = Path(cache_dir) / ref
    for name, path in CLUE_FILES.items():
        dest = target / name
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(RAW_CLUES_URL.format(ref=ref, path=path)) as response:
                dest.write_bytes(response.read())
    return target


def entry_bounds(lines, index):
    """The first and last line of the clue entry containing line ``index`` (0-based)."""
    start = index
    while start > 0 and not ENTRY_START.search(lines[start]):
        start -= 1
    builder = "builder()" in lines[start]
    end = start
    while end + 1 < len(lines):
        line = lines[end].strip()
        if builder and line.startswith(".build()"):
            break
        if not builder and line.endswith((")", "),", "));")):
            break
        if end > start and ENTRY_START.search(lines[end + 1]):
            break
        end += 1
    return start, end


def section_tier(lines, index):
    """The tier of the nearest ``// <Tier>`` comment at or above line ``index``, or None."""
    for line in reversed(lines[:index + 1]):
        match = SECTION_TIER.match(line)
        if match:
            return match.group(1).upper()
    return None


def tiers_for(file_name, lines, line_number):
    """The tiers of the clue entry around 1-based ``line_number`` of ``file_name``."""
    if file_name == "BeginnerMapClue.java":
        return ["BEGINNER"]
    if file_name == "MusicClue.java":
        found = set(ITEM_TIER.findall("\n".join(lines)))
        return [t for t in TIERS if t in found]
    start, end = entry_bounds(lines, line_number - 1)
    text = "\n".join(lines[start:end + 1])
    found = set(ITEM_TIER.findall(text))
    hot_cold = HOT_COLD_TIER.match(lines[start])
    if hot_cold:
        found.add(hot_cold.group(1))
    if not found and file_name == "CoordinateClue.java" and "itemId" not in text:
        tier = section_tier(lines, start)
        if tier:
            found.add(tier)
    return [t for t in TIERS if t in found]


def build_rows(locations, runelite_dir):
    """``(rows, excluded)``: rows are ``(tier, x, y, z, category, source)``; excluded are ``(id, reason)``."""
    sources = {}
    rows, excluded = [], []
    for location in locations:
        source = location.get("targetSource", "")
        match = re.search(r"([A-Za-z]+\.java):(\d+)$", source)
        if not match or match.group(1) not in CLUE_FILES:
            excluded.append((location["id"], "no RuneLite source"))
            continue
        file_name, line_number = match.group(1), int(match.group(2))
        if file_name not in sources:
            sources[file_name] = (Path(runelite_dir) / file_name).read_text().split("\n")
        tiers = tiers_for(file_name, sources[file_name], line_number)
        if not tiers:
            excluded.append((location["id"], "no tier at " + file_name + ":" + str(line_number)))
            continue
        x, y, z = location["target"]
        for tier in tiers:
            rows.append((tier, x, y, z, location["category"], file_name + ":" + str(line_number)))
    rows.sort(key=lambda r: (TIERS.index(r[0]), r[4], r[1], r[2], r[3]))
    return rows, excluded


def write_tsv(rows, out, runelite_ref):
    with open(out, "w") as f:
        f.write("# Clue step locations by tier, from RuneLite " + runelite_ref
                + " via scripts/build_clue_locations.py\n")
        f.write("# Tier\tDestination\tType\tSource\n")
        for tier, x, y, z, category, source in rows:
            f.write(f"{tier}\t{x} {y} {z}\t{category}\t{source}\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    runelite = parser.add_mutually_exclusive_group(required=True)
    runelite.add_argument("--runelite-ref", help="RuneLite commit to download the clue sources from")
    runelite.add_argument("--runelite-dir", help="directory holding the RuneLite clue sources, flattened")
    parser.add_argument("--locations", default=str(DEFAULT_LOCATIONS), help="clue-locations.json to read")
    parser.add_argument("--cache-dir", default=str(REPO_ROOT / "build/runelite-clues"),
                        help="where --runelite-ref downloads go")
    parser.add_argument("--out", required=True, help="TSV to write")
    args = parser.parse_args(argv)

    if args.runelite_ref:
        runelite_dir, ref = fetch_runelite(args.runelite_ref, args.cache_dir), args.runelite_ref
    else:
        runelite_dir, ref = Path(args.runelite_dir), "local " + args.runelite_dir
    with open(args.locations) as f:
        locations = json.load(f)
    rows, excluded = build_rows(locations, runelite_dir)
    write_tsv(rows, args.out, ref)

    counts = Counter(row[0] for row in rows)
    print("rows per tier: " + ", ".join(f"{t} {counts[t]}" for t in TIERS), file=sys.stderr)
    for location_id, reason in excluded:
        print(f"excluded {location_id}: {reason}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
