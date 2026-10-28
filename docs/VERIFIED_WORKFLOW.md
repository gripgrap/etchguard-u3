# 고정 시각 베이스라인 검증 실행

2026-10-28: 첫 번째 구현 범위는 **최근접 recipe baseline**이다. 일반 checkpoint 평가나 팀 모델 승격 API가 아니다.

## 입력과 기준선

```text
bundle/
  train/*.json
  golden/*.json
  policy.json
  manifest.sha256.json
```

run JSON은 기존 INTERFACE 계약을 따른다. train과 golden의 마지막 snapshot은 모두 policy의 evaluation_time_seconds와 정확히 같아야 한다. 보간이나 시간 단위 추측은 하지 않는다.

```json
{
  "evaluation_time_seconds": 15,
  "max_chamfer_um": 0.15,
  "max_depth_mae_um": 0.15,
  "max_regression_ratio": 1.1
}
```

위 수치는 합성 데모용이며 실제 모델 기준으로 사용하지 않는다. max_regression_ratio는 기존 정책과의 호환 필드다. 이번 baseline 경로에서는 이전 champion 점수와 상대 회귀 비교를 하지 않는다. 서로 다른 bundle에서 얻은 저장 점수를 비교하지 않기 위한 제한이다.

검토한 입력을 freeze한 뒤 **bundle 밖**에 expected fingerprint를 보관한다. 평가는 기준선을 생성하거나 갱신하지 않는다. 원본과 manifest를 함께 바꾸어도 외부 expected 값이 다르면 BLOCK이다.

## 실행

설치된 환경 또는 PowerShell에서 `$env:PYTHONPATH='src'` 설정 후:

```powershell
python examples/verified_workflow.py --output reports/generated/verified-001
```

새 출력 폴더에서 합성 데이터를 만들고 PASS를 기록한 뒤, golden 파일 바이트를 변경하여 BLOCK(2) 및 champion 보존을 확인한다. 출력은 덮어쓰지 않는다.

이미 준비한 bundle을 검사하려면:

```powershell
python -m etchguard.cli evaluate-bundle path/to/bundle --expected-fingerprint <TRUSTED_SHA256> --registry path/to/registry --model-id nearest-v1
```

registry는 bundle 밖에 있어야 한다. 종료 코드는 PASS=0, 모델 예측·성능 BLOCK=1, 입력·무결성 BLOCK=2다. 저장 I/O 실패는 오류로 반환하고 성공했다고 보고하지 않는다.

## 검사 순서

1. manifest 검증과 외부 기준선 대조.
2. 파일 바이트를 읽어 manifest의 SHA-256/크기와 대조하고 그 바이트를 JSON으로 파싱.
3. 필드·split·recipe identity·최종 시각·정책 유효성 검사.
4. 검증한 train으로 baseline을 만들고 golden 평가.
5. 평가 후 원본 재검사. 실행 중 관찰된 변경은 차단.
6. 지문·시각·정책·baseline descriptor와 판정을 history에 기록한 뒤 PASS일 때 current.json 갱신.

recipe identity는 고정 키 순서의 수치 tuple이다. 키 순서 차이와 1/1.0은 같은 값으로 처리하지만, 근사 오차 허용·물리적으로 동일한 recipe 판정은 하지 않는다.

## 증거와 한계

history/current의 evidence는 bundle fingerprint, 정책 digest, train 원본과 model.py에 결합한 baseline descriptor digest, 출처 표기, 고정 시각, 표본 수, 점수·사유를 담는다. descriptor는 학습된 checkpoint의 지문이 아니다. source_type은 입력의 주장이지 출처 진위 증명은 아니다.

단일 writer 및 신뢰하는 로컬 코드 환경을 전제로 한다. 멀티프로세스 승격 잠금, 악의적인 파일 동시 변경 전체 방어, 코드 전체·의존성·실행 환경의 서명은 포함하지 않는다. 평가 후 검사와 기록 사이의 원자적 트랜잭션도 보장하지 않는다. 기존 Registry.submit은 저수준 신뢰 API로 남아 있으므로 이 workflow의 검사를 강제하는 보안 경계로 소개하지 않는다.

다음 단계는 원본 VTP adapter와 파일 기반 prediction bundle 계약이다. 후보/champion을 같은 평가 자료에서 다시 실행하는 일반 모델 회귀 검증은 별도 구현한다.
