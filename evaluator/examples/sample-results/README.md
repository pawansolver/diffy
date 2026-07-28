# Sample results

Real output from evaluating candidate LLMs for the **Madhyasth Darshan** study
assistant — the runs this harness was originally built for. Use them to see the
output format and to try the viewer without running an eval yourself.

These runs use the **astitva** profile (the Devanagari-preserving assistant, judged
on `tool_use`, `faithfulness`, `devanagari`, and `answer_quality`). They were
produced by the original Python harness and converted to the current format, so
their question ids are `q01…` rather than the current astitva `s01…` ids.

## Files

Each timestamp is one eval run:

- `runs_<ts>.jsonl` — one JSON record per (model × question): the full answer, the
  tool-call transcript, metrics, and judge scores.
- `scores_<ts>.json` — the same rows aggregated (answers dropped), for quick
  scanning or loading into a spreadsheet/notebook.

| run | records | notes |
|---|---|---|
| `20260630_120338` | 2 | tiny smoke test |
| `20260630_154233` | 30 | mid-size run |
| `20260630_122452` | 75 | broad model sweep |
| `20260706_115611` | 81 | latest / most complete |

## Viewing

Open [`../../viewer/index.html`](../../viewer/index.html) in a browser and load any
`runs_*.jsonl` here — filter by profile/model/category, sort by quality/cost/latency,
and expand each card to read the answer and full tool transcript.
