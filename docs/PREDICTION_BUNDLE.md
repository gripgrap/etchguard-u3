# 파일 기반 예측 평가 계약

`evaluate-predictions`는 고정된 reference/prediction/policy 파일을 비교한다. 모델 학습이나 checkpoint 실행·승격 권한은 제공하지 않는다.

## 입력

```text
bundle/
  reference.json
  prediction.json
  policy.json
  manifest.sha256.json
```

reference는 기존 run JSON 계약을 따르며, provenance에 content_fingerprint와 time_basis가 필요하다. prediction도 같은 계약을 따르고 다음 model 필드를 추가한다.

```json
{
  "model": {
    "id": "candidate-v1",
    "kind": "model",
    "artifact_sha256": "64자리 소문자 SHA-256"
  }
}
```

kind는 model/baseline/oracle/fault_injection 중 하나다. artifact_sha256은 제출자가 주장한 지문이며 이 명령이 원본 모델 파일을 열어 확인한 것은 아니다. 결과의 model_artifact_verified와 promotion_authorized는 항상 false다. oracle의 PASS는 평가기 점검이며 모델 성능이 아니다.

policy는 max_chamfer_um, max_depth_mae_um, max_chamfer_per_snapshot_um을 유한한 음이 아닌 숫자로 요구한다. 예제 기준값은 검사 경로 시험용이며 실제 공정 합격 기준이 아니다.

## 실행

검토한 bundle을 freeze한 후 그 fingerprint를 bundle 밖의 신뢰하는 기록에 보관한다.

```powershell
python -m etchguard.cli evaluate-predictions path/to/bundle --expected-fingerprint TRUSTED_SHA256
```

검증 순서: 외부 fingerprint 대조 → 실제 바이트 capture → reference 계약·정책·model 표기 → recipe/run ID·출처 지문·시간 근거·snapshot 시각 일치 → 예측 형상 검사 → 전체/시점별 점수 → 평가 후 bundle 재검사.

recipe별 변수 값, snapshot 개수와 물리 시각을 정확히 일치시킨다. 시간 보간·가까운 recipe 대체는 하지 않는다. 단위는 기존 points_um/t_seconds 계약을 따른다. 깊이는 초기 Si 표면 y=0, 식각 방향 y<0의 가정에만 적용한다. 이 조건을 만족하지 않는 데이터는 어댑터에서 명시적으로 변환해야 한다.

출력은 평균 Chamfer·깊이 MAE·최대 snapshot Chamfer, 시점별 결과, 파일 SHA256·입력 지문·evidence digest를 포함한다. 평균이 작아도 한 시점 오차가 기준을 넘으면 BLOCK이다. PASS=0, 예측 형상/성능 오류=1, 입력·원본·시각 계약 오류=2다.

원본 raw의 실제 바이트 검사는 VTP adapter 단계의 책임이다. 이 명령은 봉인된 reference JSON을 검사하며 raw 또는 모델 checkpoint 진위를 독립적으로 인증하지 않는다. 멀티프로세스 트랜잭션·서명된 원격 승인도 이번 범위가 아니다.

## 직접 시뮬레이터 연동

[ViennaPS 실행 검증](VIENNAPS_SMOKE.md)의 드라이버는 실제 생성→VTP 검사→reference JSON→예측 파일 평가를 한 번에 실행한다. 새 학습 모델 없이도 연결·오류 차단은 실증할 수 있지만, 후보 모델 일반화 성능은 별도 데이터와 모델로 평가해야 한다.
