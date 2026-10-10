"""results.txt의 21개 출력이 json.loads()로 읽히는지(형식 준수)와 정답 일치 여부를 판정한다.

판정 기준
- Zero-shot / Few-shot: 출력 전체가 json.loads()로 읽혀야 O
- CoT: 약속한 대로 '마지막 줄'만 꺼내 json.loads()로 읽혀야 O
"""
import json
import re

ANSWER = {"1": ("배송", 1), "2": ("배송", 3), "3": ("환불", 2), "4": ("환불", 1), "5": ("배송", 2)}

text = open("results.txt", encoding="utf-8").read()
blocks = re.findall(
    r"^\[((?:zeroshot|fewshot|cot)_case\d(?:_run\d)?)\]\n(.*?)(?=\n\[|\n=====)", text, re.S | re.M
)

for name, body in blocks:
    body = body.strip()
    target = body.splitlines()[-1] if name.startswith("cot") else body
    try:
        data = json.loads(target)
        fmt = "O"
    except json.JSONDecodeError:
        data, fmt = None, "X"
    case = re.search(r"case(\d)", name).group(1)
    correct = data is not None and (data["type"], data["urgency"]) == ANSWER[case]
    print(f"{name:22s} 형식 {fmt}  정답 {'O' if correct else 'X'}  출력길이 {len(body)}자")
