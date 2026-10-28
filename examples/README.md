# Examples — synthetic-only demo artifacts

- `demo_summary.json`: 최근접 recipe 베이스라인과 3개 시연 시나리오의 예시 성적/판정.
- `demo_report.html`: 같은 결과를 보여 주는 독립 HTML 문서.

**두 파일은 실제 ViennaPS/FNO 정확도 자료가 아닙니다.** 원본 생성기 `src/etchguard/demo.py`의 Gaussian toy 식각 곡선을 사용합니다. `reports/generated/` 하위 출력은 Git 추적하지 않으며, 새로운 `--output` 경로로 재생성해 비교할 수 있습니다.

```bash
python -m etchguard.cli demo --output reports/generated/example-001
```

실제 수치 검증 결과를 examples 폴더에 넣기 전에는 출처/실행 명령/데이터 계약/CI 및 연구 한계를 함께 기록해야 합니다.
