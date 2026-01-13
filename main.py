from __future__ import annotations
import random
from dataclasses import dataclass
from typing import List, Tuple, Protocol


# ----------------------------
# Cards / Hand logic
# ----------------------------

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


def card_value(rank: str) -> int:
    """Return the base Blackjack value of a rank (Ace counts as 1 here)."""
    if rank in ("J", "Q", "K"):
        return 10
    if rank == "A":
        return 1
    return int(rank)


@dataclass
class Hand:
    """A Blackjack hand with helpers for total value, blackjack and bust checks."""
    cards: List[str]

    def add(self, rank: str) -> None:
        self.cards.append(rank)

    def value_and_usable_ace(self) -> Tuple[int, bool]:
        """
        Compute the best hand total under Blackjack Ace rules.

        Returns:
            total: best value <= 21 if possible
            usable_ace: True if an Ace is counted as 11 (soft hand)
        """
        total = 0
        aces = 0
        for c in self.cards:
            if c == "A":
                aces += 1
            total += card_value(c)

        # Upgrade one Ace from 1 to 11 (+10) if it does not bust the hand.
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
        """Natural blackjack: exactly two cards totaling 21."""
        return len(self.cards) == 2 and self.total == 21

    def is_bust(self) -> bool:
        return self.total > 21


# ----------------------------,
# Deck (infinite shoe)
# ----------------------------

class InfiniteDeck:
    """
    Infinite deck model: draws ranks with replacement.

    This simplifies Monte Carlo simulations by avoiding deck depletion and reshuffles.
    """
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def draw(self) -> str:
        return self.rng.choice(RANKS)


# ----------------------------
# Policies / Strategies
# ----------------------------

class Policy(Protocol):
    """Strategy interface: implement decide() to return 'hit' or 'stand'."""
    name: str

    def decide(self, player_hand: Hand, dealer_upcard: str) -> str:
        ...


class RandomPolicy:
    """Baseline strategy: randomly chooses between hit and stand."""
    name = "RandomPolicy"

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def decide(self, player_hand: Hand, dealer_upcard: str) -> str:
        return self.rng.choice(["hit", "stand"])


class ThresholdPolicy:
    """Hit while total < threshold, otherwise stand."""
    def __init__(self, threshold: int = 17):
        self.threshold = threshold
        self.name = f"ThresholdPolicy(threshold={threshold})"

    def decide(self, player_hand: Hand, dealer_upcard: str) -> str:
        return "hit" if player_hand.total < self.threshold else "stand"


class BasicStrategyPolicy:
    """
    Simplified basic strategy (no splits, no doubling).

    Included to compare a stronger, deterministic policy against naive baselines.
    """
    name = "BasicStrategyPolicy(no-split-no-double)"

    def decide(self, player_hand: Hand, dealer_upcard: str) -> str:
        player_total = player_hand.total
        dealer_val = 11 if dealer_upcard == "A" else card_value(dealer_upcard)

        if player_total >= 21:
            return "stand"

        # Soft hands (usable Ace)
        if player_hand.usable_ace:
            if player_total >= 19:
                return "stand"
            if player_total == 18:
                return "hit" if dealer_val in (9, 10, 11) else "stand"
            return "hit"

        # Hard hands
        if player_total >= 17:
            return "stand"
        if 13 <= player_total <= 16:
            return "stand" if 2 <= dealer_val <= 6 else "hit"
        if player_total == 12:
            return "stand" if 4 <= dealer_val <= 6 else "hit"
        return "hit"


# ----------------------------
# Game / Rules
# ----------------------------

@dataclass
class Rules:
    """Rule parameters used by the simulation (S17/H17, payout, bet)."""
    dealer_hits_soft_17: bool = False   # False => S17, True => H17
    blackjack_payout: float = 1.5
    bet: float = 1.0


@dataclass
class GameResult:
    """Structured result of a single round (useful for stats and debugging)."""
    outcome: str       # "win", "loss", "push"
    profit: float
    player_total: int
    dealer_total: int
    player_blackjack: bool
    dealer_blackjack: bool
    player_bust: bool
    dealer_bust: bool


