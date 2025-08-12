# feedback/catalog/flags.py
# Behavior-based flags (compound)
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
    },
    "slow_start": {
        "modes": ["ALL"],
        "lines": [
            "Took a while to get going — early impact was low but you found your footing later.",
            "Slow out of the gate, but improved as the match went on.",
            "Early game was quiet, but you made your presence felt in the mid to late game."
        ]
    },
    "late_game_falloff": {
        "modes": ["ALL"],
        "lines": [
            "Started strong but faded late — keep momentum into the final fights.",
            "Dominated early but couldn't maintain pressure late game.",
            "Great start, but the impact dropped off in the closing stages."
        ]
    }
}
