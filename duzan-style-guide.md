# Style guide: write like Duzan & Cooper Stickland (arXiv 2608.04735)

Written as a prompt for a drafting agent. Everything below is derived from the paper's body (§1–§6, ~5,700 words, 206 sentences) and appendices; quoted fragments are verbatim. Corpus statistics: median sentence 26 words, 16% of sentences ≤12 words, 30% ≥35 words; 91 colons, 95 parentheses, 17 semicolons, 4 em-dashes; "we" 45×, "but" 28×, "so" 22×, "however" 1×, "therefore/thus/hence/moreover/furthermore" 0×.

---

## 0. The one-paragraph version

Write in first-person plural, present tense, active voice. State each finding as a plain fact with its number in the same sentence, then use a colon to unpack it, then give the contrast or the exception, then stop. Numbers carry the argument; interpretation gets one sentence at the end of a paragraph or is deferred to the Discussion. Prefer "but", "so", "yet", "still", "while" to "however", "therefore", "moreover". Never praise the work; never editorialise ("interestingly", "importantly", "note that"); never ask the reader to trust you — point them at an appendix instead.

---

## 1. Voice and tense

- **First-person plural throughout.** "We introduce", "We test", "We find", "We validate the monitor against", "Our contribution is to vary how the intervention is delivered." Never "I", never "the authors", never "this paper shows" — the paper is always "we" or "our benchmark".
- **Present tense for everything the paper does and finds.** "Nudges reliably steer model answers in every condition." "Detection falls to 16% on average." "The explicit variant inverts this picture." Past tense only for (a) one-off procedures — "we manually labelled 120 cases", "We designed 35 candidates" — and (b) prior work's historical claims — "Lanham et al. [2023] and Turpin et al. [2023] established that…".
- **Active voice by default.** Passive is reserved for methodology facts where the agent is obvious or irrelevant: "The tasks and the nudges are held fixed across the two forms", "Full monitor prompts are in Appendix C.1", "the nudge is delivered either as a casual aside…". Roughly one passive per 150 words; never in a results sentence that reports a number.
- **The model is the grammatical subject of behaviour sentences.** "the model switches", "models leak their compliance into the CoT", "Opus rises from 6% to 76%", "Grok barely moves". Not "it was observed that the model…".
- **Contractions are permitted but rare** (one "doesn't" in a Discussion heading). Use at most one or two in the whole body, only in Discussion.

## 2. Sentence architecture

- **Two sentence types alternate.** Short declaratives that state a fact (≤12 words: "The nudge does not survive.", "This axis is orthogonal to Guan et al. [2025]'s taxonomy.") and long expository sentences (35–60 words) built around a colon or a pair of parallel clauses. A paragraph typically opens short, expands long, and closes short or medium.
- **The colon is the signature.** One per ~60 words. Its job is claim → unpacking:
  - claim : mechanism — "In particular, the hard regime is not the adversarial one: the explicit variants instruct the model to conceal its reason, yet models leak their compliance into the CoT"
  - claim : numbers — "Adding the adversarial system prompt to the explicit arm lowers detection from 62% to 52%: it falls sharply for Opus (38%→13%) and GLM (86%→20%) but changes only modestly for the other five models."
  - term : definition — "Our primary metric is monitor detection rate: the fraction of behavioral-shift cases in which the monitor detects the nudge's influence in the CoT."
  - Never use a colon to introduce a bulleted list in the body.
