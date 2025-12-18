from __future__ import annotations
import random
from dataclasses import dataclass
from typing import List, Tuple, Protocol, Dict


# ----------------------------
# Karten / Hand-Logik
# ----------------------------

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def card_value(rank: str) -> int:
    """Basiswert für Karten (Ass wird extra behandelt)."""
    if rank in ("J", "Q", "K"):
        return 10
    if rank == "A":
        return 1
    return int(rank)

@dataclass
class Hand:
    cards: List[str]

    def add(self, rank: str) -> None:
        self.cards.append(rank)

    def value_and_usable_ace(self) -> Tuple[int, bool]:
        """
        Handwert nach Blackjack-Regeln:
        - Ass zählt als 1 oder 11, je nachdem was besser ist (<=21).
        usable_ace=True bedeutet: ein Ass wird als 11 gezählt.
        """
        total = 0
        aces = 0
        for c in self.cards:
            if c == "A":
                aces += 1
            total += card_value(c)

        # Versuche ein Ass als 11 zu zählen (also +10 zusätzlich), solange <= 21
        usable_ace = False
        if aces > 0 and total + 10 <= 21:
            total += 10
            usable_ace = True

        return total, usable_ace

    @property
    def total(self) -> int:
        return self.value_and_usable_ace()[0]

    @property
    def usable_ace(self) -> bool:
        return self.value_and_usable_ace()[1]

    def is_blackjack(self) -> bool:
        """Blackjack = 2 Karten und total=21."""
        return len(self.cards) == 2 and self.total == 21

    def is_bust(self) -> bool:
        return self.total > 21


# ----------------------------
# Deck (infinite shoe)
# ----------------------------

class InfiniteDeck:
    """
    Unendliches Deck: zieht Karten mit Replacement aus einem Standarddeck-Rang-Set.
    Das ist in Simulationen üblich und sehr stabil (kein „Deck leer“ Problem).
    """
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def draw(self) -> str:
        return self.rng.choice(RANKS)


# ----------------------------
# Policies / Strategien
# ----------------------------

class Policy(Protocol):
    name: str
    def decide(self, player_hand: Hand, dealer_upcard: str) -> str:
        """
        Return "hit" oder "stand"
        """
        ...

class RandomPolicy:
    name = "RandomPolicy"
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def decide(self, player_hand: Hand, dealer_upcard: str) -> str:
        return self.rng.choice(["hit", "stand"])

class ThresholdPolicy:
    """
    Standard-Heuristik: hit bis total < threshold, sonst stand.
    """
    def __init__(self, threshold: int = 17):
        self.threshold = threshold
        self.name = f"ThresholdPolicy(threshold={threshold})"

    def decide(self, player_hand: Hand, dealer_upcard: str) -> str:
        return "hit" if player_hand.total < self.threshold else "stand"

class BasicStrategyPolicy:
    """
    Vereinfachte Basic Strategy (ohne Splits, ohne Double Down).
    Sehr brauchbar für eine Studienarbeit, weil:
    - klare Regeln
    - deutlich besser als Random/Threshold
    """

    name = "BasicStrategyPolicy(no-split-no-double)"

    def decide(self, player_hand: Hand, dealer_upcard: str) -> str:
        player_total = player_hand.total
        dealer_val = 11 if dealer_upcard == "A" else card_value(dealer_upcard)

        # Wenn bust wäre, ist eigentlich schon vorbei, aber safe:
        if player_total >= 21:
            return "stand"

        # "Soft" Hände (usable ace)
        if player_hand.usable_ace:
            # Soft totals: A+2=13 ... A+9=20
            # Vereinfachte Regeln:
            # Soft 19+ => stand
            if player_total >= 19:
                return "stand"
            # Soft 18: gegen 9/10/A eher hit, sonst stand
            if player_total == 18:
                return "hit" if dealer_val in (9, 10, 11) else "stand"
            # Soft <=17 => hit
            return "hit"

        # "Hard" Hände
        # Hard 17+ => stand
        if player_total >= 17:
            return "stand"
        # 13-16: stand gegen Dealer 2-6, sonst hit
        if 13 <= player_total <= 16:
            return "stand" if 2 <= dealer_val <= 6 else "hit"
        # 12: stand gegen 4-6, sonst hit
        if player_total == 12:
            return "stand" if 4 <= dealer_val <= 6 else "hit"
        # <=11: hit
        return "hit"


# ----------------------------
# Game / Rules
# ----------------------------

@dataclass
class Rules:
    dealer_hits_soft_17: bool = False   # False = Dealer stands on soft 17 (S17), True = hits (H17)
    blackjack_payout: float = 1.5       # Gewinn bei Player-Blackjack (wenn Dealer kein BJ hat)
    bet: float = 1.0                    # Einsatz pro Runde


@dataclass
class GameResult:
    outcome: str         # "win", "loss", "push"
    profit: float        # +1, -1, 0, +1.5 etc.
    player_total: int
    dealer_total: int
    player_blackjack: bool
    dealer_blackjack: bool
    player_bust: bool
    dealer_bust: bool


