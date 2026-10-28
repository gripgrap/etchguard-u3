# 개인 개발 진행 기록

## 2026-10-28 팀 모델 재확인과 정상 종료 재실행

- GitHub 전체 tree를 다시 확인. 한진주 e6b20fe에 MLP/FNO 코드와 저장 예측이 있지만 해당 tree에서 checkpoint·NPZ를 찾지 못함. 장민서 연결은 404. 별도 artifact의 부재까지 단정하지 않음.
- 팀 저장 예측(15초, 64점, 정답 없음)을 context에 보관하고 validate_profile 검사 오류 0 확인. 성능 평가·checkpoint 직접 실행은 하지 않음. 자체 1초 데이터와 비교하지 않음.
- FNO를 필수로 정하지 않고 재현 자료·계약·독립 평가 기준으로 MLP/FNO/기존 ridge 연결 순서를 결정. TEAM_MODEL_READINESS.md에 근거·미완료 기록. 노션 변경 없음.
- 별도 controller-smoke 계획: pilot9+dataset6, split4/1/1. 실제 생성→학습→선택→평가→최종 봉인·완료 marker까지 약478초, 상위 명령 exit0. 15개 raw manifest와 root 지문/marker 일치 확인. 증거 reports/evidence/controller-smoke-20261028.json. 운영 registry/API는 여전히 미연결이며 새 성능 주장은 하지 않음.

## 2026-10-28 국소 수치 비교·학습·최종 평가

- 9개 테스트 먼저 작성 후 미구현 import 실패 → arc resampling/split guard/ridge 구현 통과. 저장 모델의 손상 검사 추가 후 실패를 확인하고 보강했다.
- 평가 시각 선택 테스트 2개 실패 확인 → evaluation_times_seconds 구현. Linux 전체 82개 통과.
- local-study.json 계획 고정 후 pilot 9회+dataset 24회 실제 생성. medium/fine Chamfer .003235~.003544um, 깊이 차이 최대 .000496um.
- train16/val4/test4, train-only scaler, validation으로 alpha=.0001 선택. test Chamfer ridge .00116810um vs nearest .00294403um. 두 모델 모두 탐색 정책 4/4 PASS, 승격 없음.
- 원 상위 명령 비정상 종료·마지막 manifest 누락. 생성·선택·판정 파일 보존 후 33개 raw/request/모델/training digest를 검증하고 refit 없는 replay에서 모든 metric 차이 0 확인. 별도 봉인 지문은 reports/evidence 기록에 포함.
- test 2개에 train 축별 범위 밖 조건이 있으며, model 오차가 simulator 수치 설정 차이보다 작아 물리 정밀도로 해석하지 않는다. 상세 STATUS_20261028.md.

## 2026-10-28 실제 시뮬레이션과 예측 파일 평가

- 먼저 prediction bundle 10개 실패/성공 테스트 작성 → import 실패 → 구현 후 통과. 이후 시점별 최대 오차·부가 metadata·수치 overflow 차단을 추가.
- 명시 시각 테스트 2개를 먼저 실패 확인한 뒤 VTP adapter에 snapshot_times_seconds/time_basis 검사를 추가.
- Windows ViennaPS 4.5.0/ViennaLS 5.8.5 설치는 성공, import는 native DLL 오류. 요구 VTK 9.3 DLL 등 의존성을 진단했고 전역 변경 없이 WSL Ubuntu/Python 3.12.3의 별도 환경을 사용.
- `PYTHONPATH=src ../viennaps-linux-env/bin/python examples/simulate_viennaps.py --output reports/generated/viennaps-smoke-final` 실행 성공. 2 threads/100 rays/grid .05um, 0/.5/1초의 세 snapshot 생성. 동일 설정 반복 raw fingerprint 일치.
- 원본 변조 차단, oracle PASS(0), 0.2um 오차 주입 BLOCK(1), 시각 불일치 BLOCK(2). 초기 형상 baseline도 depth/max 기준으로 BLOCK. 승격 없음.
- Linux 전체 70개 테스트 통과/skip 0. 수치 수렴성과 실제 학습 모델 성능은 미검증. reports/evidence의 작은 JSON/그림과 VIENNAPS_SMOKE.md에 결과·제한 보관.

## 2026-10-28 main 작업 및 VTP 검사

