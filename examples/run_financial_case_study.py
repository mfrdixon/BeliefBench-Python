from pathlib import Path
from beliefbench import BeliefBench

HERE=Path(__file__).resolve().parent
(HERE/"output").mkdir(exist_ok=True)

with BeliefBench() as client:
    print("Service:",client.health())
    archive=client.run(
        HERE/"financial_case_study.yaml",
        HERE/"output"/"financial-example-results.zip",
        client_request_id="financial-guide-example-v1",
    )
    print("Saved:",archive)
