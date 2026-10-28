# 실데이터·모델 연동 준비 조사

조사일: 2026-10-28. 이번 단계는 코드/원본 포맷 조사와 구현 조건 확정이다. VTP를 로컬 파싱하거나 ViennaPS를 실행한 결과가 아니다.

## 확인한 원본과 재현 경계

팀 저장소는 움직이는 main 대신 커밋 `6a2dafd65a72d11324246cfdbfa5ba490c9c548f`를 기준으로 조사했다.

- [raw fixture](https://github.com/code5312/Automation-Project-etch-AI/tree/6a2dafd65a72d11324246cfdbfa5ba490c9c548f/tests/fixtures/raw): r0000~r0002, 각각 meta.json과 t000~t003 VTP가 있다. 파일 존재만으로 시뮬레이션 출처 진위가 독립 검증된 것은 아니다.
- [r0000 meta](https://github.com/code5312/Automation-Project-etch-AI/blob/6a2dafd65a72d11324246cfdbfa5ba490c9c548f/tests/fixtures/raw/r0000/meta.json): K=actual_k=3, step_min=1, ViennaPS=4.5.0, rays=300, seed=42, grid_delta=0.3. 개구 폭 약 6.62µm, 마스크 높이 약 11.21µm로 기존 toy 범위와 다르다. toy normalization/threshold를 재사용하지 않는다.
- [생성 코드](https://github.com/code5312/Automation-Project-etch-AI/blob/6a2dafd65a72d11324246cfdbfa5ba490c9c548f/src/etchpipe/sim/run_sim.py): 길이는 um, 시간은 min으로 설정하고 각 process duration을 STEP_MIN으로 호출한다. 각 snapshot의 실측 timestamp 배열은 meta에 없다. 시간은 `index * step_min * 60`의 설정 기반 유도값으로 표시하고 관측 시각으로 표현하지 않는다. 파일 누락/번호 간격은 enumerate로 덮어쓰지 않는다. 내부 적응형 시간 진행과 별도로 저장 이벤트의 실제 시각 검증은 미완료다.
- [재료 설정](https://github.com/code5312/Automation-Project-etch-AI/blob/6a2dafd65a72d11324246cfdbfa5ba490c9c548f/configs/etl/materials.yaml): 0=mask, 10=Si. 이 매핑은 해당 생성 조건의 팀 실험 보고이며 모든 VTP의 보편 규칙으로 고정하지 않는다.
- [t000 VTP](https://github.com/code5312/Automation-Project-etch-AI/blob/6a2dafd65a72d11324246cfdbfa5ba490c9c548f/tests/fixtures/raw/r0000/snapshots/t000.vtp)의 XML 헤더를 직접 조회했다. 255 points, 254 lines, verts/polys/strips=0, MaterialIds/Normals는 CellData다. 압축된 appended base64이므로 단순 XML 숫자 추출만으로 좌표를 읽을 수 없다. 좌표·재료 값의 실제 배열과 형상 연결성은 아직 디코딩하지 않았다.
- [팀 ETL](https://github.com/code5312/Automation-Project-etch-AI/blob/6a2dafd65a72d11324246cfdbfa5ba490c9c548f/src/etchpipe/etl/etl.py)은 lines.reshape(-1,3)을 사용한다. 이는 모든 line cell이 두 정점일 때만 유효하다. [PyVista 공식 lines 계약](https://docs.pyvista.org/api/core/_autosummary/pyvista.polydata.lines)은 길이가 가변인 polyline도 허용하므로 어댑터는 길이 prefix를 순회해야 한다.
- [ADR-0001](https://github.com/code5312/Automation-Project-etch-AI/blob/6a2dafd65a72d11324246cfdbfa5ba490c9c548f/docs/adr/0001-interface-freeze.md)의 recipe hash/종료 코드를 유지하고 별도 content fingerprint를 추가한다. 팀 registry의 current는 평문, EtchGuard는 current.json이므로 직접 교체하지 않는다.
- [NOTICE](https://github.com/code5312/Automation-Project-etch-AI/blob/6a2dafd65a72d11324246cfdbfa5ba490c9c548f/NOTICE)는 코드의 Apache-2.0 배포를 명시한다. 데이터/fixture 재배포 조건까지 동일하다고 단정하지 않는다. 이번에는 소스·fixture를 저장소에 복제하지 않았다.

## 환경

현재 Python 3.13.12에는 numpy가 있고 pyvista/vtk/viennaps/viennals는 없다(importlib spec 조회). 신규 설치나 simulator 실행은 하지 않았다. 어댑터는 선택 의존성으로 분리하고 기존 표준 라이브러리 CI를 보존한다. 별도 의존성 환경에서 VTP reader를 검증하는 것이 다음 준비 작업이다.

## 다음 구현 단위 A: 검증 → 평가 → 승격

새 workflow 계층을 두고 다음 조건을 테스트로 먼저 고정한다. 현재 구현 완료를 뜻하지 않는다.

1. 외부에서 승인한 fingerprint를 입력받고 freeze는 별도 작업으로 유지한다. 평가 직전에 원본을 다시 freeze하여 변조를 새 기준선으로 승인하지 않는다.
2. train/golden 원본, 설정, split, 모델 descriptor/artifact를 검증하고 평가에 사용한 메모리 레코드가 그 파일에서 유래했음을 연결한다. 검사 후 재읽기로 다른 바이트를 사용하는 문제를 방지한다.
3. recipe 키 순서에 무관한 canonical identity로 split 중복을 차단한다. 수치 허용 오차에 의한 동일 레시피 판단은 별도 정책으로 명시한다.
4. 고정 평가 시각을 명시하거나 predict(recipe,t_seconds) 인터페이스를 추가한다. 후보와 champion은 동일 원본·시각·지표로 평가한다. 다른 데이터셋에서 저장된 champion 점수와 비교하지 않는다.
5. 입력/무결성 오류는 BLOCK(2), 모델 출력/성능 오류는 BLOCK(1). 실패에도 사유를 기록하고 current.json을 유지한다. 결과 기록 실패 시 승격하지 않는다.
6. 모델 ID, artifact digest, 정책 digest, 데이터 fingerprint, source revision, 시간·단위, 지표, 판정, 이전 champion을 하나의 evidence로 연결한다. 임의 GateDecision만 전달해 승격하는 경로의 신뢰 경계를 명시한다.

필수 부정 사례: 파일 변조/추가/삭제, manifest와 외부 기준선 불일치, 잘못된 JSON 타입, run_id만 다른 동일 recipe, 최종 시각 불일치, 비유한 임계값, 예측 예외, champion의 평가셋 불일치, 실패 후 champion 불변. 다중 프로세스와 악의적 동시 파일 변경 방어는 별도 위협 모델로 남긴다.

## 다음 구현 단위 B: 읽기 전용 VTP 검사

1. 출처 커밋·파일 SHA256·meta·재료 mapping을 함께 고정하고 외부 raw는 기본 Git 제외 경로에 저장한다.
2. cell별 재료를 먼저 선택한다. 점에 닿은 재료 ID를 평균하여 mask/Si를 결정하지 않는다.
3. line/polyline 연결성을 순회해 Si edge graph를 복원한다. 지점 ID 범위, 중복/퇴화 edge, 비유한 좌표, z 평면 허용 오차, 분기/분리 성분을 검사한다.
4. 단일 열린 polyline 정책을 우선 사용한다면 endpoint 2개·내부 차수 2를 요구한다. 여러 성분/폐곡선/주기 경계는 임의로 이어 붙이지 않고 미지원 사유를 남긴다. x 정렬은 undercut을 손상하므로 사용하지 않는다.
5. 전처리 전후 좌표 변환·단위와 시각 근거를 기록한다. 외부 provenance가 부족하면 검사는 가능해도 simulation-origin 확정 판정은 보류한다.

완료 조건: 원본 1건의 읽기·연결성 검증, 조작 사본 차단, source/config/time evidence JSON 생성. 이때도 surrogate 성능 검증 완료를 주장하지 않는다.

## 팀 모델 연동에 필요한 인수 항목

checkpoint와 해시, 모델/전처리 코드 revision, dependency lock, 입력 변수의 물리적 정의·범위·단위, scaler의 train-only 학습 증거, 출력 표현과 시간 단위, split recipe 목록, 평가 정책, 추론 명령·예상 출력이 필요하다. 초기에는 기존 모델 코드를 직접 import하기보다 파일 기반 prediction bundle을 받아 동일 평가기로 비교하는 경로를 우선 검토한다. fixture의 정상 파싱만으로 모델 통합 완료로 보지 않는다.
