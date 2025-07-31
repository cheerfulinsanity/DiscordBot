# feedback/catalog.py

# Tiered feedback phrasing per stat
PHRASE_BOOK = {
    "gpm": {
        "mild": [
            "Farm was okay — not terrible, not amazing (+{delta:.0f}%)",
            "Slight gold advantage — keep optimizing rotations (+{delta:.0f}%)"
        ],
        "strong": [
            "Solid gold gain. Lane and jungle use was efficient (+{delta:.0f}%)",
            "You farmed well — look at how you pushed ahead (+{delta:.0f}%)"
        ],
        "extreme": [
            "Incredible GPM — you outpaced the enemy cores (+{delta:.0f}%)",
            "Gold machine. This was a farm diff (+{delta:.0f}%)"
        ]
    },
    "imp": {
        "mild": ["Had some impact, especially midgame (+{delta:.0f}% IMP)"],
        "strong": ["Strong influence across fights (+{delta:.0f}% IMP)"],
        "extreme": ["Dominated the game — high impact throughout (+{delta:.0f}% IMP)"]
    },
    "deaths": {
        "mild": ["A bit death-heavy — stay tighter to team next time (-{delta:.0f}%)"],
        "strong": ["Too many deaths. Think about position and map awareness (-{delta:.0f}%)"],
        "extreme": ["Severe feeding — rethink your engagements (-{delta:.0f}%)"]
    },
    "campStack": {
        "mild": ["Minimal stacking. Look for downtime to stack more (+{delta:.0f}%)"],
        "strong": ["Good stacking game — nice support efficiency (+{delta:.0f}%)"],
        "extreme": ["Excellent stacking — you juiced the jungle (+{delta:.0f}%)"]
    },
    "killParticipation": {
        "mild": ["Some fight presence — room to be more involved (+{delta:.0f}%)"],
        "strong": ["High participation — you showed up when it counted (+{delta:.0f}%)"],
        "extreme": ["Nearly every kill involved you. Team player (+{delta:.0f}%)"]
    }
}

# Phrases triggered by specific behavior tags
COMPOUND_FLAGS = {
    "farmed_did_nothing": [
        "You had farm but no impact. Focus more on fight timing and positioning.",
        "High GPM, low presence. Next time convert gold into pressure."
    ],
    "no_stacking_support": [
        "Very low stacks. If nothing's happening, get to the jungle and stack.",
        "Supports create space too — stacking helps your carry a lot."
    ],
    "low_kp": [
        "Low kill participation — be more active in team fights.",
        "You missed a lot of fights. Stay more connected to your team."
    ],
    "fed_no_impact": [
        "High deaths with little impact. Play safer when behind.",
        "Died a lot and didn’t turn fights. Focus on smarter positioning."
    ],
    "impact_without_farm": [
        "Low GPM, high impact — great support work.",
        "Not much gold, but you still contributed. Nice job."
    ]
}

# Optional tips based on delta patterns or missed roles
TIP_LINES = {
    "campStack": "Try to stack during quiet moments — it adds up quickly.",
    "deaths": "Use your minimap more aggressively to avoid blind deaths.",
    "killParticipation": "Stay closer to your team during skirmishes.",
    "gpm": "Push lanes before jungling to get more out of rotations."
}
