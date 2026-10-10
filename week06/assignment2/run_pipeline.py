# run_pipeline.py — reviews_sample.csv 전체를 분류하고 실패를 집계·보고한다
import argparse
import csv
import random
import unicodedata
from collections import Counter
from pathlib import Path

from classify import classify_review

HERE = Path(__file__).resolve().parent
TYPES = ["codefence", "chatter", "truncated"]
TYPE_LABEL = {"codefence": "코드펜스형", "chatter": "사족형", "truncated": "잘린 JSON형"}


def pad(text, width):
    """한글(2칸)을 고려해 터미널 표시 폭 기준으로 왼쪽 정렬한다."""
    w = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return text + " " * max(width - w, 0)


def load_reviews(path):
    with open(path, encoding="utf-8") as f:
        return [row["review_text"] for row in csv.DictReader(f)]


def run(reviews, rescue=False):
    """리뷰 전체를 처리하고 집계 결과를 돌려준다. 실패 건은 건너뛰되 반드시 센다."""
    stats = Counter()        # 카테고리별 성공 건수
    injected = Counter()     # 유형별 불량 응답 발생 건수
    recovered = Counter()    # 유형별 복구 건수
    fail_reasons = Counter()
    failed = 0

    for review in reviews:
        trace = {}
        result = classify_review(review, trace=trace, rescue=rescue)
        if trace["malformed"]:
            injected[trace["malformed"]] += 1
            if result is not None:
                recovered[trace["malformed"]] += 1
        if result is None:   # 조용히 버리지 않고 센다
            failed += 1
            fail_reasons[trace["fail"]] += 1
            continue
        stats[result["category"]] += 1

    return {"total": len(reviews), "failed": failed, "stats": stats,
            "injected": injected, "recovered": recovered, "fail_reasons": fail_reasons}


def print_report(r):
    total, failed = r["total"], r["failed"]
    bad = sum(r["injected"].values())
    rec = sum(r["recovered"].values())

    print(f"처리 {total}건 / 실패 {failed}건  (성공 {total - failed}건, 성공률 {(total - failed) / total:.1%})")
    print()
    print(f"[불량 응답 유형별 결과]  불량 응답 {bad}건 ({bad / total:.1%}) 중 복구 {rec}건, 실패 {bad - rec}건")
    print(f"  {pad('유형', 14)}{pad('발생', 6)}{pad('복구', 6)}실패")
    for t in TYPES:
        n, ok = r["injected"][t], r["recovered"][t]
        print(f"  {pad(TYPE_LABEL[t], 14)}{n:<6}{ok:<6}{n - ok}")
    print(f"  {pad('합계', 14)}{bad:<6}{rec:<6}{bad - rec}")
    print()
    reason = f"코드펜스형 {r['recovered']['codefence']}건을 방어 1이 걷어내 정상 처리"
    if r["recovered"]["chatter"]:
        reason += f", 사족형 {r['recovered']['chatter']}건을 정규식이 {{...}}만 골라내 복구"
    print(f"[실패 M건 < 불량 응답 건수인 이유] 실패 {failed}건 < 불량 {bad}건: {reason}했기 때문")
    print(f"[실패 사유] {dict(r['fail_reasons'])}")
    print(f"[카테고리 집계] {dict(r['stats'].most_common())}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=str(HERE / "reviews_sample.csv"))
    parser.add_argument("--seed", type=int, default=42, help="재현용 난수 시드")
    parser.add_argument("--mode", choices=["basic", "rescue", "compare"], default="compare",
                        help="basic=3중 방어만, rescue=정규식 복구 추가, compare=둘 다 실행해 비교")
    args = parser.parse_args()
    reviews = load_reviews(args.csv)

    results = {}
    for mode in (["basic", "rescue"] if args.mode == "compare" else [args.mode]):
        random.seed(args.seed)   # 두 모드가 똑같은 불량 응답을 받도록 같은 시드로 시작
        title = "기본 방어 (방어 1~3)" if mode == "basic" else "도전: 정규식 복구 추가"
        print(f"=== [{title}] {Path(args.csv).name}, seed={args.seed} ===")
        results[mode] = run(reviews, rescue=(mode == "rescue"))
        print_report(results[mode])
        print()

    if args.mode == "compare":
        b, s = results["basic"], results["rescue"]
        print("=== 비교: 정규식 복구 효과 ===")
        print(f"실패 {b['failed']}건 → {s['failed']}건 ({b['failed'] - s['failed']}건 감소)")
        print(f"사족형 복구 {b['recovered']['chatter']}건 → {s['recovered']['chatter']}건, "
              f"잘린 JSON형 복구 {b['recovered']['truncated']}건 → {s['recovered']['truncated']}건")
        print("잘린 JSON은 닫는 '}'와 뒤쪽 키·값이 응답에 아예 없어서, 정규식으로 골라낼 JSON 자체가 존재하지 않는다.")


if __name__ == "__main__":
    main()
