from __future__ import annotations
import os
from pathlib import Path
from typing import Any
import httpx, yaml
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

class BeliefBenchError(RuntimeError): pass

class BeliefBench:
    def __init__(self,base_url: str | None=None,openai_api_key: str | None=None,service_token: str | None=None,timeout: float=1800):
        self.base_url=(base_url or os.getenv("BELIEFBENCH_API_URL") or "https://beliefbench-api.onrender.com").rstrip("/")
        self.openai_api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key: raise ValueError("An OpenAI API key is required; pass openai_api_key or set OPENAI_API_KEY")
        self.service_token=service_token or os.getenv("BELIEFBENCH_SERVICE_TOKEN")
        self._client=httpx.Client(base_url=self.base_url,timeout=timeout,follow_redirects=False)

    def health(self) -> dict[str,Any]:
        response=self._client.get("/v1/health"); response.raise_for_status(); return response.json()

    def run(self,config: dict[str,Any] | str | Path,output: str | Path="beliefbench-results.zip",client_request_id: str | None=None,show_progress: bool=True) -> Path:
        if isinstance(config,(str,Path)): config=yaml.safe_load(Path(config).read_text())
        headers={"X-OpenAI-API-Key":self.openai_api_key}
        if self.service_token: headers["Authorization"]=f"Bearer {self.service_token}"
        request={"config":config,"client_request_id":client_request_id}
        if show_progress:
            with Progress(SpinnerColumn(),TextColumn("[bold blue]Running BeliefBench[/]"),BarColumn(),TimeElapsedColumn()) as progress:
                progress.add_task("benchmark",total=None)
                response=self._client.post("/v1/benchmark",json=request,headers=headers)
        else: response=self._client.post("/v1/benchmark",json=request,headers=headers)
        if response.status_code >= 400:
            try: detail=response.json().get("detail",response.text)
            except ValueError: detail=response.text
            raise BeliefBenchError(f"BeliefBench API returned {response.status_code}: {detail}")
        destination=Path(output); destination.write_bytes(response.content); return destination

    def close(self): self._client.close()
    def __enter__(self): return self
    def __exit__(self,*_): self.close()
