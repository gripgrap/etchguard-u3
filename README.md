# EtchGuard

> 2026-10-28 업데이트: [고정 시각 baseline workflow](docs/VERIFIED_WORKFLOW.md)와 [읽기 전용 VTP 어댑터](docs/VTP_INSPECTION.md)를 추가했습니다. 선택 의존성을 설치한 Windows 환경에서 **54개 통과·권한 미지원 1개 skip**을 확인했고, 고정된 외부 fixture 4개 snapshot을 실제로 읽었습니다. 시뮬레이터 직접 실행·팀 모델 품질 검증과는 구분합니다.

**식각 AI 데이터·모델 검증 및 승인 자동화 | U3 개인 개발 프로젝트**  
*Evidence-first quality gate for semiconductor etch surrogate models*

> **현재 상태: v0.1 / synthetic-fixture 기반으로 실행 검증한 독립 MVP.** 실제 ViennaPS 시뮬레이션·FNO/MeshGraphNet 학습·공정 적합성은 아직 본 저장소에서 검증하지 않았습니다. 테스트용 `PASS`는 연구용 규칙에 대한 기능 검증이며, 생산 설비 배포 승인이나 물리적 정확성 인증이 아닙니다.

## 30초 이해하기

반도체의 **식각(etching)** 은 웨이퍼의 재료를 원하는 모양으로 깎는 공정입니다. 물리 시뮬레이터 ViennaPS는 조건에 따른 단면 형상을 계산하고, AI **대리 모델(surrogate model)** 은 그 계산을 빠르게 근사하려고 학습합니다. 그런데 예측이 빨라도 *잘못된 원본 데이터, 단위, 시각, 훼손된 모델*을 놓치면 결과를 신뢰할 수 없습니다.

**EtchGuard는 그 사이에서 데이터 출처를 검사하고, 예측 오차를 측정하고, 미리 정해 둔 기준에 따라 후보 모델 승격을 허용하거나 차단합니다.** 팀 모델과 경쟁하는 대체 프로젝트가 아니라 **모델 앞뒤에 붙는 독립 검증 계층**입니다.

```text
ViennaPS / 외부 데이터 / 팀원 모델                 [현재 구현: synthetic fixture로 검증]
             │
       출처·원본·설정 확인           → 데이터 내용 지문(SHA-256), 단위/시각/형상 검사
             │
       동일 평가 계약 적용           → 베이스라인/모델 예측 vs 별도 평가 레시피
             │
       회귀 게이트 평가               → Chamfer·깊이 오차 / 기존 챔피언 성능
             │
       ├─ PASS (코드 0)            → 승인 이력, champion 포인터 갱신
       ├─ BLOCK 성능 (코드 1)      → 기존 champion 유지, 사유 기록
       └─ BLOCK 무결성 (코드 2)    → 기존 champion 유지, 사유 기록
```

## 현재 할 수 있는 것 / 아직 할 수 없는 것

| 항목 | 상태 | 정확한 의미 |
|---|---|---|
| 7개 레시피 필드·2D 단면·시간(초) 검사 | **구현·로컬 검증** | 내부 JSON 계약 및 선택 VTP reader; 단일 열린 평면 경계만 지원 |
| 원본 파일 집합 SHA-256 fingerprint | **구현·로컬 검증** | 추가·삭제·바이트 변경 탐지. 자기 서명된 데이터 진위 보증은 아님 |
| 최근접 레시피 baseline, Chamfer·깊이 MAE | **구현·로컬 검증** | toy 형상에서만 평가. 학습된 신경망 아님 |
| PASS / BLOCK(성능·무결성), champion 보존 | **구현·로컬 검증** | 예시용 게이트 임계값. 실제 제조 승인 아님 |
| HTML 요약 및 JSON 이력 | **구현·로컬 검증** | 브라우저로 결과 열람, 상호작용형 생산 대시보드 아님 |
| 실제 ViennaPS 4.5.0 + ViennaLS 5.8.5 연동 | **미구현** | 설치·실제 원본·시간/재료/좌표 규격 검증 필요 |
| 실제 FNO/MGN/MLP 모델 성능·골든셋 | **미검증** | 팀원 보고 수치를 본인 실행 결과로 표기 금지 |
| drift → retrain → promote/rollback, 배포 | **미구현** | 독립 평가·모델 체크포인트·CI 연동이 선행돼야 함 |

