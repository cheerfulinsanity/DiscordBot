# feedback/catalog.py

# Tiered feedback phrasing per stat, with allowed game modes
PHRASE_BOOK = {
    "gpm": {
        "modes": ["NON_TURBO"],
        "tiers": {
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
        }
    },
    "xpm": {
        "modes": ["NON_TURBO"],
        "tiers": {
            "mild": [
                "Reasonable XP gain (+{delta:.0f}%) — steady flow."
            ],
            "strong": [
                "Strong XPM — you were always in the action (+{delta:.0f}%)"
            ],
            "extreme": [
                "Explosive XP rate — constant fights and pushes (+{delta:.0f}%)"
            ]
        }
    },
    "imp": {
        "tiers": {
            "mild": [
                "Had some impact, especially midgame (+{delta:.0f}% IMP)"
            ],
            "strong": [
                "Strong influence across fights (+{delta:.0f}% IMP)"
            ],
            "extreme": [
                "Dominated the game — high impact throughout (+{delta:.0f}% IMP)"
            ]
        }
    },
    "deaths": {
        "tiers": {
            "mild": [
                "A bit death-heavy — stay tighter to team next time (-{delta:.0f}%)"
            ],
            "strong": [
                "Too many deaths. Think about position and map awareness (-{delta:.0f}%)"
            ],
            "extreme": [
                "Severe feeding — rethink your engagements (-{delta:.0f}%)"
            ]
        }
    },
    "campStack": {
        "tiers": {
            "mild": [
                "Minimal stacking. Look for downtime to stack more (+{delta:.0f}%)"
            ],
            "strong": [
                "Good stacking game — nice support efficiency (+{delta:.0f}%)"
            ],
            "extreme": [
                "Excellent stacking — you juiced the jungle (+{delta:.0f}%)"
            ]
        }
    },
    "killParticipation": {
        "tiers": {
            "mild": [
                "Some fight presence — room to be more involved (+{delta:.0f}%)"
            ],
            "strong": [
                "High participation — you showed up when it counted (+{delta:.0f}%)"
            ],
            "extreme": [
                "Nearly every kill involved you. Team player (+{delta:.0f}%)"
            ]
        }
    },
    "assists": {
        "tiers": {
            "mild": [
                "Some solid assists (+{delta:.0f}%) — you backed up your team."
            ],
            "strong": [
                "You were setting up kills consistently (+{delta:.0f}%)"
            ],
            "extreme": [
                "Assist god — you enabled everyone (+{delta:.0f}%)"
            ]
        }
    },
    "kills": {
        "tiers": {
            "mild": [
                "Picked up a few kills (+{delta:.0f}%) — nice pickoffs."
            ],
            "strong": [
                "Reliable finisher — strong kill count (+{delta:.0f}%)"
            ],
            "extreme": [
                "Slaughtered them. You were the carry (+{delta:.0f}%)"
            ]
        }
    },
    "level": {
        "tiers": {
            "mild": [
                "Respectable leveling pace (+{delta:.0f}%)"
            ],
            "strong": [
                "You leveled fast — good fight participation and XP usage (+{delta:.0f}%)"
            ],
            "extreme": [
                "XP king — massive level lead (+{delta:.0f}%)"
            ]
        }
    }
}

# Phrases triggered by specific behavior tags
COMPOUND_FLAGS = {
    "farmed_did_nothing": {
        "modes": ["NON_TURBO"],
        "lines": [
            "You had farm but no impact. Focus more on fight timing and positioning.",
            "High GPM, low presence. Next time convert gold into pressure."
        ]
    },
    "no_stacking_support": {
        "lines": [
            "Very low stacks. If nothing's happening, get to the jungle and stack.",
            "Supports create space too — stacking helps your carry a lot."
        ]
    },
    "low_kp": {
        "lines": [
            "Low kill participation — be more active in team fights.",
            "You missed a lot of fights. Stay more connected to your team."
        ]
    },
    "fed_no_impact": {
        "lines": [
            "High deaths with little impact. Play safer when behind.",
            "Died a lot and didn’t turn fights. Focus on smarter positioning."
        ]
    },
    "impact_without_farm": {
        "modes": ["NON_TURBO"],
        "lines": [
            "Low GPM, high impact — great support work.",
            "Not much gold, but you still contributed. Nice job."
        ]
    }
}

# Optional tips based on delta patterns or missed roles
TIP_LINES = {
    "campStack": {
        "text": "Try to stack during quiet moments — it adds up quickly."
    },
    "deaths": {
        "text": "Use your minimap more aggressively to avoid blind deaths."
    },
    "killParticipation": {
        "text": "Stay closer to your team during skirmishes."
    },
    "gpm": {
        "modes": ["NON_TURBO"],
        "text": "Push lanes before jungling to get more out of rotations."
    },
    "assists": {
        "text": "Consider buying utility items that scale with assists."
    },
    "xpm": {
        "modes": ["NON_TURBO"],
        "text": "Aim for XP runes and split-push waves for faster scaling."
    }
}