- **Parentheses carry the numbers and the pointers,** never the argument. Three uses only: per-model ranges after an average — "detection averages 62% across models (23–86%)"; appendix and section pointers — "(Appendix B.1)", "(Section 4.5)", "(per-model rates in Appendix D.3)"; short glosses — "(an addition a developer might use to reduce off-topic influence on the model's outputs)". A parenthesis sits at the end of its clause, not mid-clause.
- **Semicolons join parallel results,** typically two or three clauses with the same shape: "Setting 3 implicit is perfect agreement, and the weakest cell is Setting 1 explicit (κ = 0.53, still at 80% agreement), where the small per-cell n makes κ sensitive to one or two cases." Not for joining unrelated thoughts.
- **Em-dashes are almost absent** (4 in the body). Do not use them for asides; use parentheses or a new sentence.
- **Parallel construction is deliberate.** "implicit, where the nudge appears as a casual aside, and explicit, where the user directly instructs the model to act on the nudge and to conceal having done so." Both halves have the same grammar. When listing conditions, repeat the noun: "implicit delivery, explicit delivery, implicit delivery with a guidance system prompt (…), and explicit delivery with an adversarial system prompt".
- **Gerund openers describe an intervention and its effect in one sentence.** "Adding the guidance system prompts to the implicit arm pushes detection down further", "Making the nudge load-bearing on the implicit arm significantly recovers detection", "Making reasoning load-bearing helps, but doesn't close the gap." Use this for any "we changed X and Y happened" sentence.
- **Sentence openers, in order of frequency:** The / We / Our / In [Setting n] / Each / For each / Under [condition] / Adding / Making / This / Across / When. Avoid opening with "It is", "There is/are", "Note that", "Notably", "Interestingly", "Importantly", "As expected", "As shown".

## 3. Paragraph architecture

- **Results paragraph, fixed order:** (1) behaviour-shift confirmation with the range — "Nudges reliably steer model answers in every condition, with per-model switch rates of 31–53% under implicit delivery"; (2) figure pointer — "Figure 3 shows the monitor's detection rate under each condition"; (3) the primary contrast with averages and per-model spread — "Under explicit delivery, detection averages 62% across models (23–86%), despite the concealment instruction. Under implicit delivery of the same nudges, it falls to 16% on average, with no model above 40%"; (4) the secondary conditions, one sentence each; (5) the exception or outlier, named — "Opus sits at 0% in both arms because…"; (6) a forward pointer — "(Section 4.5)".
- **One paragraph, one contrast.** A paragraph never reports two independent findings. If a second finding needs saying, it gets its own paragraph, and that paragraph's first sentence names it.
- **Setup paragraphs start with structure, end with a pointer.** "All four settings share a common structure. Each presents the model with a baseline task, elicits a default behavior, then re-runs the task with a small nudge: a detail added to the prompt that is irrelevant to the task's stated criteria but still steers the answer, e.g. a passing remark that one airline has been criticized for labor practices." … "Nudge taxonomy, scenario filtering, and exact prompt wording are in Appendix B.1." Every setup subsection's last sentence sends the reader to an appendix.
- **The interpretation sentence is last and short.** "This suggests that explicit-influence settings may give a poor estimate of CoT monitorability in the wild." One per paragraph at most; most results paragraphs have none.
- **Caveats are enumerated inline.** "However this comes with two caveats. First, recovery is only partial: … Second, the depth needed to make the nudge load-bearing grew with model strength: …" — "First/Second", each followed by a colon.

## 4. Numbers and quantities

- **Percentages, no decimals in the body.** "62%", "16%", "5%". Decimals only in appendix tables ("16.2%", "κ = 0.73").
- **Ranges with an en-dash, no spaces:** "23–86%", "31–53%", "41–46 percentage points", "60–94%".
- **Change with an arrow inside parentheses:** "(38%→13%)", "(86%→20%)", "(12%→51%)". In running text: "from 62% to 52%", "rises from 16% to 51%".
- **Differences in "percentage points"**, never "percent lower".
- **Averages always come with the spread:** "averages 62% across models (23–86%)"; "a pooled 60% (38–97% per model)".
- **Counts as "n of m" in words:** "in two of four settings", "6/7 models near 0%", "three of four domains". Sample sizes as "n = 15", with spaces round the equals sign.
- **Statistics named tersely and once:** "Bonferroni-corrected p < 0.05, |mean shift| ≥ 0.5", "Welch's t-test", "Cohen's κ is 0.73", "pooled agreement is 88.3%". The test is named where the criterion is defined (§3), not repeated in every results sentence.
- **Ceiling and floor are vocabulary, not metaphors:** "already near ceiling", "near-zero", "floor effect", "leaves no room for further reduction", "sits at 0%".
- **Model names:** full name with version at first mention and in figure legends ("Claude Haiku 4.5, Sonnet 4.5, and Opus 4.5"; "GLM-4.7"; "gpt-oss-120b"); short form thereafter in prose ("Opus", "Sonnet", "Grok", "GLM", "Kimi"). Never "the Anthropic model".

