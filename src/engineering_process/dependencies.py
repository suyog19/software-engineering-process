import re, subprocess, fnmatch
from pathlib import Path
from .errors import ProcessError

LOCKS=("lock", "package-lock.json", "go.sum")
MANIFESTS=("pyproject.toml","requirements.txt","package.json","pom.xml","build.gradle","Cargo.toml","go.mod")

def dependency_signals(root:Path, base:str, head:str, changes:list[dict], hints:list[str]|None=None):
    signals=[]; chars={}
    paths=[c["path"] for c in changes]
    for path in paths:
        low=path.lower()
        if low.endswith(LOCKS): signals.append({"source":"git_dependency","value":path,"characteristic":"mechanical_lock_refresh","matched_rule":"lockfile"}); chars["mechanical_lock_refresh"]=True
        if any(low.endswith(x.lower()) for x in MANIFESTS): signals.append({"source":"git_dependency","value":path,"characteristic":"dependency_change","matched_rule":"manifest"}); chars["dependency_change"]=True
        if low.startswith(".github/workflows/"): chars["dependency_change"]=True
        if "dockerfile" in low or low.endswith((".containerfile",".github/dependabot.yml",".npmrc","pip.conf")): chars["dependency_change"]=True
        if any(fnmatch.fnmatch(path,h) for h in (hints or [])): chars["dependency_change"]=True; signals.append({"source":"git_dependency","value":path,"characteristic":"dependency_change","matched_rule":"repository dependency hint"})
    if not chars: return chars,signals
    r=subprocess.run(["git","diff","--unified=0",base,head,"--",*paths],cwd=root,text=True,capture_output=True)
    if r.returncode: raise ProcessError("cannot inspect dependency diff")
    added="\n".join(line[1:] for line in r.stdout.splitlines() if line.startswith("+") and not line.startswith("+++"))
    checks=[(r"(?:git\+|https?://).*(?:HEAD|main|master|@[^0-9a-f]|$)","unpinned_vcs_dependency"),
            (r"uses:\s*[^\s]+@(main|master|v\d+)\b","mutable_action"),
            (r"^\s*FROM\s+[^\s]+(?::latest)?\s*$","mutable_container_base"),
            (r"registry|index-url|registry-url","registry_source_change")]
    for pattern,kind in checks:
        if re.search(pattern,added,re.I|re.M): chars["dependency_trust_boundary"]=True; signals.append({"source":"git_dependency","value":kind,"characteristic":"dependency_trust_boundary","matched_rule":pattern})
    if chars.get("dependency_change") and re.search(r"^\s*[+\"']?[A-Za-z0-9_.-]+\s*(?:[=~^<>]|$)",added,re.M):
        signals.append({"source":"git_dependency","value":"added_or_changed_requirement","characteristic":"dependency_change","matched_rule":"added manifest entry"})
    return chars,signals
