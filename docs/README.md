# Documentation Hub — 사람과 Codex를 위한 읽기 안내

**처음 보는 사람:** 루트 [README](../README.md) → [PROJECT_CONTEXT](PROJECT_CONTEXT.md) → [ARCHITECTURE](ARCHITECTURE.md) → [ROADMAP](ROADMAP.md).  
**Codex/개발 에이전트:** [AGENTS](../AGENTS.md) → [INTERFACE](INTERFACE.md) → [LOCAL_VERIFICATION](LOCAL_VERIFICATION.md) → [DECISIONS](DECISIONS.md) → [CODEX_NEXT](CODEX_NEXT.md).

## 문서 분류

현재 진행 상태: [현황 보고](STATUS_20261028.md) · [소형 모델 실험](LOCAL_STUDY.md).

최신 실증: [ViennaPS 직접 실행](VIENNAPS_SMOKE.md) · [예측 파일 평가 계약](PREDICTION_BUNDLE.md).

실제 VTP 읽기 결과와 선택 어댑터: [VTP_INSPECTION](VTP_INSPECTION.md).

구현된 고정 시각 baseline 경로: [VERIFIED_WORKFLOW](VERIFIED_WORKFLOW.md).

최신 준비 자료: [연동 준비 조사](INTEGRATION_PREPARATION.md) · [GitHub 자동화](GITHUB_AUTOMATION.md).

| 문서 | 질문 | 출처/성격 |
|---|---|---|
| [PROJECT_CONTEXT](PROJECT_CONTEXT.md) | U3 팀 프로젝트가 어떻게 변경되었고 개인 MVP를 왜 시작했나? | 회의/팀 노션/대화 맥락, 조사 스냅샷 |
| [TEAM_REFERENCE](TEAM_REFERENCE.md) | 누가 무엇을 실제로 구현했다고 기록했고 무엇이 미확인인가? | 팀 노션·GitHub 검증/보고 구분 |
| [DECISIONS](DECISIONS.md) | 포크 대신 왜 독립 검증 계층인가? | 명시적 설계 의사결정/대안 비교 |
| [ARCHITECTURE](ARCHITECTURE.md) | 데이터→평가→승격의 실제 구현 경계는? | 코드 기반 설계 및 제한 |
| [INTERFACE](INTERFACE.md) | 7변수, 단위, 스냅샷, 해시 및 게이트 계약은? | 현재 코드 계약 |
| [ROADMAP](ROADMAP.md) | 무엇부터 구현하고 언제 완료로 보나? | 구현 단계/완료 조건 |
| [CODEX_NEXT](CODEX_NEXT.md) | 다음 Codex 세션의 첫 실행은 무엇인가? | 재사용 가능한 실행 지침 |
| [LOCAL_VERIFICATION](LOCAL_VERIFICATION.md) | 실제로 무엇을 실행했고 무엇은 미검증인가? | 로컬 명령/출력 기반 증거 |
| [PERSONAL_PROGRESS](PERSONAL_PROGRESS.md) | 개인 기여와 Git 커밋을 어떻게 기록하나? | 작업 로그 |
| [START_GITHUB](START_GITHUB.md) | GitHub와 협업/CI를 어떻게 시작하나? | 저장소 운영 규칙 |

## 유지 규칙

1. **검증 수준은 네 단계로 분리:** `구현` / `로컬 실행 검증` / `GitHub CI 검증` / `실제 ViennaPS/모델 성능 검증`. 서로 자동 승급시키지 않습니다.
2. 팀원 노션에서 **보고한 결과**와 GitHub 파일/워크플로를 **직접 확인한 결과**를 분리합니다. 서로 다른 시점의 기록은 가장 최신이라고 단정하지 않습니다.
3. 신규 수치에는 데이터셋, 단위, 하드웨어, 실행 명령, commit SHA, 측정 시점을 함께 기록합니다. 근거 없으면 `미확인`.
4. 실험 임계값은 실행 전 고정하고, 모델 성능에 맞춰 사후 완화한 경우 별도 실험으로 표기합니다.
5. 공개 저장소에는 Notion에서 확인한 **팀원 개인 연락처, 이메일, 학번 등**을 옮기지 않습니다.
6. 문서의 상태가 바뀌면 루트 README의 현재 상태 표와 이 목차를 같이 갱신합니다.

## 폴더별 사용 안내

- [src/etchguard](../src/etchguard/README.md): 코드 인터페이스와 모듈 관계
- [tests](../tests/README.md): 테스트 범위와 실행 명령
- [configs](../configs/README.md): 게이트 기준 및 예제 정책
- [examples](../examples/README.md): 재생성 가능한 정적 시연 결과
- [.github/workflows](../.github/workflows/README.md): CI 설명과 검증 경계
