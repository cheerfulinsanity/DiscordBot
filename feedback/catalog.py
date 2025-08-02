# feedback/catalog.py

# --- Phrasing for stat-based tags ---
PHRASE_BOOK = {
    "gpm": {
        "modes": ["NON_TURBO"],
        "positive": [
            "Excellent GPM — you farmed efficiently.",
            "You kept your gold income high the whole game."
        ],
        "negative": [
            "Your gold gain was too low — you need better farming patterns.",
            "Low GPM. Look at your downtime between fights and waves."
        ]
    },
    "xpm": {
        "modes": ["NON_TURBO"],
        "positive": [
            "Strong XPM — you stayed active and leveled well.",
            "Your experience gain was solid — good tempo."
        ],
        "negative": [
            "You fell behind on XP — stay active in fights and lanes.",
            "Low XPM — consider staying in lane longer or joining fights earlier."
        ]
    },
    "imp": {
        "positive": [
            "You had solid impact — your presence was felt.",
            "Strong game presence — you contributed meaningfully."
        ],
        "negative": [
            "Low impact — consider your positioning and spell usage.",
            "You struggled to affect key fights. Look at your map involvement."
        ]
    },
    "kills": {
        "positive": [
            "Great kill count — you secured the fights.",
            "You finished a lot of enemies. Clean execution."
        ],
        "negative": [
            "Low kill count — focus on target selection and spell timing.",
            "You struggled to finish kills. Think about follow-up opportunities."
        ]
    },
    "deaths": {
        "positive": [
            "Low deaths — you played safely and efficiently.",
            "Good survival — you stayed alive through pressure."
        ],
        "negative": [
            "Too many deaths — work on positioning and awareness.",
            "Frequent deaths slowed your momentum. Consider safer paths."
        ]
    },
    "assists": {
        "positive": [
            "High assist count — great team contribution.",
            "You backed up your team consistently. Nice support."
        ],
        "negative": [
            "Low assists — be more present in fights and rotations.",
            "You weren’t nearby for fights. Try to follow your core's moves."
        ]
    },
    "campStack": {
        "positive": [
            "You stacked well — strong support habits.",
            "Great use of downtime — jungle economy boosted."
        ],
        "negative": [
            "You didn’t stack much — it's a free way to help.",
            "No jungle stacks. Supports can create gold for others too."
        ]
    },
    "level": {
        "positive": [
            "High level gain — you scaled well.",
            "You stayed ahead in XP — good tempo management."
        ],
        "negative": [
            "You fell behind in XP — focus on staying active.",
            "Low level by midgame. Consider how you move between lanes."
        ]
    },
    "killParticipation": {
        "positive": [
            "Great kill participation — always involved.",
            "You contributed to nearly every fight. Team player."
        ],
        "negative": [
            "Low kill participation — missed too many engagements.",
            "You were often absent from fights. Stay more connected."
        ]
    }
}

# --- Phrasing for compound behavior tags ---
COMPOUND_FLAGS = {
    "farmed_did_nothing": {
        "modes": ["NON_TURBO"],
        "lines": [
            "You farmed well, but didn’t convert it into pressure.",
            "High GPM with low impact. Work on map presence."
        ]
    },
    "no_stacking_support": {
        "lines": [
            "Zero stacks as support — use quiet moments to help your cores.",
            "If nothing's happening, go stack jungle camps."
        ]
    },
    "low_kp": {
        "lines": [
            "Low fight involvement — too much solo play.",
            "You missed too many engagements. Stay tighter to team."
        ]
    },
    "fed_no_impact": {
        "lines": [
            "High deaths with little impact — try defensive items or safer paths.",
            "Died too often without contributing — rethink your timing."
        ]
    },
    "impact_without_farm": {
        "modes": ["NON_TURBO"],
        "lines": [
            "Low gold, high impact — great support effort.",
            "Even without much farm, you made it count."
        ]
    },
    "fed_early": {
        "lines": [
            "Rough start — early deaths set you back hard.",
            "You fed early and never recovered. Focus on safer lanes."
        ]
    },
    "no_neutral_item": {
        "lines": [
            "You didn’t equip a neutral item — that’s free power.",
            "No neutral item found — check drops more closely."
        ]
    },
    "hoarded_gold": {
        "lines": [
            "You sat on a lot of gold. Consider spending earlier.",
            "Holding too much gold — buy impact items sooner."
        ]
    },
    "lane_violation": {
        "lines": [
            "As support, don’t take core lanes like mid or jungle.",
            "Lane assignment mismatch — make sure your role fits your lane."
        ]
    },
    "intentional_feeder": {
        "lines": [
            "Multiple intentional feeds detected. That’s not it chief.",
            "This game had griefing behavior. Not a good look."
        ]
    }
}

# --- Strategic tips triggered by stat tag presence ---
TIP_LINES = {
    "campStack": {
        "text": "Try to stack during quiet moments — it adds up quickly.",
        "modes": ["ALL"]
    },
    "deaths": {
        "text": "Use your minimap more aggressively to avoid blind deaths.",
        "modes": ["ALL"]
    },
    "killParticipation": {
        "text": "Stay closer to your team during skirmishes.",
        "modes": ["ALL"]
    },
    "gpm": {
        "text": "Push waves before jungling to get more out of rotations.",
        "modes": ["NON_TURBO"]
    },
    "assists": {
        "text": "Buy items that reward teamplay — glimmers, greaves, etc.",
        "modes": ["ALL"]
    },
    "xpm": {
        "text": "Look for tomes, XP runes, and split-pushing to boost levels.",
        "modes": ["NON_TURBO"]
    },
    "kills": {
        "text": "Think about kill angles before fights — who can you burst?",
        "modes": ["ALL"]
    },
    "level": {
        "text": "XP isn’t just from kills — soak waves, jungle, and fight.",
        "modes": ["ALL"]
    }
}
