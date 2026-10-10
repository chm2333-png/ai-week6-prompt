# mock_llm.py — 6~12주차용 모의 LLM 모듈 (6주차 과제 2: 불량 응답 주입 추가)
import random

# 불량 응답 확률과 유형 (과제 1단계)
MALFORMED_RATE = 0.2
MALFORMED_TYPES = ["codefence", "chatter", "truncated"]


def _make_malformed(canned, kind):
    """정상 JSON 문자열(canned)을 실제 LLM이 자주 내놓는 불량 형태로 바꾼다."""
    if kind == "codefence":   # 코드펜스 포함: ```json ... ```
        return f"```json\n{canned}\n```"
    if kind == "chatter":     # 사족 포함: 앞에 인사말이 붙음
        return f"물론입니다! 분석 결과는 다음과 같습니다. {canned}"
    if kind == "truncated":   # 잘린 JSON: max_tokens에 걸려 중간에 끊김
        cut = random.randint(5, len(canned) - 2)   # 닫는 } 앞 어딘가에서 자름
        return canned[:cut]
    raise ValueError(f"unknown malformed type: {kind}")


def mock_llm_call(system, user_message, temperature=0.2, max_tokens=500):
    """실제 API와 동일한 인터페이스를 갖는 모의 함수.
    13주차에 이 함수의 내부만 실제 Anthropic 호출로 교체한다."""
    reviews_keywords = {
        "배송": '{"category": "배송", "sentiment": "긍정", "score": 4}',
        "환불": '{"category": "환불", "sentiment": "부정", "score": 2}',
        "품질": '{"category": "품질", "sentiment": "긍정", "score": 5}',
    }
    canned = '{"category": "기타", "sentiment": "중립", "score": 3}'
    for keyword, text in reviews_keywords.items():
        if keyword in user_message:
            canned = text
            break

    text, stop_reason, malformed = canned, "end_turn", None
    if random.random() < MALFORMED_RATE:            # 20% 확률로 불량 응답
        malformed = random.choice(MALFORMED_TYPES)   # 세 유형 중 무작위 1개
        text = _make_malformed(canned, malformed)
        if malformed == "truncated":
            stop_reason = "max_tokens"               # 실제 API도 잘리면 이렇게 알려 준다

    return {"text": text, "stop_reason": stop_reason,
            "usage": {"input_tokens": 120, "output_tokens": 35},
            # 테스트 전용 메타데이터: 어떤 불량을 주입했는지 기록해 유형별 복구율을 집계한다.
            # 실제 API 응답에는 없는 필드이므로 13주차 교체 시 함께 제거한다.
            "_malformed": malformed}
