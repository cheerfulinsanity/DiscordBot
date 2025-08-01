import os
import json
from bot.formatter import format_match

# Enable debug logging for stat extraction
os.environ["DEBUG_MODE"] = "1"

def test_format_normal_match():
    with open("tests/samples/match_normal.json") as f:
        match = json.load(f)

    result = format_match(
        player_name="TestPlayer",
        player_id=123456789,
        hero_name="npc_dota_hero_vengefulspirit",
        kills=9,
        deaths=4,
        assists=15,
        won=True,
        full_match=match
    )

    assert isinstance(result, str)
    print("✅ Normal match output:\n", result)


def test_format_turbo_match():
    with open("tests/samples/match_turbo.json") as f:
        match = json.load(f)

    result = format_match(
        player_name="TestPlayer",
        player_id=123456789,
        hero_name="npc_dota_hero_sniper",
        kills=12,
        deaths=8,
        assists=6,
        won=False,
        full_match=match
    )

    assert isinstance(result, str)
    print("✅ Turbo match output:\n", result)


# CLI trigger
if __name__ == "__main__":
    test_format_normal_match()
    print("\n" + "="*80 + "\n")
    test_format_turbo_match()
