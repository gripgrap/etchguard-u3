# `ci.yml` — CI scope

1. GitHub checkout
2. Python 3.11 설치
3. `pip install -e .`
4. `unittest discover -s tests -v`
5. `etchguard.cli demo --output reports/generated/ci-demo`

**검증 가능:** Python 패키지 설치·toy fixture 계약·fingerprint/게이트 로직·CLI 작동.  
**검증 불가:** 실제 ViennaPS import, 실데이터 변환, FNO/MGN 학습, 물리 수치 수렴, 원격 배포/승격/롤백.

CI가 실패하면 저장소 Actions에서 job log를 보관하고 원인 수정 후 재실행합니다. green badge를 실제 실행 전에 README에 미리 달지 않습니다.
