# fourteen-thinkers

Fourteen Independent Thinkers, Read Side by Side

An AI-assisted synthesis of fourteen commentators who write and speak outside the mainstream about money, war and power. Their interviews and articles are read in their own words, compared with each other rather than with official fact-checks, and quoted exactly. A small program checks every quotation against the saved texts.

The fourteen: Richard Werner, Alex Krainer, Brian Berletic, Simon Dixon, Catherine Austin Fitts, Ben Norton, Patrick Henningsen, Chris Martenson, Michael Hudson, Alastair Crooke, Lawrence Wilkerson, Glenn Diesen, Whitney Webb and Richard Wolff. Noam Chomsky and K.J. Noh are cited as references. Larry Johnson (sonar21.com) and the energy analyst Karl Miller are used as sources of facts only.

## What is here

- `synthesis.md`: the main document, with these sections:
  - where the authors agree;
  - the mechanism they describe between them;
  - where they contradict each other, and the precise questions that would settle it;
  - their forecasts on the Iran war, judged by their own later accounts;
  - a closing set of hypotheses, each with its supporters, objections and tests.
- `author-axes.html`: the charts page. Download it and open it in a browser. It shows:
  - each author scored from 1 to 5 on thirteen questions, every score backed by the author's own words;
  - who sits close to whom, and who is on the margin;
  - a chart of the personal advice the authors give;
  - test cases, the hypotheses and the evidence grids.
- `medium-draft.html`: a first-person article about the experiment.
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

- The fourteen were chosen for a shared outlook, so part of their agreement is built in.
- They share hosts, platforms and sometimes sources, so their agreement is not fully independent.
- Every score and every mark in the evidence grids is a judgement. Each one shows its quote or reason so it can be challenged.
