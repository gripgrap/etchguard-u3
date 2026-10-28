"""CPU-only physical simulator smoke run, then prediction-evaluator fault tests.

Own small driver using public ViennaPS APIs. No model training or fab claim.
Requires the pinned simulation environment described in docs/VIENNAPS_SMOKE.md.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time

from etchguard.adapters.viennaps import inspect_run
from etchguard.integrity import freeze, manifest_for
from etchguard.metrics import chamfer_um
from etchguard.predictions import evaluate_prediction_bundle


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    script_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    revision = subprocess.run(['git','rev-parse','HEAD'], capture_output=True, text=True, check=True).stdout.strip()
    config = {'recipe': {'ion_flux': 10., 'etchant_flux': 4500., 'oxygen_flux': 800.,
              'ion_mean_energy': 100., 'ion_exponent': 500., 'mask_width': .5, 'mask_height': .3},
              'grid_delta_um': .05, 'x_extent_um': 2., 'rays': 100, 'seed': 42,
              'threads': 2, 'snapshot_times_seconds': [0., .5, 1.]}
    write(output/'config.json', config)
    record = {'status': 'STARTED', 'started_utc': datetime.now(timezone.utc).isoformat(),
              'python': platform.python_version(), 'platform': platform.platform(),
              'source_revision': revision, 'driver_sha256': script_sha,
              'config_sha256': hashlib.sha256((output/'config.json').read_bytes()).hexdigest(),
              'versions': {k: importlib.metadata.version(k) for k in ['ViennaPS','ViennaLS','pyvista','vtk']}}
    write(output/'execution.json', record)
    started = time.perf_counter()
    try:
        import viennaps as ps
        ps.setDimension(2)
        ps.setNumThreads(config['threads'])
        ps.Length.setUnit('um')
        ps.Time.setUnit('s')
        raw = output/'raw'
        (raw/'snapshots').mkdir(parents=True)
        recipe = config['recipe']
        domain = ps.Domain(xExtent=config['x_extent_um'], gridDelta=config['grid_delta_um'])
        ps.MakeTrench(domain, trenchWidth=recipe['mask_width'], trenchDepth=0.,
                      maskHeight=recipe['mask_height'], maskTaperAngle=0.).apply()
        params = ps.SF6O2Etching.defaultParameters()
        params.ionFlux = recipe['ion_flux']
        params.etchantFlux = recipe['etchant_flux']
        params.passivationFlux = recipe['oxygen_flux']
        params.Ions.meanEnergy = recipe['ion_mean_energy']
        params.Ions.sigmaEnergy = 10.
        params.Ions.exponent = recipe['ion_exponent']
        model = ps.SF6O2Etching(params)
        ray = ps.RayTracingParameters()
        ray.raysPerPoint = config['rays']
        ray.useRandomSeeds = False
        ray.rngSeed = config['seed']
        coverage = ps.CoverageParameters()
        coverage.tolerance = 1e-4
        coverage.maxIterations = 10
        domain.saveSurfaceMesh(str(raw/'snapshots/t000.vtp'), addInterfaces=True)
        durations = config['snapshot_times_seconds']
        events = []
        for i,(a,b) in enumerate(zip(durations,durations[1:]),1):
            tick = time.perf_counter()
            process = ps.Process(domain, model)
            process.setProcessDuration(b-a)
            process.setParameters(ray)
            process.setParameters(coverage)
            process.apply()
            domain.saveSurfaceMesh(str(raw/f'snapshots/t{i:03d}.vtp'), addInterfaces=True)
            events.append({'snapshot_index': i, 'requested_duration_seconds': b-a,
                           'configured_cumulative_seconds': b, 'wall_seconds': time.perf_counter()-tick})
        write(raw/'meta.json', {'params': recipe, 'actual_k': 2, 'K': 2,
              'step_min': .5/60, 'viennaps': record['versions']['ViennaPS'],
              'snapshot_times_seconds': durations, 'time_basis': 'explicit_process_durations',
              'rays': config['rays'], 'seed': config['seed'], 'grid_delta': config['grid_delta_um']})
        record.update(status='SIMULATION_COMPLETE', wall_seconds=time.perf_counter()-started, events=events)
        write(output/'execution.json', record)
        source_manifest = manifest_for(raw)
        write(output/'source-manifest.json', source_manifest)
        reference = inspect_run(raw, source_manifest['content_fingerprint'], source_revision=revision)
        reference['provenance'].update(source_type='viennaps_simulation',
            observation='generated_by_this_driver_in_this_execution',
            execution_record_sha256=hashlib.sha256((output/'execution.json').read_bytes()).hexdigest())
        write(output/'reference.json', reference)
        with tempfile.TemporaryDirectory() as temp:
            changed = Path(temp)/'raw'
            shutil.copytree(raw, changed)
            p = changed/'snapshots/t001.vtp'
            p.write_bytes(p.read_bytes()+b' ')
            try:
                inspect_run(changed, source_manifest['content_fingerprint'], source_revision=revision)
            except ValueError as exc:
                if 'fingerprint' not in str(exc):
                    raise
            else:
                raise ValueError('tampered raw was accepted')
        if manifest_for(raw) != source_manifest:
            raise ValueError('original raw changed')
        change = chamfer_um(reference['snapshots'][0]['points_um'], reference['snapshots'][-1]['points_um'])
        if change <= 1e-9:
            raise ValueError('no measurable shape evolution')
        # Fixed before evaluation. Tutorial values, not physical acceptance thresholds.
        policy = {'max_chamfer_um': .02, 'max_depth_mae_um': .02,
                  'max_chamfer_per_snapshot_um': .03}
        results = {}
        for kind in ['oracle','fault_injection','initial_shape_baseline','wrong_time']:
            bundle = output/kind
            bundle.mkdir()
            prediction = copy.deepcopy(reference)
            label = 'baseline' if kind=='initial_shape_baseline' else 'fault_injection' if kind=='wrong_time' else kind
            prediction['model'] = {'id': kind, 'kind': label,
                                   'artifact_sha256': script_sha}
            for snap in prediction['snapshots']:
                if kind == 'fault_injection':
                    snap['points_um'] = [[x,y-.2] for x,y in snap['points_um']]
                elif kind == 'initial_shape_baseline':
                    snap['points_um'] = copy.deepcopy(reference['snapshots'][0]['points_um'])
            if kind == 'wrong_time':
                prediction['snapshots'][-1]['t_seconds'] += .1
            write(bundle/'reference.json', reference)
            write(bundle/'prediction.json', prediction)
            write(bundle/'policy.json', policy)
            fp = freeze(bundle)['content_fingerprint']
            write(output/f'{kind}-expected.json', {'fingerprint': fp})
            results[kind] = evaluate_prediction_bundle(bundle, fp)
            write(output/f'{kind}-result.json', results[kind])
        summary = {'status': 'PASS', 'scope': 'simulator_to_evaluator_smoke_not_model_accuracy',
            'source_fingerprint': source_manifest['content_fingerprint'],
            'shape_change_chamfer_um': change,
            'snapshot_points': [len(s['points_um']) for s in reference['snapshots']],
            'exit_codes': {k:v['exit_code'] for k,v in results.items()},
            'promotion_authorized': False, 'simulation_wall_seconds': record['wall_seconds'],
            'coverage_convergence_verified': False, 'mesh_ray_convergence_verified': False,
            'separate_process_per_interval': True, 'tampered_raw_blocked': True}
        if (results['oracle']['exit_code'] != 0 or results['fault_injection']['exit_code'] != 1
                or results['wrong_time']['exit_code'] != 2):
            raise ValueError('prediction evaluator control checks failed')
        write(output/'summary.json', summary)
        print(json.dumps(summary, indent=2))
    except Exception as exc:
        write(output/'failure.json', {'error': str(exc), 'wall_seconds': time.perf_counter()-started})
        raise
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
