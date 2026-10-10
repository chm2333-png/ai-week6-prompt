# AI 오케스트레이션 스튜디오 · 6주차 과제 — LLM API 구조와 프롬프트 엔지니어링

| 과제 | 제출물 |
|---|---|
| **과제 1** 프롬프트 3기법 비교 분석 리포트 (개인) | [week06/assignment1/report.md](week06/assignment1/report.md) · [실행 캡처 21장](week06/assignment1/captures/) · [출력 원문](week06/assignment1/results.txt) · [프롬프트 원본](week06/assignment1/prompts.txt) · [형식 판정 코드](week06/assignment1/format_check.py) |
| **과제 2** Mock 분류기 확장 (개인) | [week06/assignment2/README.md](week06/assignment2/README.md) · [mock_llm.py](week06/assignment2/mock_llm.py) · [classify.py](week06/assignment2/classify.py) · [run_pipeline.py](week06/assignment2/run_pipeline.py) · [실행 캡처](week06/assignment2/captures/) |
| 공통 | [보안 체크리스트 S1~S10](week06/SECURITY_CHECKLIST.md) · AI 사용 기록은 각 리포트에 포함 |

## 저장소 구조

```
week06/
├── SECURITY_CHECKLIST.md
├── assignment1/
│   ├── report.md
│   ├── results.txt
│   ├── prompts.txt
│   ├── prompts_filled.txt
│   ├── format_check.py
│   └── captures/          # ChatGPT 실행 화면 캡처 21장
└── assignment2/
    ├── README.md           # 과제 2 설명·결과·분석
    ├── mock_llm.py         # 20% 불량 응답 주입
    ├── classify.py         # classify_review (3중 방어 + 실패 추적 + 정규식 복구)
    ├── run_pipeline.py     # 200건 전체 실행·집계
    ├── reviews_sample.csv
    └── captures/
```

## 과제 1 요약

- 과업: 고객 문의를 [주문/배송/환불/제품문의/기타]로 분류하고 긴급도(1~3)를 판정
- 실행: ChatGPT 무료 웹 UI, 3기법 × 5건 = 15회 + 애매 사례 #4 반복 6회 = 21회
- 결과: 형식 준수는 세 기법 모두 7/7. 정답은 Zero-shot 7/7, Few-shot 7/7, CoT 6/7
- 결론: **명시적 경계 규칙 + Few-shot**을 기본 전략으로 채택. CoT는 출력이 약 8배 길지만 이번 과업에서 정확성·일관성 개선이 없었음

## 과제 2 요약

- `mock_llm_call`이 20% 확률로 코드펜스형 / 사족형 / 잘린 JSON형 불량 응답을 반환
- `reviews_sample.csv` 200건 (seed=42): **처리 200건 / 실패 31건.** 불량 50건 중 코드펜스형 19건은 방어 1이 복구
- 도전 과제: 정규식으로 `{...}`만 골라내 사족형을 복구 → 실패 31건 → **14건**. 잘린 JSON은 정보 자체가 없어 복구 불가

과제 1 형식 판정 재현:

```bash
cd week06/assignment1
python format_check.py
```

과제 2 실행:

```bash
cd week06/assignment2
python run_pipeline.py
```
