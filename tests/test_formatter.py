from bot.formatter import format_match
import json

def test_format_normal_match():
    with open("tests/samples/match_normal.json") as f:
        match = json.load(f)
    result = format_match("TestPlayer", 123456789, "npc_dota_hero_axe", 8, 3, 12, True, match)
    print(result)

def test_format_turbo_match():
    with open("tests/samples/match_turbo.json") as f:
        match = json.load(f)
    result = format_match("TestPlayer", 123456789, "npc_dota_hero_lina", 15, 2, 10, False, match)
    print(result)
