# 설계 결정 기록 (ADR-lite)

## D-010 실제 simulator→예측 파일 평가 연결 — 2026-10-28

- Windows wheel DLL import 실패 후 시스템 DLL 변경 대신 별도 WSL 환경에서 ViennaPS 4.5.0/ViennaLS 5.8.5를 실행했다.
- reference/prediction/policy 봉인 bundle의 recipe·출처 지문·시간 근거·시각을 검사한 뒤 평균/최대 오차를 평가한다. 결과는 파일 평가이며 승격 권한은 없다. 모델 artifact SHA는 제출 주장으로 구분한다.
- 직접 관찰한 생성 실행은 실행 기록·driver/config digest와 묶는다. 외부 원본의 source_type은 자동으로 simulation으로 바꾸지 않는다.
- explicit snapshot_times_seconds/time_basis를 지원하며 누락·비증가 시각은 차단한다. 초 단위 process duration 누적값과 callback 관측 시각은 구별한다.
- oracle/오류 주입은 평가기 제어 검사다. 실제 모델 학습·일반화 성능, coverage/mesh/ray 수렴은 미검증. [실행 근거](VIENNAPS_SMOKE.md).

## D-009 실제 VTP 읽기 전용 검사 — 2026-10-28

- PyVista는 vtp 선택 의존성으로 격리. 순수 연결성 검사는 표준 라이브러리로 실행한다.
- 팀 고정 fixture를 저장소 밖에서 읽고 Si cell connectivity로 열린 2D 경계를 복원한다. 실제 시각 근거가 없으면 유도 시각으로 명시하고 external_research 출처를 유지한다.
- 지원하지 않는 성분·분기·폐곡선은 추측 변환하지 않는다. [범위와 실행 증거](VTP_INSPECTION.md).

## D-008 검증된 bundle의 고정 시각 baseline 실행 — 2026-10-28

- 외부 expected fingerprint를 기준으로 train/golden/policy를 함께 검사하고, 확인한 바이트를 평가 입력으로 사용한다. 실행 중 자동 freeze는 하지 않는다.
- recipe identity와 최종 물리 시각이 맞지 않으면 BLOCK(2). 결과 evidence를 history에 기록한 뒤 PASS일 때 champion 포인터를 갱신한다.
- 범위는 비신경망 baseline 및 단일 writer다. 임의 checkpoint 승격, 서로 다른 평가셋의 저장 점수 비교, 동시 실행 트랜잭션은 이번에 추가하지 않는다.
- 인터페이스와 위협 모델: [VERIFIED_WORKFLOW](VERIFIED_WORKFLOW.md).

결정은 **검증된 사실 / 선택한 제안 / 보류/미확인**을 구분합니다. 변경 시 날짜, 근거, 대안, 영향, 실행 증거를 남깁니다.

## D-001 독립 EtchGuard 검증 계층 우선 개발 — 채택

**배경:** 팀 각자 구현 요구와 최신 팀원 연구에서 데이터 생성·FNO 모델·웹 시연 등이 이미 존재. 하지만 실행 증거/승인 규칙/단위/해시가 완전히 공통화되지 않음.

| 대안 | 장점 | 단점 | 채택 판단 |
|---|---|---|---|
| A. 팀원 파이프라인 포크 | API/학습/데모 빠른 재사용 | checkpoint·raw가 Git에 없을 수 있음, 비공개 라이선스·독립기여 설명 위험 | 미채택 |
| B. ViennaPS+FNO+MGN+CI 전체 신규 재구현 | end-to-end 독립 | 시간·자원 위험, 팀원과 중복, 검증 누락 가능성 | 후속 옵션 |
| **C. 독립 품질 검증 계층** | 누구의 데이터/모델도 검증할 수 있고 독립 테스트로 기술적 기여가 명확 | 초기 버전에는 학습 모델 자체가 없음 | **채택** |

**성과 정의:** `실제로 확인된 데이터 계약·원본 fingerprint·평가·회귀 gate·챔피언 보존`의 증거. GUI보다 자동 검사·재현성이 우선.

