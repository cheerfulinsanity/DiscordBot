# bot/formatter.py
import json
from pathlib import Path
import hashlib
import random
from feedback.engine import analyze_player as analyze_normal
from feedback.engine_turbo import analyze_player as analyze_turbo
from feedback.advice import generate_advice, get_title_phrase
from feedback.extract import extract_player_stats
from datetime import datetime
import os

# --- Canonical stat sets (reference only) ---
NORMAL_STATS = [
    "kills", "deaths", "assists", "imp", "level",
    "gold", "goldSpent", "gpm", "xpm",
    "heroHealing", "heroDamage", "towerDamage", "buildingDamage", "damageTaken",
    "actionsPerMinute", "killParticipation", "fightParticipationPercent",
    "stunDuration", "disableDuration",
    "runePickups", "wardsPlaced", "sentryWardsPlaced", "observerWardsPlaced", "wardsDestroyed",
    "campStack", "neutralKills", "laneCreeps", "jungleCreeps",
    "networth", "networthPerMinute", "experiencePerMinute"
]

TURBO_STATS = [
    stat for stat in NORMAL_STATS
    if stat not in {"gpm", "xpm", "gold", "goldSpent", "networth", "networthPerMinute"}
]

# --- Game mode ID to label mapping ---
GAME_MODE_NAMES = {
    0: "Unknown",
    1: "All Pick",
    2: "Captains Mode",
    3: "Random Draft",
    4: "Single Draft",
    5: "All Random",
    6: "Intro",
    7: "Diretide",
    8: "Reverse Captains Mode",
    9: "Greeviling",
    10: "Tutorial",
    11: "Mid Only",
    12: "Ability Draft",
    13: "Event",
    14: "AR Deathmatch",
    15: "1v1 Mid",
    16: "Captains Draft",
    17: "Balanced Draft",
    18: "Ability All Pick",
    20: "Turbo",
    21: "Mutation",
    22: "Ranked All Pick",
    23: "Turbo",
    24: "Ranked Draft",
    25: "Ranked Random Draft"
}

# --- Raw Stratz gameModeName fallback mappings ---
RAW_MODE_LABELS = {
    "MODE_TURBO": "Turbo",
    "MODE_ALL_PICK": "All Pick",
    "ALL_PICK_RANKED": "Ranked All Pick",
    "CAPTAINS_MODE": "Captains Mode",
    "SINGLE_DRAFT": "Single Draft",
    "RANDOM_DRAFT": "Random Draft",
    "ABILITY_DRAFT": "Ability Draft",
    "CAPTAINS_DRAFT": "Captains Draft",
    # Allow raw enums without MODE_ prefix
    "TURBO": "Turbo",
    "ALL_PICK": "All Pick",
    "RANKED_ALL_PICK": "Ranked All Pick",
}

# --- Utility: Normalize hero name from full name string ---
def normalize_hero_name(raw_name: str) -> str:
    if not raw_name:
        return "unknown"
    if raw_name.startswith("npc_dota_hero_"):
        return raw_name.replace("npc_dota_hero_", "").lower()
    return raw_name.lower()

# --- Deprecated fallback functions ---
def get_role(hero_name: str) -> str:
    return "unknown"

def get_baseline(hero_name: str, mode: str) -> dict | None:
    return None

# --- Helpers for compact tokens and budgeting ---
def _safe_num(x, default=0.0):
    try:
        if x is None:
            return default
        if isinstance(x, bool):
            return float(x)
        return float(x)
    except Exception:
        return default

def _avg_seq(seq):
    if isinstance(seq, list) and seq:
        vals = [_safe_num(v, 0.0) for v in seq]
        return sum(vals) / len(vals) if vals else 0.0
    return _safe_num(seq, 0.0)

def _fmt_pct(p):
    try:
        return f"{max(0.0, min(1.0, float(p))) * 100:.0f}%"
    except Exception:
        return "0%"

def _join_bullets(lines, max_chars=1024):
    """Join bullets and hard-trim to Discord field limit."""
    if not lines:
        return ""
    out = []
    total = 0
    for line in lines:
        bullet = f"• {line}".strip()
        add = len(bullet) + (1 if out else 0)  # newline cost
        if total + add > max_chars:
            break
        out.append(bullet)
        total += add
    # If nothing fits (very unlikely), hard truncate first line
    if not out:
        return (f"• {lines[0]}")[:max_chars]
    return "\n".join(out)

