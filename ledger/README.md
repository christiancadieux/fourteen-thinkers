# Ledger

The checking and chart layer for `synthesis.md`.

## Files

- `ledger.json`: the master data.
  - `charts`: each chart page's authors, axes, scores (with the reason for each) and personal advice.
  - `forecasts`: dated predictions, with the date each resolves and its status (open, hit, partly, miss). Authors' forecasts are judged by the authors' own later accounts. Hypothesis indicators (Treasury holdings, gold purchases, freight and so on) are judged on public data, with the source named.
  - `cases`: events that test the positions, such as the October 2026 diesel collision. They are shown on the chart page, and their quotes are checked.
  - `hypotheses`: the competing explanations, with supporting and opposing authors, tests and status. The build writes them into the closing "Hypotheses" section of `synthesis.md`, between the `<!-- hypotheses -->` markers (don't edit that block by hand), and onto the chart page.
  - `ach`: evidence grids (analysis of competing hypotheses). Each grid lists facts and explanations, marks each fact as fitting (C), against (I) or not bearing on (N) each explanation, and flags facts that could be staged. The build ranks the explanations by weighted facts against them (high reliability 1, medium 0.7, low 0.4), with and without the staged facts. It writes the ranking between the `<!-- ach -->` markers in `synthesis.md` and onto the chart page.
  - `checks`: dated checks that group forecasts and public-data indicators around one event, such as the November 2026 midterms. Forecasts belong to a check through their `check` field. The build writes each check into `synthesis.md` between its `<!-- check-… -->` markers.
  - `manual_checks`: quotes verified by hand where the saved text differs, for example a transcript spelling such as "deskkills".
- `sources/`: the authors' own texts, one folder per author. `index.json` maps each file to its URL where one was recoverable.
- `templates/`: the chart page template. Their data blocks are overwritten on every build.
- `build.py`: the checks and generation step.
- `report.md`: the output of the latest build. Don't edit it by hand.
- `build/`: the generated chart pages, used for publishing, and `quotes.json`, which lists every checked quotation with its source.
- `import_initial.py`: the one-off script that created `ledger.json` from the old pages. It is kept for reference and doesn't need to be run again.

## What a build does

1. Checks every quotation in `synthesis.md` against the named author's own texts. If no author is named on the line, it uses the author named in the preceding lines. It reports quotes found only under another author, or not found at all.
2. Checks every "N of the fifteen (A, B and C)" count against its list.
3. Checks the quotes inside chart reasons and advice.
4. Lists chart scores whose reason has no checked quote, or only one. That list shows where more reading would pay off.
5. Writes the chart data from `ledger.json` into `build/*.html` and the standalone copy `../author-axes.html`.

## Adding an author or a score

1. Save their texts in `sources/<Name>/`.
2. Add the author, their scores and any advice to `ledger.json`.
3. Add their colour and class to the template, the same way as the existing authors.
4. Write the prose in `synthesis.md`.
5. Run `python3 build.py`, and fix anything listed in `report.md` before publishing.
