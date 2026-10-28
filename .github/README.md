# GitHub Automation

`workflows/ci.yml`은 패키지를 설치하고 **표준 라이브러리 기반 unittest + synthetic demo**를 실행합니다. 실제 ViennaPS 물리 시뮬레이션이나 학습 체크포인트를 CI에서 재현한다는 뜻이 아닙니다.

작업은 새 브랜치에서 하고, 문서나 코드의 설계 계약 변경에는 [DECISIONS](../docs/DECISIONS.md) 갱신과 PR 검토를 권장합니다. 시작 규칙은 [AGENTS](../AGENTS.md)를 따릅니다.