# --- Main match analysis entrypoint ---
def format_match_embed(player: dict, match: dict, stats_block: dict, player_name: str = "Player") -> dict:
    game_mode_field = match.get("gameMode")  # may be int (ID) or str enum (e.g., "TURBO")
    raw_label = (match.get("gameModeName") or "").upper()

    # Resolve human-readable mode name without using "Mode " prefix
    if isinstance(game_mode_field, str) and game_mode_field:
        game_mode_name = (
            RAW_MODE_LABELS.get(game_mode_field.upper())
            or RAW_MODE_LABELS.get(raw_label)
            or game_mode_field.replace("_", " ").title()
            or "Unknown"
        )
    else:
        # numeric ID path
        game_mode_name = (
            RAW_MODE_LABELS.get(raw_label)
            or GAME_MODE_NAMES.get(game_mode_field)
            or (raw_label.replace("_", " ").title() if raw_label else None)
            or "Unknown"
        )

    # Hardened Turbo detection (supports both numeric IDs and string enums)
    is_turbo = (
        game_mode_field in (20, 23, "TURBO")
        or RAW_MODE_LABELS.get(raw_label) == "Turbo"
        or raw_label == "MODE_TURBO"
    )
    mode = "TURBO" if is_turbo else "NON_TURBO"

    team_kills = player.get("_team_kills") or sum(
        p.get("kills", 0) for p in match.get("players", [])
        if p.get("isRadiant") == player.get("isRadiant")
    )

    # Extract player stats
    stats = extract_player_stats(player, stats_block, team_kills, mode)

    # Ensure correct duration source from match-level field
    stats["durationSeconds"] = match.get("durationSeconds", 0)

    # --- Defensive: replace None with safe defaults by expected type ---
    for k in list(stats.keys()):
        v = stats[k]
        if v is None:
            if k in {"lane", "roleBasic"}:
                stats[k] = ""
            elif k == "statsBlock":
                stats[k] = {}
            else:
                # default numeric-safe
                stats[k] = 0

    engine = analyze_turbo if is_turbo else analyze_normal
    result = engine(stats, {}, player.get("roleBasic", ""), team_kills)

    tags = result.get("feedback_tags", {})
    is_victory = player.get("isVictory", False)

    # Deterministic phrasing
    try:
        seed_str = f"{match.get('id')}:{player.get('steamAccountId')}"
        random.seed(hashlib.md5(seed_str.encode()).hexdigest())
    except Exception:
        pass

    advice = generate_advice(tags, stats, mode=mode)

    score = float(result.get("score") or 0.0)  # ✅ Ensure numeric
    emoji, title = get_title_phrase(score, is_victory, tags.get("compound_flags", []))
    title = title[:1].lower() + title[1:]

    # --- New: quick tokens for fancy embed ---
    kills = _safe_num(player.get("kills"), 0)
    deaths = _safe_num(player.get("deaths"), 0)
    assists = _safe_num(player.get("assists"), 0)
    kp = (kills + assists) / team_kills if team_kills > 0 else 0.0  # engines compute too; safe to recompute here
    stacks = _safe_num(stats.get("campStack"), 0)
    apm_src = stats.get("actionsPerMinute", 0)
    apm = _avg_seq(apm_src)
    hero_dmg = _safe_num(player.get("heroDamage"), 0)
    tower_dmg = _safe_num(player.get("towerDamage"), 0)

    quick = {
        "kp": _fmt_pct(kp),
        "stacks": int(stacks),
        "apm": int(round(apm)),
        "hdmg": int(hero_dmg),
        "tdmg": int(tower_dmg),
        "kda": f"{int(kills)}/{int(deaths)}/{int(assists)}"
    }

    # Light tokens to append to advice lines where appropriate
    # (Never attach econ tokens in Turbo.)
    token_map = []
    if kp > 0:
        token_map.append(f"KP {quick['kp']}")
    if stacks > 0:
        token_map.append(f"+{int(stacks)} stacks")
    if not is_turbo and hero_dmg > 0:
        token_map.append(f"{quick['hdmg']} HDMG")

    token_suffix = f" ({'; '.join(token_map)})" if token_map else ""

    # Expand advice density *slightly* with tokens while keeping ≤3 primary lines
    positives = [line + token_suffix for line in (advice.get("positives", [])[:3])]
    negatives = [line + token_suffix for line in (advice.get("negatives", [])[:3])]
    flags_out = advice.get("flags", [])[:3]

    # Tips can fit more if budget allows; we’ll allow up to 5 and budget in build step
    tips = advice.get("tips", [])[:5]

    return {
        "playerName": player_name,
        "emoji": emoji,
        "title": title,
        "score": score,
        "mode": mode,
        "gameModeName": game_mode_name,
        "role": player.get("roleBasic", "unknown"),
        "hero": player.get("hero", {}).get("displayName") or normalize_hero_name(player.get("hero", {}).get("name", "")),
        "kda": quick["kda"],
        "duration": match.get("durationSeconds", 0),
        "isVictory": is_victory,
        "positives": positives,
        "negatives": negatives,
        "flags": flags_out,
        "tips": tips,
        "matchId": match.get("id"),
        # --- New payload for richer embed ---
        "quick": quick,
        "highlight": tags.get("highlight"),
        "lowlight": tags.get("lowlight"),
    }

