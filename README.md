# elef-loop-test

Three small experiments on the worker–reviewer protocol ("the loop"), run on 11 to 13 November 2026. In each one a worker does a task in a local database with made-up data, and a reviewer session rules on the work from the record of the calls and from the answers of a few instruments. The harness plays ELEF's side: it records every call, holds the gates, and takes the answers.

Each experiment has a brief, a harness, the kept runs, every session as it was sent and answered, and a results note. Start with the notes.

## The experiments

| Experiment | Question | Sessions | Results note |
|---|---|---|---|
| 1 | Can a reviewer that sees no content tell where a task stands when it stops and when it resumes? | 30, on one model | [`results/note.md`](results/note.md) |
| 1b | Do the fixes close the gaps that experiment 1 found, and does the result hold on cheaper models? | 105, on Opus, Sonnet and Haiku | [`results_1b/note.md`](results_1b/note.md) |
| X1 | What does a reviewer's own inspection plan catch, with a price on each check and without? | 90, on Opus, Sonnet and Haiku | [`results_x1/note.md`](results_x1/note.md) |

In one line each:

- **Experiment 1:** yes, at this scale. In all 15 blind sessions the counts matched the stop record, and no session treated an unconfirmed call as free to try again.
- **Experiment 1b:** yes on all three models. A trace settles whether a doubtful call wrote its row, and the finding is kept apart from the record and the release.
- **X1:** a flat result. All 90 plans covered what the library of instruments could cover, and every ruling was right by the key. With a library that states its limits, the plan was within reach of all three models, so the experiment says little about how they differ in planning.

Each note gives its limits. These are single tasks in one environment, with a handful of sessions for each cell. They show how the protocol behaves on these cases, and they are not rates.

## What is where

| Path | What it holds |
|---|---|
| `uploads/` | The briefs as they were given. X1 has three: draft 2 (no suffix), draft 3 (`-1`) and draft 4 (`-2`). X1 was run on draft 4, with a clock line added to each wake after a pilot. |
| `loop/` | The harness, the views shown to a session, the blind checks, the scorers and the table makers. Files ending in `_fx` belong to 1b and files ending in `_x1` to X1. |
| `runs/`, `runs_1b/`, `runs_x1/` | The kept runs: the database, the record, and the answers taken at each moment. |
| `results/`, `results_1b/`, `results_x1/` | For each experiment: `note.md`, `tables.md`, `scores.json`, the hand judgements, the blind checks, and every session under `sessions/`. Pilots are kept apart and not counted. |
| `results_x1/report_before_the_90.md`, `results_x1/reply_after_the_90.md` | The two reports written to the brief's reviewer during X1. The second gives 13 sessions for a fault in the view; the note has the checked count, 14. |

## Running it

It needs Python 3 (run on 3.13, standard library only) and the `claude` command line tool, signed in. The sessions are headless `claude -p` calls, so running them costs money: the 90 sessions of X1 cost about $24.

The scorers and the tables read the kept sessions and cost nothing:

```sh
python -m loop.score_x1      # results_x1/scores.json
python -m loop.report_x1     # results_x1/tables.md
python -m loop.diff_x1       # how runs 1 to 4 differ from run 0
```

Note that these write over the kept files in `results_x1/`.

To make the runs of X1 again and run sessions:

```sh
python -m loop.x1                              # runs 0 to 4 under runs_x1/, and the prices
python -m loop.check_blind_x1 --sessions       # the blind check on the views and on everything sent
python -m loop.review_x1 sonnet priced 2 1 --pilot   # one session, kept apart
python -m loop.review_x1 all 8                 # the 90 sessions, 8 at a time
```

Experiments 1 and 1b work the same way through `loop.run_worker`, `loop.review`, `loop.score` and `loop.report`, and through `loop.fixes`, `loop.review_fx`, `loop.score_fx` and `loop.report_fx`. Each file gives its usage in its first lines.

Sessions run in a working folder outside the project, so that no project file is in their reach. Set `LOOP_SCRATCH` to choose it. The default is a folder under the system's temporary directory.

## Two things to know before reading the results

- **The reviewer sessions are blind to the experiment.** No session is told anything about runs, cuts, models or what is measured, and no session sees the key. A check scans every view and everything sent for strings that would give this away.
- **The runtime shows a session more than the harness sends.** Each session also sees a date for today, the name of its own model, the path of its working folder, and the signed-in account's email address. The harness could not remove this. Neither the address nor the path is in any file here.
