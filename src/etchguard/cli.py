"""EtchGuard command line. `demo` is a fully reproducible fixture-only smoke test."""
from __future__ import annotations
import argparse
import json
import shutil
import sys
from pathlib import Path
from .contracts import validate_run
from .demo import generate,load_runs
from .gate import evaluate_candidate
from .integrity import freeze,verify,IntegrityError
from .model import NearestRecipeBaseline
from .registry import Registry
from .report import write_html


class DegradedModel:
    """Fault injection. NOT a model fitted on simulator data."""
    def __init__(self, base,shift_um=0.75):
        self.base=base;self.shift=shift_um
    def predict(self,recipe):
        return [[x,y-self.shift] for x,y in self.base.predict(recipe)]


def _demo(output:Path):
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing evidence: {output}")
    runs=generate(output/"data")
    train=load_runs(runs/"train")
    golden=load_runs(runs/"golden")
    ids_train={r["run_id"] for r in train}
    ids_golden={r["run_id"] for r in golden}
    if ids_train & ids_golden:
        raise ValueError("split leakage")
    for r in train+golden:
        problems=validate_run(r)
        if problems:raise ValueError(f"invalid run {r.get('run_id')}: {problems}")
    frozen=freeze(runs/"golden")
    current=verify(runs/"golden")
    config=json.loads((Path(__file__).resolve().parents[2]/"configs"/"demo_gate.json").read_text())
    baseline=NearestRecipeBaseline(train)
    params=dict(max_chamfer_um=config["max_chamfer_um"],max_depth_mae_um=config["max_depth_mae_um"],
                max_regression_ratio=config["max_regression_ratio"],
                expected_fingerprint=frozen["content_fingerprint"],actual_fingerprint=current["content_fingerprint"])
    good=evaluate_candidate(baseline,golden,**params)
    registry=Registry(output/"registry")
    registry.submit("nearest-recipe-baseline-v1",good,fingerprint=frozen["content_fingerprint"])
    saved=registry.champion()
    bad=evaluate_candidate(DegradedModel(baseline),golden,**params,
                           champion_metrics=saved["metrics"] if saved else None)
    registry.submit("degraded-fault-injection",bad,fingerprint=frozen["content_fingerprint"])
    tampered=evaluate_candidate(baseline,golden,**{**params,"actual_fingerprint":"tampered"})
    registry.submit("fingerprint-fault-injection",tampered,fingerprint="tampered")
    cases=[
        {"scenario":"baseline PASS (tutorial)","expected_exit_code":0,"actual_exit_code":good.exit_code,"reasons":good.reasons},
        {"scenario":"degraded model BLOCK","expected_exit_code":1,"actual_exit_code":bad.exit_code,"reasons":bad.reasons},
        {"scenario":"fingerprint mismatch BLOCK","expected_exit_code":2,"actual_exit_code":tampered.exit_code,"reasons":tampered.reasons},
    ]
    champion_unchanged=registry.champion() and registry.champion()["model_id"]=="nearest-recipe-baseline-v1"
    all_ok=all(x["expected_exit_code"]==x["actual_exit_code"] for x in cases) and bool(champion_unchanged)
    summary={"status":"PASS" if all_ok else "FAIL","source_type":"synthetic_fixture",
             "notes":"Illustrative threshold and toy data. No actual ViennaPS generated/parsed.",
             "model":"nearest-recipe-baseline (non-neural)","n_train":len(train),"n_golden":len(golden),
             "golden_content_fingerprint":frozen["content_fingerprint"],
             "metrics":good.metrics,"gate_config":config,"cases":cases,
             "champion_preserved_after_blocks":bool(champion_unchanged)}
    (output/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    write_html(output/"report.html",summary,golden[0]["snapshots"][-1]["points_um"],baseline.predict(golden[0]["recipe"]))
    for x in cases:
        print(f'{x["scenario"]}: exit {x["actual_exit_code"]} (expected {x["expected_exit_code"]})')
    print("Champion unchanged after BLOCK:",bool(champion_unchanged))
    print("Report:",output/"report.html")
    return 0 if all_ok else 1


def main(argv=None):
    p=argparse.ArgumentParser(description="EtchGuard: research-only reliability and gate MVP")
    sub=p.add_subparsers(dest="action",required=True)
    a=sub.add_parser("demo");a.add_argument("--output",default="reports/generated/demo")
    b=sub.add_parser("freeze");b.add_argument("directory")
    c=sub.add_parser("verify");c.add_argument("directory")
    ns=p.parse_args(argv)
    try:
        if ns.action=="demo":return _demo(Path(ns.output))
        if ns.action=="freeze":print(json.dumps(freeze(ns.directory),indent=2));return 0
        if ns.action=="verify":print(json.dumps(verify(ns.directory),indent=2));return 0
    except (OSError,ValueError,IntegrityError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        return 2
    return 2

if __name__=="__main__":
    sys.exit(main())