## 5. Vocabulary

- **Verbs of movement, graded by size** (use these, not synonyms): rises / falls / drops / lowers / cuts / pushes down / recovers / collapses (for ≥30 points) / barely moves / changes only modestly / stands out / leaves essentially unchanged / sits at / inverts this picture / widens the gap / brings it to.
- **Nouns of design:** setting, arm, condition, delivery (form), nudge, baseline, variant, regime, cell, case, subset, matched pair, screening, filtering, taxonomy.
- **Nouns of measurement:** detection rate, switch rate, flip, behavior shift, behavioral-shift cases, compliance, true-negative rate, pooled, per-model, aggregate.
- **Adjectives that recur:** matched, held fixed, load-bearing, near-ceiling, near-zero, benign-looking, monitor-aware, deployment-relevant, realistic, favorable (of monitor conditions), structurally different, uninstructed.
- **Hedges, plain and few:** "suggests", "may", "plausibly", "consistent with", "is suggestive rather than conclusive", "we view that as a complementary research direction", "a natural follow-up is", "a natural extension is". Never "we believe", "we argue", "arguably", "it seems".
- **Connectives:** but (28×), so (22×, causal: "so the monitor often misses it"), while (13×, contrastive), yet (3×), still, even, only, rather than, instead of, in particular, as in the other settings, in contrast to. Do not use: however (≤1 in the whole paper), therefore, thus, hence, moreover, furthermore, additionally (≤2), consequently, nevertheless, notably, importantly, interestingly, crucially.
- **Words that never appear:** novel, state-of-the-art, comprehensive, rigorous, careful (of own work), extensive, robustly (of own claims), clearly, obviously, we believe, we hope, it is worth noting, note that, in this paper, in this work, to the best of our knowledge.
- **US spelling:** behavior, labeled/labelled both occur (pick "labeled"), color, optimize, summarized.

## 6. Definitions, emphasis and typography

- **New term: italic on first use, then a colon or "where".** "*explicit-influence settings*: setups where the prompt directly incentivizes the model to hide something"; "implicit, where the nudge appears as a casual aside".
- **Bold for named conditions in setup and for run-in headings.** "**prefill**, which asks the model to begin its CoT with a confident opening phrase, and **practical-focus**, which instructs it to…"; appendix run-in headings "**Nudge taxonomy.**", "**Explicit variant.**", "**Adversarial system prompt.**" — bold, sentence case, terminal full stop, text continues on the same line.
- **Quotation marks for imagined model or user speech and for prompt fragments.** "(e.g., 'they want X, so I'll go with it')", "an instruction ('do this hidden side-task')". Prompt text longer than a clause is set as an italic block quote.
- **Code font for identifiers only:** `inspect_ai`, `answer_type = multipleChoice`, `max_completion_tokens=2048`.
- **Section titles are Title Case with a colon for settings:** "3.1 Setting 1: Binary Preference Elicitation with Injected Constraints". One rhetorical-question title in the whole paper ("4.5 What if Acting on the Nudge Requires Multi-step Reasoning?") — permitted once.

## 7. Citations and prior work

- **Author-year in square brackets, natbib style:** "[Zolkowski et al., 2025]", "[Guan et al., 2025, Baker et al., 2025]".
- **Prior work as grammatical subject, present tense, verb of what they did:** "Arnav et al. [2025] instruct the monitored model to complete a harmful side task…", "Emmons et al. [2025] prompt models to actively evade a CoT monitor, finding that…", "Guan et al. [2025] report aggregate g-mean² of roughly 0.7–0.8".
- **Agreement phrased as "consistent with X, who show that":** "The direction of this effect is consistent with Emmons et al. [2025], who show that when acting on the intervention requires multi-step arithmetic, unattributed influences disappear entirely. In our case, recovery is only partial (where theirs is near total)."
- **Positioning is a contrast of scope, never a criticism of people:** "but frames the question as one of CoT faithfulness rather than CoT-monitor evaluation", "but as separate evaluations on different tasks, so detection rates across the two regimes are confounded by task differences, and the suite does not focus on the distinction. No prior work compares the two regimes directly."
- **Borrowed structure is credited in one sentence:** "This is the intervention structure of Guan et al. [2025]: the nudge is a controlled intervention on the input, and the monitor must infer from the CoT whether it drove the model's behavior. Our contribution is to vary how the intervention is delivered."

