import shlex, subprocess
from datetime import datetime, timezone
from pathlib import Path
from .errors import ProcessError

def verify_context(root:Path, entries:list[dict]):
    findings=[]
    for item in entries:
        high=item.get("criticality")=="high"
        if high and not item.get("owner"): findings.append(f"critical context missing owner: {item['path']}")
        if high and not item.get("verification"): findings.append(f"critical context missing verification: {item['path']}")
        cadence=item.get("review_cadence_days"); reviewed=item.get("reviewed_at")
        if cadence and reviewed:
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(reviewed.replace("Z","+00:00"))).days
            if age>cadence and high: findings.append(f"critical context review overdue by {age-cadence} days: {item['path']}")
        v=item.get("verification")
        if not v: continue
        target=v["target"]
        if v["type"] in {"file","link","generated"}:
            p=(root/target).resolve()
            if root.resolve() not in p.parents and p!=root.resolve(): findings.append(f"context verification escapes repository: {item['path']}")
            elif not p.exists(): findings.append(f"broken {v['type']} context claim {target}: {item['path']}")
        elif v["type"]=="command":
            try: result=subprocess.run(shlex.split(target),cwd=root,capture_output=True,text=True,shell=False,timeout=60)
            except (OSError,subprocess.TimeoutExpired) as exc: findings.append(f"context command unavailable for {item['path']}: {exc}"); continue
            if result.returncode: findings.append(f"context command failed for {item['path']}: {target}")
    if findings: raise ProcessError("context truth verification failed: " + "; ".join(findings))
    return {"verified":len(entries),"findings":[]}
