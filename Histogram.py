from __future__ import annotations

import random
from typing import List

import matplotlib.pyplot as plt

# Import from your main Blackjack simulation
from main import (
    Rules,
    Policy,
    RandomPolicy,
    ThresholdPolicy,
    BasicStrategyPolicy,
    simulate,
)


def plot_outcome_rates(
    policies: List[Policy],
    win_rates: List[float],
    loss_rates: List[float],
    push_rates: List[float],
    filename: str
) -> None:
    """
    Grouped bar chart: win / loss / push rates per strategy
    """
    x = list(range(len(policies)))
    width = 0.25

    plt.figure()

    plt.bar([i - width for i in x], win_rates, width=width, label="Win rate")
    plt.bar([i for i in x], loss_rates, width=width, label="Loss rate")
    plt.bar([i + width for i in x], push_rates, width=width, label="Push rate")

    labels = [getattr(p, "name", p.__class__.__name__) for p in policies]
    plt.xticks(x, labels, rotation=25, ha="right")

    plt.ylim(0, 1)
    plt.xlabel("Strategy")
    plt.ylabel("Rate")
    plt.title("Blackjack Strategy Comparison: Win / Loss / Push Rates")
    plt.legend()

    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def plot_average_profit(
    policies: List[Policy],
    avg_profits: List[float],
    filename: str
) -> None:
    """
    Bar chart: average profit per game per strategy
    """
    plt.figure()

    labels = [getattr(p, "name", p.__class__.__name__) for p in policies]
    plt.bar(labels, avg_profits)
    plt.xticks(rotation=25, ha="right")

    plt.xlabel("Strategy")
    plt.ylabel("Average Profit per Game")
    plt.title("Blackjack Strategy Comparison: Average Profit")

    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def main() -> None:
    n_games = 50_000
    rules = Rules(
        dealer_hits_soft_17=False,
        blackjack_payout=1.5,
        bet=1.0
    )

    policies: List[Policy] = [
        RandomPolicy(rng=random.Random(1)),
        ThresholdPolicy(threshold=17),
        ThresholdPolicy(threshold=16),
        BasicStrategyPolicy(),
    ]

    win_rates = []
    loss_rates = []
    push_rates = []
    avg_profits = []

    for i, policy in enumerate(policies):
        summary = simulate(
            policy,
            n_games=n_games,
            seed=100 + i,
            rules=rules
        )

        win_rates.append(summary.win_rate)
        loss_rates.append(summary.loss_rate)
        push_rates.append(summary.push_rate)
        avg_profits.append(summary.profit_avg)

    plot_outcome_rates(
        policies,
        win_rates,
        loss_rates,
        push_rates,
        filename="diagram_outcome_rates.png"
    )

    plot_average_profit(
        policies,
        avg_profits,
        filename="diagram_average_profit.png"
    )

    print("✔ Diagrams successfully created:")
    print(" - diagram_outcome_rates.png")
    print(" - diagram_average_profit.png")


if __name__ == "__main__":
    main()

