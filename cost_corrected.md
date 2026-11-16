# The cost figures, corrected

**16 November 2026.** The runtime's cost figure for a resumed session is a running total over its turns. The harness of experiments 1, 1b, X1 and X7 added that figure up turn by turn, so a session's cost was counted several times over. Here a turn costs the difference from the turn before, and a session costs its last figure. The figure is the runtime's price of the tokens at list prices; on a subscription it is not a sum that was paid. Tokens, wall time and every other measure were right and are unchanged. Made by `python -m loop.cost` from the kept sessions.

## The totals

| experiment | sessions | as the notes gave it | corrected |
|---|---|---|---|
| 1 | 30 | $83.90 | $25.41 |
| 1b | 105 | $76.43 | $20.53 |
| X1 | 90 | $24.10 | $6.89 |
| X7 | 120 | $64.33 | $18.69 |

## Experiment 1: the cost of a review

One model, `claude-fable-5-2`. A review is one session: the four moments of one run.

| arm | sessions | as the note gave it, a review | corrected, a review | corrected, all |
|---|---|---|---|---|
| blind | 15 | $2.54 | $0.78 | $11.71 |
| sighted | 15 | $3.05 | $0.91 | $13.70 |
| both | 30 | $2.80 | $0.85 | $25.41 |

The pilot session: $0.73 (as first summed $2.42).

## Experiment 1b: the cost of a review, by model

| model | condition | sessions | as the note gave it, a review | corrected, a review | corrected, all |
|---|---|---|---|---|---|
| opus | asis | 15 | $1.21 | $0.385 | $5.77 |
| opus | fixes | 20 | $1.72 | $0.414 | $8.29 |
| opus | both | 35 | $1.50 | $0.402 | $14.06 |
| sonnet | asis | 15 | $0.46 | $0.151 | $2.27 |
| sonnet | fixes | 20 | $0.74 | $0.182 | $3.63 |
| sonnet | both | 35 | $0.62 | $0.169 | $5.90 |
| haiku | asis | 15 | $0.04 | $0.014 | $0.22 |
| haiku | fixes | 20 | $0.07 | $0.018 | $0.35 |
| haiku | both | 35 | $0.06 | $0.016 | $0.57 |
| all | both | 105 |  |  | $20.53 |

The six pilot sessions: $1.36 (as first summed $6.04).

## X1: the cost of a session, by model and condition

| model | condition | sessions | as the note gave it, a session | corrected, a session | corrected, all | the plan | wake A1 | wake A2 | the verdict |
|---|---|---|---|---|---|---|---|---|---|
| opus | priced | 20 | $0.467 | $0.140 | $2.81 | $0.026 | $0.056 | $0.039 | $0.077 |
| opus | free | 10 | $0.849 | $0.227 | $2.27 | $0.029 | $0.053 | $0.047 | $0.097 |
| opus | both | 30 | $0.594 | $0.169 | $5.08 | $0.027 | $0.055 | $0.043 | $0.087 |
| sonnet | priced | 20 | $0.144 | $0.044 | $0.88 | $0.008 | $0.016 | $0.017 | $0.025 |
| sonnet | free | 10 | $0.281 | $0.078 | $0.78 | $0.007 | $0.019 | $0.021 | $0.031 |
| sonnet | both | 30 | $0.190 | $0.056 | $1.67 | $0.008 | $0.017 | $0.019 | $0.028 |
| haiku | priced | 20 | $0.015 | $0.004 | $0.08 | $0.001 | $0.001 | $0.001 | $0.002 |
| haiku | free | 10 | $0.029 | $0.007 | $0.07 | $0.002 | $0.002 | $0.001 | $0.002 |
| haiku | both | 30 | $0.019 | $0.005 | $0.15 | $0.001 | $0.001 | $0.001 | $0.002 |
| all | both | 90 |  |  | $6.89 |  |  |  |  |

A session that goes to the end (run 0), corrected: opus priced $0.186, free $0.225; sonnet priced $0.060, free $0.080; haiku priced $0.005, free $0.006.

The pilots of X1, six sessions each:

| pilot | sessions | as first summed | corrected | opus | sonnet | haiku |
|---|---|---|---|---|---|---|
| pilot | 6 | $2.54 | $0.61 | $0.42 | $0.17 | $0.01 |
| pilot_draft2 | 6 | $2.58 | $0.60 | $0.44 | $0.15 | $0.01 |
| pilot_draft3 | 6 | $3.00 | $0.67 | $0.50 | $0.16 | $0.01 |
| pilot_draft4_no_time | 6 | $2.82 | $0.64 | $0.46 | $0.17 | $0.01 |

## X7: the cost of a session, by model, by run and by act

