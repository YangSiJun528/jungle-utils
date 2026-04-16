# jungle-utils

크래프톤 정글 활동을 하면서 자주 반복하게 될 작업을 돕는 Codex 도구 모음.

## 포함된 스킬

### 1. `prompt-logging-hook-setup`

`UserPromptSubmit` 프롬프트 로깅 훅을 설치하거나 점검하고 복구하는 스킬.

### 2. `prompt-retro-analysis`

프롬프트 로깅 훅이 남긴 `logs/{username}-prompt-log.jsonl`을 CSV와 세션 단위 리포트로 바꿔서 작업을 회고하는 스킬.

프롬프트 로깅 파일과 Git 커밋 작성자의 커밋 내역을 비교하여 결과물을 반환한다.

### 3. `github-project-week-issues`

`github-projects/week*_issues_complete.csv` 같은 주차별 CSV를 읽어 GitHub Issues 생성 계획을 만들고, 필요하면 GitHub Project에 추가하는 스킬.

정글 주차별 과제의 요구사항이 정리된 csv 파일이다, 공식적으로 자동화 스크립트를 제공하지만, 내가 원하는 라벨링이나 기능을 추가하게 하기 위해 SKILL로 만들어 관리하고 있다.

### 4. `transcript-markdown-cleanup`

회의록, 발표 연습, 피드백 녹취처럼 정글에서 자주 생길 수 있는 원시 전사본을 읽기 좋은 마크다운 스크립트로 정리하는 스킬.

원문 말투와 반복은 최대한 유지하고, 문맥상 확실한 음성 인식 오류만 최소한으로 고친다. 안전하게 복원할 수 없는 표현은 억지로 고치지 않고 체크리스트로 분리한다.

## 참고

- `prompt-logging-hook-setup`이 만드는 파일은 대상 작업 레포에 들어가는 산출물이지, 이 저장소의 기본 상태가 아니다.
