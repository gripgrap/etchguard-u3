# 팀 모델 연결 재확인 — 2026-10-28

결론: FNO는 선택 후보다. 먼저 재현 가능한 예측과 정답을 같은 평가 경로에 연결한다. 이번 작업은 저장된 팀 예측의 형식·기하 검사이며 checkpoint 추론이나 정확도 검증이 아니다. 노션은 갱신하지 않았다.

## 실제로 다시 확인한 자료

GitHub 연결 도구로 재조회한 전체 tree는 truncated=false였다. 한진주 저장소는 `e6b20fe392b98dbd0d55537d8227b7691972c886`, 김민규 저장소는 `6a2dafd65a72d11324246cfdbfa5ba490c9c548f`였다. 두 tree에서 pt/pth/ckpt/npz/npy/onnx/safetensors 파일을 찾지 못했다. Git tree 밖의 Releases·별도 저장소·로컬 파일이 없다는 뜻은 아니다. 장민서 저장소는 현재 연결에서 404였다.

- [모델 구현](https://github.com/pearlhan-stack/etch-ai-pipeline/blob/e6b20fe392b98dbd0d55537d8227b7691972c886/src/etch_pipeline/models.py): MLP와 native PyTorch FNO가 모두 있다. 코드 존재와 실행 재현은 구분한다.
- [독립 추론](https://github.com/pearlhan-stack/etch-ai-pipeline/blob/e6b20fe392b98dbd0d55537d8227b7691972c886/src/etch_pipeline/infer.py): checkpoint 내부 설정·정규화·state_dict로 추론하며, 초기 ViennaPS 형상을 재구성한다. checkpoint 하나만으로 환경 없이 실행되는 구조가 아니다.
- [저장 예측](https://github.com/pearlhan-stack/etch-ai-pipeline/blob/e6b20fe392b98dbd0d55537d8227b7691972c886/reports/demo/c8-v1/after-block-prediction.json): fno-v1, 15초, 단일 component의 64점. ground_truth=null, truth_status=not_available다. 파일 안 gate PASS와 점수는 우리 재평가 결과가 아니다.

## 이번 직접 검사

저장 예측을 오늘 작업의 context 폴더에만 보관하고 현재 validate_profile로 검사했다. 단일 열린 polyline의 기본 기하 오류는 없었다. 이는 연결 형식을 받을 수 있다는 확인이며 전체 물리 타당성·정확성 인증은 아니다. 원본·checkpoint는 개인 Git에 추가하지 않았다.

현재 자체 데이터는 1초, opening .5µm, mask .3µm, ion exponent 500이다. 팀 예측은 15초에 다른 recipe다. 좌표 수가 64개로 같아도 같은 평가 문제가 아니다. 시간을 억지로 바꾸거나 정답을 예측에서 만들어 비교하지 않는다. smoke 설정의 trenchWidth 범위 .28~.42, maskHeight .16~.24, exponent 800~1200과도 자체 조건이 다르다. 이 설정이 해당 checkpoint와 정확히 일치하는지는 artifact를 받아 확인해야 한다.

## 모델 선택의 대안

| 후보 | 역할 | 채택 전 확인 |
| --- | --- | --- |
| 최근접 기준 | 비교의 출발점 | 동일 train·시간·표현 |
| Ridge | 이미 확보한 국소 학습 실증 | 좁은 2변수 범위와 외삽 제한 |
| MLP | 팀 코드에도 있는 신경망 후보 | checkpoint·scaler·split·공통 정답 |
| FNO | 격자장 예측 후보 | 초기 SDF·격자·시간·단위·contour 변환 계약 |
| MGN | 연결 구조 예측의 후속 후보 | topology·정점 대응·순서 보존과 유효성 |

복잡한 모델 순서로 도입하지 않는다. artifact 확보 가능성, 계약 호환성, 독립 평가, 형상 실패율, 동일 환경의 warm/cold 추론 비용으로 결정한다. 현재 시험 4개로 모델 계열의 우열을 결론내리지 않는다.

## 다음 실행 단위와 종료 조건

1. 팀 모델 종류에 관계없이 한 묶음의 reference/prediction·동일 recipe/time·학습 split 이력을 확보한다. 없는 정답과 불명확한 분리는 NOT_EVALUABLE로 기록한다. 기존 시험 결과를 보며 튜닝한 경우 새 독립 자료를 사용한다.
2. 변수 alias를 생성 코드의 물리 정의와 대조한다. 특히 trenchWidth/mask_width는 이름만 보고 치환하지 않는다. SDF→contour 변환은 원 좌표·연결성·변환 오차를 남긴다. 외부 파일 검사를 통과한 것과 checkpoint를 실행한 것을 구분한다.
3. 현재 ridge로 먼저 최소 운영 연결을 검증한다. 저장 모델 지문 검사→독립 평가→연구용 registry 등록/차단→등록 모델 재로드 추론을 연결한다. 예측 파일 PASS만으로 승격하지 않으며, 기존 기준 모델을 같은 평가셋에서 다시 비교한다. 손상 모델·성능 악화 시 current 불변을 확인한다.
4. 별도로 작은 새 계획으로 생성→학습→평가→최종 manifest/완료 marker의 정상 종료를 확인한다. 이전 33회 실행의 사후 봉인 성공을 이 새 정상 종료 증거로 대체하지 않는다. 이 실행은 orchestration 확인이며 새로운 성능 주장에 쓰지 않는다.
5. 자료가 확보되면 MLP/FNO 등 팀 checkpoint를 연결한다. 팀 artifact를 확보하지 못하면 그 사실을 유지하고 자체 모델로 검증 경로를 진행한다. FNO 자체 학습은 필수 선행 조건이 아니다.

## 축소 E2E 정상 종료 재실행

위 4번을 별도 계획으로 실행했다. pilot 9회 + dataset 6회, train/val/test=4/1/1이다. WSL에서 `examples/local_surrogate_study.py --plan ../context/controller-smoke-plan.json --output reports/generated/controller-smoke-001`을 실행해 약 478초에 종료 코드 0을 확인했다. 실제 생성→변환→분리→학습→선택→저장 모델 추론→예측 파일 판정→통합 봉인→외부 완료 marker까지 정상 종료했다.

현재 verify()로 통합 지문과 marker 일치를 확인하고 15개 raw의 원래 manifest도 재검사했다. [작은 실행 증거](../reports/evidence/controller-smoke-20261028.json)에 기록했다. 이는 완료 처리의 실증이며 새 정확도 주장이나 기존 24 recipe 실험의 정상 종료 증거가 아니다. 작은 계획과 raw/model은 generated/context에 유지한다.

현재 운영 E2E와 위 3번은 계획이다. registry 등록·API 추론·drift 재학습까지 완료했다고 기록하지 않는다. [앞선 실제 실험 상태](STATUS_20261028.md), [예측 파일 평가 경계](PREDICTION_BUNDLE.md)를 함께 읽는다.
