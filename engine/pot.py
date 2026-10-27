"""
Pot and Side-Pot Manager for Texas Hold'em Poker.
Handles main pot, side pots, all-in contributions, and split payouts.
"""
from typing import List, Dict, Set


class Pot:
    def __init__(self, amount: int, eligible_players: Set[str]):
        self.amount = amount
        self.eligible_players = eligible_players  # Player IDs who can win this pot

    def to_dict(self) -> dict:
        return {
            "amount": self.amount,
            "eligible_players": list(self.eligible_players)
        }


class PotManager:
    def __init__(self):
        # player_id -> cumulative chips contributed in current hand
        self.total_contributions: Dict[str, int] = {}
        # player_id -> chips put in current betting round
        self.round_contributions: Dict[str, int] = {}

    def reset_hand(self):
        self.total_contributions.clear()
        self.round_contributions.clear()

    def reset_round(self):
        self.round_contributions.clear()

    def add_bet(self, player_id: str, amount: int):
        self.total_contributions[player_id] = self.total_contributions.get(player_id, 0) + amount
        self.round_contributions[player_id] = self.round_contributions.get(player_id, 0) + amount

    def get_total_pot(self) -> int:
        return sum(self.total_contributions.values())

    def get_player_round_bet(self, player_id: str) -> int:
        return self.round_contributions.get(player_id, 0)

    def get_current_max_bet(self) -> int:
        if not self.round_contributions:
            return 0
        return max(self.round_contributions.values())

    def calculate_pots(self, active_player_ids: List[str], folded_player_ids: Set[str]) -> List[Pot]:
        """
        Calculates main pot and side pots based on all-in amounts and contributions.
        folded_player_ids: players who folded (their chips stay in the pot, but they cannot win).
        """
        if not self.total_contributions:
            return []

        # List of distinct non-zero contribution levels from active (non-folded) players
        active_contribs = {
            pid: self.total_contributions[pid]
            for pid in self.total_contributions
            if pid not in folded_player_ids and self.total_contributions[pid] > 0
        }

        if not active_contribs:
            # If all players folded except perhaps one or none
            return [Pot(amount=self.get_total_pot(), eligible_players=set(active_player_ids))]

        sorted_levels = sorted(set(active_contribs.values()))
        pots: List[Pot] = []
        previous_level = 0

        for level in sorted_levels:
            pot_amount = 0
            eligible: Set[str] = set()

            for pid, total in self.total_contributions.items():
                if total > previous_level:
                    contribution_to_level = min(total, level) - previous_level
                    pot_amount += contribution_to_level
                    if pid not in folded_player_ids and total >= level:
                        eligible.add(pid)

            if pot_amount > 0 and eligible:
                pots.append(Pot(amount=pot_amount, eligible_players=eligible))
            previous_level = level

        # If any chips remain due to folded players overcontributing beyond max active
        max_active_level = max(active_contribs.values())
        unclaimed = sum(max(0, amt - max_active_level) for amt in self.total_contributions.values())
        if unclaimed > 0 and pots:
            # Add back into the last pot
            pots[-1].amount += unclaimed

        return pots
