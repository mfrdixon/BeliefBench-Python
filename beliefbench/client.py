from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Any, Callable
import httpx, yaml
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

class BeliefBenchError(RuntimeError): pass

class BeliefBench:
    def __init__(self,base_url: str | None=None,openai_api_key: str | None=None,service_token: str | None=None,timeout: float=1800,openai_model: str | None=None):
        self.base_url=(base_url or os.getenv("BELIEFBENCH_API_URL") or "https://beliefbench-api.onrender.com").rstrip("/")
        self.openai_api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key: raise ValueError("An OpenAI API key is required; pass openai_api_key or set OPENAI_API_KEY")
        self.openai_model=openai_model or os.getenv("OPENAI_MODEL")
        self.service_token=service_token or os.getenv("BELIEFBENCH_SERVICE_TOKEN")
        self._client=httpx.Client(base_url=self.base_url,timeout=timeout,follow_redirects=False)

    def health(self) -> dict[str,Any]:
        response=self._client.get("/v1/health"); response.raise_for_status(); return response.json()

    def run(self,config: dict[str,Any] | str | Path,output: str | Path="beliefbench-results.zip",client_request_id: str | None=None,show_progress: bool=True,progress_callback: Callable[[dict[str,Any]],None] | None=None,poll_interval: float=2.0) -> Path:
        if isinstance(config,(str,Path)): config=yaml.safe_load(Path(config).read_text())
        config=dict(config)
        if self.openai_model: config["model"]=self.openai_model
        else: config.setdefault("model","gpt-4.1-mini")
        headers={"X-OpenAI-API-Key":self.openai_api_key}
        if self.service_token: headers["Authorization"]=f"Bearer {self.service_token}"
        request={"config":config,"client_request_id":client_request_id}
        response=self._client.post("/v1/jobs",json=request,headers=headers)
        if response.status_code == 404:
            response=self._client.post("/v1/benchmark",json=request,headers=headers)
        elif response.status_code < 400:
            job_id=response.json()["job_id"]
            progress_context=Progress(SpinnerColumn(),TextColumn("[bold blue]Running BeliefBench[/]"),BarColumn(),TextColumn("{task.percentage:>5.1f}%"),TimeElapsedColumn()) if show_progress else None
            if progress_context: progress_context.start(); task_id=progress_context.add_task("benchmark",total=1)
            try:
                while True:
                    status=self._client.get(f"/v1/jobs/{job_id}",headers=headers); status.raise_for_status(); state=status.json()
                    if progress_callback: progress_callback(state)
                    if progress_context: progress_context.update(task_id,total=max(1,state["total"]),completed=state["completed"])
                    if state["status"] == "complete": break
                    if state["status"] == "failed": raise BeliefBenchError(f"BeliefBench job failed: {state.get('error') or 'unknown error'} ({state.get('error_code') or 'no provider code'})")
                    time.sleep(poll_interval)
                response=self._client.get(f"/v1/jobs/{job_id}/result",headers=headers)
            finally:
                if progress_context: progress_context.stop()
        if response.status_code >= 400:
            try: detail=response.json().get("detail",response.text)
            except ValueError: detail=response.text
            raise BeliefBenchError(f"BeliefBench API returned {response.status_code}: {detail}")
        destination=Path(output); destination.write_bytes(response.content); return destination

    def close(self): self._client.close()
    def __enter__(self): return self
    def __exit__(self,*_): self.close()
