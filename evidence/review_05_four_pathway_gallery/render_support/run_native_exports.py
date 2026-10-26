"""Windows parent: isolated CPU export per case, guarded verified continuation only."""
import os
import subprocess
from render_common import *


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id")
    args = parser.parse_args()
    verify_original_lock()
    p = read(OUT / "render_protocol.json")
    require(sha(NATIVE / "FllumaCLI.exe") == p["native_cli_sha256"], "Native CLI drift")
    for job in p["jobs"]:
        if not job["historical_scoreable"] or (args.case_id and args.case_id != job["case_id"]):
            continue
        target = local_path(job["output_dir"])
        report = target / "native_export.json"
        if report.exists():
            old = read(report)
            require(old["status"] == "EXPORTED_LOCKED_PREDICTION", "Existing export failure requires review")
            require(sha(ROOT / old["step"]["path"]) == old["step"]["sha256"], "Export asset drift")
            print("verified prior export:", job["case_id"], flush=True)
            continue
        target.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, MIRAGE_QUALITATIVE_JOB=str(OUT / "jobs" / (job["case_id"] + ".json")))
        script = Path(__file__).parent / "export_native_one.py"
        with (target / "native_cli.log").open("xb") as log:
            proc = subprocess.run([str(NATIVE / "FllumaCLI.exe"), str(script)],
                cwd=str(NATIVE), env=env, stdout=log, stderr=subprocess.STDOUT,
                timeout=240, creationflags=subprocess.CREATE_NO_WINDOW)
        require(proc.returncode == 0 and report.exists(), f"Native export did not finalize: {job['case_id']}")
        result = read(report)
        require(result["status"] == "EXPORTED_LOCKED_PREDICTION", str(result))
        print("exported:", job["case_id"], flush=True)
    print("Requested native exports complete; no model inference or metric scoring", flush=True)


if __name__ == "__main__":
    main()
