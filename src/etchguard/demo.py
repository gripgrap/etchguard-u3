"""Deterministic SYNTHETIC fixtures: function smoke tests, not ViennaPS results."""
from __future__ import annotations
import json
import random
from pathlib import Path
from math import exp
from .contracts import RECIPE_KEYS


def _shape(recipe, t_seconds: float) -> list[list[float]]:
    # Toy Gaussian depression, not a physics model or manufacturing simulation.
    depth=0.04+t_seconds/15.0*(0.20+0.10*(recipe["ion_flux"]/30)+0.025*(recipe["etchant_flux"]/6000))
    width=0.28+recipe["mask_width"]*0.65
    xs=[-1.00,-0.8,-0.6,-0.4,-0.25,-0.12,0.0,0.12,0.25,0.4,0.6,0.8,1.00]
    return [[x, round(-depth*exp(-(x/width)**4),9)] for x in xs]


def _recipe(rng):
    return {
      "ion_flux":round(rng.uniform(4,30),6),
      "etchant_flux":round(rng.uniform(800,6000),6),
      "oxygen_flux":round(rng.uniform(60,850),6),
      "ion_mean_energy":round(rng.uniform(60,130),6),
      "ion_exponent":round(rng.uniform(300,900),6),
      "mask_width":round(rng.uniform(0.22,0.55),6),
      "mask_height":round(rng.uniform(0.20,0.40),6),
    }


def generate(base: str | Path, n_train: int=40, n_golden: int=8):
    """Fixture generation deliberately separate from real simulation import."""
    root=Path(base)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"output exists: {root}")
    rng=random.Random(20261028)
    for split,n in (("train",n_train),("golden",n_golden)):
        folder=root/split
        folder.mkdir(parents=True,exist_ok=True)
        for i in range(n):
            recipe=_recipe(rng)
            snapshots=[{"t_seconds":t,"points_um":_shape(recipe,t)} for t in (0,5,10,15)]
            run={"run_id":f"{split}-{i:04d}","recipe":recipe,
                 "provenance":{"source_type":"synthetic_fixture","version":"toy-gaussian-1.0",
                               "warning":"NOT VIENNAPS / NOT PHYSICS / NOT FAB"},
                 "snapshots":snapshots}
            (folder/f"{run['run_id']}.json").write_text(json.dumps(run,indent=2)+"\n",encoding="utf-8")
    return root


def load_runs(folder: str | Path) -> list[dict]:
    paths=sorted(Path(folder).glob("*.json"))
    if not paths:
        raise ValueError(f"no run JSON in {folder}")
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]