class BlackjackGame:
    def __init__(self, rules: Rules, deck: InfiniteDeck):
        self.rules = rules
        self.deck = deck

    def _dealer_should_hit(self, dealer_hand: Hand) -> bool:
        total, usable_ace = dealer_hand.value_and_usable_ace()
        if total < 17:
            return True
        if total > 17:
            return False
        # total == 17
        if usable_ace and self.rules.dealer_hits_soft_17:
            return True
        return False

    def play_round(self, policy: Policy) -> GameResult:
        # Initial deal
        player = Hand([self.deck.draw(), self.deck.draw()])
        dealer = Hand([self.deck.draw(), self.deck.draw()])
        dealer_upcard = dealer.cards[0]

        # Check blackjacks
        player_bj = player.is_blackjack()
        dealer_bj = dealer.is_blackjack()

        # Blackjack resolution
        if player_bj or dealer_bj:
            if player_bj and dealer_bj:
                return GameResult("push", 0.0, player.total, dealer.total, True, True, False, False)
            if player_bj and not dealer_bj:
                return GameResult("win", self.rules.blackjack_payout * self.rules.bet,
                                  player.total, dealer.total, True, False, False, False)
            # dealer blackjack
            return GameResult("loss", -1.0 * self.rules.bet, player.total, dealer.total, False, True, False, False)

        # Player turn
        while True:
            if player.is_bust():
                return GameResult("loss", -1.0 * self.rules.bet, player.total, dealer.total,
                                  False, False, True, False)

            action = policy.decide(player, dealer_upcard)
            if action not in ("hit", "stand"):
                raise ValueError(f"Policy returned invalid action: {action}")

            if action == "stand":
                break

            player.add(self.deck.draw())

        # Dealer turn
        while self._dealer_should_hit(dealer):
            dealer.add(self.deck.draw())

        # Determine outcome
        player_bust = player.is_bust()
        dealer_bust = dealer.is_bust()

        if player_bust:
            return GameResult("loss", -1.0 * self.rules.bet, player.total, dealer.total,
                              False, False, True, dealer_bust)
        if dealer_bust:
            return GameResult("win", 1.0 * self.rules.bet, player.total, dealer.total,
                              False, False, False, True)

        if player.total > dealer.total:
            return GameResult("win", 1.0 * self.rules.bet, player.total, dealer.total,
                              False, False, False, False)
        if player.total < dealer.total:
            return GameResult("loss", -1.0 * self.rules.bet, player.total, dealer.total,
                              False, False, False, False)
        return GameResult("push", 0.0, player.total, dealer.total,
                          False, False, False, False)


# ----------------------------
# Simulation / Metrics
# ----------------------------

@dataclass
class Summary:
    games: int
    wins: int
    losses: int
    pushes: int
    profit_total: float
    profit_avg: float
    win_rate: float
    loss_rate: float
    push_rate: float

def simulate(policy: Policy, n_games: int, seed: int = 42, rules: Rules | None = None) -> Summary:
    rules = rules or Rules()
    rng = random.Random(seed)
    deck = InfiniteDeck(rng=rng)
    game = BlackjackGame(rules=rules, deck=deck)

    wins = losses = pushes = 0
    profit_total = 0.0

    for _ in range(n_games):
        res = game.play_round(policy)
        profit_total += res.profit
        if res.outcome == "win":
            wins += 1
        elif res.outcome == "loss":
            losses += 1
        else:
            pushes += 1

    games = n_games
    profit_avg = profit_total / games
    return Summary(
        games=games,
        wins=wins,
        losses=losses,
        pushes=pushes,
        profit_total=profit_total,
        profit_avg=profit_avg,
        win_rate=wins / games,
        loss_rate=losses / games,
        push_rate=pushes / games,
    )

def print_summary(policy_name: str, s: Summary) -> None:
    print(f"\n=== {policy_name} ===")
    print(f"Games: {s.games}")
    print(f"Wins/Losses/Pushes: {s.wins}/{s.losses}/{s.pushes}")
    print(f"Win/Loss/Push rates: {s.win_rate:.3f} / {s.loss_rate:.3f} / {s.push_rate:.3f}")
    print(f"Total profit: {s.profit_total:.2f}")
    print(f"Avg profit per game: {s.profit_avg:.5f}")


# ----------------------------
# Main (Run)
# ----------------------------

def main() -> None:
    n = 50_000
    rules = Rules(dealer_hits_soft_17=False, blackjack_payout=1.5, bet=1.0)

    # Policies
    policies: List[Policy] = [
        RandomPolicy(rng=random.Random(1)),
        ThresholdPolicy(threshold=17),
        ThresholdPolicy(threshold=16),
        BasicStrategyPolicy(),
    ]

    print("Blackjack Monte-Carlo Simulation")
    print(f"Rules: S17={not rules.dealer_hits_soft_17}, BJ payout={rules.blackjack_payout}, bet={rules.bet}")
    print(f"Simulating {n} games per policy ...")

    for i, p in enumerate(policies):
        s = simulate(p, n_games=n, seed=100 + i, rules=rules)
        print_summary(getattr(p, "name", p.__class__.__name__), s)


if __name__ == "__main__":
    main()

