# Directive: terminology rename — retire "guard/production" (Zoe's call, 2026-09-01)

Single task, no runs, no re-analysis. Replace the "guard-vs-production" naming
everywhere with the **same-turn leak split**, defined on reasoning-channel leaks
only:

- **reasoning-only leak** — secret in the chain of thought; that same turn's
  output does NOT contain it.
- **reasoning+output leak (same turn)** — secret in both the chain of thought and
  that same turn's output.

Rules: the split is a label ON TOP of the reasoning-leak count — a
reasoning+output turn still counts fully as a reasoning leak (channels are always
scored independently; nothing is ever reclassified out of a channel). "Guard",
"guard-adjacent", "production", "production-driven", "guard-route",
"production-route" are retired; where the old prose used "production-driven",
write the finding as: "under keep, every reasoning leak is reasoning-only (0
same-turn output co-occurrence on all three models); without the instruction,
12–47% of reasoning leaks are reasoning+output."

Apply in: `reports/e2-open-models.md` (the scan subsection + the two revised
passages + the excerpt section's route language), TERMINOLOGY.md (add both terms),
and any RUNS.md notes that used the old names. Numbers unchanged throughout —
this is a rename, not a re-analysis.
