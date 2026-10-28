# Configurations

`demo_gate.json`은 **Gaussian toy synthetic fixture 시연 전용** 정책입니다. Chamfer/깊이 제한과 기존 champion 대비 regression ratio를 정의합니다. **실제 ViennaPS 모델 배포 승인을 위한 검증 기준이 아닙니다.**

실제 데이터 연동 시 `configs/policy-viennaps-<version>.json`처럼 새 정책을 만들고, 평가 *전* 기준·단위·데이터셋/골든셋 해시를 커밋합니다. 보고서에 정책 파일의 SHA와 commit을 남깁니다. 모델 점수를 보고 기준을 느슨하게 바꾸어 PASS시키지 않습니다.
