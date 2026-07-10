# Financial example

This is the runnable Bull/Bear/Crisis case study described in the usage guide.
It uses one scenario, two repeats, and one trajectory step so the live example
produces a repeatability statistic while remaining inexpensive. Increase these
values only after checking `/v1/health` limits and the worst-case reservation.

```bash
export OPENAI_API_KEY='...'
export BELIEFBENCH_SERVICE_TOKEN='...'
python examples/run_financial_case_study.py
```

The result archive is written to
`examples/output/financial-example-results.zip`.

## Slim multi-seed study

`financial_full.yaml` defines four independent seeds, 30 scenarios per seed,
five elicitation repeats, one inferred-belief and decision measurement per
condition, and exact accept--reject sampling of 10 Low, 10 Medium, and 10 High
entropy scenarios per seed. The resulting 120 scenarios contain 40 observations
per entropy stratum. The BaselineRAG diagnostic is restricted to the reference
view, keeping the scientific focus on absolute frontier-model belief quality.
Run:

```bash
pip install numpy pandas
pip install https://github.com/mfrdixon/BeliefBench-Python/releases/download/v0.6.0/beliefbench-0.6.0-py3-none-any.whl
python examples/run_financial_full.py
```

The runner audits entropy balance, combines all seed outputs, and writes 95%
cluster-bootstrap intervals with `(seed, scenario_id)` as the resampling unit.
Three seed jobs run concurrently, and each server job evaluates up to eight
measurement units concurrently across scenarios, views, methods, and repeats.
Completed seed archives are reused after interruption. Adjust `seed_concurrency` and `concurrency` to
respect provider rate limits and the Render instance size.
The worst-case reservation is 135,000 output tokens per seed and 540,000 across
the study. Successful measurement units are checkpointed deterministically. The
default local backend survives job retries; for deployment-level durability set
`checkpoint.backend: s3`, plus `bucket` and an optional `prefix`, and configure
the hosted service with AWS credentials that can access only that prefix.
