# 의료법규 split standalone — deprecated

이 디렉터리의 split standalone UI는 폐기했다.

Canonical 의료법규 퀴즈는 기존 로그인/SRS가 붙은 국시 퀴즈 사이트의 동일 셸을 사용한다.

- Production: https://vercelpedsquiz.vercel.app/law
- Source generator: `quizzes/generate_medical_law_concept_quiz.py`
- Source data: `quizzes/data/medical_law_split_app_data.json`
- Generated HTML artifact: `quizzes/의료법규_국시개념_퀴즈.html`

`index.html`과 `medical_law_split_quiz_concept.html`은 위 production URL로 즉시 redirect한다.
