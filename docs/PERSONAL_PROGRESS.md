# 개인 개발 진행 기록

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
