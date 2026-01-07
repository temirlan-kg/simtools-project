# 🎰 Blackjack Monte Carlo Simulation

This project implements a **Monte Carlo simulation of Blackjack** to compare different playing strategies.
It was developed as part of a **university programming and simulation project**.

The goal is to evaluate how simple heuristics perform compared to a simplified version of **Blackjack Basic Strategy**.

---

## 📌 Features
- Complete Blackjack game engine (player vs dealer)
- Infinite deck (sampling with replacement)
- Multiple strategies implemented
- Monte Carlo simulation with configurable number of games
- Statistical evaluation of results
- Visual analysis using diagrams and histograms

---

## 🧠 Implemented Strategies
- **RandomPolicy** – Player randomly decides to hit or stand  
- **ThresholdPolicy (17)** – Player hits until total ≥ 17  
- **ThresholdPolicy (16)** – Player hits until total ≥ 16  
- **BasicStrategyPolicy** – Simplified Blackjack Basic Strategy (no splits, no double down)

---

## ⚙️ Rules & Assumptions
- Infinite deck (no card counting)
- Dealer stands on soft 17 (S17)
- Blackjack payout: 3:2
- Fixed bet per round
- No splits, no double down, no surrender

---

## 📂 Project Structure
Simtools-Project/
* `main.py` : Blackjack simulation and game logic
* `diagram.py` : Strategy comparison diagrams
* `histogram.py` : Histogram visualizations
  * `diagram_outcome_rates.png`
  * `diagram_average_profit.png`
* `README.md`


---

## ▶️ How to Run

### Install requirements
```bash
pip install matplotlib
python main.py
python diagram.py
python histogram.py



## 📊 Results & Visualizations
Strategy Outcome Rates
Average Profit per Game
The diagrams show that:
Random strategies perform worst
Threshold strategies improve results slightly
The Basic Strategy significantly reduces losses

## 📈 Monte Carlo Method
Monte Carlo simulation is used to approximate expected outcomes by simulating a large number of independent games.
This allows a statistical comparison of strategies without analytical probability calculations.

## 📝 Conclusion
The simulation demonstrates that:
Simple heuristics already outperform random play
A structured rule-based strategy (Basic Strategy) performs best
Monte Carlo simulations are well-suited for evaluating stochastic games like Blackjack

## 👥 Authors
Temirlan Anarkulov
Christian Heusler

## 📄 License
This project is for educational purposes only.



