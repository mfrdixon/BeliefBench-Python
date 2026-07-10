# BeliefBench Python SDK

This public repository contains only the thin hosted-service client. The
probabilistic benchmark engine is not distributed with the package.

```bash
pip install https://github.com/mfrdixon/BeliefBench-Python/releases/download/v0.6.0/beliefbench-0.6.0-py3-none-any.whl
export OPENAI_API_KEY='...'
export OPENAI_MODEL='gpt-4.1-mini'  # optional; this is the default
export BELIEFBENCH_SERVICE_TOKEN='...'
export BELIEFBENCH_API_URL='https://beliefbench-api.onrender.com'
```

```python
import os
from beliefbench import BeliefBench
with BeliefBench(openai_model="gpt-4.1-mini") as client:
    print(client.health())
    archive=client.run("my_world.yaml")
```

The OpenAI key is sent only in `X-OpenAI-API-Key` over HTTPS. Do not embed it in
notebooks, YAML files, source control, or shared result archives.
Model precedence is: the explicit `openai_model=` SDK argument, then
`OPENAI_MODEL`, then the YAML `model`, then the economical default
`gpt-4.1-mini`.

## Financial example

The runnable Bull/Bear/Crisis case study in `examples/` matches the usage guide:

```bash
python examples/run_financial_case_study.py
```

It writes `examples/output/financial-example-results.zip` and uses two repeats
so the repeatability statistic is defined.
