"""
Poker Hand Evaluator (Texas Hold'em 7-card and 5-card evaluation).
Mathematically precise ranking with kickers and Portuguese descriptions.
"""
from enum import IntEnum
from itertools import combinations
from typing import List, Tuple, Dict, Optional
from .card import Card, Rank, Suit


class HandCategory(IntEnum):
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

    @property
    def pt_name(self) -> str:
        return {
            HandCategory.HIGH_CARD: "Carta Alta",
            HandCategory.ONE_PAIR: "Um Par",
            HandCategory.TWO_PAIR: "Dois Pares",
            HandCategory.THREE_OF_A_KIND: "Trinca",
            HandCategory.STRAIGHT: "Sequência (Straight)",
            HandCategory.FLUSH: "Flush",
            HandCategory.FULL_HOUSE: "Full House",
            HandCategory.FOUR_OF_A_KIND: "Quadra",
            HandCategory.STRAIGHT_FLUSH: "Straight Flush",
            HandCategory.ROYAL_FLUSH: "Royal Flush",
        }[self]


class HandRank:
    def __init__(self, category: HandCategory, tie_breakers: Tuple[int, ...], description: str, best_cards: List[Card]):
        self.category = category
        self.tie_breakers = tie_breakers
        self.description = description
        self.best_cards = best_cards

    @property
    def score_tuple(self) -> Tuple:
        return (int(self.category),) + self.tie_breakers

    def __lt__(self, other: "HandRank") -> bool:
        if not isinstance(other, HandRank):
            return NotImplemented
        return self.score_tuple < other.score_tuple

    def __le__(self, other: "HandRank") -> bool:
        return self < other or self == other

    def __gt__(self, other: "HandRank") -> bool:
        if not isinstance(other, HandRank):
            return NotImplemented
        return self.score_tuple > other.score_tuple

    def __ge__(self, other: "HandRank") -> bool:
        return self > other or self == other

    def __eq__(self, other: "HandRank") -> bool:
        if not isinstance(other, HandRank):
            return False
        return self.score_tuple == other.score_tuple

    def to_dict(self) -> dict:
        return {
            "category": int(self.category),
            "category_name": self.category.pt_name,
            "description": self.description,
            "best_cards": [c.to_dict() for c in self.best_cards],
            "score": list(self.score_tuple)
        }

    def __repr__(self) -> str:
        return f"<HandRank {self.category.name}: {self.description}>"


