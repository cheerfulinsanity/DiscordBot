import os
import json
from bot.formatter import format_match

# Enable stat logging inside formatter
os.environ["DEBUG_MODE"] = "1"


def run_match_test(sample_path, player_name, player_id, hero_name, kills, deaths, assists, won):
    with open(sample_path) as f:
        match = json.load(f)

    result = format_match(
        player_name=player_name,
        player_id=player_id,
        hero_name=hero_name,
        kills=kills,
        deaths=deaths,
        assists=assists,
        won=won,
        full_match=match
    )

    game_mode = match.get("gameMode", "Unknown")
    print(f"✅ Output from Match {match.get('id', '???')} (mode {game_mode}):\n")
    print(result)
    print("\n" + "=" * 80 + "\n")


def test_format_normal_match():
    run_match_test(
        sample_path="tests/samples/match_normal.json",
        player_name="TestPlayer",
        player_id=123456789,
        hero_name="npc_dota_hero_vengefulspirit",
        kills=9,
        deaths=4,
        assists=15,
        won=True
    )


def test_format_turbo_match():
    run_match_test(
        sample_path="tests/samples/match_turbo.json",
        player_name="TestPlayer",
        player_id=123456789,
        hero_name="npc_dota_hero_sniper",
        kills=12,
        deaths=8,
        assists=6,
        won=False
    )


# ✅ Entry point for CLI
if __name__ == "__main__":
    test_format_normal_match()
    test_format_turbo_match()