# --- Embed formatting for Discord output ---
def build_discord_embed(result: dict) -> dict:
    from datetime import datetime, timezone

    hero = result.get("hero", "unknown")
    kda = result.get("kda", "0/0/0")
    victory = "Win" if result.get("isVictory") else "Loss"
    title = f"{result.get('emoji', '')} {result.get('playerName', 'Player')} {result.get('title')} {kda} as {hero} — {victory}"

    duration = result.get("duration", 0)
    duration_str = f"{duration // 60}:{duration % 60:02d}"

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    # --- Fancy bits: color + clickable title to Stratz match ---
    color = 0x3FBF5A if result.get("isVictory") else 0xD64545  # green/red
    url = f"https://stratz.com/match/{result.get('matchId')}" if result.get("matchId") else None

    # --- Meta fields (unchanged content, inline layout) ---
    meta_fields = [
        {
            "name": "🧮 Impact",
            "value": f"{result.get('score', 0.0):.2f} (typical in-game: −10 to +10, high-end ~+20–30)",
            "inline": True
        },
        {
            "name": "🧭 Role",
            "value": result.get("role", "unknown").capitalize(),
            "inline": True
        },
        {
            "name": "⚙️ Mode",
            "value": result.get("gameModeName", "Unknown"),
            "inline": True
        },
        {
            "name": "⏱️ Duration",
            "value": duration_str,
            "inline": True
        },
    ]

    # --- New: Quick stats row (compact badges) ---
    q = result.get("quick", {}) or {}
    quick_parts = []
    if q.get("kp"):
        quick_parts.append(f"KP {q['kp']}")
    if isinstance(q.get("stacks"), int) and q.get("stacks") > 0:
        quick_parts.append(f"Stacks +{q['stacks']}")
    if isinstance(q.get("apm"), int) and q.get("apm") > 0:
        quick_parts.append(f"APM {q['apm']}")
    if isinstance(q.get("hdmg"), int) and q.get("hdmg") > 0:
        quick_parts.append(f"HDMG {q['hdmg']}")
    if isinstance(q.get("tdmg"), int) and q.get("tdmg") > 0:
        quick_parts.append(f"TDMG {q['tdmg']}")

    quick_value = " · ".join(quick_parts) if quick_parts else "—"
    quick_field = {
        "name": "📊 Quick stats",
        "value": quick_value,
        "inline": False
    }

    # --- Advice sections: place side-by-side for density ---
    # We budget each field to ≤1024 chars via _join_bullets.
    pos_val = _join_bullets(result.get("positives") or [])
    neg_val = _join_bullets(result.get("negatives") or [])
    flags_val = _join_bullets(result.get("flags") or [])
    tips_val = _join_bullets(result.get("tips") or [], max_chars=1024)

    advice_left = {
        "name": "🎯 What went well",
        "value": pos_val if pos_val else "—",
        "inline": True
    }
    advice_right = {
        "name": "🧱 What to work on",
        "value": neg_val if neg_val else "—",
        "inline": True
    }

    fields = []
    fields.extend(meta_fields)
    fields.append(quick_field)
    fields.append(advice_left)
    fields.append(advice_right)

    if flags_val:
        fields.append({
            "name": "📌 Flagged behavior",
            "value": flags_val,
            "inline": False
        })

    if tips_val:
        fields.append({
            "name": "🗺️ Tips",
            "value": tips_val,
            "inline": False
        })

    # Optional highlight/lowlight capsule (very compact, only if present and room left)
    hl = result.get("highlight")
    ll = result.get("lowlight")
    if hl or ll:
        capsule = []
        if hl:
            capsule.append(f"🌟 Highlight: **{hl}**")
        if ll:
            capsule.append(f"⚠️ Lowlight: **{ll}**")
        fields.append({
            "name": "🧩 Summary",
            "value": " · ".join(capsule),
            "inline": False
        })

    # Footer with local time
    footer_text = f"Match ID: {result['matchId']} • {now.strftime('%b %d at %-I:%M %p')}" if result.get("matchId") else now.strftime('%b %d at %-I:%M %p')

    return {
        "title": title,
        "url": url,
        "description": "",
        "color": color,
        "fields": fields,
        "footer": {
            "text": footer_text
        },
        "timestamp": timestamp
    }