def evaluate_5_cards(cards: List[Card]) -> HandRank:
    """Evaluates an exact 5-card combination."""
    if len(cards) != 5:
        raise ValueError("Exatamente 5 cartas são necessárias para evaluate_5_cards.")

    # Sort descending by rank
    sorted_cards = sorted(cards, key=lambda c: c.rank.value, reverse=True)
    ranks = [c.rank.value for c in sorted_cards]
    suits = [c.suit for c in sorted_cards]
    is_flush = len(set(suits)) == 1

    # Check for straight
    # Standard check: differences of 1
    is_straight = False
    straight_high = 0

    if ranks == list(range(ranks[0], ranks[0] - 5, -1)):
        is_straight = True
        straight_high = ranks[0]
    elif ranks == [14, 5, 4, 3, 2]:  # Ace-low wheel straight (A-2-3-4-5)
        is_straight = True
        straight_high = 5  # High card of wheel is 5

    # Count rank frequencies
    rank_counts: Dict[int, int] = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1

    # Group ranks by count then by rank value descending
    # Example: [Rank.ACE: 2, Rank.KING: 2, Rank.JACK: 1] -> [(2, 14), (2, 13), (1, 11)]
    grouped_counts = sorted(
        rank_counts.items(),
        key=lambda item: (item[1], item[0]),
        reverse=True
    )
    counts = [item[1] for item in grouped_counts]
    ordered_ranks = [item[0] for item in grouped_counts]

    # Map rank value to Portuguese name
    def r_name(v: int) -> str:
        for r in Rank:
            if r.value == v:
                return r.pt_name
        return str(v)

    # 1. Royal Flush & Straight Flush
    if is_flush and is_straight:
        if straight_high == 14:
            desc = f"Royal Flush ({suits[0].pt_name})"
            return HandRank(HandCategory.ROYAL_FLUSH, (14,), desc, sorted_cards)
        else:
            desc = f"Straight Flush até {r_name(straight_high)} ({suits[0].pt_name})"
            return HandRank(HandCategory.STRAIGHT_FLUSH, (straight_high,), desc, sorted_cards)

    # 2. Four of a Kind
    if counts == [4, 1]:
        quad_rank = ordered_ranks[0]
        kicker = ordered_ranks[1]
        desc = f"Quadra de {r_name(quad_rank)} com kicker {r_name(kicker)}"
        return HandRank(HandCategory.FOUR_OF_A_KIND, (quad_rank, kicker), desc, sorted_cards)

    # 3. Full House
    if counts == [3, 2]:
        triple = ordered_ranks[0]
        pair = ordered_ranks[1]
        desc = f"Full House de {r_name(triple)} com {r_name(pair)}"
        return HandRank(HandCategory.FULL_HOUSE, (triple, pair), desc, sorted_cards)

    # 4. Flush
    if is_flush:
        desc = f"Flush de {r_name(ranks[0])} ({suits[0].pt_name})"
        return HandRank(HandCategory.FLUSH, tuple(ranks), desc, sorted_cards)

    # 5. Straight
    if is_straight:
        desc = f"Sequência até {r_name(straight_high)}"
        return HandRank(HandCategory.STRAIGHT, (straight_high,), desc, sorted_cards)

    # 6. Three of a Kind
    if counts == [3, 1, 1]:
        triple = ordered_ranks[0]
        kickers = (ordered_ranks[1], ordered_ranks[2])
        desc = f"Trinca de {r_name(triple)} com kicker {r_name(kickers[0])}"
        return HandRank(HandCategory.THREE_OF_A_KIND, (triple,) + kickers, desc, sorted_cards)

    # 7. Two Pair
    if counts == [2, 2, 1]:
        p1 = max(ordered_ranks[0], ordered_ranks[1])
        p2 = min(ordered_ranks[0], ordered_ranks[1])
        kicker = ordered_ranks[2]
        desc = f"Dois Pares, {r_name(p1)} e {r_name(p2)} com kicker {r_name(kicker)}"
        return HandRank(HandCategory.TWO_PAIR, (p1, p2, kicker), desc, sorted_cards)

    # 8. One Pair
    if counts == [2, 1, 1, 1]:
        p = ordered_ranks[0]
        kickers = tuple(ordered_ranks[1:4])
        desc = f"Par de {r_name(p)} com kicker {r_name(kickers[0])}"
        return HandRank(HandCategory.ONE_PAIR, (p,) + kickers, desc, sorted_cards)

    # 9. High Card
    desc = f"Carta Alta {r_name(ranks[0])} com kicker {r_name(ranks[1])}"
    return HandRank(HandCategory.HIGH_CARD, tuple(ranks), desc, sorted_cards)


def evaluate_hand(cards: List[Card]) -> HandRank:
    """
    Evaluates any hand of 5 to 7 cards by finding the combination of 5
    that produces the highest HandRank.
    """
    if len(cards) < 5:
        # Preflop or Flop partial evaluation
        # Sort descending
        sorted_cards = sorted(cards, key=lambda c: c.rank.value, reverse=True)
        ranks = [c.rank.value for c in sorted_cards]
        # Check pairs in partial
        rank_counts: Dict[int, int] = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        grouped = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        if grouped and grouped[0][1] >= 2:
            r_val = grouped[0][0]
            for r in Rank:
                if r.value == r_val:
                    return HandRank(HandCategory.ONE_PAIR, (r_val,), f"Par de {r.pt_name}", sorted_cards)
        top = sorted_cards[0] if sorted_cards else None
        top_name = top.rank.pt_name if top else ""
        return HandRank(HandCategory.HIGH_CARD, tuple(ranks), f"Carta Alta {top_name}", sorted_cards)

    best_rank: Optional[HandRank] = None
    for combo in combinations(cards, 5):
        combo_rank = evaluate_5_cards(list(combo))
        if best_rank is None or combo_rank > best_rank:
            best_rank = combo_rank

    return best_rank
