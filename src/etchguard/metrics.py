"""Geometry-only metrics; CHAMFER=mean of two directed mean NN distances (µm)."""
from __future__ import annotations
from math import hypot
from .contracts import validate_profile


def chamfer_um(a: list, b: list) -> float:
    problems=validate_profile(a)+validate_profile(b)
    if problems:
        raise ValueError("invalid profile: "+"; ".join(problems))
    def one_way(p,q):
        return sum(min(hypot(x-u,y-v) for u,v in q) for x,y in p)/len(p)
    return (one_way(a,b)+one_way(b,a))/2


def depth_um(points: list) -> float:
    if validate_profile(points):
        raise ValueError("invalid profile")
    # Convention: initial Si surface y=0um, etch proceeds toward negative y.
    return max(0.0, -min(y for _,y in points))


def score_pairs(pairs: list[tuple[list,list]]) -> dict:
    if not pairs:
        raise ValueError("empty evaluation set")
    errors=[chamfer_um(pred,actual) for pred,actual in pairs]
    depths=[abs(depth_um(pred)-depth_um(actual)) for pred,actual in pairs]
    return {"n":len(errors), "chamfer_mean_um":sum(errors)/len(errors), "depth_mae_um":sum(depths)/len(depths),
            "max_chamfer_um":max(errors)}
