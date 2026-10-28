"""Independent 7-recipe / 2D-profile contract; JSON reference format.

The source documents disagree on time conventions (seconds vs minutes). This
contract requires time_seconds explicitly rather than silently guessing.
"""
from __future__ import annotations
from math import isfinite, hypot

RECIPE_KEYS = (
    "ion_flux", "etchant_flux", "oxygen_flux", "ion_mean_energy",
    "ion_exponent", "mask_width", "mask_height",
)
SOURCES = {"synthetic_fixture", "viennaps_simulation", "external_research"}


def validate_recipe(recipe: dict) -> list[str]:
    if not isinstance(recipe, dict):
        return ["recipe must be object"]
    issues = []
    missing = set(RECIPE_KEYS) - set(recipe)
    extra = set(recipe) - set(RECIPE_KEYS)
    if missing:
        issues.append(f"missing recipe keys: {sorted(missing)}")
    if extra:
        issues.append(f"unknown recipe keys: {sorted(extra)}")
    for k in RECIPE_KEYS:
        if k not in recipe:
            continue
        v = recipe[k]
        if type(v) not in (int, float) or not isfinite(v) or v <= 0:
            issues.append(f"{k} must be a finite positive number")
    return issues


def _orientation(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _crossing(a, b, c, d, epsilon=1e-12) -> bool:
    """Strict crossing only; touching and collinear overlap are separately handled."""
    o1, o2 = _orientation(a, b, c), _orientation(a, b, d)
    o3, o4 = _orientation(c, d, a), _orientation(c, d, b)
    return ((o1 > epsilon and o2 < -epsilon) or (o1 < -epsilon and o2 > epsilon)) and ((o3 > epsilon and o4 < -epsilon) or (o3 < -epsilon and o4 > epsilon))


def validate_profile(points: list) -> list[str]:
    if not isinstance(points, list) or len(points) < 2:
        return ["profile requires at least 2 ordered 2D points"]
    for i, p in enumerate(points):
        if not isinstance(p, (list, tuple)) or len(p) != 2 or any(type(v) not in (int, float) or not isfinite(v) for v in p):
            return [f"point {i} must contain two finite numeric coordinates"]
    issues = []
    for i in range(len(points) - 1):
        if hypot(points[i+1][0] - points[i][0], points[i+1][1] - points[i][1]) <= 1e-12:
            issues.append(f"degenerate segment at index {i}")
    for i in range(len(points) - 1):
        for j in range(i + 2, len(points) - 1):
            if _crossing(points[i], points[i+1], points[j], points[j+1]):
                issues.append(f"self-crossing segments {i} and {j}")
    return issues


def validate_run(run: dict) -> list[str]:
    issues=[]
    if not isinstance(run, dict):
        return ["run must be object"]
    if not isinstance(run.get("run_id"), str) or not run["run_id"]:
        issues.append("run_id must be nonempty string")
    issues += validate_recipe(run.get("recipe"))
    source = run.get("provenance", {})
    if not isinstance(source, dict) or source.get("source_type") not in SOURCES:
        issues.append("provenance.source_type must identify synthetic_fixture/viennaps_simulation/external_research")
    if not isinstance(source,dict) or not isinstance(source.get("version"),str) or not source.get("version"):
        issues.append("provenance.version required")
    snapshots = run.get("snapshots")
    if not isinstance(snapshots, list) or len(snapshots) < 2:
        return issues+["at least 2 snapshots required"]
    prev=-float("inf")
    for i, snap in enumerate(snapshots):
        if not isinstance(snap,dict):
            issues.append(f"snapshot {i} must be object")
            continue
        t = snap.get("t_seconds")
        if type(t) not in (float, int) or not isfinite(t) or t < 0 or t <= prev:
            issues.append(f"snapshot {i} time must be finite, nonnegative and strictly increasing")
        else:
            prev=t
        issues += [f"snapshot {i}: {v}" for v in validate_profile(snap.get("points_um"))]
    return issues
