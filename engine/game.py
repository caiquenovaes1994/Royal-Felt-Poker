"""
Complete Texas Hold'em Game State Machine and Engine.
Handles player state, deck dealing, betting rounds (Preflop, Flop, Turn, River),
side-pot calculations, AI triggers, and showdown resolution.
"""
from enum import Enum
import time
from typing import List, Dict, Optional, Any, Set
from .card import Card, Deck
from .evaluator import evaluate_hand, HandRank
from .pot import PotManager, Pot
from .ai import BOT_PERSONALITIES, AIPersonality, decide_action


class GamePhase(str, Enum):
    IDLE = "IDLE"
    PREFLOP = "PREFLOP"
    FLOP = "FLOP"
    TURN = "TURN"
    RIVER = "RIVER"
    SHOWDOWN = "SHOWDOWN"
    HAND_OVER = "HAND_OVER"


class Player:
    def __init__(self, player_id: str, name: str, chips: int, is_human: bool = False, personality: Optional[AIPersonality] = None):
        self.id = player_id
        self.name = name
        self.chips = chips
        self.is_human = is_human
        self.personality = personality
        self.hole_cards: List[Card] = []
        self.current_bet = 0
        self.folded = False
        self.all_in = False
        self.last_action: Optional[str] = None
        self.avatar = "🤠" if is_human else (personality.avatar if personality else "🤖")
        self.title = "Jogador VIP" if is_human else (personality.title if personality else "Jogador")
        self.hand_rank: Optional[HandRank] = None
        self.sitting_out = False

    def reset_hand(self):
        self.hole_cards = []
        self.current_bet = 0
        self.folded = False
        self.all_in = False
        self.last_action = None
        self.hand_rank = None

    def to_dict(self, reveal_cards: bool = False) -> dict:
        show_cards = self.is_human or reveal_cards or self.folded
        # During showdown, show all non-folded cards
        # While folded, hole cards can be hidden or greyed out
        cards_data = []
        if self.is_human or reveal_cards:
            cards_data = [c.to_dict() for c in self.hole_cards]
        elif self.hole_cards:
            # Face down card placeholder
            cards_data = [{"face_down": True, "back_url": "https://deckofcardsapi.com/static/img/back.png"}] * len(self.hole_cards)

        return {
            "id": self.id,
            "name": self.name,
            "chips": self.chips,
            "is_human": self.is_human,
            "avatar": self.avatar,
            "title": self.title,
            "current_bet": self.current_bet,
            "folded": self.folded,
            "all_in": self.all_in,
            "last_action": self.last_action,
            "cards": cards_data,
            "cards_count": len(self.hole_cards),
            "sitting_out": self.sitting_out,
            "hand_rank": self.hand_rank.to_dict() if (self.hand_rank and (self.is_human or reveal_cards)) else None
        }


