# GitHub Automation

`workflows/ci.yml`은 패키지를 설치하고 **표준 라이브러리 기반 unittest + synthetic demo**를 실행합니다. 실제 ViennaPS 물리 시뮬레이션이나 학습 체크포인트를 CI에서 재현한다는 뜻이 아닙니다.

GitHub는 `.github/README.md`를 루트 README보다 우선하여 메인 소개에 사용합니다. 이 문서는 `docs/`에 두어 루트 README가 표시되도록 합니다. 작업 규칙은 [AGENTS](../AGENTS.md), 설계 기록은 [DECISIONS](DECISIONS.md)를 따릅니다.
