# 데이터 계약 v0.1 — 별도 JSON 형식

이 JSON 규격은 EtchGuard **독립 어댑터**의 내부 형식입니다. 팀원 ADR-0001을 수정하거나 암묵적으로 채택시키지 않습니다.

```json
{
  "run_id": "run-0001",
  "recipe": {
    "ion_flux": 10,
    "etchant_flux": 4500,
    "oxygen_flux": 800,
    "ion_mean_energy": 100,
    "ion_exponent": 500,
    "mask_width": 0.35,
    "mask_height": 0.25
  },
  "provenance": {
    "source_type": "synthetic_fixture",
    "version": "toy-gaussian-1.0"
  },
  "snapshots": [
    {"t_seconds": 0.0, "points_um": [[-1.0,0.0],[0.0,0.0],[1.0,0.0]]},
    {"t_seconds": 15.0, "points_um": [[-1.0,0.0],[0.0,-0.3],[1.0,0.0]]}
  ]
}
```

## 단위·출처
- `t_seconds`: 물리 시간 초. 팀원 C1의 `step_min`은 **분**이므로 변환 시 60배를 정확히 적용해야 합니다. 적응형 시뮬레이션은 실제 캡처된 timestamp가 우선입니다.
- `points_um`: 2D polyline 좌표, 마이크로미터(µm). 지표 `depth`는 Si surface y=0, 식각 방향 y<0이라는 **명시적인 제한적 좌표 가정**에서만 정의합니다.
- `source_type=viennaps_simulation`은 실제 ViennaPS 실행 파일과 설정/버전 증빙이 있어야 허용합니다. 지금은 표시용 메타데이터이며 독립적으로 실행 진위를 증명하지 않습니다.
- 원본 파일이 `.vtp/.npz`여도 이 내부 JSON 계약과 함께 보존할 수 있으며 실제 원본 바이트는 무결성 매니페스트에서 추적합니다.

## Fingerprint
- 기존 `params_hash`/`dataset_hash`는 레시피 집합 ID(팀 ADR)로 계속 사용 가능합니다.
- `content_fingerprint`는 **원본 파일 전체의 path/size/SHA256** 목록을 SHA256으로 요약합니다. `manifest.sha256.json` 자체는 제외합니다.
- 검증 시 파일 이름 추가·삭제·바이트 변경을 차단합니다.
- 단, 결과물과 매니페스트를 함께 바꿀 권한이 있는 공격자까지 방어하려면 신뢰 가능한 원격 저장소나 서명을 추가해야 합니다.

## Gate
- Code 0: PASS (성능 기준과 fingerprint 동시 만족)
- Code 1: BLOCK (형상·성능·회귀 오류)
- Code 2: BLOCK (golden/integrity/입력 계약 이상)
- `max_chamfer_um`, `max_depth_mae_um`, `max_regression_ratio`는 실험 착수 전에 고정합니다.
- 현재 demo 임계값은 synthetic 데이터용 설명값이며 ViennaPS/model 실증 기준으로 재사용하지 않습니다.
- CD, taper, IoU는 형상의 기준 좌표계/물질 마스크 및 측정 정의가 합의되기 전까지 제외합니다.
