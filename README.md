# jungle-utils

크래프톤 정글 활동을 하면서 자주 반복하게 될 작업을 돕는 Codex 도구 모음.

## 포함된 스킬

### 1. `prompt-logging-hook-setup`

`UserPromptSubmit` 프롬프트 로깅 훅을 설치하거나 점검하고 복구하는 스킬.

### 2. `prompt-retro-analysis`

프롬프트 로깅 훅이 남긴 `logs/{username}-prompt-log.jsonl`을 CSV와 세션 단위 리포트로 바꿔서 작업을 회고하는 스킬.

프롬프트 로깅 파일과 Git 커밋 작성자의 커밋 내역을 비교하여 결과물을 반환한다.

### 3. `transcript-markdown-cleanup`

회의록, 발표 연습, 피드백 녹취처럼 정글에서 자주 생길 수 있는 원시 전사본을 읽기 좋은 마크다운 스크립트로 정리하는 스킬.

원문 말투와 반복을 최대한 유지, 애매한 표현은 체크리스트를 만들어 사용자가 확인하고 개선할 수 있도록 한다.

## 참고

- `prompt-logging-hook-setup`이 만드는 파일은 대상 작업 레포에 들어가는 산출물이지, 이 저장소의 기본 상태가 아니다.
