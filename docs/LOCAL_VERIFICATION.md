# 로컬 구현·테스트 증거 (2026-10-28)

## 실행 환경
- 실행 컨테이너의 Python 3.13.5 (v0.1 작성 환경; 신규 checkout에서 별도 확인 필요)
- GitHub CI는 추가로 확인해야 함. 현재는 로컬 테스트만 수행.
- 실제 ViennaPS / ViennaLS 설치·실행 검증은 **아직 진행하지 않음**.

## 실제 실행 결과

```bash
python -m pip install --no-build-isolation -e . -q
PYTHONPATH=src python -m unittest discover -s tests -v
# Ran 25 tests ... OK
python -m etchguard.cli demo --output reports/generated/local-verification
# baseline PASS (tutorial): exit 0
# degraded model BLOCK: exit 1
# fingerprint mismatch BLOCK: exit 2
# Champion unchanged after BLOCK: True
python -m etchguard.cli verify reports/generated/local-verification/data/golden
# SHA256 manifest verified
```

## 예제 수치 — synthetic fixture에만 적용

- Golden: 8개 (독립 recipe id, train 40개)
- 최근접 베이스라인 Chamfer mean: 0.01096066047 µm
- 식각 깊이 MAE: 0.01508394363 µm
- 최대 Chamfer: 0.02378347923 µm
- 현재 시연 임계값: Chamfer ≤ 0.15 µm, depth MAE ≤ 0.15 µm (물리적 기준 아님)
- 형상 변화는 **Gaussian 수식으로 생성한 toy fixture**이며 실제 식각 시뮬레이터의 성능이나 물리 정확도를 의미하지 않음.

## 저장된 예시 결과

- `examples/demo_summary.json`
- `examples/demo_report.html`

## 아직 실행·검증되지 않은 것
- Windows / Ubuntu 개인 PC 클린 설치
- GitHub Actions 원격 실행
- ViennaPS/ViennaLS import 및 실제 물리 시뮬레이션
- FNO/MGN 훈련·실모델 checkpoint 로드
- 팀원 VTP 원본의 정확한 시각·재료 매핑
- 실제 golden에서 PASS/BLOCK, CD 및 IoU, 드리프트 재학습

## 2026-10-28 추가 검증

`integrity.manifest_for`의 최상위 manifest 제외 조건을 좁혀 하위 폴더의 동명 파일도 지문에 포함하도록 수정했습니다. 관련 부정 테스트 1개를 추가해 로컬 **25개 테스트 통과** 및 CLI demo PASS/BLOCK 세 시나리오를 재실행했습니다. 원격 GitHub CI는 별도 확인 대상입니다.