class BlackjackGame:
    """One-round Blackjack engine: deal, player policy turn, dealer rules, settle outcome."""
    def __init__(self, rules: Rules, deck: InfiniteDeck):
        self.rules = rules
        self.deck = deck

    def _dealer_should_hit(self, dealer_hand: Hand) -> bool:
        # Dealer draws to 17; soft-17 behavior depends on rules.
        total, usable_ace = dealer_hand.value_and_usable_ace()
        if total < 17:
            return True
        if total > 17:
            return False
        if usable_ace and self.rules.dealer_hits_soft_17:
            return True
        return False

    def play_round(self, policy: Policy) -> GameResult:
        """Play a single round and return the outcome, profit and round flags."""
        player = Hand([self.deck.draw(), self.deck.draw()])
        dealer = Hand([self.deck.draw(), self.deck.draw()])
        dealer_upcard = dealer.cards[0]

        player_bj = player.is_blackjack()
        dealer_bj = dealer.is_blackjack()

        # Immediate blackjack resolution
        if player_bj or dealer_bj:
            if player_bj and dealer_bj:
                return GameResult("push", 0.0, player.total, dealer.total, True, True, False, False)
            if player_bj:
                return GameResult("win", self.rules.blackjack_payout * self.rules.bet,
                                  player.total, dealer.total, True, False, False, False)
            return GameResult("loss", -1.0 * self.rules.bet,
                              player.total, dealer.total, False, True, False, False)

        # Player turn
        while True:
            if player.is_bust():
                return GameResult("loss", -1.0 * self.rules.bet,
                                  player.total, dealer.total, False, False, True, False)

            action = policy.decide(player, dealer_upcard)
            if action == "stand":
                break
            player.add(self.deck.draw())

        # Dealer turn
        while self._dealer_should_hit(dealer):
            dealer.add(self.deck.draw())

        # Final resolution
        if player.is_bust():
            return GameResult("loss", -1.0 * self.rules.bet,
                              player.total, dealer.total, False, False, True, dealer.is_bust())
        if dealer.is_bust():
            return GameResult("win", 1.0 * self.rules.bet,
                              player.total, dealer.total, False, False, False, True)

        if player.total > dealer.total:
            return GameResult("win", 1.0 * self.rules.bet,
                              player.total, dealer.total, False, False, False, False)
        if player.total < dealer.total:
            return GameResult("loss", -1.0 * self.rules.bet,
                              player.total, dealer.total, False, False, False, False)
        return GameResult("push", 0.0,
                          player.total, dealer.total, False, False, False, False)


# ----------------------------
# Simulation / Metrics
# ----------------------------

@dataclass
class Summary:
    """Aggregated metrics for many simulated rounds (counts, rates, and profit)."""
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
    """Run n_games Monte Carlo rounds for a policy and return aggregated statistics."""
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

    return Summary(
        games=n_games,
        wins=wins,
        losses=losses,
        pushes=pushes,
        profit_total=profit_total,
        profit_avg=profit_total / n_games,
        win_rate=wins / n_games,
        loss_rate=losses / n_games,
        push_rate=pushes / n_games,
    )


def print_summary(policy_name: str, s: Summary) -> None:
    """Print a readable summary for one policy run."""
    print(f"\n=== {policy_name} ===")
    print(f"Games: {s.games}")
    print(f"Wins/Losses/Pushes: {s.wins}/{s.losses}/{s.pushes}")
    print(f"Win/Loss/Push rates: {s.win_rate:.3f} / {s.loss_rate:.3f} / {s.push_rate:.3f}")
    print(f"Total profit: {s.profit_total:.2f}")
    print(f"Average profit per game: {s.profit_avg:.5f}")


# ----------------------------
# Main
# ----------------------------

def main() -> None:
    """Run the simulation for multiple strategies and print comparable results."""
    n = 50_000
    rules = Rules(dealer_hits_soft_17=False, blackjack_payout=1.5, bet=1.0)

    policies: List[Policy] = [
        RandomPolicy(rng=random.Random(1)),
        ThresholdPolicy(threshold=17),
        ThresholdPolicy(threshold=16),
        BasicStrategyPolicy(),
    ]

    print("Blackjack Monte Carlo Simulation")
    print(f"Rules: S17={not rules.dealer_hits_soft_17}, "
          f"BJ payout={rules.blackjack_payout}, bet={rules.bet}")
    print(f"Simulating {n} games per policy ...")

    for i, p in enumerate(policies):
        s = simulate(p, n_games=n, seed=100 + i, rules=rules)
        print_summary(getattr(p, "name", p.__class__.__name__), s)


if __name__ == "__main__":
    main()
