"""Inspect a team-style VTP run; never infer simulation authenticity from a file.

Only line-cell meshes, one open planar material boundary, and explicit metadata
are supported. Unknown topology is rejected instead of sorted or stitched.
"""
import json
import math
import re
from pathlib import Path

from ..contracts import validate_profile, validate_run
from ..integrity import manifest_for


def ordered_material_profile(points, cells, material_ids, material_id=10, plane_tolerance_um=1e-6):
    if not points or not math.isfinite(plane_tolerance_um) or plane_tolerance_um < 0:
        raise ValueError('invalid points or plane tolerance')
    for p in points:
        if len(p) != 3 or not all(math.isfinite(v) for v in p):
            raise ValueError('points must have three finite coordinates')
    if any(abs(p[2]) > plane_tolerance_um for p in points):
        raise ValueError('mesh must lie in the z=0 plane')
    adjacency, edges = {}, set()
    cursor = 0
    count = 0
    while cursor < len(cells):
        n = cells[cursor]
        if type(n) is not int or n < 2 or cursor+1+n > len(cells):
            raise ValueError('invalid line cell length')
        ids = cells[cursor+1:cursor+1+n]
        if any(type(i) is not int or i < 0 or i >= len(points) for i in ids):
            raise ValueError('invalid point index')
        if count >= len(material_ids):
            raise ValueError('material count differs from line cell count')
        mat = material_ids[count]
        if not math.isfinite(mat) or mat != int(mat):
            raise ValueError('material IDs must be finite integers')
        if mat == material_id:
            for a, b in zip(ids, ids[1:]):
                edge = tuple(sorted((a, b)))
                if a == b or edge in edges:
                    raise ValueError('duplicate or degenerate edge')
                edges.add(edge)
                adjacency.setdefault(a, set()).add(b)
                adjacency.setdefault(b, set()).add(a)
        cursor += n+1
        count += 1
    if count != len(material_ids):
        raise ValueError('material count differs from line cell count')
    if not edges:
        raise ValueError('selected material has no lines')
    if any(len(v) > 2 for v in adjacency.values()):
        raise ValueError('branched material boundary')
    ends = [i for i, neighbors in adjacency.items() if len(neighbors) == 1]
    if len(ends) != 2:
        raise ValueError('expected one open material boundary')
    current = min(ends, key=lambda i: tuple(points[i]))
    order, visited = [], set()
    while current is not None:
        if current in visited:
            raise ValueError('cycle in material boundary')
        visited.add(current)
        order.append(current)
        following = adjacency[current] - visited
        current = next(iter(following)) if following else None
    if len(visited) != len(adjacency):
        raise ValueError('disconnected material boundary')
    profile = [list(points[i][:2]) for i in order]
    issues = validate_profile(profile)
    if issues:
        raise ValueError(str(issues))
    return profile


def read_vtp(path, material_id=10):
    try:
        import pyvista as pv
    except ImportError as exc:
        raise ValueError('VTP inspection requires optional dependency: pip install .[vtp]') from exc
    mesh = pv.read(str(path))
    if not isinstance(mesh, pv.PolyData) or mesh.n_verts or mesh.GetNumberOfPolys() or mesh.n_strips:
        raise ValueError('only PolyData line cells are supported')
    if 'MaterialIds' not in mesh.cell_data:
        raise ValueError('MaterialIds cell data missing')
    return ordered_material_profile(mesh.points.tolist(), mesh.lines.tolist(),
                                    mesh.cell_data['MaterialIds'].tolist(), material_id)


def inspect_run(directory, expected_fingerprint, *, material_id=10, source_revision):
    """Read fixed source files with explicit times, or labeled derived times.

    External baseline is required; no manifest or other file is written here.
    Concurrent hostile modification is outside this read-only inspection scope.
    """
    root = Path(directory).resolve()
    before = manifest_for(root)
    if before['content_fingerprint'] != expected_fingerprint:
        raise ValueError('source fingerprint mismatch')
    if not isinstance(source_revision, str) or not source_revision.strip():
        raise ValueError('source revision is required')
    meta = json.loads((root/'meta.json').read_text(encoding='utf-8'))
    step = meta['step_min']
    actual_k = meta['actual_k']
    if type(step) not in (int, float) or not math.isfinite(step) or step <= 0:
        raise ValueError('step_min must be finite and positive')
    if type(actual_k) is not int or actual_k < 1:
        raise ValueError('actual_k must be a positive integer')
    paths = sorted((root/'snapshots').glob('*.vtp'))
    indices = []
    for p in paths:
        match = re.fullmatch(r't(\d+)\.vtp', p.name)
        if not match:
            raise ValueError('unsupported snapshot filename')
        indices.append(int(match.group(1)))
    if indices != list(range(actual_k+1)):
        raise ValueError('missing, duplicate or nonconsecutive snapshot index')
    if 'snapshot_times_seconds' in meta:
        times = meta['snapshot_times_seconds']
        if (not isinstance(times, list) or len(times) != len(paths)
                or any(type(t) not in (int,float) or not math.isfinite(t) or t < 0 for t in times)
                or any(b <= a for a,b in zip(times,times[1:]))
                or not isinstance(meta.get('time_basis'), str) or not meta['time_basis']):
            raise ValueError('invalid explicit snapshot times or time basis')
        time_basis = meta['time_basis']
    else:
        times = [i*step*60 for i in indices]
        time_basis = 'snapshot_index_times_step_min; derived_not_observed'
    run = {'run_id': root.name, 'recipe': meta['params'],
           'provenance': {'source_type': 'external_research', 'version': str(meta['viennaps']),
                          'claimed_simulator': 'ViennaPS', 'source_revision': source_revision,
                          'content_fingerprint': expected_fingerprint,
                          'time_basis': time_basis,
                          'material_id': material_id, 'length_unit_basis': 'source_generator_declares_um'},
           'snapshots': [{'t_seconds': t, 'points_um': read_vtp(p, material_id)}
                         for t, p in zip(times, paths)]}
    issues = validate_run(run)
    if issues:
        raise ValueError(str(issues))
    if manifest_for(root) != before:
        raise ValueError('source changed during VTP inspection')
    return run
