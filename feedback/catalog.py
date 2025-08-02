# feedback/catalog.py

# --- Phrasing for stat-based tags ---
PHRASE_BOOK = {
    "gpm": {
        "modes": ["NON_TURBO"],
        "positive": [
            "Excellent GPM — you farmed efficiently.",
            "Gold income stayed high throughout the game.",
            "Your farming patterns were clean and effective.",
            "You hit item timings fast — solid GPM.",
            "You created a net worth lead early and built on it."
        ],
        "negative": [
            "Your GPM was too low — optimize farming routes.",
            "You struggled to gain gold — check jungle efficiency.",
            "Low farm output. Try to split push or rotate better.",
            "Gold income never took off — focus on creep waves.",
            "You didn’t convert time into gold effectively."
        ]
    },
    "xpm": {
        "modes": ["NON_TURBO"],
        "positive": [
            "Great XPM — you scaled quickly.",
            "Strong tempo — you leveled ahead of pace.",
            "You gained XP reliably throughout the match.",
            "High uptime in fights and lane helped your XP.",
            "Good wave presence — XP flowed naturally."
        ],
        "negative": [
            "Slow XP gain — stay in lane longer or rotate smarter.",
            "You fell behind in levels early.",
            "Low XPM suggests too much idle time.",
            "Try to be near kills and soak wave XP more often.",
            "You didn’t match the pace of the game’s XP curve."
        ]
    },
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
    "campStack": {
        "positive": [
            "Good stacking — you created farm opportunities.",
            "Smart support play — you stacked efficiently.",
            "You made the jungle profitable.",
            "Excellent use of downtime for stacks.",
            "Carry appreciated your jungle work."
        ],
        "negative": [
            "No jungle stacks — missed value as support.",
            "You didn’t help your cores farm faster.",
            "Downtime wasn’t used productively.",
            "Supports should stack — it snowballs cores.",
            "You skipped a fundamental support habit."
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
    }
}

# --- Behavior-based flags ---
COMPOUND_FLAGS = {
    "farmed_did_nothing": {
        "modes": ["NON_TURBO"],
        "lines": [
            "You farmed well, but didn’t convert it into pressure.",
            "High GPM with low impact. Work on map presence.",
            "Farm isn’t enough — your gold did nothing.",
            "You were rich, but invisible. Time to fight."
        ]
    },
    "no_stacking_support": {
        "lines": [
            "Zero stacks as support — use quiet moments to help your cores.",
            "You forgot to stack. Big value lost for your carry.",
            "Supports must stack. It's expected.",
            "Jungle economy was untouched. Missed role responsibility."
        ]
    },
    "low_kp": {
        "lines": [
            "Low fight involvement — too much solo play.",
            "You missed key fights. Watch your minimap more.",
            "The team fought without you. Try shadowing your core.",
            "Your absence hurt team engagements."
        ]
    },
    "fed_no_impact": {
        "lines": [
            "Died too much with nothing to show. That’s a liability.",
            "High deaths, low contribution — rethink your fights.",
            "Feeding without pressure — brutal combo.",
            "Try to die for a reason, not just habit."
        ]
    },
    "impact_without_farm": {
        "modes": ["NON_TURBO"],
        "lines": [
            "Great contribution with low gold — excellent support play.",
            "Low farm, big impact. Well played.",
            "You squeezed value out of little. Smart support instincts.",
            "Minimal gold, maximum presence. Impressive."
        ]
    },
    "fed_early": {
        "lines": [
            "Rough early game — multiple deaths put you behind.",
            "Fed early and never recovered. Be more cautious.",
            "Your lane was a disaster — bounce back next time.",
            "Early feed snowballed the enemy. Rethink lane safety."
        ]
    },
    "no_neutral_item": {
        "lines": [
            "You didn’t equip a neutral item — that’s free power.",
            "No neutral item found — check drops more closely.",
            "Missing neutral item all game. That’s just value lost."
        ]
    },
    "hoarded_gold": {
        "lines": [
            "You sat on a lot of gold. Consider spending earlier.",
            "Gold does nothing in your pocket. Buy items sooner.",
            "Delayed purchases slowed your timing.",
            "Big savings, small impact. Spend proactively."
        ]
    },
    "lane_violation": {
        "lines": [
            "As support, don’t take core lanes like mid or jungle.",
            "Lane assignment mismatch — don’t grief mid.",
            "Wrong lane for your role. Stick to the plan.",
            "Supports don’t need to jungle farm early. Let cores scale."
        ]
    },
    "intentional_feeder": {
        "lines": [
            "This game had griefing behavior. Not a good look.",
            "Multiple intentional feeds detected. Don't ruin games.",
            "Deliberate feeding ruins the experience for others.",
            "Please queue when you're ready to play."
        ]
    }
}

# --- Situational tip lines ---
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
        "text": "Push lanes before jungling to get more out of rotations.",
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

# --- Title phrasing banks for match performance summaries ---
TITLE_BOOK = {
    "win": {
        "legendary": [
            "obliterated the enemy team",
            "made it a highlight reel",
            "went god mode this match",
            "was on another level entirely",
            "absolutely shredded the opposition"
        ],
        "high": [
            "carried the game hard",
            "dominated from start to finish",
            "was unstoppable this game",
            "put the team on their back",
            "ran the tempo and the scoreboard"
        ],
        "mid": [
            "turned up when it counted",
            "played a solid hand in the win",
            "showed up when the team needed it",
            "made the difference in key moments",
            "was a reliable presence all game"
        ],
        "low": [
            "got carried but did enough",
            "was along for the ride",
            "survived the win",
            "kept up — barely",
            "was present, if not impactful"
        ],
        "very_low": [
            "won despite doing very little",
            "contributed nearly nothing, but still won",
            "was dead weight but the team prevailed",
            "didn’t throw hard enough to lose",
            "won — but it wasn’t your doing"
        ],
        "negative": [
            "won despite being a liability",
            "barely functioned this match",
            "was carried kicking and screaming",
            "was an anchor, not a sail",
            "somehow won despite everything"
        ]
    },
    "loss": {
        "legendary": [
            "put the team on their back and still lost",
            "was legendary even in defeat",
            "did everything — except win",
            "was a solo act in a tragedy",
            "outperformed everyone — but couldn’t carry harder"
        ],
        "high": [
            "was the only reason this was close",
            "fought hard in a losing battle",
            "did everything they could",
            "stood out despite the loss",
            "was a bright spot in a bad game"
        ],
        "mid": [
            "had some moments, but not enough",
            "played okay, but couldn’t turn the tide",
            "couldn’t shift momentum",
            "gave some hope, but not consistently",
            "contributed, but didn’t shine"
        ],
        "low": [
            "struggled to have impact",
            "couldn’t keep up",
            "got overwhelmed early",
            "never found their footing",
            "failed to turn up when needed"
        ],
        "very_low": [
            "was a major factor in the loss",
            "fed hard and lost the game",
            "had zero presence this match",
            "actively harmed the team effort",
            "sank the game with poor play"
        ],
        "negative": [
            "griefed their way to a loss",
            "made every mistake imaginable",
            "dragged the whole team down",
            "looked completely lost out there",
            "barely contributed to anything all game"
        ]
    }
}
