from .errors import ProcessError

LEVELS=["human_led","assist","delegate_bounded","delegate_autonomous"]
NEGATIVE={"acceptance_clarity","boundedness","deterministic_validation","repository_test_strength","reversibility"}
HIGH={"architectural_novelty","tacit_domain_knowledge","stakeholder_negotiation","blast_radius"}

def assess_delegation(inputs: dict, human_choice: str|None=None) -> dict:
    unknown=sorted(k for k in NEGATIVE|HIGH if inputs.get(k) is None)
    severe=[k for k in HIGH if inputs.get(k) in {"high",True}]
    weak=[k for k in NEGATIVE if inputs.get(k) in {"low",False}]
    if unknown or "stakeholder_negotiation" in severe: level="human_led"
    elif severe or len(weak)>=2: level="assist"
    elif weak: level="delegate_bounded"
    else: level="delegate_autonomous"
    if human_choice:
        if human_choice not in LEVELS: raise ProcessError("unknown delegation choice")
        if LEVELS.index(human_choice)>LEVELS.index(level): raise ProcessError("human choice may be more conservative, not less")
        level=human_choice
    return {"recommendation":level,"rationale":[f"unknown: {', '.join(unknown)}"] if unknown else [f"high-impact: {', '.join(severe)}",f"weak controls: {', '.join(weak)}"],
            "boundaries":["no merge or production authority","obey resolved execution security"],
            "required_checkpoints":["human scope confirmation","independent readiness review"] if level!="delegate_autonomous" else ["readiness gate"],
            "uncertainty":unknown,"advisory":True,"outcome_link":{"recommendation":level}}
