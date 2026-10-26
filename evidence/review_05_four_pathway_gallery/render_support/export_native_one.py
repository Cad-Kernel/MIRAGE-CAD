"""Run inside FllumaCLI; execute one locked program with no repair and retain STEP."""
import os
import sys
import traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_common import *


def main():
    job = read(os.environ["MIRAGE_QUALITATIVE_JOB"])
    target = local_path(job["output_dir"])
    target.mkdir(parents=True, exist_ok=True)
    report = target / "native_export.json"
    require(not report.exists(), "No implicit export overwrite")
    code = local_path(job["code_path"])
    require(job["historical_scoreable"] and sha(code) == job["code_sha256"], "Invalid export input")
    result = {"case_id": job["case_id"], "started_utc": utc(), "code_sha256": sha(code),
        "training": False, "model_forward": False, "additional_program_repair": False,
        "historical_metrics_changed": False, "python": sys.version}
    try:
        import flluma
        from flluma.api import evaluation
        ns = {name: getattr(flluma, name) for name in dir(flluma) if not name.startswith("_")}
        ns["__name__"] = "__qualitative_locked_program__"
        exec(compile(code.read_text(encoding="utf-8"), str(code), "exec"), ns)
        require("part" in ns, "Locked code does not define part")
        part = ns["part"]
        part.build()
        result["validation"] = str(part.validate())
        step = target / "prediction.step"
        require(not step.exists(), "Prediction STEP already exists")
        part.export_step(str(step))
        require(step.is_file() and step.stat().st_size > 100, "STEP export missing")
        result["native_step_info"] = evaluation.occt_file_shape_info(str(step))
        result.update(status="EXPORTED_LOCKED_PREDICTION", step=artifact(step))
    except Exception as exc:
        result.update(status="EXPORT_FAILED_NO_SUBSTITUTION", error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
    result["completed_utc"] = utc()
    write_new(report, result)


if __name__ == "__main__":
    main()
