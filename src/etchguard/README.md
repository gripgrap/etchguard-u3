# `etchguard` 패키지 안내

작업 전 **[계약](../../docs/INTERFACE.md)** · **[설계](../../docs/ARCHITECTURE.md)** · **[Codex 규칙](../../AGENTS.md)**을 먼저 읽으세요.

| 파일 | 핵심 기능 | 직접 사용하는 것 |
|---|---|---|
| `contracts.py` | recipe 7필드·시간 단조 증가·제한된 열린 2D profile 검사 | `validate_run` |
| `integrity.py` | 경로/크기/해시 매니페스트 생성·검증 | `freeze`, `verify` |
| `demo.py` | **toy synthetic** 생성 | `generate`, `load_runs` |
| `model.py` | 학습 없는 baseline | `NearestRecipeBaseline` |
| `metrics.py` | Chamfer 및 depth error | `score_pairs` |
| `gate.py` | fingerprint 값 확인 후 metric PASS/BLOCK | `evaluate_candidate` |
| `registry.py` | 테스트용 champion/이력 저장, BLOCK 보존 | `Registry` |
| `report.py` | JSON과 연동한 HTML | `write_html` |
| `cli.py` | `demo/freeze/verify` 명령 | `python -m etchguard.cli` |

**표준 라이브러리만 사용**합니다. 실제 ViennaPS 버전/파일을 아직 검증하지 않았으며, `source_type` 메타데이터만으로 실제 출처를 보증하지 않습니다. `gate.evaluate_candidate`는 디스크를 자동 검증하지 않고 fingerprint *문자열*을 비교하므로, 실제 운영 호출 전 `integrity.verify`와 연결이 필요합니다.

새로운 adapter/모델 추가 시 단위 테스트→회귀 테스트→증거 문서→README 상태표 순서로 변경하세요. 다른 팀원 소스는 인가와 라이선스 없이 복사하지 않습니다.
