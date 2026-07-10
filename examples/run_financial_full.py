from __future__ import annotations
import zipfile
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
def run_seed(seed):
    config=dict(spec); config["seed"]=seed
    with BeliefBench(timeout=7200) as client:
        archive=client.run(config,OUTPUT/f"seed-{seed}.zip",client_request_id=f"financial-full-{seed}",show_progress=False)
    folder=OUTPUT/f"seed-{seed}"; folder.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as zf: zf.extractall(folder)
    a=pd.read_csv(folder/"belief_accuracy.csv"); a["seed"]=seed
    d=pd.read_csv(folder/"decision_consistency.csv"); d["seed"]=seed
    return a,d

with Progress(
    TextColumn("[bold blue]Full financial study[/] {task.completed}/{task.total}"),
    BarColumn(),TimeElapsedColumn(),
) as progress:
    task=progress.add_task("seeds",total=len(seeds))
    with ThreadPoolExecutor(max_workers=int(study["seed_concurrency"]),thread_name_prefix="belief-seed") as pool:
        futures={pool.submit(run_seed,seed):seed for seed in seeds}
        for future in as_completed(futures):
            a,d=future.result(); accuracy.append(a); decisions.append(d); progress.advance(task)

accuracy=pd.concat(accuracy,ignore_index=True); decisions=pd.concat(decisions,ignore_index=True)
accuracy.to_csv(OUTPUT/"belief_accuracy_all_seeds.csv",index=False)
decisions.to_csv(OUTPUT/"decision_consistency_all_seeds.csv",index=False)

reference=accuracy[(accuracy.method=="BeliefBench")&(accuracy.view=="reference")&(accuracy.repeat==0)]
strata=reference.groupby(["seed","entropy_bucket"]).size().rename("scenarios").reset_index()
strata.to_csv(OUTPUT/"entropy_strata.csv",index=False)
if not (strata.groupby("entropy_bucket").scenarios.sum()==105).all():
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
