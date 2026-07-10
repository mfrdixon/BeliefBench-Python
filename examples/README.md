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

## Full confirmatory study

`financial_full.yaml` defines seven independent seeds, 45 scenarios per seed,
five repeats, and exact accept--reject sampling of 15 Low, 15 Medium, and 15 High
entropy scenarios per seed. The resulting 315 scenarios contain 105 observations
per entropy stratum. Run:

```bash
pip install numpy pandas
pip install https://github.com/mfrdixon/BeliefBench-Python/releases/download/v0.4.0/beliefbench-0.4.0-py3-none-any.whl
python examples/run_financial_full.py
```

The runner audits entropy balance, combines all seed outputs, and writes 95%
cluster-bootstrap intervals with `(seed, scenario_id)` as the resampling unit.
Three seed jobs run concurrently, and each server job evaluates up to twenty
measurement units concurrently across scenarios, views, methods, and repeats.
Completed seed archives are reused after interruption. Adjust `seed_concurrency` and `concurrency` to
respect provider rate limits and the Render instance size.
It can reserve up to 291,900 output tokens per seed and 2,043,300 across the full
study; review provider cost and Render duration before starting it.
