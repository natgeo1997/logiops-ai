# Synthetic evaluation protocol

This small benchmark checks priority classification on twelve **fictional, hand-labelled** reports: three each for Critical, High, Medium and Low. Reference labels are illustrative judgments based on the application's priority definitions. They are not independently adjudicated ground truth or a representative production dataset.

## Reproduce

From the repository root, install `requirements-dev.txt` and choose one mode:

```bash
# No model or API call: constant-Medium comparator
python evaluation/run.py --baseline --output evaluation/results/baseline

# Real model responses: requires your own key and can incur provider charges
python evaluation/run.py --live --model gemini-2.5-flash --output evaluation/results/gemini

# Re-score previously captured responses without calling an API
python evaluation/run.py --responses evaluation/results/gemini/responses.json --output evaluation/results/rescored

python -m pytest -q
```

The live runner calls the same `analisar` function and Pydantic schema as the application. It makes one application-level request per case; the provider SDK may retry transport requests. No live run occurs in regular CI. The separate **Evaluate Gemini (manual)** Actions workflow requires a repository secret called `GEMINI_API_KEY` and an explicit manual dispatch.

Outputs: `metrics.json`, `responses.json` and a blank `human-review.json`. Generated results are ignored by Git. Review them before intentionally publishing any result; the supplied cases contain only fictional data. Missing and failed responses count as failures in the full denominator. Unknown and duplicate IDs are rejected.

## Metrics and their limits

| Metric | Definition | What it does not establish |
| --- | --- | --- |
| Valid response rate | Responses accepted by the app's schema / all cases | Truthfulness or sound advice |
| Priority accuracy | Valid responses matching the reference priority / all cases | Generalization to real incidents |
| Action-count compliance | Valid responses with 3–6 recommended and 2–4 preventive actions / all cases | Quality of those actions |
| Median latency | Median elapsed time for attempted calls with timing | A production service-level guarantee |

The constant-Medium baseline scores **3/12 = 25% priority accuracy** on this balanced fixture by construction. This is a measured comparator result, **not a Gemini score**. Placeholder text in this comparator is not a useful assessment. No Gemini accuracy result is published until a real run is performed and reviewed.

## Human review

Read each response against its report and `review_focus`. Score each dimension from 0 to 2: **0** = fails, **1** = partially meets, **2** = meets.

- **Factual grounding:** uses reported facts; avoids invented causes, times, costs and completed actions.
- **Uncertainty:** separates hypotheses from facts and requests relevant missing information.
- **Actionability:** proposes specific, proportionate next steps that follow from the report.
- **Human control:** keeps communications as drafts and decisions with the responsible professional.

Record reviewer notes and score rationale. Do not treat a blank review file as a passed review. For stronger evidence, use multiple reviewers, held-out cases, repeated model runs and representative authorized data. Prompt-injection resistance and domain-specific safety need separate evaluation; this fixture does not measure them.
