# 단계별 로드맵 (시간제한이 아닌 증거 기준)

## P0 — 직접 실행 가능한 검증 MVP (원격 CI 확인)
- [x] `unittest` 전체 통과(25개, 2026-10-28 로컬), 실행 로그 보존
- [x] synthetic demo PASS/BLOCK/integrity 각각 기대한 종료 코드 확인
- [x] 데이터 파일 조작 시 `verify`가 실패하는 부정 테스트
- [x] 차단 이후 `registry/current.json`이 변경되지 않는지 확인
- [x] 개인 GitHub [CI 성공](https://github.com/gripgrap/etchguard-u3/actions/runs/40647179084), 업로드 커밋 `273c3cc`

## 다음 실행 준비
- [연동 준비 조사](INTEGRATION_PREPARATION.md): 고정된 팀 커밋의 fixture/meta/ETL/ADR 조사와 부정 테스트·완료 조건.
- 어댑터 구현보다 먼저 무결성 검증·평가·승격의 연결 및 recipe/time 계약을 보강한다.

## P1 — 실제 ViennaPS C1/C2 어댑터
- [ ] `ViennaPS==4.5.0`, `ViennaLS==5.8.5` 독립 환경 실제 import 검증
- [ ] 팀원 `tests/fixtures/raw` 원본을 가져온다면 출처·재사용 범위 명시
- [ ] 최소 1개 실제 recipe 생성/변환 또는 공개된 실제 fixture를 read-only로 분석
- [ ] VTP cell connectivity 기반 순서 있는 2D polyline 복원·geometry check
- [ ] 입력 설정/버전/시드/rays/격자/실제 snapshot time 증거 보존
- [ ] 원본 SHA256 및 config fingerprint; 다른 recipe/원본으로 부정 테스트

## P2 — 예측·평가를 실제 데이터로 전환
- [ ] 독립된 레시피가 충분하면 train/val/test/golden 분할, split guard
- [ ] 베이스라인과 실제 ML(FNO 또는 MLP) 모델을 동일한 평가 프로토콜로 채점
- [ ] `baseline`은 비신경망 비교 기준으로 명시
- [ ] 수치·형상 오차 그래프, 불확실성·OOD, geometry false-PASS 방지
- [ ] 팀원들이 보고한 성능 수치와 무조건 비교하지 않음(데이터/단위/시간 불일치)

## P3 — 운영 자동화 + 통합 제안
- [ ] 이전 champion 동일 golden 평가, PASS 시 승격/실패 시 보존
- [ ] 드리프트 데이터 train/val/golden_drift 분리
- [ ] 회귀 게이트 CI 실행 + 실패 로그 아티팩트
- [ ] 팀 ADR-0001과의 별도 인터페이스 변환·호환성 테스트
- [ ] 실제 모델 재학습과 승인/차단 각각 1회 재현

## 보고해야 할 지표
- 실행/평가 시간, 데이터 provenance, recipe set 크기, 실제 ViennaPS 버전
- chamfer mean(µm), depth MAE(µm), 조건별 OOD, invalid-profile count
- 실제 관측 PASS/BLOCK 이력, 원본 파일 fingerprint, 시험 환경

## 중단 원칙
- ViennaPS 환경 설치가 막히면 무조건 참조 데이터로 되돌리지 말고 실패 원인/버전 기록.
- 데이터셋이 충분하지 않으면 학습 성능을 주장하지 않고 검증 데모로 한정.
- 골든이 후행 조정됐으면 그 모델의 게이트를 '독립 검증'으로 표시하지 않음.
