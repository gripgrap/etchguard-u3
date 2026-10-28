"""Append-only decision history; approved champion pointer with atomic replace."""
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime,timezone
from .gate import GateDecision

class Registry:
    def __init__(self,root):
        self.root=Path(root)
        self.root.mkdir(parents=True,exist_ok=True)

    def champion(self):
        p=self.root/"current.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def submit(self, model_id: str, decision:GateDecision, *, fingerprint: str) -> dict:
        if not model_id or any(x in model_id for x in "/\\\n"):
            raise ValueError("invalid model id")
        current=self.champion()
        evt={"model_id":model_id,"passed":decision.passed,"exit_code":decision.exit_code,
             "reasons":decision.reasons,"metrics":decision.metrics,"fingerprint":fingerprint,
             "timestamp":datetime.now(timezone.utc).isoformat(),"previous_champion":current["model_id"] if current else None}
        with (self.root/"history.jsonl").open("a",encoding="utf-8") as f:
            f.write(json.dumps(evt,ensure_ascii=False,sort_keys=True)+"\n")
        if decision.passed:
            tmp=self.root/"current.tmp"
            tmp.write_text(json.dumps({"model_id":model_id,"metrics":decision.metrics,"fingerprint":fingerprint},indent=2)+"\n",encoding="utf-8")
            os.replace(tmp,self.root/"current.json")
        return evt
