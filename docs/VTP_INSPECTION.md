# 읽기 전용 VTP 어댑터와 실제 fixture 확인

2026-10-28. `adapters/viennaps.py`는 팀 형식의 meta.json과 VTP를 읽는 선택 어댑터다. ViennaPS 시뮬레이션을 직접 실행한 결과가 아니다.

## 실제로 읽은 원본

- 저장소: [code5312/Automation-Project-etch-AI](https://github.com/code5312/Automation-Project-etch-AI/tree/6a2dafd65a72d11324246cfdbfa5ba490c9c548f/tests/fixtures/raw/r0000)
- 고정 commit: `6a2dafd65a72d11324246cfdbfa5ba490c9c548f`.
- 조사 파일: meta.json과 t000~t003.vtp. GitHub 파일 API의 원본 바이트를 저장소 밖 `1028/external/viennaps-r0000`에 보관했다. 팀 raw 파일은 이 저장소에 재배포하지 않는다.
- 파일 집합 SHA-256 fingerprint: `5b3a2aafe12206370f6c9ab0dc569a17006fe7d6027d3d998cb7c7dece42e17e`.
- 별도 Python 3.13.12 환경: PyVista 0.49.1 / VTK 9.7.1. 기본 코어 의존성은 늘리지 않았다.

| 파일 | Si 단면 점 수 | 설정으로 유도한 시각 |
| --- | --- | --- |
| t000.vtp | 25 | 0초 |
| t001.vtp | 47 | 60초 |
| t002.vtp | 71 | 120초 |
| t003.vtp | 95 | 180초 |

MaterialIds=10은 조사 대상 생성기의 Si mapping이다. 모든 외부 파일에 보편 적용되는 규칙은 아니다. 실제 관측 timestamp 배열은 없으므로 `index * step_min * 60`을 사용하고 `derived_not_observed`로 명시했다. source_type은 `external_research`이며, 파일을 읽었다는 이유로 simulation 출처 진위를 인증하지 않는다.

## 검사하는 것

1. 외부에서 고정한 fingerprint와 원본 파일 집합을 대조한다. 어댑터는 freeze나 원본 쓰기를 하지 않는다.
2. VTK reader로 압축 appended VTP를 읽는다. line-only PolyData 및 MaterialIds cell 배열을 요구한다.
3. 가변 길이 line/polyline을 순회하고 선택 재료의 edge graph로 순서를 복원한다. x값 정렬이나 끊긴 성분 이어붙이기를 하지 않는다.
4. 중복·퇴화 edge, 분기, 분리, 닫힌 경계, 잘못된 인덱스, 비유한 좌표·재료, z=0 평면 이탈을 거부한다.
5. snapshot 파일 번호가 actual_k와 맞는지 확인한다. 누락된 번호를 enumerate로 새 시각에 배정하지 않는다.
6. 기존 JSON 데이터 계약을 검증하고 읽기 후 원본 지문을 다시 확인한다.

현재 지원은 **단일 열린 평면 재료 경계**다. 다중 성분·폐곡선·다층 재료·주기 경계, 일반 3D 메시, 실측 시간 대체·보간은 지원하지 않는다. 기존 profile 검사 범위를 넘어선 모든 접촉·겹침 topology를 보증하지 않는다. 동시 악의적 파일 변경에 대한 원자적 snapshot도 보장하지 않는다.

## 실행

```powershell
python -m pip install ".[vtp]"
python examples/inspect_vtp.py path/to/raw-run --expected-fingerprint TRUSTED_SHA256 --source-revision COMMIT_SHA --material-id 10 --output reports/generated/inspection/run.json
```

검토된 별도 source manifest 또는 원격 기록에서 기준 fingerprint를 확보한다. 매번 현재 파일에서 지문을 다시 계산해 승인 기준을 바꾸면 변조 검사의 의미가 사라진다. 출력은 원본 밖의 새 파일만 허용한다.

## 검증

- 순수 연결성 테스트 9개 및 PyVista 압축 round-trip·변조·누락 파일·재료 배열 누락·출처 누락 테스트 5개.
- 실제 고정 fixture 4개 snapshot을 읽고 검사.
- 원본을 복사한 뒤 t001 바이트 변경 시 fingerprint mismatch 차단, 원본 집합 지문 불변 확인.
- 어댑터를 설치하지 않은 기본 환경은 선택 reader 테스트만 skip한다. 별도 VTP 환경에서 해당 테스트를 실제 실행한다.

## 다음 작업

이 원본 형식을 파일 기반 prediction bundle 계약과 연결한다. 유도 시각을 사용하는 데이터와 실제 timestamp를 가진 데이터는 동일한 것으로 합치지 않는다. 1개 recipe 검사 성공을 모델 일반화 성능이나 실제 공정 정확도 증거로 사용하지 않는다.
