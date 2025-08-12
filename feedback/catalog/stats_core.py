# feedback/catalog/stats_core.py
# Core, mode-agnostic stats (non-economy)
PHRASE_BOOK = {
    "imp": {
        "positive": [
            "You had high impact — consistently contributed.",
            "Good influence in fights and objectives.",
            "You made your presence known every phase.",
            "You pressured effectively with rotations.",
            "Clutch spell usage raised your impact rating."
        ],
        "negative": [
            "Low impact — try joining fights earlier.",
            "You didn’t affect enough team fights.",
            "Poor positioning or usage limited your presence.",
            "You were alive but distant. Find better angles.",
            "Minimal influence on momentum shifts."
        ]
    },
    "kills": {
        "positive": [
            "You secured key kills — well played.",
            "Strong kill count — you punished mistakes.",
            "You finished targets reliably.",
            "You were a finisher in most fights.",
            "Great kill score — you set the pace."
        ],
        "negative": [
            "Low kill count — try to connect better in fights.",
            "You couldn’t secure kills — look for squishier targets.",
            "Lack of damage or poor timing hurt kill chances.",
            "Missed follow-ups cost kill opportunities.",
            "Your hero wasn’t threatening enough."
        ]
    },
    "deaths": {
        "positive": [
            "Low death count — good survival instincts.",
            "Stayed alive through pressure — smart plays.",
            "Strong positioning kept you safe.",
            "Good use of defensive items or escapes.",
            "You gave away little gold — efficient survival."
        ],
        "negative": [
            "Too many deaths — work on map awareness.",
            "You fed heavily — reconsider your movement paths.",
            "Deaths stacked up and hurt your impact.",
            "You respawned too often to stay relevant.",
            "Getting picked off delayed your team’s plans."
        ]
    },
    "assists": {
        "positive": [
            "High assist count — you supported well.",
            "Great backup — you enabled your cores.",
            "You showed up when needed. Reliable.",
            "Clean team play — you were involved.",
            "Good vision and follow-up boosted assists."
        ],
        "negative": [
            "Low assists — not enough presence in fights.",
            "You weren’t with your team during engagements.",
            "No impact on your allies’ kills.",
            "You arrived late or missed team rotations.",
            "Your hero wasn’t enabling your team enough."
        ]
    },
    "level": {
        "positive": [
            "You kept your level up with the pace.",
            "Fast leveling — good XP decisions.",
            "You stayed relevant throughout the game.",
            "You scaled naturally with the game tempo.",
            "Well-distributed XP gains."
        ],
        "negative": [
            "You were underleveled much of the game.",
            "Not enough time in XP zones.",
            "Low impact due to slow scaling.",
            "XP gain lagged behind lane partner.",
            "Level deficit held back your spell timings."
        ]
    },
    "killParticipation": {
        "positive": [
            "You were active in fights — great presence.",
            "High kill participation — team player.",
            "Always showed up when needed.",
            "You followed the team’s tempo well.",
            "Tight coordination led to shared kills."
        ],
        "negative": [
            "Low participation — disconnected from team.",
            "You weren’t present for most kills.",
            "You missed too many fights.",
            "Slow rotations led to missed fights.",
            "Team fought without you too often."
        ]
    },
}