class TexasHoldemGame:
    def __init__(
        self,
        small_blind: int = 10,
        big_blind: int = 20,
        starting_chips: int = 1000
    ):
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.starting_chips = starting_chips
        self.deck = Deck()
        self.pot_manager = PotManager()

        # Players setup: 1 Human + 4 AI Bots
        self.players: List[Player] = [
            Player("player_0", "Você", starting_chips, is_human=True),
        ]
        for idx, bot in enumerate(BOT_PERSONALITIES):
            self.players.append(
                Player(f"bot_{idx+1}", bot.name, starting_chips, is_human=False, personality=bot)
            )

        self.community_cards: List[Card] = []
        self.phase: GamePhase = GamePhase.IDLE
        self.dealer_idx = -1
        self.current_player_idx = -1
        self.current_bet = 0
        self.min_raise = big_blind
        self.last_raise_amt = big_blind
        self.action_history: List[dict] = []
        self.winners: List[dict] = []
        self.hand_count = 0
        self.acted_players: Set[str] = set()

        # Stats tracking for Human
        self.stats = {
            "hands_played": 0,
            "hands_won": 0,
            "biggest_pot": 0,
            "total_profit": 0
        }

    def log(self, message: str, action_type: str = "info", player_id: Optional[str] = None):
        entry = {
            "message": message,
            "type": action_type,
            "player_id": player_id,
            "time": time.strftime("%H:%M:%S")
        }
        self.action_history.append(entry)
        if len(self.action_history) > 60:
            self.action_history.pop(0)

    def active_players_in_hand(self) -> List[Player]:
        """Players who haven't folded in the current hand."""
        return [p for p in self.players if not p.folded and not p.sitting_out]

    def players_with_chips(self) -> List[Player]:
        """Players eligible to start a new hand."""
        return [p for p in self.players if p.chips > 0 and not p.sitting_out]

    def start_new_hand(self) -> bool:
        """Starts a new hand if at least 2 players have chips."""
        eligible = self.players_with_chips()
        if len(eligible) < 2:
            self.log("Jogadores insuficientes para iniciar uma nova mão.", "warning")
            return False

        self.hand_count += 1
        self.stats["hands_played"] += 1
        self.deck.reset()
        self.pot_manager.reset_hand()
        self.community_cards = []
        self.winners = []
        self.current_bet = 0
        self.min_raise = self.big_blind
        self.last_raise_amt = self.big_blind
        self.acted_players.clear()

        # Reset player hand states
        for p in self.players:
            p.reset_hand()
            if p.chips <= 0:
                p.sitting_out = True

        # Advance dealer button to next active player with chips
        num_players = len(self.players)
        for _ in range(num_players):
            self.dealer_idx = (self.dealer_idx + 1) % num_players
            if self.players[self.dealer_idx].chips > 0 and not self.players[self.dealer_idx].sitting_out:
                break

        dealer = self.players[self.dealer_idx]
        self.log(f"--- Mão #{self.hand_count} iniciada. {dealer.name} está no Botão (D). ---", "round")

        # Post Small Blind
        sb_idx = self._next_active_seat(self.dealer_idx)
        sb_player = self.players[sb_idx]
        sb_amt = min(sb_player.chips, self.small_blind)
        sb_player.chips -= sb_amt
        sb_player.current_bet = sb_amt
        self.pot_manager.add_bet(sb_player.id, sb_amt)
        if sb_player.chips == 0:
            sb_player.all_in = True
        sb_player.last_action = f"Small Blind ${sb_amt}"
        self.log(f"{sb_player.name} pagou o Small Blind de ${sb_amt}.", "blind", sb_player.id)

        # Post Big Blind
        bb_idx = self._next_active_seat(sb_idx)
        bb_player = self.players[bb_idx]
        bb_amt = min(bb_player.chips, self.big_blind)
        bb_player.chips -= bb_amt
        bb_player.current_bet = bb_amt
        self.pot_manager.add_bet(bb_player.id, bb_amt)
        if bb_player.chips == 0:
            bb_player.all_in = True
        bb_player.last_action = f"Big Blind ${bb_amt}"
        self.log(f"{bb_player.name} pagou o Big Blind de ${bb_amt}.", "blind", bb_player.id)

        self.current_bet = max(sb_amt, bb_amt)
        self.min_raise = self.big_blind

        # Deal 2 hole cards to each active player
        for _ in range(2):
            for p in self.players:
                if not p.sitting_out and p.chips >= 0:
                    p.hole_cards.append(self.deck.draw_one())

        # Update initial human hand rank
        human = self.get_human_player()
        if human and human.hole_cards:
            human.hand_rank = evaluate_hand(human.hole_cards)

        self.phase = GamePhase.PREFLOP

        # First action preflop is Under The Gun (UTG), left of Big Blind
        self.current_player_idx = self._next_acting_seat(bb_idx)
        return True

    def _next_active_seat(self, from_idx: int) -> int:
        """Finds next player who hasn't folded and isn't sitting out."""
        num = len(self.players)
        for i in range(1, num + 1):
            idx = (from_idx + i) % num
            if not self.players[idx].sitting_out and not self.players[idx].folded:
                return idx
        return from_idx

    def _next_acting_seat(self, from_idx: int) -> int:
        """Finds next player who can act (not folded, not sitting out, not all-in)."""
        num = len(self.players)
        for i in range(1, num + 1):
            idx = (from_idx + i) % num
            p = self.players[idx]
            if not p.sitting_out and not p.folded and not p.all_in:
                return idx
        return -1

    def player_action(self, player_id: str, action: str, amount: int = 0) -> bool:
        """
        Executes an action (fold, check, call, raise).
        """
        if self.phase in (GamePhase.IDLE, GamePhase.SHOWDOWN, GamePhase.HAND_OVER):
            return False

        cur_p = self.players[self.current_player_idx]
        if cur_p.id != player_id:
            return False

        to_call = self.current_bet - cur_p.current_bet
        acted = False

        if action == "fold":
            cur_p.folded = True
            cur_p.last_action = "Fold"
            self.log(f"{cur_p.name} deu Fold.", "fold", cur_p.id)
            acted = True

        elif action == "check":
            if to_call > 0:
                # Cannot check if there's a bet to call
                return False
            cur_p.last_action = "Check"
            self.log(f"{cur_p.name} deu Check.", "check", cur_p.id)
            acted = True

        elif action == "call":
            call_amt = min(to_call, cur_p.chips)
            cur_p.chips -= call_amt
            cur_p.current_bet += call_amt
            self.pot_manager.add_bet(cur_p.id, call_amt)
            if cur_p.chips == 0:
                cur_p.all_in = True
                cur_p.last_action = f"All-in Call (${call_amt})"
                self.log(f"{cur_p.name} deu All-in Call de ${call_amt}!", "allin", cur_p.id)
            else:
                cur_p.last_action = f"Call ${call_amt}"
                self.log(f"{cur_p.name} deu Call de ${call_amt}.", "call", cur_p.id)
            acted = True

        elif action == "raise":
            # Amount passed is the target total bet in this round
            # Must be at least current_bet + min_raise (or all-in)
            needed = amount - cur_p.current_bet
            if needed > cur_p.chips:
                # Can only put in remaining chips -> All-in
                needed = cur_p.chips
                actual_total = cur_p.current_bet + needed
            else:
                actual_total = amount

            if actual_total < self.current_bet + self.min_raise and (cur_p.chips > needed):
                # Invalid raise size unless all-in
                return False

            raise_diff = actual_total - self.current_bet
            if raise_diff > self.min_raise:
                self.min_raise = raise_diff

            cur_p.chips -= needed
            cur_p.current_bet = actual_total
            self.pot_manager.add_bet(cur_p.id, needed)
            self.current_bet = actual_total

            # A raise resets who has acted this round to ensure others can respond
            self.acted_players.clear()

            if cur_p.chips == 0:
                cur_p.all_in = True
                cur_p.last_action = f"All-in (${actual_total})"
                self.log(f"{cur_p.name} foi All-in com ${actual_total}!", "allin", cur_p.id)
            else:
                cur_p.last_action = f"Raise ${actual_total}"
                self.log(f"{cur_p.name} aumentou a aposta para ${actual_total}.", "raise", cur_p.id)
            acted = True

        if not acted:
            return False

        self.acted_players.add(cur_p.id)

        # Check if hand ended prematurely (only 1 player remaining)
        active = self.active_players_in_hand()
        if len(active) == 1:
            self._handle_single_winner(active[0])
            return True

        # Check if betting round is complete
        if self._is_betting_round_complete():
            self._advance_phase()
        else:
            # Advance to next player
            self.current_player_idx = self._next_acting_seat(self.current_player_idx)

        return True

    def _is_betting_round_complete(self) -> bool:
        """
        Round is complete when all active players who can act have matched current_bet
        and have had a chance to act.
        """
        can_act = [p for p in self.active_players_in_hand() if not p.all_in]
        if not can_act:
            # All players are all-in or folded
            return True

        for p in can_act:
            if p.id not in self.acted_players or p.current_bet < self.current_bet:
                return False
        return True

    def _advance_phase(self):
        """Advances from PREFLOP -> FLOP -> TURN -> RIVER -> SHOWDOWN."""
        # Reset round bets for pot tracking
        for p in self.players:
            p.current_bet = 0
            if not p.folded and not p.all_in:
                p.last_action = None
        self.pot_manager.reset_round()
        self.current_bet = 0
        self.min_raise = self.big_blind
        self.acted_players.clear()

        # Update human player's hand rank
        human = self.get_human_player()
        if human and human.hole_cards:
            human.hand_rank = evaluate_hand(human.hole_cards + self.community_cards)

        # Check if all or all-but-one remaining players are all-in
        non_allin = [p for p in self.active_players_in_hand() if not p.all_in]
        auto_deal = (len(non_allin) <= 1 and len(self.active_players_in_hand()) > 1)

        if self.phase == GamePhase.PREFLOP:
            self.phase = GamePhase.FLOP
            # Burn 1 card, deal 3 flop cards
            self.deck.draw(1)
            self.community_cards.extend(self.deck.draw(3))
            self.log(f"--- Flop: {' '.join(str(c) for c in self.community_cards)} ---", "phase")

        elif self.phase == GamePhase.FLOP:
            self.phase = GamePhase.TURN
            # Burn 1 card, deal 1 turn card
            self.deck.draw(1)
            self.community_cards.append(self.deck.draw_one())
            self.log(f"--- Turn: {self.community_cards[-1]} (Mesa: {' '.join(str(c) for c in self.community_cards)}) ---", "phase")

        elif self.phase == GamePhase.TURN:
            self.phase = GamePhase.RIVER
            # Burn 1 card, deal 1 river card
            self.deck.draw(1)
            self.community_cards.append(self.deck.draw_one())
            self.log(f"--- River: {self.community_cards[-1]} (Mesa: {' '.join(str(c) for c in self.community_cards)}) ---", "phase")

        elif self.phase == GamePhase.RIVER:
            self._handle_showdown()
            return

        # Update hand evaluation with new board cards
        if human and human.hole_cards:
            human.hand_rank = evaluate_hand(human.hole_cards + self.community_cards)

        if auto_deal:
            # No further bets possible because players are all in
            # Immediately advance to next phase until showdown
            self._advance_phase()
            return

        # First to act post-flop is first active seat after dealer
        self.current_player_idx = self._next_acting_seat(self.dealer_idx)
        if self.current_player_idx == -1:
            # Everyone is all-in
            self._advance_phase()

    def _handle_single_winner(self, winner: Player):
        """When all opponents fold, the remaining player wins the entire pot."""
        total_pot = self.pot_manager.get_total_pot()
        winner.chips += total_pot
        self.phase = GamePhase.HAND_OVER
        self.winners = [{
            "player_id": winner.id,
            "player_name": winner.name,
            "amount": total_pot,
            "reason": "Todos os oponentes deram fold.",
            "hand_desc": "Vencedor por desistência"
        }]
        self.log(f"🏆 {winner.name} venceu o pote de ${total_pot} (todos desistiram)!", "win", winner.id)

        if winner.is_human:
            self.stats["hands_won"] += 1
            self.stats["biggest_pot"] = max(self.stats["biggest_pot"], total_pot)
            self.stats["total_profit"] += total_pot

    def _handle_showdown(self):
        """Calculates winners for main and side pots using evaluate_hand."""
        self.phase = GamePhase.SHOWDOWN
        active_players = self.active_players_in_hand()

        # Evaluate hands for all active players
        for p in active_players:
            p.hand_rank = evaluate_hand(p.hole_cards + self.community_cards)

        # Get side pots and main pot
        folded_ids = {p.id for p in self.players if p.folded}
        active_ids = [p.id for p in active_players]
        pots: List[Pot] = self.pot_manager.calculate_pots(active_ids, folded_ids)

        self.winners = []
        payouts: Dict[str, int] = {}

        for pot_idx, pot in enumerate(pots):
            eligible = [p for p in active_players if p.id in pot.eligible_players]
            if not eligible:
                continue

            # Sort eligible by hand rank descending
            eligible.sort(key=lambda p: p.hand_rank, reverse=True)
            best_rank = eligible[0].hand_rank
            pot_winners = [p for p in eligible if p.hand_rank == best_rank]

            # Split pot equally among winners
            split_amount = pot.amount // len(pot_winners)
            remainder = pot.amount % len(pot_winners)

            pot_name = "Pote Principal" if pot_idx == 0 else f"Pote Paralelo #{pot_idx}"

            for i, winner in enumerate(pot_winners):
                win_share = split_amount + (1 if i < remainder else 0)
                winner.chips += win_share
                payouts[winner.id] = payouts.get(winner.id, 0) + win_share
                self.winners.append({
                    "player_id": winner.id,
                    "player_name": winner.name,
                    "amount": win_share,
                    "pot_name": pot_name,
                    "hand_desc": best_rank.description,
                    "best_cards": [c.to_dict() for c in best_rank.best_cards]
                })
                self.log(f"🏆 {winner.name} ganhou ${win_share} do {pot_name} com {best_rank.description}!", "win", winner.id)

        human = self.get_human_player()
        if human and human.id in payouts:
            self.stats["hands_won"] += 1
            self.stats["biggest_pot"] = max(self.stats["biggest_pot"], payouts[human.id])
            self.stats["total_profit"] += payouts[human.id]

        self.phase = GamePhase.HAND_OVER

    def trigger_ai_turn_if_needed(self) -> Optional[dict]:
        """
        If current player is an AI, calculates and executes its action.
        Returns the action taken or None if human turn or game over.
        """
        if self.phase in (GamePhase.IDLE, GamePhase.SHOWDOWN, GamePhase.HAND_OVER):
            return None

        if self.current_player_idx < 0 or self.current_player_idx >= len(self.players):
            return None

        cur_p = self.players[self.current_player_idx]
        if cur_p.is_human or cur_p.folded or cur_p.all_in or cur_p.sitting_out:
            return None

        # Call AI decision engine
        action, amount = decide_action(
            personality=cur_p.personality,
            hole_cards=cur_p.hole_cards,
            community_cards=self.community_cards,
            current_bet=self.current_bet,
            player_current_bet=cur_p.current_bet,
            player_chips=cur_p.chips,
            pot_total=self.pot_manager.get_total_pot(),
            min_raise=self.min_raise,
            big_blind=self.big_blind
        )

        success = self.player_action(cur_p.id, action, amount)
        return {
            "player_id": cur_p.id,
            "player_name": cur_p.name,
            "action": action,
            "amount": amount,
            "success": success
        }

    def rebuy_human(self, amount: int = 1000):
        """Allows the human player to reload chips if busted."""
        human = self.get_human_player()
        if human:
            human.chips += amount
            human.sitting_out = False
            self.log(f"{human.name} recarregou ${amount} em fichas!", "info", human.id)

    def get_human_player(self) -> Optional[Player]:
        for p in self.players:
            if p.is_human:
                return p
        return None

    def to_dict(self) -> dict:
        reveal_all = (self.phase in (GamePhase.SHOWDOWN, GamePhase.HAND_OVER))
        total_pot = self.pot_manager.get_total_pot()

        # Calculate human player call/raise constraints
        human = self.get_human_player()
        human_actions = {}
        if human and self.current_player_idx == self.players.index(human) and self.phase not in (GamePhase.IDLE, GamePhase.SHOWDOWN, GamePhase.HAND_OVER):
            to_call = self.current_bet - human.current_bet
            can_check = (to_call == 0)
            can_call = (to_call > 0 and human.chips > 0)
            call_amount = min(to_call, human.chips)
            min_bet_total = max(self.current_bet + self.min_raise, self.current_bet + self.big_blind)
            max_bet_total = human.current_bet + human.chips

            human_actions = {
                "can_fold": True,
                "can_check": can_check,
                "can_call": can_call,
                "call_amount": call_amount,
                "can_raise": (human.chips > to_call),
                "min_raise": min(min_bet_total, max_bet_total),
                "max_raise": max_bet_total,
                "current_bet_round": human.current_bet,
                "pot_size": total_pot
            }

        return {
            "phase": self.phase.value,
            "hand_count": self.hand_count,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "total_pot": total_pot,
            "current_bet": self.current_bet,
            "dealer_idx": self.dealer_idx,
            "current_player_idx": self.current_player_idx,
            "community_cards": [c.to_dict() for c in self.community_cards],
            "players": [p.to_dict(reveal_cards=reveal_all) for p in self.players],
            "winners": self.winners,
            "action_history": self.action_history[-20:],
            "human_actions": human_actions,
            "stats": self.stats
        }
