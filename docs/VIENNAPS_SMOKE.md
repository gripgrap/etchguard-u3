# ViennaPS 직접 실행과 EtchGuard 연결 검증

2026-10-28. 공개 fixture를 읽는 단계에서 더 나아가, 실제 ViennaPS로 생성한 단면을 EtchGuard 입력과 예측 파일 평가까지 연결했다.

## 어디까지 실증했나

| 수준 | 이번 결과 |
| --- | --- |
| 합성 fixture 검사 | 기존 기능·테스트 유지 |
| 외부 VTP 읽기 | 앞 단계에서 팀 고정 fixture 4개 확인 |
| 직접 시뮬레이션 생성 | WSL Ubuntu에서 ViennaPS 4.5.0 + ViennaLS 5.8.5 실행 성공 |
| 실제 원본→평가기 연결 | 생성한 3개 VTP를 Si 연결성으로 복원해 reference/prediction 계약으로 평가 |
| 모델 학습·일반화 정확도 | 미실행. oracle/오류 주입/초기 형상 baseline만 사용 |
| 실제 fab 정확도·공정 승인 | 검증하지 않음 |

## 실행 환경과 설정

- WSL Ubuntu, Python 3.12.3, CPU 2 threads.
- ViennaPS 4.5.0 / ViennaLS 5.8.5 / PyVista 0.49.1 / VTK 9.7.1.
- 길이 um, 시간 s. grid=0.05um, domain width=2um, trench width=0.5um, mask height=0.3um.
- ion/etchant/oxygen flux=10/4500/800, mean energy=100, exponent=500, energy sigma=10.
- rays=100, random seeds 비활성·seed=42. 이 숫자들을 실제 장비 플럭스 값으로 해석하지 않는다.
- 0초 형상을 저장한 뒤 0.5초 process를 두 번 적용. 세 snapshot은 구성된 누적 시각 0/0.5/1초다. callback에서 관측한 adaptive timestamp가 아니므로 time_basis는 explicit_process_durations다.

작은 연결 시험을 위한 설정이다. process를 구간마다 새로 생성하여 coverage가 다시 초기화될 수 있다. 단일 1초 process 또는 팀의 다른 시간 저장 방법과 물리적으로 동등하다고 주장하지 않는다.

## 확인된 결과

- Si profile 3개 모두 단일 열린 경계로 읽었고 각 11개 점을 복원했다.
- 초기↔최종 Chamfer는 **0.03243511276um**로 형상 변화가 있었다.
- 동일 설정 재실행에서도 raw/meta 파일 집합 fingerprint가 같았다: `1849effefd9ae8540a381da4e7e31e07f41f67abb3f50718871c4fcbeb56d849`.
- 정답 복사 oracle은 오차 0으로 PASS, 0.2um 아래로 이동한 오류 주입 결과는 BLOCK.
- 초기 형상만 반환한 persistence baseline은 depth MAE와 최대 시점 Chamfer 기준 초과로 BLOCK. 평균 Chamfer만 보면 기준 안이었던 사례다.
- 원본 변조 사본과 예측 시각 불일치도 별도 차단 검사에 포함한다.

각 raw/meta/설정/드라이버 지문, 버전·실행시간·process event, reference와 판정은 reports/generated/viennaps-smoke-*에 저장한다. source_revision은 실행 당시 저장소 HEAD, driver_sha256은 실행한 미커밋 드라이버까지 식별한다. 원본 VTP는 Git에 올리지 않고 작은 실행 요약만 reports/evidence에 보관한다.

## 수치 품질에 대한 제한

로그에 coverage delta가 tolerance보다 큰 상태도 남아 있어 coverage 수렴을 확인했다고 표현하지 않는다. grid/rays 수렴성, seed 반복, 물리적 보정, 장시간 rollout도 검증하지 않았다. PASS는 생성·파싱·평가 경로와 결함 주입 검사의 성공이지, 정밀 정답 데이터나 모델 승인 기준 통과가 아니다.

## 설치·재현

Windows native wheel 설치는 성공했지만 import에서 DLL 오류가 났다. 바이너리는 VTK 9.3 계열·Embree·OpenMP DLL을 요구하며 현재 Windows VTP 환경만으로 해결되지 않았다. 시스템 전역 DLL 변경 대신 기존 WSL을 사용했다. Docker 엔진은 실행 중이 아니었다.

검증한 Linux 경로:

```bash
python3 -m venv /path/to/simulation-env
/path/to/simulation-env/bin/python -m pip install -r requirements-simulation.txt
PYTHONPATH=src /path/to/simulation-env/bin/python examples/simulate_viennaps.py --output reports/generated/new-smoke-run
```

출력은 덮어쓰지 않는다. 실행 로그를 파일로 보존하고 timeout을 두는 것을 권장한다. 드라이버의 PASS 제어 검사는 결과를 보고 임계값을 조정하지 않는다.

## 통합 방향에 대한 판단

실제 ViennaPS 통합은 유용하며 이번에 작은 CPU 경로가 가능함을 확인했다. 다만 코어 테스트·기본 실행에 시뮬레이터 설치를 강제하지 않고 별도 실행 환경과 선택 어댑터를 유지한다.

다음 실증은 수치 설정과 시간 저장 방법을 고정한 소수 recipe 생성 → recipe 단위 train/validation/evaluation 분리 → 팀 모델 또는 작은 학습 모델의 prediction bundle 평가다. 독립 평가셋과 기준을 먼저 정하고, 이번 oracle 결과를 모델 성과로 재사용하지 않는다.

공식 API 참고: [고정 버전 예제](https://github.com/ViennaTools/ViennaPS/blob/v4.5.0/examples/holeEtching/holeEtching.py), [공식 저장소](https://github.com/ViennaTools/ViennaPS). 자체 드라이버로 실행했으며 upstream 소스나 checkpoint를 복사하지 않았다. 의존성 및 향후 배포 라이선스 판단은 실제 배포 형태에 맞춰 별도로 한다.
