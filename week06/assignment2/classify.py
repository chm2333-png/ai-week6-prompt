# classify.py — 강의노트 3.3절 classify_review (3중 방어) + 실패 추적
import json

from mock_llm import mock_llm_call

SYSTEM = """당신은 고객 리뷰 분류기입니다. 반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트를 절대 포함하지 마세요.
{"category": "배송|품질|가격|서비스|기타", "sentiment": "긍정|부정|중립", "score": 1~5 사이의 정수}"""

VALID_CATEGORIES = ["배송", "품질", "가격", "환불", "서비스", "기타"]


def classify_review(review_text, trace=None, verbose=False):
    """리뷰 1건을 분류하여 딕셔너리로 반환. 실패 시 None.

    trace(dict)를 넘기면 집계용 정보를 채운다.
      - malformed : mock이 주입한 불량 유형 (None / codefence / chatter / truncated)
      - fixed_by  : 불량 응답을 살려낸 방어 이름 (None / "defense1")
      - fail      : 실패 사유 (None / "parse_error" / "invalid_category")
    """
    if trace is None:
        trace = {}
    trace.update(malformed=None, fixed_by=None, fail=None)

    result = mock_llm_call(SYSTEM, f"리뷰: {review_text}")
    trace["malformed"] = result.get("_malformed")
    raw = result["text"].strip()  # 앞뒤 공백·줄바꿈 제거

    # 방어 1: 마크다운 코드 블록 제거 (포맷 정규화): ```json ... ``` 코드 제거
    if raw.startswith("```"):
        raw = raw.strip("`")                       # 앞뒤 백틱 제거
        raw = raw.replace("json", "", 1).strip()   # 언어 표기 "json" 1회 제거
        trace["fixed_by"] = "defense1"

    # 방어 2: 파싱 실패는 언제든 일어날 수 있다 → 예외 처리 필수
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        if verbose:
            print(f"[경고] JSON 파싱 실패: {raw[:50]}...")
        trace["fixed_by"] = None
        trace["fail"] = "parse_error"
        return None

    # 방어 3: 필드 존재와 값의 유효성 검증
    if data.get("category") not in VALID_CATEGORIES:
        trace["fixed_by"] = None
        trace["fail"] = "invalid_category"
        return None
    return data
