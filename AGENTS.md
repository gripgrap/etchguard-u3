# EtchGuard — Codex 작업 원칙

## 사용자 작업 방식 (2026-10-28)
- 별도 작업 브랜치 없이 main에 반영하되, 반영 전에 추가 검증한다.
- PR을 사용하는 경우 제목은 `feat: 한글 제목` 또는 `fix: 한글 제목`, 본문도 한글로 작성한다. 커밋도 같은 형식을 따른다.
- 각 구현 뒤 테스트·실패 사례·실제 실행을 확인하는 작은 피드백 루프를 유지한다.

## 정의
- 개인 repo의 독립 검증/승인 연구용 MVP. 기존 팀 프로젝트의 포크가 아님.
- 현재 v0.1 데모 데이터는 명시적으로 synthetic_fixture; 어떤 보고서에서도 실제 ViennaPS 성능이라 표시하지 않는다.
- 기능: C1/C2 입력·무결성 검증 → C4 평가 → C5 게이트 → C6 레지스트리 → C8 연동 예정.
- 모델: v0.1은 최근접 베이스라인. 학습된 FNO/MGN으로 표현하지 않는다.

## 신규 Codex 세션 시작할 때 반드시 읽는 문서
1. `README.md` (현재 할 수 있는 것과 없는 것).
2. `docs/README.md` (전체 문서 목차).
3. `docs/PROJECT_CONTEXT.md` 및 `docs/TEAM_REFERENCE.md` (대화에서 확인된 팀 개발 상황과 근거).
4. `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/INTERFACE.md` (설계·검증 경계).
5. `docs/LOCAL_VERIFICATION.md`, `docs/ROADMAP.md`, `docs/CODEX_NEXT.md` (실행 증거와 다음 작업).

**목표:** 코드를 무작정 확대하기보다, 현재 검증 수준을 테스트로 확인한 후 ViennaPS 실제 데이터를 **읽기 전용**으로 연결한다.

## 우선순위
1. `python -m unittest discover -s tests -v` 실행 확인.
2. `python -m etchguard.cli demo --output reports/generated/NEW-NAME` 실행 확인.
3. `docs/INTERFACE.md`의 데이터 계약 보존.
4. 파일·설정 content fingerprint 원본 변조/추가/삭제 부정 테스트.
5. 실제 ViennaPS 데이터를 연동하되 코드 실행 증거가 없으면 simulation-origin으로 표시하지 않는다.

## 절대 금지
- 통과 기준을 결과가 좋게 나올 때까지 조정하고 "검증"으로 포장하지 않는다.
- test/golden 자료를 학습에 사용하지 않는다.
- fixture를 실제 fab 또는 ViennaPS 데이터라고 표시하지 않는다.
- 외부 개인 저장소의 코드/원본/체크포인트를 라이선스·출처 확인 없이 복제하지 않는다.
- 실제 장비 제어/인터락·안전 승인 등을 주장하지 않는다.
- 비밀키, 거대 데이터, checkpoint를 Git에 추가하지 않는다.

## 구현 방법
- 작업 단위 최대 2개. 먼저 테스트와 실패 사례를 작성한 뒤 코드 변경.
- 단위/좌표/시각/정규화/평가셋은 검토 없이 변환하지 않는다.
- `recipe identity`와 `artifact content fingerprint`를 구별하고 기존 ADR 스키마와 충돌시키지 않는다.
- 시간 단위는 `t_seconds`, 형상 좌표는 `points_um`으로 명시한다.
- 실행 명령·실제 결과·불확실성을 `docs/PERSONAL_PROGRESS.md`에 기록한다.
- 다음 구현 전에 README의 성취 수준을 실제 실행 결과에 맞춰 갱신한다.

## 다음 1순위 요청
첫째, 로컬 테스트와 데모를 실행해 현재 결과를 확인한다.
둘째, `code5312/Automation-Project-etch-AI`의 ViennaPS raw fixture/VTP를 조회해 별도 선택적 어댑터를 만든다.
단, polyline 순서·cell_data 재료 ID·실제 시각·시뮬레이터 버전 불일치를 검사한다.
