# BeliefBench Python SDK

This public repository contains only the thin hosted-service client. The
probabilistic benchmark engine is not distributed with the package.

```bash
pip install https://github.com/mfrdixon/BeliefBench-Python/releases/download/v0.3.0/beliefbench-0.3.0-py3-none-any.whl
export OPENAI_API_KEY='...'
export BELIEFBENCH_SERVICE_TOKEN='...'
export BELIEFBENCH_API_URL='https://beliefbench-api.onrender.com'
```

```python
import os
from beliefbench import BeliefBench
with BeliefBench() as client:
    print(client.health())
    archive=client.run("my_world.yaml")
```

The OpenAI key is sent only in `X-OpenAI-API-Key` over HTTPS. Do not embed it in
notebooks, YAML files, source control, or shared result archives.

## Financial example

The runnable Bull/Bear/Crisis case study in `examples/` matches the usage guide:

```bash
python examples/run_financial_case_study.py
```

It writes `examples/output/financial-example-results.zip` and uses two repeats
so the repeatability statistic is defined.
