"""Model gate; generic enough to accept any model with .predict(recipe)."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from .contracts import validate_run
from .metrics import score_pairs

@dataclass
class GateDecision:
    passed: bool
    exit_code: int
    reasons: list[str]
    metrics: dict
    checks: dict

    def as_dict(self):
        return asdict(self)


def evaluate_candidate(model, golden: list[dict], *, max_chamfer_um: float,
                       max_depth_mae_um: float, expected_fingerprint: str,
                       actual_fingerprint: str, champion_metrics: dict|None=None,
                       max_regression_ratio:float=1.10) -> GateDecision:
    if not golden:
        return GateDecision(False,2,["golden set empty"],{}, {})
    if not expected_fingerprint or not actual_fingerprint or expected_fingerprint != actual_fingerprint:
        return GateDecision(False,2,["golden/content fingerprint mismatch"],{}, {"integrity":False})
    for run in golden:
        p=validate_run(run)
        if p:
            return GateDecision(False,2,["invalid golden run: "+"; ".join(p)],{}, {"integrity":False})
    try:
        pairs=[(model.predict(r["recipe"]),r["snapshots"][-1]["points_um"]) for r in golden]
        scores=score_pairs(pairs)
    except (ValueError, TypeError, IndexError,KeyError,OverflowError) as e:
        return GateDecision(False,1,["invalid prediction: "+str(e)],{}, {"integrity":True})
    checks={"integrity":True,"chamfer":scores["chamfer_mean_um"]<=max_chamfer_um,
            "depth":scores["depth_mae_um"]<=max_depth_mae_um}
    reasons=[]
    if not checks["chamfer"]: reasons.append("chamfer exceeds predeclared gate")
    if not checks["depth"]: reasons.append("depth MAE exceeds predeclared gate")
    if champion_metrics is not None:
        incumbent=champion_metrics["chamfer_mean_um"]
        checks["regression"] = scores["chamfer_mean_um"] <= incumbent*max_regression_ratio
        if not checks["regression"]: reasons.append("regression versus champion")
    ok=all(checks.values())
    return GateDecision(ok,0 if ok else 1,reasons,scores,checks)
