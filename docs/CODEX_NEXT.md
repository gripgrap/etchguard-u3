# Codex 후속 구현 지시서 (저장소를 열어 첫 작업부터 실행)

**목표:** 독립 EtchGuard v0.1은 synthetic 테스트 데이터로 25개 테스트가 통과했다. 이제 팀 공통 ViennaPS 데이터의 출처/해시/시간/형상 검증을 추가하고, 가급적 실제 데이터로 C5 게이트를 재실행한다.

## 첫 요청 (복사해서 Codex에 입력)

```
이 저장소는 U3 반도체 식각 AI surrogate 모델의 신뢰성 검증용 독립 MVP, EtchGuard다.

반드시 README.md, AGENTS.md, docs/INTERFACE.md, docs/ROADMAP.md를 먼저 읽어라.
이번 작업은 실제 ViennaPS 연동을 위한 검증만 수행하며, 원래 기능을 깨뜨리지 말아라.

1. Python/OS/설치 환경 확인 후 현재 25개 unittest와 CLI demo를 직접 실행한다.
2. 팀 레퍼런스 https://github.com/code5312/Automation-Project-etch-AI 의
   tests/fixtures/raw, src/etchpipe/sim, src/etchpipe/etl 경로와 ADR-0001을 읽고,
   진짜 VTP/metadata 파일 포맷과 snapshot 시간·물질 좌표를 확인한다.
3. 팀 소스 파일을 복사할 필요가 있으면 라이선스를 먼저 확인하고,
   원본을 직접 다운로드하지 않은 경우에는 그 사실을 명시한다.
4. 가급적 별도 선택적 의존성 pyvista를 통한
   adapters/viennaps.py (VTP→ordered 2D points)와 테스트를 추가한다.
5. 실제 형상 파일의 내용 해시와 meta/config/버전을 함께 고정하며,
   데이터가 한 바이트라도 바뀌거나 파일이 추가되면 BLOCK되도록 한다.
6. step_min은 분, 이 저장소의 t_seconds는 초이다.
   적응형 스냅샷의 실제 timestamp가 확인되지 않으면 추측하지 말고 미확인으로 남긴다.
7. golden과 학습의 레시피가 겹치지 않는지 검사한다.
8. 새로운 의존성 설치에 실패하면 원인을 기록하고 v0.1 실행 상태를 보존한다.
9. 주요 함수에 단위 테스트를 추가하고 코드를 실행해 확인한다.
10. 작업 요약은 구현 파일, 실제 실행 명령, 테스트 결과, 불확실한 사항, 다음 단계로 구분한다.

절대로 synthetic_fixture를 실제 ViennaPS 데이터로 바꿔 적지 말고,
실제 학습하지 않은 FNO/MGN을 학습 성공이라고 말하지 마라.
```

## 중요 검증 가설

- 팀원 `compute_dataset_hash()`는 recipe `params_hash`에 의존. raw snapshot 바이트를 바꾸어도 recipe가 같으면 식별자 불변인 구조다.
- EtchGuard는 별도 `content_fingerprint`를 통해 데이터 바이트와 파일 목록의 변경을 잡는다.
- 본인 `content_fingerprint`는 `params_hash`와 별도이며 팀 ADR 인터페이스를 덮어쓰지 않는다.
- 기존 팀원들 간 모델 output 좌표/시간/변수 명칭이 다른 점에 대한 어댑터가 필요하다.

## 성공 판정

- 새 환경 `unittest` 전체 통과
- 실제 VTP 원본 + source/version/mesh metadata가 있는 1개 이상의 레코드 변환 성공
- 원본 변조 부정 테스트 실패(차단)
- 실제 시뮬레이션 기반/fixture 기반 보고서를 혼용하지 않음
- CI 초록

## P2 후속 작업

데이터가 충분히 확보되면 FNO 또는 MLP를 같은 데이터 분할로 학습하고,
베이스라인과 같은 형상/Chamfer/깊이/CD 측정 기준으로 비교.
임계값은 사전에 기록하고, OOD·golden은 학습에 절대 사용하지 않는다.