- 사용자 요청에 따라 main 직접 반영 + 추가 검증으로 변경. PR #1은 이미 병합돼 main c31f359 동기화, 원격/로컬 feat/verified-evaluation 삭제. PR 제목도 feat: 한글 형식으로 변경했다.
- 연결성 실패 테스트 9개 작성 → 미구현 import 실패 → 어댑터 구현 후 통과. 별도 vtp-env에서 압축 reader 포함 14개 통과.
- PyVista 0.49.1 / VTK 9.7.1 설치 후 팀 고정 fixture 1 recipe/4 snapshots 직접 읽음. 점 수 25/47/71/95, 유도 시각 0/60/120/180초.
- 원본/실제 생성 실행의 진위는 확정하지 않았으며 external_research 표기. 상세 fingerprint·지원 범위는 VTP_INSPECTION.md.
- 추가 검증: vtp-env 전체 55개 중 54개 통과/Windows symlink 1개 skip. 실제 fixture 변조 사본은 BLOCK, 원본 지문은 그대로 유지됨.

## 2026-10-28 검증 루프: bundle 평가

- 브랜치: feat/verified-evaluation. 작업 단위 1은 검증 workflow, 단위 2는 CLI와 evidence 기록이다.
- 먼저 12개 실패/성공 계약 테스트 작성 → workflow 미구현 import 실패 확인 → 구현 후 12개 통과.
- CLI·기록 실패·성능 차단 등 4개 추가 → CLI 미구현 실패 확인 → CLI 연결.
- Windows Python 3.13.12, PYTHONPATH=src, TEMP/TMP=1028/review-tmp: 전체 41개 중 40개 통과/1개 skip. symlink 생성 권한 WinError 1314만 skip하며 Linux에서는 실제 차단 검사를 유지한다.
- 기존 demo도 PASS(0)/열화 BLOCK(1)/해시 BLOCK(2)/champion 보존 재확인.
- 실제 VTP·checkpoint 연동과 CPU 클러스터 진단은 이번 범위에 포함하지 않음.

## 2026-10-28 README 표시 수정 및 연동 준비
- `.github/README.md`를 docs/GITHUB_AUTOMATION.md로 이동. 커밋 `88bcff8`, GitHub readme API의 path가 README.md인 것을 확인.
- [수정 CI 성공](https://github.com/gripgrap/etchguard-u3/actions/runs/40648008012).
- 팀 커밋 `6a2dafd`의 raw meta/VTP 헤더, run_sim, ETL, 재료 mapping, ADR, NOTICE를 읽고 INTEGRATION_PREPARATION.md에 근거·미확인·부정 사례·완료 조건 작성.
- pyvista/vtk/viennaps/viennals 미설치 확인. VTP 디코딩·시뮬레이션·모델 통합은 아직 실행하지 않음.

## 2026-10-28 Windows 인수
- 오늘 작업 폴더는 임시 기준이며 팀 통합 시 이동 가능. 상세: [HANDOFF_20261028](HANDOFF_20261028.md).
- Python 3.13.12, PYTHONPATH=src, 작업 폴더 내부 TEMP/TMP로 unittest 실행: 24개 통과, symlink 생성 권한 오류 1개.
- CLI demo PASS/BLOCK 3개 시나리오, champion 보존 및 golden verify 성공.
- GitHub 플러그인 쓰기 403 확인 후 유효한 로컬 Git 인증으로 기존 main 이력을 보존해 업로드 진행.

## 현재 시작 상태
- 2026-10-28: 독립 starter v0.1 작성; 팀원 코드 파일을 복사하지 않고 자체 구현.
- 기술 방향: ViennaPS 데이터/형상 검증 → 베이스라인/실제 모델 평가 → 회귀 게이트 → champion 보존.
- 아직 실행하지 않은 항목은 완료라고 표시하지 않는다.

## 실행 확인 (본인 환경에서 작성)
| 단계 | 명령 | 실제 출력/실패 | 커밋 SHA |
|---|---|---|---|
| 설치 | `python -m pip install --no-build-isolation -e . -q` | 컨테이너에서 성공 | - |
| 단위 테스트 | `PYTHONPATH=src python -m unittest discover -s tests -v` | 25개 통과 / 실패 0 | - |
| 데모 | `python -m etchguard.cli demo --output reports/generated/local-verification` | PASS(0), 열화 BLOCK(1), 해시 BLOCK(2), champion 보존 | - |
| GitHub Actions | 저장소 Actions URL | 미기록 | - |
| ViennaPS 실제 실행 | 예정 | 미실행 | - |

## 이후 결정/오류 기록
- 날짜:
- 목표:
- 설계 선택 및 근거:
- 변경 파일:
- 실제 실행한 명령:
- 출력과 실패:
- 해결:
- 다음 작업:
