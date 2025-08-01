import os
import json
import sys
from pathlib import Path
import importlib.util

# ✅ Set DEBUG mode to enable stat dumps
os.environ["DEBUG_MODE"] = "1"

# ✅ Locate formatter manually
ROOT_DIR = Path(__file__).resolve().parent.parent
FORMATTER_PATH = ROOT_DIR / "bot" / "formatter.py"

spec = importlib.util.spec_from_file_location("formatter", FORMATTER_PATH)
formatter = importlib.util.module_from_spec(spec)
sys.modules["formatter"] = formatter
spec.loader.exec_module(formatter)

# ✅ Pull function directly from loaded module
format_match = getattr(formatter, "format_match", None)
if not callable(format_match):
    raise RuntimeError("❌ Could not locate format_match in formatter.py")

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

    mode = match.get("gameMode", "Unknown")
    match_id = match.get("id", "???")
    print(f"✅ Output from Match {match_id} (mode {mode}):\n")
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


if __name__ == "__main__":
    test_format_normal_match()
    test_format_turbo_match()
