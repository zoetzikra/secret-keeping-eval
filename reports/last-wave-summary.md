# Last wave of runs — summary

## Background (one line)

The project measures how well a model keeps a prompt-given secret under an
extraction attack, and which channel it leaks in (output vs reasoning). E2 asks
whether telling the model to "never reveal" the secret makes it mention the secret
more in its reasoning.

## 1. Frontier models re-run on Petri — done

**What.** Re-ran four targets — Opus 4.6, Opus 4.8, Gemini 3.1 Pro, gpt-5-mini —
on the Petri auditor, both the keep arm and the no-instruction arm (8 runs, paired
on the same 20 secrets, 60 turns).

**Why.** These four had their keep arm run only on the weaker plain-harness
auditor, and had no no-instruction arm at all. So they weren't comparable to the
other targets (already on Petri), and E2 had no keep-vs-no-instruction contrast for
them.

**Result.**
- Under the stronger Petri auditor the four survival curves drop (they were flat on
  the plain harness), so the cross-model survival figure is now on one auditor and
  comparable.
- E2 result depends on the model's default behavior. gpt-5-mini keeps the secret
  by default (leaks nothing without the instruction) and is the only model where
  the keep instruction adds reasoning-channel leakage. Opus 4.6/4.8 and Gemini
  share the secret by default, and there the keep instruction reduces leakage
  rather than adding it.

## 2. Hidden-goal poster figures — done

**What.** Built two figures from existing hidden-goal logs (no new sampling for the
figures), and ran the three missing bare arms (S6, S5neg, S5aff) so those scenarios
have the full bare/default/keep axis.

**Why.** The poster needs the hidden-goal survival curve (panel 2) and the
concealment gradient.

**Result.**
- S3 survival figure shows the same channel split as the password eval: telling the
  model to hide its goal quiets the output channel but not the reasoning channel.
- Concealment gradient shows that fabricating a cover story is provoked by the
  credit scenarios (S2a/S2b), not by the benign constraint scenarios.

## 3. DeepSeek hidden-goal replication — running / queued

**What.** Replicating the hidden-goal scenarios on DeepSeek v4 Pro. S7 done; S2a
nearly done (2 samples short); S6 running now; S1 queued.

**Why.** DeepSeek returns its raw reasoning, so the reasoning-channel disclosure
counts are point estimates. The frontier models mostly hide or only summarize their
reasoning, so their counts are lower bounds.

**Status.** DeepSeek audits are slow (~20 min/sample), so this is the long-running
piece — roughly 20 hours left. Feeds the written report, not the poster.

## How it ties together

Waves 1 and 2/3 are the same two questions in the two settings the project uses:
the password setting (secret is a code) and the hidden-goal setting (secret is a
hidden instruction). This wave (a) put the frontier models on the same auditor so
they can be compared and gave E2 a keep-vs-no-instruction contrast on them, and
(b) produced the hidden-goal poster figures plus a raw-reasoning cross-model check
(DeepSeek) where the reasoning counts are exact rather than lower bounds.
