# fourteen-thinkers

Fourteen Independent Thinkers, Read Side by Side

An AI-assisted synthesis of sixteen independent writers, all critical of the US foreign-policy consensus, on money, war and power. Their interviews and articles are read in their own words, compared with each other rather than with official fact-checks, and quoted exactly. A small program checks every quotation against the saved texts.

The authors: Richard Werner, Alex Krainer, Brian Berletic, Simon Dixon, Catherine Austin Fitts, Ben Norton, Patrick Henningsen, Chris Martenson, Michael Hudson, Alastair Crooke, Lawrence Wilkerson, Glenn Diesen, Whitney Webb and Richard Wolff, joined later by John Mearsheimer and Jeffrey Sachs. The title still says fourteen; there are now sixteen. Noam Chomsky and K.J. Noh are cited as references. Larry Johnson (sonar21.com), the energy analyst Karl Miller and Philip Pilkington are used as sources of facts only. Jiang Xueqin (Predictive History) is cited only for his forecasts; his factual claims were checked and found overstated. Cameron MacGregor and Stanislav Krapivnik are cited for one dated forecast each, from an interview recorded on 6 October 2026.

## What is here

- `synthesis.md`: the main document, with these sections:
  - where the authors agree;
  - the mechanism they describe between them;
  - where they contradict each other, and the precise questions that would settle it;
  - their forecasts on the Iran war, judged by their own later accounts;
  - a closing set of hypotheses, each with its supporters, objections and tests.
- `author-axes.html`: the charts page. Download it and open it in a browser. It shows:
  - the vantage points each author looks from (states, institutions, class, energy, money, hidden networks), and how well they predict what each concludes;
  - one map placing all sixteen authors on the three dimensions that separate them most, any two at a time;
  - each of the sixteen authors scored from 1 to 5 on thirteen questions, every score backed by the author's own words;
  - who sits close to whom, and who is on the margin;
  - a chart of the personal advice the authors give;
  - test cases, the hypotheses and the evidence grids.
- `article.html`: the full first-person article about the experiment, step by step: the method and what it found.
- `critical-thinking.html`: a shorter article, "Teaching an AI to Doubt", on what the project taught about getting an AI to think critically. It links to `article.html` for the detail.
- `ledger/`: the data and the checking program. See `ledger/README.md`. It contains:
  - `ledger.json`, the master data: chart scores and their quotes, forecasts, cases, hypotheses and evidence grids;
  - `sources/`, the authors' saved texts, one folder per author;
  - `build.py`, which checks every quotation and every count in `synthesis.md`, writes `report.md`, and regenerates the charts page.
- `transcripts/`: the interview transcripts used as sources.

## How claims are tested

- **Against each other.** Where the authors agree, and where one author's account contradicts another's.
- **Against documents the authors cite.** For example, the 2009 Brookings paper "Which Path to Persia?".
- **Forecasts against outcomes.** Authors' forecasts are judged by their own later accounts. Indicators for the hypotheses (Treasury holdings, central-bank gold buying, munitions stocks) are judged on public data, with the source named.
- **Evidence grids.** These use analysis of competing hypotheses (Richards Heuer's method). Facts are listed and marked as fitting, contradicting or not bearing on each explanation. The explanation with the fewest solid facts against it ranks first. Two grids are worked through:
  - What is the Iran war for?
  - Is the plan working?

## Framing

The actors are interest blocs (arms, energy, finance, technology, lobbies), not countries or leaders. Money is described as flows between blocs, not as what "the US pays". Ideas are credited to the authors whose material they come from.

## Rebuilding

```
cd ledger
python3 build.py
```

This needs only Python 3. Fix anything listed in `ledger/report.md` before publishing.

## Limits

- The authors were chosen for a shared outlook, so part of their agreement is built in.
- Some of them share sources; where two authors rely on the same document or witness, their agreement counts once, not twice.
- Every score and every mark in the evidence grids is a judgement. Each one shows its quote or reason so it can be challenged.
