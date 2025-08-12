# feedback/catalog/stats_economy.py
# Economy/efficiency stats (gated to NON_TURBO where appropriate)
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
}
