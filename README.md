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

## Documentation

- [BeliefBench Usage Guide](docs/BeliefBench-Usage-Guide.pdf) explains installation, user-defined benchmark worlds, evidence templates, hosted execution, outputs, and diagnostic interpretation.
- [BeliefBench Technical Report](docs/BeliefBench-Technical-Report.pdf) presents the probabilistic measurement framework, exact-reference design, identifiability results, and the initial GPT-4.1-mini financial case study.

## Citation

If you use BeliefBench in research, evaluation, model validation, or governance work, please cite the technical report. A LaTeX `\bibitem` entry is:

```latex
\bibitem{dixon2026beliefbench}
Matthew F. Dixon.
\newblock BeliefBench: A Probabilistic Measurement Framework for Evaluating
  Belief Elicitation in Large Language Models.
\newblock Technical Report, Quiota LLC, 2026.
\newblock Available at:
  \url{https://github.com/mfrdixon/BeliefBench-Python/blob/main/docs/BeliefBench-Technical-Report.pdf}.
```

BibTeX users may use:

```bibtex
@techreport{dixon2026beliefbench,
  author      = {Dixon, Matthew F.},
  title       = {BeliefBench: A Probabilistic Measurement Framework for
                 Evaluating Belief Elicitation in Large Language Models},
  institution = {Quiota LLC},
  year        = {2026},
  type        = {Technical Report},
  url         = {https://github.com/mfrdixon/BeliefBench-Python/blob/main/docs/BeliefBench-Technical-Report.pdf}
}
```

## Related research

BeliefBench complements three reports that develop downstream uses of probabilistic belief states in agentic AI:

- [Belief at Risk: Quantifying Agentic AI Model Risk with LLM-Inferred Bayesian State Filters](https://arxiv.org/abs/2606.15473) — connects inferred belief states, Bayesian filtering, uncertainty diagnostics, and tail-risk measurement.
- [Model Validation of Agentic AI Systems: A POMDP-Based Framework for Belief-State, Forecast, and Policy Validation](https://arxiv.org/abs/2606.17383) — separates validation of information, beliefs, forecasts, policies, and utilities.
- [Adaptive AI Delegation under Uncertainty: A Bayesian Governance Policy for Sequential Decision Authority](https://arxiv.org/abs/2606.29406) — treats delegated AI authority as a sequential decision that responds to evidence and uncertainty.
