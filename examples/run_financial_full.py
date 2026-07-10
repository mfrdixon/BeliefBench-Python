from __future__ import annotations
import zipfile
import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from beliefbench import BeliefBench

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/"output"/"financial-full"
OUTPUT.mkdir(parents=True,exist_ok=True)
spec=yaml.safe_load((HERE/"financial_full.yaml").read_text())
study=spec.pop("study"); seeds=study["seeds"]

accuracy=[]; decisions=[]
progress_ref=None; seed_tasks={}
log_lock=threading.Lock(); last_percent={seed:-1 for seed in seeds}; completed_units={seed:0 for seed in seeds}
scenario_count=int(spec["balanced_entropy"]["per_stratum"])*3
method_views=3+len(spec.get("baseline_views",["reference","partial","noisy"]))
units_per_seed=scenario_count*method_views*int(spec["repeats"])+int(spec["trajectory_length"])*2
def load_validated_seed(seed,folder):
    a=pd.read_csv(folder/"belief_accuracy.csv"); a["seed"]=seed
    d=pd.read_csv(folder/"decision_consistency.csv"); d["seed"]=seed
    t=pd.read_csv(folder/"belief_trajectories.csv"); keys=["scenario_id","repeat","method","view"]
    expected=scenario_count*method_views*int(spec["repeats"])
    expected_decisions=scenario_count*method_views*int(spec.get("decision_repeats",spec["repeats"]))
    if len(a)!=expected or a.duplicated(keys).any() or len(d)!=expected_decisions or d.duplicated(keys).any() or len(t)!=int(spec["trajectory_length"])*2:
        raise RuntimeError(f"Seed {seed} failed completeness validation")
    return a,d

def run_seed(seed):
    config=dict(spec); config["seed"]=seed
    archive=OUTPUT/f"seed-{seed}.zip"; folder=OUTPUT/f"seed-{seed}"
    if archive.exists() and not (folder/"belief_accuracy.csv").exists():
        try:
            folder.mkdir(exist_ok=True)
            with zipfile.ZipFile(archive) as zf: zf.extractall(folder)
        except zipfile.BadZipFile:
            archive.unlink()
    if archive.exists() and (folder/"belief_accuracy.csv").exists() and (folder/"decision_consistency.csv").exists():
        return load_validated_seed(seed,folder)
    with BeliefBench(timeout=7200) as client:
        def update(state):
            completed_units[seed]=int(state["completed"]); percent=int(state["percent"])
            if progress_ref is not None:
                progress_ref.update(seed_tasks[seed],total=max(1,state["total"]),completed=state["completed"],description=f"Seed {seed} · {state['phase']}")
            if percent > last_percent[seed]:
                with log_lock:
                    last_percent[seed]=percent
                    overall=100*sum(completed_units.values())/(units_per_seed*len(seeds))
                    print(f"[{datetime.now().isoformat(timespec='seconds')}] Seed {seed}: {state['completed']}/{state['total']} ({state['percent']:.1f}%) · {state['phase']} | Overall {overall:.1f}%",flush=True)
        for attempt in range(1,int(study["max_seed_attempts"])+1):
            try:
                archive=client.run(config,archive,client_request_id=f"financial-full-{seed}-attempt-{attempt}",show_progress=False,progress_callback=update)
                break
            except Exception as exc:
                if "insufficient_quota" in str(exc) or attempt == int(study["max_seed_attempts"]): raise
                with log_lock: print(f"[{datetime.now().isoformat(timespec='seconds')}] Seed {seed}: attempt {attempt} failed ({type(exc).__name__}); retrying durable checkpoint after {study['retry_cooldown_seconds']}s",flush=True)
                time.sleep(float(study["retry_cooldown_seconds"]))
    folder.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as zf: zf.extractall(folder)
    return load_validated_seed(seed,folder)

with Progress(
    TextColumn("{task.description:<30}"),BarColumn(),TextColumn("{task.percentage:>5.1f}%"),TimeElapsedColumn(),
) as progress:
    progress_ref=progress
    task=progress.add_task("Full financial study",total=len(seeds))
    seed_tasks={seed:progress.add_task(f"Seed {seed} · queued",total=1) for seed in seeds}
    with ThreadPoolExecutor(max_workers=int(study["seed_concurrency"]),thread_name_prefix="belief-seed") as pool:
        futures={pool.submit(run_seed,seed):seed for seed in seeds}
        failures=[]
        for future in as_completed(futures):
            seed=futures[future]
            try:
                a,d=future.result(); accuracy.append(a); decisions.append(d)
                progress.update(seed_tasks[seed],total=1,completed=1,description=f"Seed {seed} · complete"); progress.advance(task)
            except Exception as exc:
                failures.append((seed,type(exc).__name__)); progress.update(seed_tasks[seed],description=f"Seed {seed} · exhausted retries")
        if failures: raise RuntimeError(f"Study incomplete after retries: {failures}")

accuracy=pd.concat(accuracy,ignore_index=True); decisions=pd.concat(decisions,ignore_index=True)
accuracy.to_csv(OUTPUT/"belief_accuracy_all_seeds.csv",index=False)
decisions.to_csv(OUTPUT/"decision_consistency_all_seeds.csv",index=False)

reference=accuracy[(accuracy.method=="BeliefBench")&(accuracy.view=="reference")&(accuracy.repeat==0)]
strata=reference.groupby(["seed","entropy_bucket"]).size().rename("scenarios").reset_index()
strata.to_csv(OUTPUT/"entropy_strata.csv",index=False)
expected_per_stratum=int(spec["balanced_entropy"]["per_stratum"])*len(seeds)
if not (strata.groupby("entropy_bucket").scenarios.sum()==expected_per_stratum).all():
    raise RuntimeError("Balanced entropy audit failed")

rng=np.random.default_rng(20260710); reps=int(study["bootstrap_replicates"])
alpha=(1-float(study["confidence_level"]))/2
metric_frames={
    "mean_js":(accuracy,"js_to_reference"),
    "mean_inferred_js":(accuracy,"inferred_js_to_reference"),
    "brier":(accuracy,"brier"),
    "log_loss":(accuracy,"log_loss"),
    "decision_consistency":(decisions,"consistent"),
    "reference_agreement":(decisions,"reference_agreement"),
    "regret":(decisions,"regret"),
}
rows=[]
for metric,(frame,column) in metric_frames.items():
    for method,part in frame.groupby("method"):
        cluster_stats=part.groupby(["seed","scenario_id"])[column].agg(["sum","count"])
        sums=cluster_stats["sum"].to_numpy(); counts=cluster_stats["count"].to_numpy()
        draws=rng.integers(0,len(cluster_stats),size=(reps,len(cluster_stats)))
        values=sums[draws].sum(axis=1)/counts[draws].sum(axis=1)
        rows.append({"method":method,"metric":metric,"estimate":float(part[column].mean()),"ci_lower":float(np.quantile(values,alpha)),"ci_upper":float(np.quantile(values,1-alpha)),"clusters":len(cluster_stats),"rows":len(part)})
pd.DataFrame(rows).to_csv(OUTPUT/"study_summary_cluster_bootstrap.csv",index=False)
print(f"Saved full study to {OUTPUT}")
