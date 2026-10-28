# 국소 레시피 데이터와 소형 대리모델 비교

기준: 2026-10-28. 앞선 단일 recipe의 생성→평가 연결 실증에서, 여러 독립 recipe로 학습·검증·최종 평가를 나누는 단계로 확장한다. 실행 계획은 `configs/local-study.json`이며 결과를 보기 전에 고정했다.

## 실험 범위

- ViennaPS 4.5.0 + ViennaLS 5.8.5, WSL Ubuntu/Python 3.12.3, CPU 2 threads.
- 변동 변수: ion_flux 8~12, ion_mean_energy 80~120. 나머지 5개 recipe 변수는 고정한다. 7변수 전체 모델을 검증하는 실험이 아니다.
- 길이 um, 시간 s, 최종 시각 1초. 레시피마다 하나의 process를 적용한다. 앞선 smoke의 0.5초 process 두 번과 수치를 동일 실험처럼 비교하지 않는다.
- coverage tolerance=.001, maxIterations=100. 마지막 로그 delta를 보관하지만 모든 단계의 coverage 수렴을 인증하지는 않는다.

## 수치 설정 점검

대표 조건 3개에서 coarse(.05um/100rays), medium(.025um/300rays), fine(.0125um/600rays)를 비교한다. 모든 프로파일을 연결 순서에 따른 균등 호 길이 64점으로 재표본화한다. x 정렬은 하지 않는다.

사전에 정한 진행 조건은 세 anchor 모두 medium↔fine Chamfer와 깊이 차이 각각 .01um 이하다. 통과하면 medium을 데이터 생성에 사용하고, 실패하면 학습을 중단한다. 이는 국소 탐색 조건이며 물리적으로 보정된 허용 기준은 아니다.

grid와 rays를 함께 바꾸므로 개별 원인의 기여를 분리하지 못한다. fine도 정답이라고 확정하지 않는다. 최대 차이, 표본 범위, 표현 해상도를 모델 오차와 함께 해석한다.

## 데이터·모델 선택

- seed=20261028의 2차원 Latin hypercube 방식으로 24개 recipe 설계.
- train 16 / validation 4 / test 4. recipe와 run_id 교집합, 최종 시각 일치를 실행 중 검사한다.
- 정규화는 train에서만 계산한다. 64점 최종 형상의 x/y 좌표를 2차 다항 ridge 회귀로 예측한다. 신경망·FNO·MGN이 아니다.
- alpha 후보 .0001/.01/1을 validation Chamfer로 선택한 뒤, 고정 모델을 JSON으로 저장·다시 읽어 test를 평가한다.
- 비교 대상은 동일 train에서 찾은 최근접 recipe의 최종 형상이다. 둘 다 같은 재표본화와 최종 시각으로 평가한다.
- 초기 형상은 입력·계약 확인에 쓰되 점수에 포함하지 않는다. prediction bundle 정책의 evaluation_times_seconds=[1.0]으로 최종 단면만 채점한다.

test 4건은 작은 독립 확인 자료다. 성능 개선 비율이 나오더라도 전역 일반화·7변수 범위·OOD·실제 fab 정확도를 주장할 근거는 아니다. threshold 통과도 탐색 평가에 한정하고 승격하지 않는다.

## 재현

```bash
PYTHONPATH=src /path/to/simulation-env/bin/python examples/local_surrogate_study.py --output reports/generated/new-local-study
```

원본, 설정, native 로그, 실행 기록, split, 정규화된 레코드, alpha별 모델, 선택 기록, recipe별 판정과 지문은 출력 폴더에 보관한다. 기존 출력은 덮어쓰지 않는다. 학습 모델과 raw는 Git에 추가하지 않고 작은 결과·지문·그림만 reports/evidence에 보관한다.

## 이번 실행 결과

수치 비교 9회와 데이터 생성 24회, 총 33회 시뮬레이션을 완료했다. medium↔fine Chamfer는 .003235~.003544um, 깊이 차이 최대 .000496um로 사전 진행 조건을 통과했다.

validation에서 alpha=.0001을 선택했다. test 4개에서 ridge Chamfer 평균 .00116810um, 최근접 baseline .00294403um로 이 표본에서는 약 60.3% 감소했다. 최대 recipe 오차는 각각 .00296409/.00385503um다. 깊이 MAE는 .00004825/.00364269um였다. 두 모델 모두 사전 탐색 정책에서 4/4 PASS이며 승격은 하지 않았다.

test 중 r021의 ion_flux와 r023의 ion_mean_energy는 해당 train 표본의 축별 min/max 밖에 있다. 다만 모두 계획한 국소 범위 안에 있으며, 별도의 전역 OOD 평가를 구성한 것은 아니다.

상위 실행 명령은 비정상 종료했고 마지막 통합 manifest가 없었다. 수치 결과를 바꾸거나 다시 학습하지 않고 33개 raw/request 지문, training 기록·모델 지문을 재검사하고, 저장된 모델을 로드해 test를 재생했다. 모든 점수가 동일했고 별도로 통합 manifest를 만들었다. 원 실행 전체가 정상 종료했다고 기록하지 않는다.

```powershell
$env:PYTHONPATH='src'
python examples/verify_local_study.py reports/generated/local-study-001 --record reports/generated/new-verification.json
```

모델 선택을 다시 하는 명령이 아니라 기존 모델과 원본을 확인하는 명령이다. 이후 드라이버는 실행 전 소스 사본을 보관하고, 최종 봉인 후 외부 완료 marker를 남기도록 보강했다. 이번 결과의 당시 driver SHA와 보강 후 코드를 구분한다.

모델 오차보다 medium/fine 수치 차이가 더 크다. 이 결과는 **선택한 simulator 설정을 근사한 정도**이며 그 오차를 실제 공정 정밀도로 해석하지 않는다. 표본 4개·단일 설계 seed·2변수·1초 결과의 한계가 있다. [상황 보고](STATUS_20261028.md)와 reports/evidence/local-study-20261028.json에 상세 근거를 남겼다.
