# classify.py — 강의노트 3.3절 classify_review (3중 방어) + 실패 추적
import json
import re

from mock_llm import mock_llm_call

SYSTEM = """당신은 고객 리뷰 분류기입니다. 반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트를 절대 포함하지 마세요.
{"category": "배송|품질|가격|서비스|기타", "sentiment": "긍정|부정|중립", "score": 1~5 사이의 정수}"""

VALID_CATEGORIES = ["배송", "품질", "가격", "환불", "서비스", "기타"]

# (도전 과제) 응답 안에서 첫 '{'부터 마지막 '}'까지를 찾아낸다
JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def classify_review(review_text, trace=None, verbose=False, rescue=False):
    """리뷰 1건을 분류하여 딕셔너리로 반환. 실패 시 None.

    trace(dict)를 넘기면 집계용 정보를 채운다.
      - malformed : mock이 주입한 불량 유형 (None / codefence / chatter / truncated)
      - fixed_by  : 불량 응답을 살려낸 방어 이름 (None / "defense1" / "regex")
      - fail      : 실패 사유 (None / "parse_error" / "invalid_category")

    rescue=True이면 방어 2에서 파싱이 실패했을 때 정규식으로 {...} 부분만 꺼내 한 번 더 파싱한다.
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
        data = _rescue_json(raw) if rescue else None
        if data is not None:
            trace["fixed_by"] = "regex"
    if data is None:
        if verbose:
            print(f"[경고] JSON 파싱 실패: {raw[:50]}...")
        trace["fixed_by"] = None
        trace["fail"] = "parse_error"
        return None

    # 방어 3: 필드 존재와 값의 유효성 검증
    if not isinstance(data, dict) or data.get("category") not in VALID_CATEGORIES:
        trace["fixed_by"] = None
        trace["fail"] = "invalid_category"
        return None
    return data


def _rescue_json(raw):
    """(도전 과제) 사족 사이에 묻힌 JSON 객체를 정규식으로 골라내 파싱한다.

    - 사족형: '물론입니다! ... {"category": ...}' → { } 구간이 온전히 있으므로 복구된다.
    - 잘린 JSON형: '{"category": "배송", "sentim' → 닫는 '}'가 없어 정규식이 아예 매치되지 않고,
      설령 매치되더라도 빠진 키·값은 원문 어디에도 없으므로 복구할 수 없다.
    """
    match = JSON_BLOCK.search(raw)
    if match is None:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
