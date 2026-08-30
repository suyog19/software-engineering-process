MODES=["Foundation","Assured","Protected","Governed"]

def adoption_report(manifest:dict)->dict:
    repo=manifest.get("repository",{}); over=manifest.get("overrides",{}); adapters=manifest.get("adapters",{})
    checks={
      "Foundation": bool(manifest.get("process") and repo.get("name")),
      "Assured": bool(over.get("validation",{}).get("commands") and repo.get("trusted_ci_workflows") and repo.get("authorized_review_workflows") and adapters.get("github")),
      "Protected": False,
      "Governed": False}
    ex=over.get("agent_execution",{})
    checks["Protected"]=checks["Assured"] and all(ex.get(k) for k in ("sandbox","network_enforcement","audit_sink"))
    critical=[c for c in manifest.get("local_context",[]) if c.get("criticality")=="high"]
    checks["Governed"]=checks["Protected"] and manifest.get("adoption",{}).get("metrics_enabled") is True and all(c.get("owner") and c.get("verification") for c in critical)
    achieved=max((m for m in MODES if checks[m]),key=MODES.index,default=None)
    target=manifest.get("adoption",{}).get("target_mode","Foundation")
    missing=[]
    if MODES.index(achieved)<MODES.index(target):
        for mode in MODES[MODES.index(achieved)+1:MODES.index(target)+1]:
            if not checks[mode]: missing.append(f"{mode} prerequisites are incomplete")
    return {"configured_mode":target,"achieved_mode":achieved,"achieved":not missing,"missing_prerequisites":missing,
            "locked_controls":"retain one canonical meaning in every mode","delivery_profile_independent":True}
