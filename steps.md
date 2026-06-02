The notebook is where we build and test the logic.

Later, we move the good functions into Python files, for example:

src/
  prediction.py
  simulation.py
  bracket.py
  utils.py

app.py

Then Streamlit imports them like this:

from src.prediction import predict_match
from src.simulation import simulate_tournament
from src.bracket import build_round_32_bracket

So the workflow is:

Notebook = experiment and validate
Python scripts = clean reusable code
Streamlit app = user interface




-- -- -- -- -- -- 

Page 1: Tournament Probability Dashboard
- Run Monte Carlo
- Slider for number of simulations
- Table of all teams and stage probabilities
- Bar chart of winner probabilities

Page 2: Live Tournament Simulation
- Button: Run one tournament
- Group match results appear
- Group tables appear
- Qualified teams fill Round of 32
- Knockout bracket fills round by round
- Final winner revealed

Page 3: Match Explorer
- Select Team A and Team B
- Show xG
- Show win/draw/loss probabilities
- Show Elo, FIFA rank, form, H2H context