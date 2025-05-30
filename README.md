# jeebench25

## Getting Started

Create a `.env` file in the root directory to place your OpenAI API key in

```
OPENAI_API_KEY=...
```

After that, create a venv and install requirements 
```
python3 -m venv .venv
pip install -r requirements.txt
```

## Scripts

There are a bunch of scripts that make up this directory. A short description 
of each is:

1. `annotator.py` - Launches a webapp to help annotate the dataset. 
2. `solver.py` - Submits questions from the dataset via OpenAI API and stores 
   responses in JSON.
3. `evaluator.py` - Evaluates the runs and scores them
4. `cost.py` - Computes run cost in $
5. `centre.py` - filters the JEE(A) 2024 centres for third-party non-educational 
   institutions
6. `duration.py` - obtains the duration of a run by analysing the run's logfile
7. `answer_repatch.py` - answers were initially single values. This script was 
   written to repatch the answers in the runs with updated answers from the 
   dataset.
