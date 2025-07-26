import requests
import json
import time
import os
import random
from feedback_engine import generate_feedback
from feedback_catalog import FEEDBACK_LIBRARY

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# Load hero role and baseline data
with open("hero_roles.json", "r") as f:
    HERO_ROLES = json.load(f)

with open("hero_baselines.json", "r") as f:
    HERO_BASELINES = json.load(f)

HERO_BASELINE_MAP = {h["hero"]: h for h in HERO_BASELINES}

# ENV from GitHub Secrets
GIST_TOKEN = os.getenv("GIST_TOKEN")
GIST_ID = os.getenv("GIST_ID")

GIST_API_URL = f"https://api.github.com/gists/{GIST_ID}"
GIST_HEADERS = {
    "Authorization": f"token {GIST_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

TAG_MESSAGES = {
    "Smashed": [
        "smashed it.", "had damage numbers you screenshot.",
        "ran the game like a smurf.", "deleted cores for fun.",
        "queued to grief the enemy.", "should probably calm down.",
        "made space... for the morgue.", "styled on them. Pure ego gameplay."
    ],
    "Did Work": [
        "put in solid work.", "held the line.", "delivered the goods.",
        "showed up and clocked in.", "played like an adult.",
        "brought lunch and packed wards.", "kept it tidy.", "did their 20%. Respect."
    ],
    "Got Carried": [
        "got carried harder than a divine 5 in herald queue.",
        "watched the team win.", "still doesn't know what happened, but it’s a W.",
        "survived long enough to see victory.", "was emotional support.",
        "won by being present. Technically.", "contributed moral encouragement.",
        "rode the MMR elevator straight up."
    ],
    "Fed": [
        "fed like they were getting paid for it.", "kept the enemy carry well-fed.",
        "had more deaths than creeps.", "died for every ward and then some.",
        "looked like a turbo player in ranked.", "became part of the jungle rotation — for the enemy.",
        "was reverse couriering gold all game.", "had a direct portal to the fountain."
    ],
    "Support MVP": [
        "babysat like a professional nanny.", "put wards in every bush in the game.",
        "played the game on hard mode — support.", "kept the cores alive and ungrateful.",
        "set up every kill and took none.", "healed, stunned, died — support life.",
        "had more map awareness than the rest of the team combined.",
        "made the enemy jungle feel like a warzone."
    ],
    "Invisible": [
        "played with their monitor off.", "still loading into the game.",
        "took a vow of non-intervention.", "was on mute — and not just comms.",
        "queued up, got lost, came back post-game.", "farmed clarity potions in base.",
        "took the observer role literally.", "entered spectator mode mid-match."
    ],
    "Even Game": [
        "played an honest match.", "was neither the problem nor the solution.",
        "kept things balanced.", "had a mid-tier performance. Literally.",
        "showed up and clicked buttons.", "participated meaningfully. Kinda.",
        "made plays. Also made mistakes.", "was present and accounted for."
    ],
}

GROUP_FLAVOR_LINES = {
    "carry": [
        "{carry} queued for MMR. The others queued for the ride.",
        "{carry} solo’d the lobby while the stack took notes.",
        "{carry} carried harder than Divine 5 in Herald queue.",
        "Without {carry}, this would've been a Turbo loss.",
        "{carry} pressed the right buttons. No one else did."
    ],
    "feeder": [
        "{feeder} was the enemy team’s best initiator.",
        "The real MVP was {feeder} — for the other side.",
        "{feeder} kept it interesting by dying constantly.",
        "{feeder} fed more than bounty runes at minute zero.",
        "MMR loss sponsored by {feeder}’s life insurance policy."
    ],
    "carry_feeder": [
        "{carry} carried. {feeder}… was also there.",
        "{carry} ascended. {feeder} descended.",
        "{feeder} fell so {carry} could rise.",
        "{carry} popped off. {feeder} popped… repeatedly.",
        "{carry} got MVP. {feeder} got psychological damage."
    ],
    "support": [
        "{support} did everything but queue for the rest of them.",
        "{support} was the glue holding this tragedy together.",
        "{support} deserves danger pay.",
        "They won, because {support} refused to quit.",
        "{support} landed every spell. Still lost. Tragic."
    ],
    "all_good": [
        "Guild synergy too strong. Send harder enemies.",
        "Everyone showed up. Almost suspiciously competent.",
        "This stack moved like a pub stomp squad.",
        "Good Dota from everyone. What's going on here?",
        "They partied up — and everyone fragged. Rare footage."
    ],
    "all_bad": [
        "Full guild stack, full teamfeed experience.",
        "The enemy team said thanks for the MMR.",
        "Felt more like turbo warmups than real Dota.",
        "This one’s going straight into the 'we tried' folder.",
        "Everyone griefed equally. Beautiful, in a way."
    ],
    "chaos": [
        "One carried, one fed, one pinged. A classic trio.",
        "The stack had no draft, no plan, no shame.",
        "Like a pub, but louder. And with worse synergy.",
        "Drafted chaos. Executed chaos. Result: chaos.",
        "It was a Dota match. That's all we can confirm."
    ]
}

def get_score_tag(k, d, a, won):
    if (k + a >= 30 and d <= 5) or (k >= 20 and d <= 3):
        return "Smashed"
    elif (k + a >= 18 and d <= 8):
        return "Did Work"
    elif won and (k + a <= 5) and d >= 10:
        return "Got Carried"
    elif d >= 12 and (k + a) <= 8:
        return "Fed"
    elif a >= 18 and k < 5 and d <= 6:
        return "Support MVP"
    elif k == 0 and a == 0 and d <= 3:
        return "Invisible"
    else:
        return "Even Game"

def load_state():
    try:
        res = requests.get(GIST_API_URL, headers=GIST_HEADERS)
        if res.status_code != 200:
            print("⚠️ Failed to fetch state.json from Gist.")
            return {}
        content = res.json()["files"]["state.json"]["content"]
        return json.loads(content)
    except Exception as e:
        print("⚠️ Error loading state.json:", e)
        return {}

def save_state(state):
    try:
        payload = {
            "files": {
                "state.json": {
                    "content": json.dumps(state, indent=2)
                }
            }
        }
        res = requests.patch(GIST_API_URL, headers=GIST_HEADERS, json=payload)
        if res.status_code != 200:
            print("⚠️ Failed to update Gist:", res.text)
    except Exception as e:
        print("⚠️ Error saving to Gist:", e)

def get_latest_match(steam_id32):
    url = f"https://api.opendota.com/api/players/{steam_id32}/recentMatches"
    res = requests.get(url)
    if res.status_code != 200:
        print(f"Error fetching match for {steam_id32}: {res.text}")
        return None
    data = res.json()
    return data[0] if data else None

def group_flavor(players):
    smashed = [p for p in players if p['tag'] == "Smashed"]
    fed = [p for p in players if p['tag'] == "Fed"]
    support = [p for p in players if p['tag'] == "Support MVP"]

    if len(smashed) == 1 and len(fed) == 0:
        return random.choice(GROUP_FLAVOR_LINES["carry"]).format(carry=smashed[0]['name'])
    if len(fed) == 1 and len(smashed) == 0:
        return random.choice(GROUP_FLAVOR_LINES["feeder"]).format(feeder=fed[0]['name'])
    if len(smashed) == 1 and len(fed) == 1:
        return random.choice(GROUP_FLAVOR_LINES["carry_feeder"]).format(
            carry=smashed[0]['name'], feeder=fed[0]['name'])
    if len(support) == 1 and len(players) >= 2:
        return random.choice(GROUP_FLAVOR_LINES["support"]).format(support=support[0]['name'])
    if all(p['tag'] in ["Smashed", "Did Work"] for p in players):
        return random.choice(GROUP_FLAVOR_LINES["all_good"])
    if all(p['tag'] in ["Fed", "Invisible"] for p in players):
        return random.choice(GROUP_FLAVOR_LINES["all_bad"])
    return random.choice(GROUP_FLAVOR_LINES["chaos"])

def post_to_discord(message):
    if config.get("test_mode", False):
        print("TEST MODE ENABLED — would have posted:\n", message)
        return
    payload = {"content": message}
    r = requests.post(config['webhook_url'], json=payload)
    if r.status_code not in [200, 204]:
        print("⚠️ Failed to send message to Discord:", r.text)

def format_message(name, match):
    k, d, a = match['kills'], match['deaths'], match['assists']
    duration = time.strftime("%Mm%Ss", time.gmtime(match['duration']))
    match_url = f"https://www.opendota.com/matches/{match['match_id']}"

    is_radiant = match['player_slot'] < 128
    won = (match['radiant_win'] and is_radiant) or (not match['radiant_win'] and not is_radiant)
    result_emoji = "🟢" if won else "🔴"
    result_text = "Victory!" if won else "Defeat."

    tag = get_score_tag(k, d, a, won)
    tag_line = random.choice(TAG_MESSAGES[tag])

    msg = (
        f"{result_emoji} **{name}** went `{k}/{d}/{a}` — {tag_line}\n"
        f"**{result_text}** | ⏱ {duration}\n"
        f"🔗 {match_url}"
    )

    hero_name = match.get("hero_name")
    baseline = HERO_BASELINE_MAP.get(hero_name)
    roles = HERO_ROLES.get(hero_name, [])
    if baseline and roles:
        player_stats = {
            "kills": k,
            "deaths": d,
            "assists": a,
            "last_hits": match.get("last_hits", 0),
            "denies": match.get("denies", 0)
        }
        feedback = generate_feedback(player_stats, baseline, roles)
        msg += f"\n\n{feedback['title']}\n" + "\n".join(f"- {line}" for line in feedback['lines'])

    return msg

# Main loop
state = load_state()
matches = {}

for name, steam_id in config['players'].items():
    match = get_latest_match(steam_id)
    if not match:
        continue
    match_id = match['match_id']
    if str(steam_id) in state and state[str(steam_id)] == match_id:
        continue
    k, d, a = match['kills'], match['deaths'], match['assists']
    is_radiant = match['player_slot'] < 128
    won = (match['radiant_win'] and is_radiant) or (not match['radiant_win'] and not is_radiant)
    tag = get_score_tag(k, d, a, won)
    entry = {
        'name': name, 'id': steam_id, 'match': match,
        'tag': tag, 'k': k, 'd': d, 'a': a, 'won': won
    }
    matches.setdefault(match_id, []).append(entry)

for match_id, players in matches.items():
    if len(players) == 1:
        p = players[0]
        msg = format_message(p['name'], p['match'])
        post_to_discord(msg)
        state[str(p['id'])] = match_id
    else:
        names = [p['name'] for p in players]
        intro = f"🎮 {', '.join(names[:-1])} and {names[-1]} queued together!\n"
        lines = []
        for p in players:
            result_emoji = "🟢" if p['won'] else "🔴"
            line = f"{result_emoji} **{p['name']}** went `{p['k']}/{p['d']}/{p['a']}` — {random.choice(TAG_MESSAGES[p['tag']])}"
            lines.append(line)
        flavor = group_flavor(players)
        match_url = f"https://www.opendota.com/matches/{match_id}"
        message = intro + "\n".join(lines) + "\n\n" + f"🧠 {flavor}\n🔗 {match_url}"
        post_to_discord(message)
        for p in players:
            state[str(p['id'])] = match_id

save_state(state)