## D-002 recipe identity와 content fingerprint를 분리 — 채택

- **기존 팀 계약:** `params_hash`와 `dataset_hash`는 원래 팀 코드/ADR의 값이며 변경하지 않음.
- **추가 독립 계약:** `content_fingerprint`는 root 상대 경로·파일 크기·각 파일 SHA-256을 정렬/직렬화한 문서의 SHA-256.
- **검증된 한계:** 원본과 manifest를 동시에 바꾸면 독립 신뢰 보증 X. 파일 내용 변경 검출과 출처 진위/서명은 별개.
- **후속:** config, library build, git SHA, 실제 run ID, raw snapshot manifest를 하나의 attestation으로 연결.

## D-003 시험용 toy fixture와 ViennaPS 출처 구분 — 채택

- 현재 Gaussian toy profile은 `source_type=synthetic_fixture`. 어떠한 출력이나 시각화에서도 실제 fab/ViennaPS로 쓰지 않음.
- `viennaps_simulation` 표시는 **원본 시뮬레이션 artifact/실행 로그/설정/버전**이 확보된 뒤에만 사용.
- 팀원 보고 수치를 본인 실측 수치로 승격 금지. 실제 학습 전 FNO/MGN 구현 성과 주장 금지.

## D-004 평가 데이터/시간/단위 계약 — 채택

- 레시피 7개 필드 사용하되 팀의 alias와 물리 정의가 같다는 가정은 하지 않음.
- 내부 `t_seconds`, `points_um`; 팀의 `step_min` (분)에는 명시적 변환 단계 필요.
- train·val·test·golden·OOD는 **recipe-level**로 완전 분리. train-only normalization.
- `Chamfer`는 구현 정의와 물리 단위가 있을 때만 비교. CD/IoU는 동일한 기준면/마스크가 합의되기 전까지 v0.1에서 제외.

## D-005 gate의 허용 기준과 의미 — 채택

- v0.1 설정값은 toy demo만의 **설명용 초기 값**. 실제 배포 허용이나 물리 기준이 아님.
- 후보가 BLOCK되면 incumbent champion 그대로 유지. 판정 이력은 항상 기록.
- 단 현재 `evaluate_candidate`는 호출자가 공급하는 fingerprint를 **비교**합니다. 곧바로 디스크를 `verify()`하는 구조는 아니므로 **파일 무결성 검증→게이트를 하나의 fail-closed workflow로 결합하는 P1 보강이 필수**.
- 데이터 완전성·성능/회귀·독립 golden을 분리해 검증. 골든 정책은 결과를 보기 전 고정.

## D-006 외부 의존성/배포/라이선스 — 보류

- v0.1 코어는 Python 표준 라이브러리. `ViennaPS 4.5.0 + ViennaLS 5.8.5`는 **팀에서 검증했던 호환 후보**이며 이 저장소 자체에선 미검증.
- ViennaPS 정식 연동 시 의존성/OS별 호환을 로컬 실험, PyVista 선택 의존성, VTP 읽기 전용 adapter로 격리.
- 저장소가 public이라도 라이선스가 자동 부여되는 것은 아님. 독립 코드에 대한 LICENSE 결정 및 제3자 코드 직접 포함 시 GPL 등 검토 필요.

## D-007 작업 운영 — 채택

- 본인 GitHub `gripgrap/etchguard-u3` 를 단일 작업 거점으로 사용.
- 루트 `AGENTS.md`와 `docs/`를 **Codex 세션 간 기억의 기준 문서**로 사용. Codex/AI가 읽어야 할 문서 순서를 명확히 기록.
- 코드 수정은 새 branch + PR 권장. 첫 commit은 부트스트랩 예외 가능. GitHub Actions 초록 여부는 실제 workflow run 링크로 확인.
- `PERSONAL_PROGRESS.md`에 실행 명령·stdout요약·commit SHA·미완료를 남김.