## 시작하기

**Python 3.10 이상**을 권장합니다. v0.1 코어는 추가 런타임 패키지 없이 동작합니다.

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m etchguard.cli demo --output reports/generated/demo-local-001
```

Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m etchguard.cli demo --output reports/generated/demo-local-001
```

마지막 명령은 `reports/generated/demo-local-001/`에 `report.html`, `summary.json`, `registry/`, `data/`를 만듭니다. `report.html`을 브라우저로 열어 볼 수 있습니다. 결과물은 재현성 보존을 위해 **덮어쓰지 않으므로**, 같은 명령을 재실행할 때 `--output`의 새 경로를 사용하세요.

**원본 폴더 지문 만들기/검사:**

```bash
python -m etchguard.cli freeze path/to/raw-run
python -m etchguard.cli verify path/to/raw-run
```

`freeze`는 검사 대상 폴더에 `manifest.sha256.json`을 만듭니다. 원본을 수정한 다음 `verify`하면 실패합니다. 다른 사람이 manifest와 원본을 함께 바꾸는 위협까지 다루려면 별도 신뢰 저장소나 서명이 필요합니다.

### 실제 실행 확인 범위

2026-10-28 기준 로컬 Python 3.13 환경에서 **unittest 25개 통과**, synthetic demo의 `PASS(0) / 성능 BLOCK(1) / fingerprint BLOCK(2)`, BLOCK 이후 기존 champion 보존을 확인했습니다. **GitHub Actions에서 25개 테스트 및 demo 성공을 확인했습니다**([실행 결과](https://github.com/gripgrap/etchguard-u3/actions/runs/40647179084)). Windows의 symlink 권한 오류는 별도 환경 제한으로 남아 있습니다. 기록: [LOCAL_VERIFICATION](docs/LOCAL_VERIFICATION.md).

## 저장소 읽는 순서

| 대상 | 역할 |
|---|---|
| **[docs/README.md](docs/README.md)** | 모든 설계·검증 문서의 목차와 읽는 순서 |
| **[docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md)** | U3 프로젝트 전체 흐름, 팀원 현황 조사 및 기존 논의의 변화 |
| **[docs/DECISIONS.md](docs/DECISIONS.md)** | 복제 vs 신규 구축 비교, EtchGuard 채택 이유, 기술적 선택과 미확정 사항 |
| **[docs/TEAM_REFERENCE.md](docs/TEAM_REFERENCE.md)** | ViennaPS·팀원 GitHub/Notion의 근거와 검증 수준·호환성 이슈 |
| **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** | 아키텍처, 위험 경계, 단계별 PASS/BLOCK 설계 |
| **[docs/INTERFACE.md](docs/INTERFACE.md)** | 독립 내부 데이터 계약·단위·fingerprint·종료 코드 |
| **[docs/ROADMAP.md](docs/ROADMAP.md)** | P0–P3 우선순위, 완료 조건과 실행 경로 |
| **[docs/CODEX_NEXT.md](docs/CODEX_NEXT.md)** | Codex가 저장소에서 다음 작업을 시작할 수 있는 프롬프트 |
| **[docs/PERSONAL_PROGRESS.md](docs/PERSONAL_PROGRESS.md)** | 검증된 작업, 실행 명령, 실험·결정 로그 |
| **[AGENTS.md](AGENTS.md)** | AI 코드 에이전트 공통 규칙 및 금지사항 |

코드 안내: [src/etchguard/README.md](src/etchguard/README.md) · [tests/README.md](tests/README.md) · [configs/README.md](configs/README.md) · [examples/README.md](examples/README.md).

## 이 프로젝트가 해결하려는 실제 문제

1. **원본 vs 레시피 ID:** 팀의 `dataset_hash`는 recipe `params_hash`를 연결한 값입니다. 같은 레시피여도 원본 형상 바이트/시뮬레이터 설정이 바뀌면 현재 계산만으로 감지하기 어려워, EtchGuard가 **별도의 content fingerprint**를 둡니다. 기존 팀 계약은 임의로 변경하지 않습니다.
2. **시각·단위 차이:** 팀 코드에서는 `step_min`(분)을 사용하고 일부 생성기에서는 적응형 실제 스냅샷 시각을 별도 저장합니다. EtchGuard 내부는 `t_seconds`·`points_um`을 명시하고, 증거 없는 보간/시간 추정을 금지합니다.
3. **비교 불가능한 모델 점수:** 팀원들의 실험은 레시피 범위·스냅샷·격자·CD 정의·골든 정책이 다릅니다. 같은 프로토콜이 확정되기 전에는 점수를 직접 순위화하지 않습니다.
4. **회귀 게이트와 실제 품질:** 실모델이 극단 레시피에서 불합격한 사례가 있습니다. 테스트용 PASS와 실제 독립 골든셋 PASS를 구분하고, 실패한 후보는 기존 champion을 유지합니다.

## 개발 방향 및 범위

- **지금:** synthetic fixture 기반 v0.1을 GitHub에 보존하고, 재현 가능한 CI를 확보합니다.
- **다음 P1:** 실제 ViennaPS 형상/메타데이터의 **읽기 전용 어댑터**, 원본 fingerprint, 시각·단위 검사, 레시피 분리 검증을 구현합니다.
- **이후 P2:** 동일한 데이터·지표를 사용하는 베이스라인 대 실제 ML 후보 비교, golden/OOD·형상 실패 검증.
- **확장 P3:** 드리프트 후 재학습·재검증·승격/차단·롤백 증거, 팀 공통 계약과의 호환성 테스트.
- **제외:** 실제 설비 인터락·제어, 공장 품질 인증, 물리적 정확성의 과대 해석, 무단 팀 코드 복제, 무근거 임계값 완화.

다음 구현의 근거와 완료 조건은 [연동 준비 조사](docs/INTEGRATION_PREPARATION.md)에 정리했습니다.

자세한 의사결정과 실패 위험은 [DECISIONS](docs/DECISIONS.md)와 [ROADMAP](docs/ROADMAP.md)을 참고하세요.

## 참고 자료 및 라이선스

- [ViennaTools/ViennaPS](https://github.com/ViennaTools/ViennaPS): 공식 시뮬레이터. upstream GPL-3.0; 본 저장소에 직접 소스 복사·포함 없음.
- [김민규의 ETL/게이트 파이프라인](https://github.com/code5312/Automation-Project-etch-AI): 공개 연구 참고. 실제 더미 기반 CI 스켈레톤이 있으며 직접 코드 복제는 하지 않음.
- [한진주의 연구 파이프라인](https://github.com/pearlhan-stack/etch-ai-pipeline): 비공개 저장소이며 접근/사용 권한을 가정하지 않음. 실제 데이터·체크포인트는 새 checkout에 없음.
- [협업 Notion 스냅샷(10/27_3)](https://app.notion.com/p/1ce34713f167822ebbf001374e615bc4): 조사 당시 팀 개인 페이지·회의 기록 참고. 페이지 접근 권한이 필요할 수 있음.

각 팀원 보고 수치는 **제3자 연구 기록**이며 본 프로젝트 재실험 결과가 아닙니다. 상세 내용은 [TEAM_REFERENCE](docs/TEAM_REFERENCE.md). 공개 저장소의 라이선스는 아직 정하지 않았습니다: [LICENSE-DECISION](LICENSE-DECISION.md). 팀원 개인 연락처 등 민감정보는 기록하지 않았습니다.
