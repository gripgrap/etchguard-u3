"""Predeclared two-variable CPU study: sensitivity pilot -> split -> ridge fit.

Run in the pinned Linux simulation environment. Test recipes are never used for
model selection. One final-time prediction per recipe; no FNO/MGN claims.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import random
import re
import subprocess
import sys
import time

from etchguard.adapters.viennaps import inspect_run
from etchguard.contracts import RECIPE_KEYS
from etchguard.integrity import freeze, manifest_for
from etchguard.metrics import score_pairs
from etchguard.model import NearestRecipeBaseline
from etchguard.predictions import evaluate_prediction_bundle
from etchguard.surrogate import RidgeProfileModel, resample_profile, validate_splits


def write(path, value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_case(request_path):
    import viennaps as ps
    request = json.loads(request_path.read_text())
    output = request_path.parent
    config,recipe,profile = request['simulation'],request['recipe'],request['profile']
    started = time.perf_counter()
    ps.setDimension(2); ps.setNumThreads(config['threads'])
    ps.Length.setUnit('um'); ps.Time.setUnit('s')
    raw = output/'raw'; (raw/'snapshots').mkdir(parents=True)
    domain = ps.Domain(xExtent=config['x_extent_um'],gridDelta=profile['grid_delta_um'])
    ps.MakeTrench(domain,trenchWidth=recipe['mask_width'],trenchDepth=0.,
                  maskHeight=recipe['mask_height'],maskTaperAngle=0.).apply()
    p = ps.SF6O2Etching.defaultParameters()
    p.ionFlux=recipe['ion_flux']; p.etchantFlux=recipe['etchant_flux']
    p.passivationFlux=recipe['oxygen_flux']; p.Ions.meanEnergy=recipe['ion_mean_energy']
    p.Ions.sigmaEnergy=10.; p.Ions.exponent=recipe['ion_exponent']
    model=ps.SF6O2Etching(p)
    ray=ps.RayTracingParameters(); ray.raysPerPoint=profile['rays']
    ray.useRandomSeeds=False; ray.rngSeed=config['seed']
    coverage=ps.CoverageParameters(); coverage.tolerance=config['coverage_tolerance']
    coverage.maxIterations=config['coverage_max_iterations']
    domain.saveSurfaceMesh(str(raw/'snapshots/t000.vtp'),addInterfaces=True)
    process=ps.Process(domain,model)
    process.setProcessDuration(config['duration_seconds'])
    process.setParameters(ray); process.setParameters(coverage)
    process.apply()
    domain.saveSurfaceMesh(str(raw/'snapshots/t001.vtp'),addInterfaces=True)
    write(raw/'meta.json',{'params':recipe,'actual_k':1,'K':1,
        'step_min':config['duration_seconds']/60,'viennaps':importlib.metadata.version('ViennaPS'),
        'snapshot_times_seconds':[0.,config['duration_seconds']],
        'time_basis':'explicit_single_process_duration','grid_delta':profile['grid_delta_um'],
        'rays':profile['rays'],'seed':config['seed']})
    source=manifest_for(raw)
    write(output/'source-manifest.json',source)
    record={'status':'SIMULATION_COMPLETE','wall_seconds':time.perf_counter()-started,
        'request_sha256':digest(request_path),'driver_sha256':digest(__file__),
        'source_fingerprint':source['content_fingerprint'],'versions':{
            k:importlib.metadata.version(k) for k in ['ViennaPS','ViennaLS','pyvista','vtk','numpy']}}
    write(output/'execution.json',record)
    run=inspect_run(raw,source['content_fingerprint'],source_revision=request['source_revision'])
    run['run_id']=request['run_id']
    run['provenance'].update(source_type='viennaps_simulation',
        observation='generated_by_local_study_case',execution_record_sha256=digest(output/'execution.json'))
    write(output/'run.json',run)


def normalized(run, n):
    run=copy.deepcopy(run)
    for snapshot in run['snapshots']:
        snapshot['points_um']=resample_profile(snapshot['points_um'],n)
    run['provenance']['profile_resampling']=f'uniform_arclength_{n}_points'
    return run


def study(output, plan_path):
    output.mkdir(parents=True,exist_ok=False)
    plan=json.loads(plan_path.read_text())
    write(output/'plan.json',plan)
    driver_snapshot=output/'driver-source.py'
    driver_snapshot.write_bytes(Path(__file__).read_bytes())
    revision=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
    write(output/'started.json',{'started_utc':datetime.now(timezone.utc).isoformat(),
        'plan_sha256':digest(output/'plan.json'),'driver_sha256':digest(driver_snapshot),
        'source_revision':revision,'test_use':'only_after_validation_model_selection'})
    started=time.perf_counter()

    def simulate(group, ident, recipe, profile):
        request={'recipe':recipe,'simulation':plan['simulation'],
                 'profile':profile,'run_id':ident,'source_revision':revision}
        folder=output/group/ident
        folder.mkdir(parents=True,exist_ok=False)
        write(folder/'request.json',request)
        wall=time.perf_counter()
        with (folder/'native.log').open('w') as log:
            subprocess.run([sys.executable,str(driver_snapshot.resolve()),'--case',
                str((folder/'request.json').resolve())],stdout=log,stderr=subprocess.STDOUT,
                check=True,timeout=90)
        pairs=re.findall(r'eCoverage:\s*([\d.eE+-]+)\s*pCoverage:\s*([\d.eE+-]+)',
                         (folder/'native.log').read_text())
        qa={'case_wall_seconds':time.perf_counter()-wall,
            'last_reported_coverage_delta':[float(v) for v in pairs[-1]] if pairs else None,
            'coverage_convergence_certified':False}
        write(folder/'qa.json',qa)
        run=json.loads((folder/'run.json').read_text())
        print(f'{group}/{ident}: {qa["case_wall_seconds"]:.2f}s',flush=True)
        return normalized(run,plan['profile_points'])

    profiles={p['name']:p for p in plan['numerical_profiles']}
    pilot=[]
    for i,(flux,energy) in enumerate(plan['pilot_anchors']):
        recipe={**plan['fixed_recipe'],'ion_flux':flux,'ion_mean_energy':energy}
        runs={name:simulate('pilot',f'anchor-{i}-{name}',recipe,p) for name,p in profiles.items()}
        row={'anchor':recipe}
        for name in ('coarse','medium'):
            row[name+'_vs_fine']=score_pairs([(runs[name]['snapshots'][-1]['points_um'],
                                             runs['fine']['snapshots'][-1]['points_um'])])
        pilot.append(row)
    rules=plan['pilot_acceptance']
    pilot_pass=all(r['medium_vs_fine']['chamfer_mean_um']<=rules['medium_vs_fine_chamfer_um_max']
        and r['medium_vs_fine']['depth_mae_um']<=rules['medium_vs_fine_depth_um_max'] for r in pilot)
    write(output/'pilot-summary.json',{'passed_predeclared_screen':pilot_pass,'comparisons':pilot,
          'scope':'combined_grid_ray_sensitivity_on_three_anchors_not_full_convergence'})
    if not pilot_pass:
        write(output/'summary.json',{'status':'STOPPED_NUMERICAL_PILOT','model_training_performed':False})
        return

    rng=random.Random(plan['design_seed']); count=plan['n_recipes']
    variables={}
    for key,(lo,hi) in plan['variable_ranges'].items():
        values=[lo+(hi-lo)*(i+rng.random())/count for i in range(count)]
        rng.shuffle(values); variables[key]=values
    recipes=[{**plan['fixed_recipe'],**{k:v[i] for k,v in variables.items()}} for i in range(count)]
    sizes=plan['split_sizes']
    if sum(sizes.values())!=count: raise ValueError('split sizes mismatch')
    split_ids={}; begin=0
    for label in ('train','val','test'):
        split_ids[label]=[f'r{i:03d}' for i in range(begin,begin+sizes[label])]; begin+=sizes[label]
    write(output/'design.json',{'recipes':recipes,'splits':split_ids,'plan_sha256':digest(output/'plan.json')})
    runs=[simulate('dataset',f'r{i:03d}',recipe,profiles['medium']) for i,recipe in enumerate(recipes)]
    lookup={r['run_id']:r for r in runs}
    splits={k:[lookup[i] for i in ids] for k,ids in split_ids.items()}
    validate_splits(splits)
    write(output/'normalized-runs.json',runs)
    models=output/'models'; models.mkdir()
    candidates=[]
    for alpha in plan['ridge_alphas']:
        model=RidgeProfileModel.fit(splits['train'],alpha=alpha,n_points=plan['profile_points'])
        artifact=models/f'ridge-{alpha}.json'; write(artifact,model.to_dict())
        pairs=[(model.predict(r['recipe']),r['snapshots'][-1]['points_um']) for r in splits['val']]
        candidates.append({'alpha':alpha,'artifact':str(artifact),'metrics':score_pairs(pairs)})
    chosen=min(candidates,key=lambda c:c['metrics']['chamfer_mean_um'])
    write(output/'selection.json',{'selection_split':'val','candidates':candidates,'chosen':chosen,
                                'test_accessed_for_selection':False})
    model_path=Path(chosen['artifact'])
    trained=RidgeProfileModel.from_dict(json.loads(model_path.read_text()))
    baseline=NearestRecipeBaseline(splits['train'])
    model_sha=digest(model_path)
    baseline_card={'model':'nearest_recipe','train_ids':split_ids['train'],
                   'training_sha256':trained.to_dict()['training_sha256']}
    write(models/'nearest.json',baseline_card)
    final={}
    for name,predictor,artifact in [('ridge',trained,model_path),('nearest',baseline,models/'nearest.json')]:
        pairs=[]; decisions=[]
        for run in splits['test']:
            prediction=copy.deepcopy(run)
            prediction['snapshots'][-1]['points_um']=predictor.predict(run['recipe'])
            prediction['model']={'id':name,'kind':'model' if name=='ridge' else 'baseline',
                                  'artifact_sha256':digest(artifact)}
            bundle=output/'evaluation'/name/run['run_id']; bundle.mkdir(parents=True)
            write(bundle/'reference.json',run); write(bundle/'prediction.json',prediction)
            write(bundle/'policy.json',plan['evaluation_policy'])
            fp=freeze(bundle)['content_fingerprint']
            write(bundle.parent/(run['run_id']+'-expected.json'),{'fingerprint':fp})
            result=evaluate_prediction_bundle(bundle,fp)
            write(bundle.parent/(run['run_id']+'-result.json'),result)
            decisions.append({'run_id':run['run_id'],'exit_code':result['exit_code'],
                              'metrics':result['metrics'],'reasons':result['reasons']})
            pairs.append((prediction['snapshots'][-1]['points_um'],run['snapshots'][-1]['points_um']))
        final[name]={'metrics':score_pairs(pairs),'cases':decisions}
    if digest(model_path)!=model_sha: raise ValueError('model artifact changed during evaluation')
    write(output/'summary.json',{'status':'EXPLORATORY_STUDY_COMPLETE','n_recipes':count,
        'split_sizes':sizes,'variables':list(plan['variable_ranges']),'selected_alpha':chosen['alpha'],
        'pilot':pilot,'test':final,'wall_seconds':time.perf_counter()-started,
        'model_artifact_sha256':model_sha,'model_artifact_verified_in_study':True,
        'promotion_authorized':False,'numerical_convergence_certified':False})
    sealed=freeze(output)
    write(output.parent/(output.name+'-complete.json'),{
        'status':'COMPLETE','fingerprint':sealed['content_fingerprint'],
        'completed_utc':datetime.now(timezone.utc).isoformat()})
    print(json.dumps(json.loads((output/'summary.json').read_text()),indent=2))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output')
    parser.add_argument('--plan',default='configs/local-study.json')
    parser.add_argument('--case')
    args=parser.parse_args()
    if args.case: run_case(Path(args.case)); return
    if not args.output: parser.error('--output required')
    study(Path(args.output),Path(args.plan))


if __name__=='__main__': main()
