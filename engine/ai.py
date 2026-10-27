"""
AI Opponent Engine for Texas Hold'em Poker.
Includes distinct player personalities, pot odds evaluation, draw detection,
and balanced bluffing heuristics.
"""
import random
from typing import List, Tuple, Optional
from .card import Card, Rank, Suit
from .evaluator import evaluate_hand, HandCategory, HandRank


class AIPersonality:
    def __init__(self, name: str, title: str, avatar: str, aggression: float, looseness: float, bluff_rate: float):
        self.name = name
        self.title = title
        self.avatar = avatar
        self.aggression = aggression    # 0.0 to 1.0 (tendency to bet/raise vs check/call)
        self.looseness = looseness      # 0.0 to 1.0 (willingness to play marginal hands)
        self.bluff_rate = bluff_rate    # 0.0 to 1.0 (frequency of bluffing with weak hands)


BOT_PERSONALITIES = [
    AIPersonality(
        name="Viktor",
        title="O Rochedo (Tight-Aggressive)",
        avatar="👨‍💼",
        aggression=0.75,
        looseness=0.25,
        bluff_rate=0.08
    ),
    AIPersonality(
        name="Elena",
        title="Rainha do Blefe (Loose-Aggressive)",
        avatar="👩‍🦰",
        aggression=0.85,
        looseness=0.70,
        bluff_rate=0.35
    ),
    AIPersonality(
        name="Marco",
        title="O Xerife (Calling Station)",
        avatar="🤠",
        aggression=0.30,
        looseness=0.80,
        bluff_rate=0.05
    ),
    AIPersonality(
        name="Sofia",
        title="A Mestre (GTO Pro)",
        avatar="👩‍💻",
        aggression=0.65,
        looseness=0.50,
        bluff_rate=0.20
    )
]


def score_preflop(c1: Card, c2: Card) -> float:
    """
    Simplified Chen formula / preflop strength metric (approx 0 to 20).
    High pairs (AA=20, KK=16, etc.), suited bonus, connectedness bonus.
    """
    r1, r2 = max(c1.rank.value, c2.rank.value), min(c1.rank.value, c2.rank.value)
    score = 0.0

    # Base score on high card
    base_scores = {
        14: 10, 13: 8, 12: 7, 11: 6, 10: 5,
        9: 4.5, 8: 4, 7: 3.5, 6: 3, 5: 2.5, 4: 2, 3: 1.5, 2: 1
    }
    score = base_scores.get(r1, 1.0)

    # Pair bonus
    if r1 == r2:
        score = max(score * 2, 5.0)
        if r1 >= 10:  # TT+
            score += 4.0
        return score

    # Suited bonus
    if c1.suit == c2.suit:
        score += 2.0

    # Gap penalty
    gap = r1 - r2 - 1
    if gap == 0:
        score += 1.0  # Connected
    elif gap == 1:
        score -= 1.0
    elif gap == 2:
        score -= 2.0
    elif gap >= 3:
        score -= 4.0

    return max(0.0, score)


def count_draw_outs(hole_cards: List[Card], community_cards: List[Card]) -> int:
    """Estimate draw outs (flush draws, straight draws) after flop or turn."""
    if len(community_cards) not in (3, 4):
        return 0

    all_cards = hole_cards + community_cards
    outs = 0

    # Flush draw check
    suit_counts = {}
    for c in all_cards:
        suit_counts[c.suit] = suit_counts.get(c.suit, 0) + 1
    for count in suit_counts.values():
        if count == 4:
            outs += 9  # 9 remaining cards of that suit

    # Straight draw check
    ranks = sorted(set(c.rank.value for c in all_cards))
    # Add Ace as 1 if present
    if 14 in ranks:
        ranks = [1] + ranks

    for i in range(len(ranks) - 3):
        span = ranks[i+3] - ranks[i]
        if span == 3:
            outs += 8  # Open-ended straight draw
            break
        elif span == 4:
            outs += 4  # Gutshot straight draw
            break

    return min(outs, 15)


