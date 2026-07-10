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
