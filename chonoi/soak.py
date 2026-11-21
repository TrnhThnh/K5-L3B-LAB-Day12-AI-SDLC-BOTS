"""Run deterministic headless day cycles and report soak results."""

import argparse
import json
from pathlib import Path
import sys
import tempfile
from time import perf_counter

from .contract import load_contract
from .runner import run


def _positive_int(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if number < 1:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def _read_results(path, days, day_plan):
    results = []
    plan_days = []
    pending_shop = None
    end = None
    templates = sorted(day_plan, key=lambda plan: plan["day"])
    if not templates:
        raise ValueError("tuning.day_plan must contain at least one plan")
    with path.open(encoding="utf-8") as trace:
        for line in trace:
            row = json.loads(line)
            if row.get("type") == "event" and row.get("name") == "day_plan":
                day = row["day"]
                expected = templates[(day - 1) % len(templates)]
                if row["data"] != {
                    "dishes": expected["dishes"],
                    "ingredients": expected["ingredients"],
                }:
                    raise ValueError(f"day {day}: plan did not repeat as expected")
                plan_days.append(day)
            if row.get("type") == "event" and row.get("name") == "shop_end":
                if pending_shop is not None:
                    raise ValueError("shop_end without a closing snapshot")
                pending_shop = (row["day"], row["tick"])
            elif pending_shop is not None and row.get("type") == "snapshot":
                day, tick = pending_shop
                if row["tick"] != tick:
                    raise ValueError(f"day {day}: missing shop-close snapshot")
                results.append({
                    "day": day,
                    "earned": row["earned"],
                    "reputation": row["reputation"],
                    "score": row["score"],
                })
                pending_shop = None
            if row.get("type") == "end":
                end = row

    completed = end.get("days_completed", 0) if end else 0
    expected_days = list(range(1, days + 1))
    result_days = [result["day"] for result in results]
    complete = (
        end is not None
        and end.get("reason") == "days_complete"
        and completed == days
        and result_days == expected_days
        and plan_days == expected_days
        and pending_shop is None
    )
    return completed, results, complete


def _run_once(tuning, seed, days):
    ticks_per_day = round(
        tuning["tick_hz"] * (tuning["gather"]["duration_s"] + tuning["quan"]["duration_s"])
    ) + tuning["shop"]["max_ticks"]
    ticks = ticks_per_day * days
    with tempfile.TemporaryDirectory() as tmp:
        trace = Path(tmp) / "soak.jsonl"
        run("day", tuning, {}, seed, [], ticks, trace, ticks + 1, days=days)
        return _read_results(trace, days, tuning["day_plan"])


def _gameplay_signature(outcome):
    completed, results, _ = outcome
    return completed, results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--days", required=True, type=_positive_int)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    started = perf_counter()
    crashes = 0
    days_completed = 0
    results = []
    exit_code = 0
    try:
        tuning = load_contract()["tuning"]
        first = _run_once(tuning, args.seed, args.days)
        days_completed, results, complete = first
        if not complete:
            sys.stderr.write("soak did not complete all requested day cycles\n")
            exit_code = 1
        else:
            try:
                replay = _run_once(tuning, args.seed, args.days)
            except Exception as error:
                crashes += 1
                sys.stderr.write(f"soak replay crashed: {error}\n")
                exit_code = 1
            else:
                if _gameplay_signature(first) != _gameplay_signature(replay):
                    sys.stderr.write("soak replay produced different gameplay results\n")
                    exit_code = 1
    except Exception as error:
        crashes += 1
        sys.stderr.write(f"soak crashed: {error}\n")
        exit_code = 1

    report = {
        "days": args.days,
        "days_completed": days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": round(perf_counter() - started, 3),
    }
    try:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        sys.stderr.write(f"cannot write soak report: {error}\n")
        return 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
