# EtchGuard 기술 구조

## 범위와 책임 경계

EtchGuard는 물리 시뮬레이터, ML training framework 또는 fab 제어 소프트웨어가 아닙니다. **기존 데이터/후보 모델과 승인 레지스트리 사이**에 두는 검증·기록 컴포넌트입니다. 처음에는 toy 데이터를 만들어 경로를 테스트한 뒤 실제 ViennaPS 어댑터를 붙입니다.

```text
[현재: toy generator]                  [후속: ViennaPS raw / 팀 모델, 권한·형식 검증 후]
          │                                    │
          └────────────┬───────────────────────┘
                       ▼
               [Adapter & Contract]
           7 recipe fields, t_seconds, points_um
                provenance, validity
                       ▼
              [Integrity / Audit]
           raw content SHA256 + manifest
                       ▼
                 [Split Guard]
             recipe disjointness (P1)
                       ▼
               [Evaluation C4]
        baseline/model → Chamfer, depth
                       ▼
                [Gate C5]
        integrity + performance + regression
            ├─────────────┐
         PASS             BLOCK (1/2)
            ▼               │
        [Registry C6]        └──> audit / incumbent unchanged
            ▼
       evidence JSON / HTML
```

## 실제 파일별 역할 (v0.1)

| 코드 | 역할 | P1 개선 포인트 |
|---|---|---|
| `contracts.py` | recipe·출처·시간·2D 선분의 기본 무결성 검사 | touch/overlap, material/geometry/domain 고도화 |
| `integrity.py` | 경로·크기·SHA-256 manifest, 추가·삭제·변경 검사 | 설정·실제 raw origin과 서명, nested-manifest·symlink 공격 모델 |
| `demo.py` | Gaussian synthetic recipe/profile 생성 | 실제 ViennaPS와 혼용 금지 |
| `model.py` | 학습 없는 최근접 레시피 baseline | ML adapter 별도 구현 |
| `metrics.py` | Chamfer·depth 계산 | 물리 CD/IoU, invalid-profile penalty |
| `gate.py` | candidate metric과 fingerprint 비교, 사전 기준 판정 | **직접 verify된 artifact 객체만 받아 fail-closed** |
| `registry.py` | PASS 승격, BLOCK 보존, history 기록 | 원자적 champion 갱신, model 파일 해시·rollback |
| `cli.py` | `demo`, `freeze`, `verify` 서브커맨드 | `inspect-viennaps`, `gate --artifact` |
| `report.py` | 단일 HTML 보고서 | 실제 provenance/불확실성 명시 |

## 경고: 현재 v0.1은 '완성된 품질 보증'이 아님

- `evaluate_candidate()`가 제공받는 `actual_fingerprint` 문자열을 **자동으로 디스크에 대해 재계산하지 않습니다**. 그러므로 외부 호출자가 값을 거짓으로 줄 수 있습니다. 향후 실제 승인 경로에서 `verify`와 분리한 채로 쓰지 말아야 합니다.
- `source_type`은 사용자 전달 메타데이터이며 서명된 출처 증명이 아닙니다.
- `validate_profile`은 strict self-crossing을 검사하지만 모든 접촉/겹침/닫힌 메시를 지원하지 않습니다. v0.1 검사는 제한된 열린 단면 예제만 다룹니다.
- `depth`는 Si surface `y=0` 및 식각 방향 `y<0`이라는 예제 가정으로 산출합니다.
- Registry의 승인 기록은 초기 기능 테스트 용도이며 실제 model checkpoint 저장·원자적 배포·자동 rollback이 구현되지 않았습니다.

## 실제 ViennaPS 연동 시 우선 판단할 사항

1. **시뮬레이터 호환성:** Python/OS와 `ViennaPS/ViennaLS` 버전을 실제 import/1-run으로 확인.
2. **표면 연결성:** VTP의 선분 connectivity에서 순서 있는 열린 2D 단면 복원. 단순 점 좌표 정렬은 self-crossing을 만들 수 있음.
3. **재료 구분:** cell `MaterialIds`가 데이터/버전에서 무엇을 의미하는지 검증; Si와 mask를 추정으로 강제하지 않음.
4. **시간:** adaptive snapshot이면 요청 시간/실제 저장 시간 별도로 기록. 추정 `k*step_min`으로 실제 물리 시각을 대체하지 않음.
5. **데이터 분리:** recipe ID 기준 split guard, train-only scaler, independent golden/OOD; 모델 비교 시 동일 snapshot/metric.
6. **물리적 신뢰성:** 시뮬레이터의 정답 자체가 mesh/ray/seed에 민감할 수 있으므로 수치 안정성 증거를 별도 관리.

## 다음 작은 수직 슬라이스 (P1)

`actual sample raw + meta` 1건 읽기 → 원본 및 설정 freeze → 조작한 사본 verify BLOCK → 2D profile/실제 snapshot time 읽기 → toy gate와 별도 'ViennaPS read-only inspection' 증거 JSON. 이 단계까지는 실제 surrogate 모델 품질을 주장하지 않습니다.
