from collections import defaultdict
from datetime import datetime
from .errors import ProcessError

def _ts(v): return datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()

def outcome_report(events: list[dict]) -> dict:
    seen, changes = set(), defaultdict(list)
    for e in events:
        missing={"eventId","repository","changeId","timestamp","type"}-set(e)
        if missing: raise ProcessError("incomplete metric event: " + ", ".join(sorted(missing)))
        if e["eventId"] in seen: raise ProcessError("contradictory duplicate metric event id")
        seen.add(e["eventId"]); changes[e["changeId"]].append(e)
    rows, missing = [], []
    for change, items in changes.items():
        by = defaultdict(list)
        for e in items: by[e["type"]].append(e)
        if any(len(by[t]) > 1 for t in ("issue_opened","pr_opened","merged")):
            raise ProcessError(f"contradictory lifecycle events for {change}")
        def duration(a,b):
            value=_ts(by[b][0]["timestamp"])-_ts(by[a][0]["timestamp"]) if by[a] and by[b] else None
            if value is not None and value<0: raise ProcessError(f"contradictory event ordering for {change}")
            return value
        row={"changeId":change,"local_coding_seconds":duration("implementation_started","pr_opened"),
             "end_to_end_seconds":duration("issue_opened","merged"),"review_seconds":duration("review_started","review_completed"),
             "correction_cycles":len(by["correction"]),"ci_retries":max(0,len(by["ci_run"])-1),
             "defects":len(by["defect"]),"reverts":len(by["revert"]),
             "cost":sum(float(e.get("value",0)) for e in by["cost"]),
             "complexity_delta":sum(float(e.get("value",0)) for e in by["complexity"]),
             "characteristics":items[0].get("characteristics",[]),"workflow":items[0].get("workflow")}
        if row["end_to_end_seconds"] is None: missing.append({"changeId":change,"field":"end_to_end_seconds"})
        rows.append(row)
    complete=[r for r in rows if r["end_to_end_seconds"] is not None]
    return {"contractVersion":1,"changes":rows,"missing":missing,
            "repository_baseline":{"sampleSize":len(complete),"meanEndToEndSeconds":sum(r["end_to_end_seconds"] for r in complete)/len(complete) if complete else None},
            "interpretation":{"benefit":"lower end-to-end time without worse defects/reverts/complexity","neutral":"local speed changes without end-to-end or quality change","bottleneck_displacement":"local coding improves while review, correction, CI, or stability worsens"},
            "privacy":"repository/process improvement only; individual ranking prohibited"}

def compare_outcomes(before:list[dict],after:list[dict]):
    b,a=outcome_report(before),outcome_report(after)
    bv,av=b["repository_baseline"]["meanEndToEndSeconds"],a["repository_baseline"]["meanEndToEndSeconds"]
    return {"contractVersion":1,"before":b["repository_baseline"],"after":a["repository_baseline"],
            "endToEndDeltaSeconds": av-bv if av is not None and bv is not None else None,
            "interpretation":a["interpretation"],"missing":b["missing"]+a["missing"]}