## 8. Cross-references

- Every method detail that would take more than two sentences is replaced by a pointer: "(construction details and example pairs in Appendices B.1–B.4)", "the screening procedures are setting-specific and detailed in Appendix B", "Full monitor prompts are in Appendix C.1".
- Figures are introduced with "Figure 3 shows…" or "Figure 7 reports results on…", then read left to right in prose. Tables likewise: "Table 1 organizes the works we cite by…".
- Forward references are parenthetical and specific: "(Section 4.5)", "(Appendix D.5)". No "see below" / "as discussed above" without a number.

## 9. Section-specific templates

- **Abstract (8–9 sentences, one beat each):** field claim → what most evaluations study (with the term in italics) → the complementary axis (with the term) → "We introduce the first…" → what is varied → scale ("four task formats … and seven frontier extended-thinking models") → headline number for regime 1 → headline number for regime 2 with the gap in points → the deployment-relevant twist with its number → "These results suggest that…" → code URL.
- **Introduction:** paragraph 1 = the field's optimism with three citations in one sentence; paragraph 2 = "We propose classifying… by…" with both terms defined in italics and an example in quotation marks; paragraph 3 = "This axis is orthogonal to…"; paragraph 4 = prior work in explicit settings (three named studies) then "Cases of implicit influence have been studied, but…" (four named studies) then "No prior work compares the two regimes directly."; paragraph 5 = "We present…" with the design in one sentence and the headline in the next; paragraph 6 = the twist; then "Our main contributions and findings are:" and four bullets, each a bold sentence followed by one or two plain sentences with numbers.
- **Related work:** a taxonomy table with a two-sentence caption; then bold run-in paragraphs ("**What is known about CoT faithfulness and monitorability.**", "**Comparison to existing monitorability evaluations.**"); every sentence cites; closes by computing the other paper's metric on your data.
- **Experimental setup:** §3.0 common structure (five sentences, ending with the design's borrowed lineage); §3.n one per setting, each three paragraphs — task and nudges, screening, guidance prompt names in bold; §3.models — list, reasoning budgets, one caveat about CoT access; §3.measuring — the monitor's conditions ("operates under favorable conditions: it receives the full CoT, is told exactly which nudge to look for…"), what it does not know, the primary metric with a colon definition, the validation numbers.
- **Results:** one subsection per setting, titled identically to its setup subsection; figure per subsection; paragraph structure as in §3 above. A final subsection for the mechanism variant ("What if…"), which opens by stating what the two arms are comparable to and not comparable to.
- **Discussion and Future Work:** bold run-in headings that are complete claims, 3–6 sentences each: a restatement with the numbers; a "helps, but doesn't close the gap" paragraph with "two caveats. First… Second…"; "**Limitations: the monitor is an LLM judge.**" with the plain sentence "so the gap we report is a gap in X, not a claim that Y"; a deployment-relevant caveat ("This is a deployment-relevant input rather than a deliberate choice to discard signal"); "**Toward worst-case…**"; "**Model organisms…**" ending with pointers to exploratory appendices.
- **Conclusion (one long paragraph + one short):** "We introduced a distinction between… and showed that… To compare the two regimes directly, we built… The comparison shows a consistent ordering." Then the three headline numbers again, then "These findings suggest that…", then "More work is needed to characterize when and why … before it can be relied upon as…".
- **Figure captions:** first sentence names the setting and unit ("Setting 1 (binary preference elicitation), per model."); second defines the bar ("Each bar shows the detection rate (percentage of flip cases in which the monitor detects the nudge's influence) under each condition."); optional third names the exception ("Under implicit delivery, Grok 3 Mini is the exception to near-total opacity."). Multi-panel captions use bold **Left:** / **Middle:** / **Right:**.
- **Appendix prose:** same voice, run-in bold headings, bulleted taxonomies allowed, footnotes for non-estimable cells ("† Not estimable. … so we report no value."), and one-paragraph "Interpretation." subsections that explain what a metric does and does not show.

## 10. What the style refuses to do

- No rhetorical build-up before a number. The number is in the first sentence of the paragraph.
- No adjectives about the work's quality. Rigor is shown by pointers to validation, not asserted.
- No bulleted lists in the body except the contribution list.
- No "we hypothesise that…" preambles; hypotheses appear as the reason a condition exists ("since they have little effect under explicit delivery (Appendix D.5)").
- No repetition of the p-value convention in results sentences once it is defined in setup.
- No summary sentence at the end of a results subsection; the subsection ends on its last datum or pointer.
- No softening of a null: "The result is a null: the identical string that takes Setting 4's implicit arm from 93% to 57% does essentially nothing (94→95%) on the explicit arm."

---

## 11. Worked example — one of Fifi's results rewritten in this style

Source content: `reports/e2-open-models.md`, frontier + open E2 table.

> **4.2 The instruction effect tracks the provider baseline**
>
> The keep instruction raises reasoning-channel leakage on only one target. Figure 2 shows reasoning-channel leaks per target under each arm, paired on the same twenty secrets. On gpt-5-mini, the secret appears in the reasoning of 13 of 20 investigations under the keep instruction and in none without it (exact McNemar p = 0.0002); its no-instruction arm leaks nothing in any channel, so it is the only target that protects the secret by default. On the six targets that share the secret by default, the same instruction never raises reasoning leakage: it is flat on DeepSeek (19 vs 19) and Gemini (16 vs 16), and lower on Opus 4.6 (20→5, p = 0.0001) and GLM (20→10, p = 0.002). Across these six targets, not one secret leaked in reasoning under keep but not under no-instruction. The output channel tells the complementary story: the instruction cuts output leaks on every target that needs it (DeepSeek 16→4, GLM 16→1, Kimi 11→1, Opus 4.6 18→2), and has nothing to cut on gpt-5-mini.
>
> The two arms' reasoning mentions are not the same kind of event. Under keep, none of the reasoning mentions on any raw-CoT target co-occur with the secret in that turn's output (93–100% reasoning-only); under no-instruction, 12–47% do on the open models, 74% on Opus 4.6 and 94% on Gemini. So the instruction does not add rehearsal on top of sharing: where the model would have shared, it removes the sharing, and where the model would have said nothing, it adds the rehearsal. This is the white-bear effect of Section 3.1, but only on the side of the split where the baseline is silent.
>
> The plain-harness anchor points the same way. On gpt-5-mini under the scripted auditor, keep leaks in reasoning in 15/20 and 12/20 investigations across two runs against 2/20 without the instruction (p = 0.002, p = 0.006), with output at 1/20 in every arm and reasoning visibility at 60–64% throughout. Two auditors, one direction (Appendix D.2). The contrast reported here differs from the one we pre-stated: the design was frozen to test whether instruction-induced rehearsal replicates on raw-CoT targets, and it does not; the dependence on the baseline was identified after the runs, on this seed set (Section 5).

What the rewrite does, mapped to the rules: opens on the finding with its number (§3); colon after every claim (§2); arrows and "vs" inside parentheses (§4); "so" and "but" as the only connectives; the model as subject; one interpretation sentence per paragraph, at the end; the pre-registration caveat stated as a plain fact with a pointer, not as an apology (§10).

## 12. Checklist for the drafting agent, per paragraph

1. First sentence: finding + number. No preamble.
2. At least one colon doing claim → evidence work.
3. Every average has its spread in parentheses; every change has an arrow or "from X to Y".
4. Connectives drawn from: but / so / while / yet / still / even / only / rather than.
5. Zero occurrences of: however, therefore, thus, moreover, furthermore, notably, importantly, interestingly, note that, novel, rigorous, comprehensive, we believe.
6. Interpretation ≤ 1 sentence, last.
7. Ends with a datum or a pointer, not a summary.
8. Passive only for setup facts; results sentences active with the model or the metric as subject.
9. Prior work: "[Author et al., year]" as subject or "consistent with X, who show that".
10. Hedge vocabulary limited to: suggests / may / plausibly / consistent with / suggestive rather than conclusive.
