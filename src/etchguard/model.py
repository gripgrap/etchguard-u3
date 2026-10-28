"""Explicit non-neural nearest-recipe baseline; not a trained FNO/MGN."""
from __future__ import annotations
from math import sqrt
from .contracts import RECIPE_KEYS,validate_run


class NearestRecipeBaseline:
    def __init__(self, train_runs: list[dict]):
        if not train_runs:
            raise ValueError("training set empty")
        for run in train_runs:
            problems=validate_run(run)
            if problems:
                raise ValueError(f"invalid training run: {problems}")
        self.train=train_runs
        self.lower={k:min(row["recipe"][k] for row in train_runs) for k in RECIPE_KEYS}
        self.upper={k:max(row["recipe"][k] for row in train_runs) for k in RECIPE_KEYS}

    def out_of_range(self, recipe: dict) -> list[str]:
        return [k for k in RECIPE_KEYS if not self.lower[k]<=recipe[k]<=self.upper[k]]

    def predict(self, recipe: dict) -> list:
        def distance(run):
            return sqrt(sum(((recipe[k]-run["recipe"][k])/max(1e-9,self.upper[k]-self.lower[k]))**2 for k in RECIPE_KEYS))
        best=min(self.train,key=distance)
        return [p[:] for p in best["snapshots"][-1]["points_um"]]
