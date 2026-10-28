# 외부/팀원 자료 검토 — 검증 수준을 구분한 스냅샷

**조사 기준: 2026-10-28.** 이 문서의 `팀원 보고`는 Notion/README에 기록된 주장이고 `직접 확인`은 GitHub 코드 구조·커밋·CI 상태를 실제로 열어 본 범위입니다. 해당 팀원들의 로컬 원본·체크포인트는 EtchGuard가 독립 실행한 증거가 아닙니다. 공개 저장소에 개인 연락처를 옮기지 않습니다.

## 자료 요약

| 참조 | 팀원/범위 | 확인된 내용 | 현재 한계와 통합 시 주의 |
|---|---|---|---|
| [ViennaPS 공식](https://github.com/ViennaTools/ViennaPS) | 물리 기반 표면 식각 시뮬레이터 | SF6/O2 관련 예제·모델·Python API, 버전별 사용법 참조 | 버전 혼용/재료 ID/표면 형상 추출 시 재현 검증 필수; fab 실측 정답 아님 |
| [Automation-Project-etch-AI](https://github.com/code5312/Automation-Project-etch-AI) | 김민규, 파이프라인 구조·MLOps | C1/C2, 게이트 0/1/2, 레지스트리, 서빙 스켈레톤; 10/28 KST CI 성공 직접 확인 | 스모크는 더미 모델 사용; 실제 FNO 성능·drift 승격 검증으로 혼동 금지 |
| [etch-ai-pipeline](https://github.com/pearlhan-stack/etch-ai-pipeline) | 한진주, ViennaPS/FNO/MLP 실험 | Notion 및 GitHub의 FNO·MLP, 로컬 웹, C8 드리프트 차단 자료 | 저장소는 private; raw/checkpoint 빠져 있어 신규 clone 재현 불명. 자동 정상 승격/롤백 미검증 |
| [10/27 윤정인 진행](https://app.notion.com/p/a9034713f1678363b131015d2fbb6a73) | 윤정인, 시뮬레이션/모델/시연 | FNO/MGN v2, 조건 변화의 폭 오차 5.55%→2.51%, 0/2/4/6/8/10초 예측 화면을 **Notion에 보고** | 두 변수 중심과 7변수 확대 필요를 명시. 최신 코드/135건 진행 종료 별도 증거 미확인 |
| [장민서 진행](https://app.notion.com/p/f2a34713f16783d9b6e2014a56477418) | 장민서, 148 레시피·FNO/MGN 실험 | 골든 10, 극단 2개 영향, FNO/BLOCK, drift retrain 후 성능 악화 등 **Notion에 보고** | [GitHub](https://github.com/alstj123/etch-pipeline) 조회 시 404. 외부 원본/실행 로그는 직접 검증 못함 |
| [홍수민 개인 자료](https://app.notion.com/p/72734713f16782eea1a5817ec8624b4d) | 이전 FDC/인수인계 설계 | 기존 주제 배경과 합성 데이터 | 본 EtchGuard의 직접 학습·검증 데이터 아님 |

## 김민규 파이프라인에서 실제 코드로 확인한 기술 사항

- `src/etchpipe/etl/etl.py`: `compute_dataset_hash()`는 recipe별 `params_hash` 연결에 대한 짧은 SHA-1이며 **원본 VTP/NPZ 파일 바이트 해시는 포함하지 않음**. 재생성 조건/파일 변경을 잡는 별도 무결성 지문 필요. 단 기존 팀 ADR-0001은 이 방식을 레시피 ID 계약으로 동결했으므로, 바로 기존 키를 바꾸는 대신 EtchGuard에 `content_fingerprint`를 **추가**함.
- `src/etchpipe/etl/etl.py`: `dist_field()`는 개발 단계에서 unsigned distance field(UDF), 부호 있는 SDF는 후속 과제로 명시됨. `etl_run()`은 snapshot index×`step_min`을 사용. 실제 adaptive snapshot time 증거가 없는 경우 추정 시간으로 주의해서 다룸.
- `src/etchpipe/gate/gate.py`: 초기 게이트는 golden Chamfer와 후반 rollout 오차 검사 중심. 무결성 해시 값은 **외부에서 전달된 두 값 비교** 방식이므로 파일 내용 검증 수행 주체를 별도 확인해야 함.
- `docs/adr/0001-interface-freeze.md`: `meta.json`, `dataset_hash`, gate exit code 0/1/2, registry `current`, `/health`·`/model`·`/predict` 입력/출력 계약. **팀 인터페이스 임의 변경 금지**.
- CI: 2026-10-28 KST 02:17경 [성공 실행](https://github.com/code5312/Automation-Project-etch-AI/actions/runs/40549120140) 확인. 이는 스모크/단위 수준이며 전체 surrogate 실제 학습 통과와 동일하지 않음.

## 한진주와 장민서의 상충 보고를 어떻게 해석할 것인가

- 한진주: 개선 fine-v2 64레시피(40/12/12), FNO test Chamfer 0.003686µm / IoU 0.946134 **팀원 보고**. C8 drift `A_ie` 변경 후 새로운 후보 golden CD 0.041910 > gate 0.040000µm → **BLOCK, 이전 champion 유지** 보고. 초기 문서에 C8 미구현이라고 적힌 곳은 뒤 실험 시점과 충돌하므로 최신 단계별 로그 구분 필요.
- 장민서: 148 레시피(104 train/12 val/12 test + golden10 + OOD10), FNO test Chamfer 0.019µm, golden 평균 0.088µm > 0.020µm → **BLOCK** 보고. 극단 조합 2개에서 형상이 비정상; MeshGraphNet의 정점 순서/선분 꼬임 문제도 보고.
- **수치를 직접 비교할 수 없는 이유:** 레시피 설계·원본 시간·해상도·면적/CD 정의·골든 구성·Chamfer 구현이 다르기 때문. 서로 높은/낮은 숫자만 보고 품질 순위를 결정하지 않음.

## 팀 통합 전 필수 합의

1. **레시피 변수 이름/단위/범위:** `oxygen_flux`와 `passivationFlux`, `mask_width`와 `trenchWidth`처럼 alias가 다른 경우 정의에 기반해 명시적 mapping. `trenchWidth`가 `mask_width`와 물리적으로 같은지 확인되지 않으면 무조건 치환 금지.
2. **스냅샷 시간:** 실제 시뮬레이터가 저장한 물리 시각·`step_min`·초 단위 변환. adaptive time을 균등 시간으로 간주 금지.
3. **2D 형상:** 연결성·좌표계·재료 ID·Si/MASK, polyline vs SDF vs grid; 정점 집합만 같은 self-crossing 선은 불합격.
4. **평가:** 상호 배타적인 recipe-level train/val/test/golden/OOD, train-only normalization, 동일 코드의 Chamfer 정의/단위, 깊이/CD 측정 평면.
5. **게이트:** threshold 선고정, golden 원본·artifact fingerprint, incumbent와 같은 데이터 기준 비교, invalid prediction 차단, 결과 JSON+commit/실행환경 기록.
6. **재학습:** drift dataset을 학습·검증으로 나눠 **실제 개선**과 **회귀 실패** 시나리오 분리. 실패 시 champion 보존만으로 성공 승격 완주 주장 금지.

## 외부 코드 사용 정책

- 링크는 개념·포맷 참고를 위한 것. 팀원의 원본 파일·model checkpoint를 이 repo에 **복사하거나 첨부하지 않음**.
- 실제 파일이 필요한 경우 작성자에게 공유 권한·라이선스·버전/해시를 확인한 뒤, 외부/비공개 artifact를 보관해야 하면 접근 제어된 별도 위치를 이용.
- ViennaPS GPL-3.0 소스 복사/링크/배포 관련 의무는 실제 도입 방식에 따라 검토; `pip install` 사용만으로 이 레포의 독립 코드가 어떤 라이선스가 되는지 단정하지 않음.
