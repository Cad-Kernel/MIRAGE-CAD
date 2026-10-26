"""One current CPU illustration execution inside FllumaCLI, no repair."""
import ast
import hashlib
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path


def main():
    job = json.loads(Path(os.environ["MIRAGE_PARAMETER_VISUAL_JOB"]).read_text(encoding="utf-8"))
    out = Path(job["output_dir"])
    code = Path(job["code_path"])
    assert hashlib.sha256(code.read_bytes()).hexdigest() == job["code_sha256"]
    report = out / "native_export.json"
    assert not report.exists()
    result = {"case_id":job["case_id"],"side":job["side"],"code_sha256":job["code_sha256"],"python":sys.version,
              "started_utc":datetime.now(timezone.utc).isoformat(),"additional_repair":False,"historical_statistics_modified":False,
              "gates":{k:False for k in ("syntax_ok","exec_ok","build_ok","solid_valid","step_export_ok")}}
    stage = "syntax_ok"
    with (out / "native_events.jsonl").open("x",encoding="utf-8") as events:
        def event(stage):
            events.write(json.dumps({"stage":stage,"utc":datetime.now(timezone.utc).isoformat()})+"\n")
            events.flush()
        try:
            text = code.read_text(encoding="utf-8")
            event(stage)
            ast.parse(text)
            result["gates"][stage] = True
            stage = "exec_ok"
            event(stage)
            import flluma
            from flluma.api import evaluation
            ns = {k:getattr(flluma,k) for k in dir(flluma) if not k.startswith("_")}
            ns["__name__"] = "__current_parameter_illustration__"
            exec(compile(text,str(code),"exec"),ns)
            part = ns.get("part")
            if part is None:
                raise ValueError("Program did not define part")
            result["gates"][stage] = True
            stage = "build_ok"
            event(stage)
            part.build()
            result["gates"][stage] = True
            stage = "solid_valid"
            event(stage)
            validation = part.validate()
            result["validation"] = str(validation)
            if validation is False:
                raise ValueError("part.validate returned False")
            result["gates"][stage] = True
            stage = "step_export_ok"
            event(stage)
            step = out / "model.step"
            assert not step.exists()
            part.export_step(str(step))
            if not step.is_file() or step.stat().st_size < 100:
                raise ValueError("No nonempty STEP output")
            result["gates"][stage] = True
            result.update(status="CURRENT_CPU_STEP_EXPORTED",step_sha256=hashlib.sha256(step.read_bytes()).hexdigest(),
                          step_bytes=step.stat().st_size,native_shape_info=evaluation.occt_file_shape_info(str(step)))
        except Exception as exc:
            result.update(status="CURRENT_CPU_EXECUTION_FAILED_NO_SUBSTITUTION",failure_stage=stage,error=f"{type(exc).__name__}: {exc}",traceback=traceback.format_exc())
    result["completed_utc"] = datetime.now(timezone.utc).isoformat()
    with report.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2,default=str)
        stream.write("\n")


if __name__ == "__main__":
    main()