The acts are means over the sessions that reached the act. A session that goes to the end is one that reached the verdict.

| model | run | sessions | as the note gave it, a session | corrected, a session | corrected, all | the plan | wake A1 | wake A2 | the verdict | reached the verdict | a session to the end |
|---|---|---|---|---|---|---|---|---|---|---|---|
| opus | 0 | 10 | $1.579 | $0.449 | $4.49 | $0.047 | $0.107 | $0.067 | $0.228 | 10 | $0.449 |
| opus | U | 10 | $0.814 | $0.243 | $2.43 | $0.048 | $0.124 | $0.071 | — | 0 | — |
| opus | R1 | 10 | $0.327 | $0.146 | $1.46 | $0.051 | $0.095 | — | — | 0 | — |
| opus | R2 | 10 | $1.669 | $0.470 | $4.70 | $0.048 | $0.115 | $0.069 | $0.238 | 10 | $0.470 |
| opus | all | 40 | $1.097 | $0.327 | $13.08 | $0.048 | $0.110 | $0.069 | $0.233 | 20 | $0.459 |
| sonnet | 0 | 10 | $0.639 | $0.156 | $1.56 | $0.019 | $0.056 | $0.033 | $0.049 | 10 | $0.156 |
| sonnet | U | 10 | $0.362 | $0.108 | $1.08 | $0.019 | $0.060 | $0.029 | — | 0 | — |
| sonnet | R1 | 10 | $0.154 | $0.075 | $0.75 | $0.019 | $0.056 | — | — | 0 | — |
| sonnet | R2 | 10 | $0.660 | $0.166 | $1.66 | $0.019 | $0.055 | $0.033 | $0.059 | 10 | $0.166 |
| sonnet | all | 40 | $0.454 | $0.126 | $5.05 | $0.019 | $0.057 | $0.032 | $0.054 | 20 | $0.161 |
| haiku | 0 | 10 | $0.069 | $0.016 | $0.16 | $0.003 | $0.005 | $0.003 | $0.004 | 10 | $0.016 |
| haiku | U | 10 | $0.042 | $0.012 | $0.12 | $0.003 | $0.006 | $0.003 | — | 0 | — |
| haiku | R1 | 10 | $0.057 | $0.013 | $0.13 | $0.003 | $0.005 | $0.003 | $0.003 | 8 | $0.014 |
| haiku | R2 | 10 | $0.062 | $0.014 | $0.14 | $0.003 | $0.004 | $0.003 | $0.004 | 10 | $0.014 |
| haiku | all | 40 | $0.058 | $0.014 | $0.55 | $0.003 | $0.005 | $0.003 | $0.004 | 28 | $0.015 |
| all | all | 120 |  |  | $18.69 |  |  |  |  |  |  |

The pilots of X7, six sessions each: `pilot_1_draft2` $1.48 (as first summed $6.10); `pilot` $0.70 (as first summed $2.30).

## X7: cost by reading

The sessions on the two runs whose cut shows only in the record, set apart by whether the session had the lines in front of it (table 7 of X7), with what a session of each kind cost. A session that proves a cut ends there, so on R1 a find ends at A1 and costs less than a miss that goes on to the verdict; on R2 the cut is at A3 and both go to the end.

| run | model | the reading | sessions | found and proved | questions to the record, mean | corrected, a session | as first summed |
|---|---|---|---|---|---|---|---|
| R1 | opus | all the account reads covered | 10 | 10 | 3.7 | $0.146 | $0.327 |
| R1 | sonnet | all the account reads covered | 10 | 10 | 2.2 | $0.075 | $0.154 |
| R1 | haiku | all the account reads covered | 2 | 2 | 3.5 | $0.010 | $0.021 |
| R1 | haiku | not | 8 | 0 | 4.0 | $0.014 | $0.066 |
| R2 | opus | all 100 sending lines with their times returned | 10 | 10 | 10.1 | $0.470 | $1.669 |
| R2 | sonnet | all 100 sending lines with their times returned | 2 | 2 | 7.0 | $0.229 | $0.821 |
| R2 | sonnet | not | 8 | 0 | 5.6 | $0.150 | $0.619 |
| R2 | haiku | not | 10 | 0 | 5.1 | $0.014 | $0.062 |

On clean work (run 0), where every session goes to the end, by how much of the sending lines the session had returned with their times:

| model | sessions | sending lines with their times returned, mean of 100 | questions to the record, mean | corrected, a session |
|---|---|---|---|---|
| opus | 10 | 90.4 | 9.5 | $0.449 |
| sonnet | 10 | 1.8 | 6.4 | $0.156 |
| haiku | 10 | 3.4 | 4.5 | $0.016 |
