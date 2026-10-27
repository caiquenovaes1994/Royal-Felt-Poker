"""
Card and Deck module for Texas Hold'em Poker.
Uses Deck of Cards CDN compatible notation.
"""
from enum import Enum, IntEnum
import random
from typing import List, Tuple


class Suit(Enum):
    SPADES = "S"      # ♠ Espadas
    HEARTS = "H"      # ♥ Copas
    DIAMONDS = "D"    # ♦ Ouros
    CLUBS = "C"       # ♣ Paus

    @property
    def symbol(self) -> str:
        return {
            Suit.SPADES: "♠",
            Suit.HEARTS: "♥",
            Suit.DIAMONDS: "♦",
            Suit.CLUBS: "♣"
        }[self]

    @property
    def pt_name(self) -> str:
        return {
            Suit.SPADES: "Espadas",
            Suit.HEARTS: "Copas",
            Suit.DIAMONDS: "Ouros",
            Suit.CLUBS: "Paus"
        }[self]

    @property
    def color(self) -> str:
        return "red" if self in (Suit.HEARTS, Suit.DIAMONDS) else "black"


class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    @property
    def code(self) -> str:
        if self == Rank.TEN:
            return "0"  # Deck of Cards API standard for 10
        elif self == Rank.JACK:
            return "J"
        elif self == Rank.QUEEN:
            return "Q"
        elif self == Rank.KING:
            return "K"
        elif self == Rank.ACE:
            return "A"
        return str(self.value)

    @property
    def label(self) -> str:
        if self == Rank.TEN:
            return "10"
        elif self == Rank.JACK:
            return "J"
        elif self == Rank.QUEEN:
            return "Q"
        elif self == Rank.KING:
            return "K"
        elif self == Rank.ACE:
            return "A"
        return str(self.value)

    @property
    def pt_name(self) -> str:
        return {
            Rank.TWO: "2",
            Rank.THREE: "3",
            Rank.FOUR: "4",
            Rank.FIVE: "5",
            Rank.SIX: "6",
            Rank.SEVEN: "7",
            Rank.EIGHT: "8",
            Rank.NINE: "9",
            Rank.TEN: "10",
            Rank.JACK: "Valete",
            Rank.QUEEN: "Dama",
            Rank.KING: "Rei",
            Rank.ACE: "Ás"
        }[self]


class Card:
    def __init__(self, rank: Rank, suit: Suit):
        self.rank = rank
        self.suit = suit

    @property
    def code(self) -> str:
        """Deck of Cards API code, e.g., 'AS', '0H', 'KD'."""
        return f"{self.rank.code}{self.suit.value}"

    @property
    def image_url(self) -> str:
        return f"https://deckofcardsapi.com/static/img/{self.code}.png"

    @property
    def svg_url(self) -> str:
        # Fallback jsdelivr SVG card
        # CardsJS uses 10S, AS, KS etc.
        rank_str = self.rank.label
        return f"https://cdn.jsdelivr.net/gh/richardschneider/cardsJS@master/cards/{rank_str}{self.suit.value}.svg"

    def to_dict(self) -> dict:
        return {
            "rank": self.rank.value,
            "rank_label": self.rank.label,
            "rank_name": self.rank.pt_name,
            "suit": self.suit.value,
            "suit_symbol": self.suit.symbol,
            "suit_name": self.suit.pt_name,
            "color": self.suit.color,
            "code": self.code,
            "image_url": self.image_url,
            "svg_url": self.svg_url
        }

    def __repr__(self) -> str:
        return f"{self.rank.label}{self.suit.symbol}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))

    def __lt__(self, other) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank < other.rank


class Deck:
    def __init__(self):
        self.cards: List[Card] = []
        self.reset()

    def reset(self):
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        self.shuffle()

    def shuffle(self):
        # High-quality pseudo-random shuffle
        random.shuffle(self.cards)

    def draw(self, count: int = 1) -> List[Card]:
        if count > len(self.cards):
            raise ValueError(f"Não há cartas suficientes no baralho ({len(self.cards)} restantes)")
        drawn = [self.cards.pop() for _ in range(count)]
        return drawn

    def draw_one(self) -> Card:
        return self.draw(1)[0]

    def __len__(self) -> int:
        return len(self.cards)
