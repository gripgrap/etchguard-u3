# GitHub 작업 거점 — gripgrap/etchguard-u3

본 저장소 주소: https://github.com/gripgrap/etchguard-u3  
기본 브랜치: `main` / 현재 작업 기준: `AGENTS.md`, `docs/`.

## 신규 Codex 세션 온보딩

1. 이 저장소를 GitHub에서 연결해 클론합니다.
2. `README.md` → `AGENTS.md` → `docs/README.md` → `docs/PROJECT_CONTEXT.md` → `docs/DECISIONS.md` → `docs/INTERFACE.md` → `docs/CODEX_NEXT.md` 순으로 읽습니다.
3. 새 환경에서 설치와 25개 로컬 테스트를 직접 실행합니다. 실제 실행 전 25개 통과를 주장하지 않습니다.
4. `python -m etchguard.cli demo --output reports/generated/<새-실험명>` 실행으로 toy PASS/BLOCK 시연을 확인합니다.
5. 후속 작업은 `feat/<scope>` 브랜치에서 진행하고, 테스트·증거·문서를 같은 PR에 포함합니다.

## GitHub CI 및 버전관리

- `.github/workflows/ci.yml`: Python 3.11, `pip install -e .`, unittest, fixture demo. Actions가 실제 성공했는지 URL/커밋으로 확인.
- 실패한 CI는 원인을 기록하고 범위를 축소. green badge만으로 실제 ViennaPS 실행/학습 완료로 표현하지 않음.
- 산출물은 `docs/PERSONAL_PROGRESS.md`에 날짜, 명령, 실제 결과, 실패/해결, 변경 파일, commit/PR 링크로 기록.
- 팀원 저장소는 참조용. 소스 복사는 사용/배포 권한과 라이선스 확인 후 결정.
- 비밀키, `.env`, 원본 대용량/비공개 데이터, 원본 체크포인트는 Git에 커밋하지 않음.

## 주의

공개 저장소지만 라이선스 결정은 보류 상태(`LICENSE-DECISION.md`)입니다. 라이선스 정책과 개인 소유 코드의 권리 범위를 결정한 뒤 파일을 추가합니다. 최초 작업 기록은 이 세션에서 v0.1 프로젝트와 docs를 생성한 기록입니다. 새로운 실행 증거는 반드시 Codex 환경에서 다시 검증해야 합니다.
