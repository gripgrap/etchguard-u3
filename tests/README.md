# Tests — 신뢰할 수 있는 것과 아직 못하는 것

```bash
python -m unittest discover -s tests -v
```

2026-10-28 로컬 실행: **25 tests, OK**. CI는 GitHub Actions run을 별도 확인해야 합니다.

| 파일 | 범위 |
|---|---|
| `test_contracts.py` | 입력 레시피, 비유한 좌표, 시간 순서·단면 유효성 |
| `test_integrity.py` | freeze/verify, 파일 변조·추가·삭제, 매니페스트 요구 |
| `test_metrics_gate.py` | toy baseline Chamfer/깊이, gate 정상/열화/무결성, champion 불변, CLI demo |

테스트 fixture는 **실제 ViennaPS 결과가 아닙니다.** `source_type=synthetic_fixture`를 유지해야 합니다. 새 tests가 실제 VTP/mesh 또는 모델 checkpoint를 필요로 하면 이를 분리한 **opt-in integration**으로 만들어, CI가 fixture만 실행하고도 실제 시뮬레이션을 검증했다고 주장하지 않도록 합니다.

새 테스트 우선순위: (1) 실제 `verify`를 gate 호출 전에 강제하는 fail-closed path (2) 같은 recipe 다른 raw bytes 차단 (3) adaptive timestamp·분→초 변환 (4) split 누수/모델 교체 회귀 검증.