def decide_action(
    personality: AIPersonality,
    hole_cards: List[Card],
    community_cards: List[Card],
    current_bet: int,
    player_current_bet: int,
    player_chips: int,
    pot_total: int,
    min_raise: int,
    big_blind: int
) -> Tuple[str, int]:
    """
    Decides the AI's action.
    Returns (action_name, amount) where action_name is one of:
    - 'fold', 0
    - 'check', 0
    - 'call', call_amount
    - 'raise', total_bet_amount
    """
    to_call = current_bet - player_current_bet
    can_check = (to_call == 0)

    # 1. PRE-FLOP DECISION
    if not community_cards:
        pf_score = score_preflop(hole_cards[0], hole_cards[1])
        # Looseness lowers requirement to play
        threshold = 7.0 - (personality.looseness * 4.0)

        # Bluff roll
        bluffing = random.random() < personality.bluff_rate

        # Strong hand (AA, KK, QQ, AK, etc.)
        if pf_score >= 12.0:
            if player_chips > 0 and random.random() < personality.aggression:
                # Raise 2.5x to 4x BB
                raise_size = max(current_bet + min_raise, current_bet + int(big_blind * random.uniform(2.5, 4.0)))
                raise_amount = min(player_chips + player_current_bet, raise_size)
                return ("raise", raise_amount)
            return ("call", min(to_call, player_chips)) if to_call > 0 else ("check", 0)

        # Playable hand
        if pf_score >= threshold or bluffing:
            if to_call == 0:
                # Sometimes raise if aggressive
                if random.random() < (personality.aggression * 0.4):
                    raise_size = max(current_bet + min_raise, current_bet + big_blind * 2)
                    return ("raise", min(player_chips + player_current_bet, raise_size))
                return ("check", 0)
            elif to_call <= big_blind * 3 or (to_call <= player_chips * 0.1):
                if bluffing and random.random() < personality.aggression:
                    raise_size = current_bet + min_raise
                    return ("raise", min(player_chips + player_current_bet, raise_size))
                return ("call", min(to_call, player_chips))
            else:
                # Bet is large preflop
                if pf_score >= 10.0:
                    return ("call", min(to_call, player_chips))
                return ("fold", 0)

        # Weak hand preflop
        if can_check:
            return ("check", 0)
        return ("fold", 0)

    # 2. POST-FLOP DECISION (Flop, Turn, River)
    all_cards = hole_cards + community_cards
    eval_result: HandRank = evaluate_hand(all_cards)
    hand_cat = eval_result.category
    outs = count_draw_outs(hole_cards, community_cards)

    # Pot odds calculation
    pot_after_call = pot_total + to_call
    pot_odds = to_call / pot_after_call if pot_after_call > 0 else 0.0

    # Draw equity estimation (Rule of 4 & 2)
    cards_to_come = 2 if len(community_cards) == 3 else (1 if len(community_cards) == 4 else 0)
    draw_equity = (outs * 4 if cards_to_come == 2 else outs * 2) / 100.0

    bluffing = random.random() < (personality.bluff_rate * 0.7)

    # Monster hands (Full house, Quads, Flush, Straight, Set)
    if hand_cat >= HandCategory.THREE_OF_A_KIND:
        if random.random() < personality.aggression:
            # Bet or raise 50% - 100% of pot
            target_raise = current_bet + max(min_raise, int(pot_total * random.uniform(0.5, 0.85)))
            return ("raise", min(player_chips + player_current_bet, target_raise))
        if to_call > 0:
            return ("call", min(to_call, player_chips))
        return ("check", 0)

    # Two Pair
    if hand_cat == HandCategory.TWO_PAIR:
        if to_call == 0:
            if random.random() < personality.aggression:
                target_raise = current_bet + max(min_raise, int(pot_total * 0.5))
                return ("raise", min(player_chips + player_current_bet, target_raise))
            return ("check", 0)
        else:
            if to_call <= pot_total * 0.75 or to_call <= player_chips * 0.4:
                return ("call", min(to_call, player_chips))
            return ("fold", 0)

    # One Pair
    if hand_cat == HandCategory.ONE_PAIR:
        # Check if top pair
        top_community_rank = max(c.rank.value for c in community_cards)
        pair_rank = eval_result.tie_breakers[0] if eval_result.tie_breakers else 0
        is_top_pair = pair_rank >= top_community_rank

        if can_check:
            if is_top_pair and random.random() < (personality.aggression * 0.6):
                target_raise = current_bet + max(min_raise, int(pot_total * 0.4))
                return ("raise", min(player_chips + player_current_bet, target_raise))
            return ("check", 0)
        else:
            # Call reasonable bets with top/middle pair
            if is_top_pair or personality.looseness > 0.6:
                if to_call <= pot_total * 0.5 or to_call <= big_blind * 4:
                    return ("call", min(to_call, player_chips))
            elif to_call <= big_blind * 2:
                return ("call", min(to_call, player_chips))
            return ("fold", 0)

    # Strong Draw (Flush draw or open straight draw with 8+ outs)
    if outs >= 8 and cards_to_come > 0:
        if can_check:
            # Semi-bluff occasionally
            if bluffing and random.random() < personality.aggression:
                target_raise = current_bet + max(min_raise, int(pot_total * 0.5))
                return ("raise", min(player_chips + player_current_bet, target_raise))
            return ("check", 0)
        else:
            # Call if pot odds favorable or reasonable
            if draw_equity >= pot_odds * 0.8 or to_call <= pot_total * 0.35:
                return ("call", min(to_call, player_chips))
            return ("fold", 0)

    # Pure Bluff attempt on River or checked pots
    if bluffing and random.random() < personality.aggression:
        if can_check and random.random() < 0.4:
            target_raise = current_bet + max(min_raise, int(pot_total * 0.45))
            return ("raise", min(player_chips + player_current_bet, target_raise))

    # Weak hand / Nothing
    if can_check:
        return ("check", 0)
    return ("fold", 0)
