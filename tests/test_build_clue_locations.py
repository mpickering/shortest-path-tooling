import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build_clue_locations as bcl  # noqa: E402

COORDINATE = """\
	static final ImmutableMap<WorldPoint, CoordinateClue> CLUES = List.of(
		// Medium
		CoordinateClue.builder()
			.itemId(ItemID.TRAIL_MEDIUM_SEXTANT_EXP2)
			.location(new WorldPoint(1, 1, 0))
			.build(),
		// Hard
		CoordinateClue.builder()
			.location(new WorldPoint(2, 2, 0))
			.build(),
		CoordinateClue.builder()
			.itemId(ItemID.TRAIL_CLUE_HARD_SEXTANT001)
			.location(new WorldPoint(3, 3, 0))
			.build()
	);
"""

CRYPTIC = """\
		CrypticClue.builder()
			.itemIds(Set.of(ItemID.TRAIL_ELITE_SKILL_EXP1, ItemID.TRAIL_ELITE_SKILL_EXP2))
			.text("Show this to Sherlock.")
			.location(new WorldPoint(4, 4, 0))
			.build(),
		CrypticClue.builder()
			.itemId(ItemID.CLUEQUEST_CLUE1)
			.location(new WorldPoint(5, 5, 0))
			.build(),
"""

EMOTE = """\
		new EmoteClue(ItemID.TRAIL_CLUE_MASTER, "Dance.", "Temple", null, new WorldPoint(6, 6, 0), DANCE, item(ItemID.IBANSTAFF)),
		new EmoteClue(ItemID.TRAIL_CLUE_EASY_EMOTE017, "Cheer.", "Room", null, new WorldPoint(7, 7, 0), CHEER),
"""

HOT_COLD = """\
	ASGARNIA_WARRIORS(MASTER, new WorldPoint(8, 8, 0), ASGARNIA, "North.", BRASSICAN_MAGE),
	DRAYNOR_BANK(BEGINNER, new WorldPoint(9, 9, 0), MISTHALIN, "South.", BEGINNER_MAGE),
"""

MUSIC = """\
	private static final WorldPoint LOCATION = new WorldPoint(10, 10, 0);
	static final List<MusicClue> CLUES = ImmutableList.of(
		new MusicClue(ItemID.TRAIL_CLUE_EASY_MUSIC001, "Vision"),
		new MusicClue(ItemID.TRAIL_CLUE_HARD_MUSIC001, "Tiptoe")
	);
"""

BEGINNER_MAP = """\
		new BeginnerMapClue(InterfaceID.TRAIL_MAP01, new WorldPoint(11, 11, 0), MapClue.CHAMPIONS_GUILD),
"""


def write_sources(tmp_path):
    for name, text in [("CoordinateClue.java", COORDINATE), ("CrypticClue.java", CRYPTIC),
                       ("EmoteClue.java", EMOTE), ("HotColdLocation.java", HOT_COLD),
                       ("MusicClue.java", MUSIC), ("BeginnerMapClue.java", BEGINNER_MAP)]:
        (tmp_path / name).write_text(text)


def location(location_id, category, target, source):
    return {"id": location_id, "category": category, "target": list(target), "targetSource": source}


def line_of(text, needle):
    return next(i for i, line in enumerate(text.split("\n"), 1) if needle in line)


def test_tiers_come_from_item_names_hot_cold_type_and_fallbacks(tmp_path):
    write_sources(tmp_path)
    src = "runelite-client/src/main/java/net/runelite/client/plugins/cluescrolls/clues/"
    locations = [
        location("medium-coord", "coordinate", (1, 1, 0), src + "CoordinateClue.java:" + str(line_of(COORDINATE, "WorldPoint(1, 1"))),
        location("section-coord", "coordinate", (2, 2, 0), src + "CoordinateClue.java:" + str(line_of(COORDINATE, "WorldPoint(2, 2"))),
        location("hard-coord", "coordinate", (3, 3, 0), src + "CoordinateClue.java:" + str(line_of(COORDINATE, "WorldPoint(3, 3"))),
        location("sherlock", "cryptic", (4, 4, 0), src + "CrypticClue.java:" + str(line_of(CRYPTIC, "WorldPoint(4, 4"))),
        location("quest", "cryptic", (5, 5, 0), src + "CrypticClue.java:" + str(line_of(CRYPTIC, "WorldPoint(5, 5"))),
        location("master-emote", "emote", (6, 6, 0), src + "EmoteClue.java:1"),
        location("easy-emote", "emote", (7, 7, 0), src + "EmoteClue.java:2"),
        location("hot-cold-master", "hot_cold_possible", (8, 8, 0), "hotcold/HotColdLocation.java:1"),
        location("hot-cold-beginner", "hot_cold_possible", (9, 9, 0), "hotcold/HotColdLocation.java:2"),
        location("music", "music", (10, 10, 0), src + "MusicClue.java:1"),
        location("beginner-map", "beginner_map", (11, 12, 0), src + "BeginnerMapClue.java:1"),
        location("manual", "manual", (12, 12, 0), "from discord"),
    ]

    rows, excluded = bcl.build_rows(locations, tmp_path)

    tiers = {}
    for tier, x, y, z, category, source in rows:
        tiers.setdefault((x, y), []).append(tier)
    assert tiers == {
        (1, 1): ["MEDIUM"],
        (2, 2): ["HARD"],
        (3, 3): ["HARD"],
        (4, 4): ["ELITE"],
        (6, 6): ["MASTER"],
        (7, 7): ["EASY"],
        (8, 8): ["MASTER"],
        (9, 9): ["BEGINNER"],
        (10, 10): ["EASY", "HARD"],
        (11, 12): ["BEGINNER"],
    }
    assert [location_id for location_id, _ in excluded] == ["quest", "manual"]


def test_tsv_has_header_and_one_row_per_tier(tmp_path):
    out = tmp_path / "clues.tsv"
    bcl.write_tsv([("HARD", 1, 2, 0, "coordinate", "CoordinateClue.java:9")], out, "abc123")
    assert out.read_text().split("\n") == [
        "# Clue step locations by tier, from RuneLite abc123 via scripts/build_clue_locations.py",
        "# Tier\tDestination\tType\tSource",
        "HARD\t1 2 0\tcoordinate\tCoordinateClue.java:9",
        "",
    ]
