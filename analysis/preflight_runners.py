"""Static preflight for the training_25k runner scripts.

Written after three bugs shipped in a row, each of which a machine could have caught
before the run started rather than hours into it:

  1. CODE_DIR was referenced but never assigned -- would have died under `set -u`
     forty minutes in.
  2. Configuration B ran on --limit 100 (the first hundred) against a configuration A
     built from a seeded random hundred. Four parts overlapped. Nothing crashed; the
     comparison was simply meaningless.
  3. B3 fed a 100-row plan file to a generator that iterates its input, produced
     100-row outputs into a directory named `_full`, and exited 0. The guard tested
     for a crash; the failure mode was silent under-coverage.

So this checks, per script:

  A. every $VAR used is assigned somewhere above it (the set -u trap)
  B. every --flag handed to a python script is declared in that script's argparse
     (the "it takes --predicted-jsonl not --predictions" trap)
  C. every input path that looks like a file exists in WSL, with its row count when
     the script names an expected size (the under-coverage trap)
  D. every .jsonl the printed PowerShell block consumes is one this script actually
     writes (the "PowerShell points at a file nobody produced" trap)
  E. outputs that already exist, which the `[ -s "$OUT" ]` skip logic would silently
     treat as complete (the "re-run quietly reuses the bad data" trap)
  F. the printed block is PowerShell, not bash (the "you pasted a for-loop into
     PowerShell" trap)

It is deliberately static: no GPU, no model load, no side effects. Run it before
starting anything long. Works from either side, and lints whichever copy of the tree it
is sitting in -- so running it in WSL checks the scripts that will actually execute:

    # WSL, from ~/workspace/MIRAGE/src
    python scratch/preflight_runners.py [script.sh ...]

    # Windows, from the repo root
    python src/scratch/preflight_runners.py [script.sh ...]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Runs from either side. WIN_SRC is where the scripts being linted live -- always the
# tree this file sits in, so `python scratch/preflight_runners.py` works in WSL and
# `python src/scratch/preflight_runners.py` works from the Windows repo root. WSL_SRC is
# where outputs/ and data/ live, which on Windows means reaching across the UNC share
# and on Linux is the same tree.
WIN_SRC = Path(__file__).resolve().parent.parent
WSL_SRC = (Path(r"\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src")
           if sys.platform == "win32" else WIN_SRC)
# Discovered, not listed. A hardcoded list silently stops covering new runners: this one
# had stalled at 29 while 30 through 36 were written and never checked, which is exactly the
# failure this tool exists to catch.
#
# Numbered 25 and up: that is where the two-environment convention this tool checks begins
# (WSL does the work, a trailing heredoc prints the PowerShell half). The earlier scripts
# predate it and would only produce noise.
DEFAULT = sorted(f"training_25k/{p.name}" for p in (WIN_SRC / "training_25k").glob("[0-9]*.sh")
                 if p.name[:2].isdigit() and int(p.name[:2]) >= 25) \
    if (WIN_SRC / "training_25k").is_dir() else []

# Shell builtins / environment names that need no local assignment.
SHELL_OK = {
    "PATH", "HOME", "PWD", "IFS", "PS1", "LINENO", "RANDOM", "SECONDS", "BASH",
    "BASH_SOURCE", "FUNCNAME", "PIPESTATUS", "LASTEXITCODE", "PYTORCH_CUDA_ALLOC_CONF",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "@", "*", "#", "?", "$", "!", "-",
}

problems: list[tuple[str, str, str]] = []   # (script, severity, message)


def note(script: str, sev: str, msg: str) -> None:
    problems.append((script, sev, msg))


def wsl(rel: str) -> Path:
    """Resolve a path written relative to the source root."""
    return WSL_SRC / rel.replace("\\", "/")


def strip_comments(text: str, drop_heredocs: bool = False) -> str:
    """Drop comment lines. With drop_heredocs, also blank heredoc bodies.

    Heredoc bodies must be excluded from the shell-variable analysis: they hold the
    PowerShell block, whose `$m` and `$T` are PowerShell variables, not undefined bash
    ones. Reporting those was this checker's own first false positive.
    """
    out, in_heredoc, delim = [], False, None
    for line in text.splitlines():
        if in_heredoc:
            out.append("" if drop_heredocs else line)
            if line.strip() == delim:
                in_heredoc, delim = False, None
            continue
        m = re.search(r"<<\s*'?([A-Za-z]+)'?\s*$", line)
        if m:
            in_heredoc, delim = True, m.group(1)
            out.append(line if not drop_heredocs else "")
            continue
        out.append("" if line.lstrip().startswith("#") else line)
    return "\n".join(out)


def strip_awk(code: str) -> str:
    """Blank single-quoted awk/sed programs -- their $NF, $1 are not shell variables."""
    return re.sub(r"(awk|sed)\s+'[^']*'", r"\1 ''", code)


def logical_lines(code: str) -> list[str]:
    """Join backslash continuations so a multi-line python invocation is one string."""
    joined, buf = [], ""
    for line in code.splitlines():
        if line.rstrip().endswith("\\"):
            buf += line.rstrip()[:-1] + " "
        else:
            joined.append(buf + line)
            buf = ""
    if buf:
        joined.append(buf)
    return joined


def declared_flags(py: Path) -> set[str] | None:
    if not py.is_file():
        return None
    s = py.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r'add_argument\(\s*["\'](--[a-zA-Z0-9_-]+)["\']', s))


# Flags whose default silently bounds how much data a run covers. A missing one of these
# does not crash and does not warn -- it just produces a smaller answer that looks like a
# full one, which is failure mode 3 in this file's header and has now happened three times.
CAPPING = {"--limit", "--max-rows", "--max-samples", "--head", "--n", "--num-samples",
           "--subset", "--sample-size"}

# Scripts whose entire job is to produce a subset of a stated size. A size default there is
# the intent, not a leftover, so flagging it is noise -- and noise in an ERROR channel is
# what teaches you to stop reading it.
SUBSET_MAKERS = {"training_25k/scripts/make_random_subset.py"}


def capping_defaults(py: Path) -> dict[str, str]:
    """{flag: default} for capping flags whose default is not None."""
    if not py.is_file():
        return {}
    s = py.read_text(encoding="utf-8", errors="replace")
    out = {}
    for flag, body in re.findall(r'add_argument\(\s*["\'](--[a-zA-Z0-9_-]+)["\']([^)]*)', s):
        if flag not in CAPPING:
            continue
        m = re.search(r"default\s*=\s*([^,)\s]+)", body)
        if m and m.group(1) not in ("None", "0"):
            out[flag] = m.group(1)
    return out


# --------------------------------------------------------------------- checks
def check_vars(name: str, code: str) -> dict[str, str]:
    assigned: dict[str, str] = {}
    for line in logical_lines(code):
        # plain assignment; the `pattern) VAR=value ;;` form inside a case block, which a
        # ^-anchored regex misses (this checker's second false positive); and `local x=`
        # / `declare` / `export`, which is its fourth -- a script that did its work in
        # shell functions had every one of its locals reported as unassigned, and six
        # spurious ERRORs is how a checker teaches you to stop reading its ERRORs.
        for m in re.finditer(r"(?:^|\)\s+|;\s*|&&\s*|\b(?:local|declare|typeset|export)\s+)"
                             r"\s*([A-Za-z_][A-Za-z0-9_]*)=(\S*)", line):
            assigned.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
        for m in re.finditer(r"\bfor\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\b", line):
            assigned.setdefault(m.group(1), "<loop>")
        for m in re.finditer(r"\bread\s+([A-Za-z_][A-Za-z0-9_]*)", line):
            assigned.setdefault(m.group(1), "<read>")
    used = set(re.findall(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)", code))
    # ${VAR:-default} and ${VAR:+x} are safe under set -u even if unassigned
    guarded = set(re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\s*:[-+?]", code))
    missing = sorted(used - set(assigned) - SHELL_OK - guarded)
    for v in missing:
        note(name, "ERROR", f"${v} is used but never assigned -- dies under `set -u`")
    return assigned


def expand(val: str, env: dict[str, str], glob_loops: bool = False) -> str:
    """Substitute assigned variables. With glob_loops, loop variables become `*`, so a
    path like $WORK/genB_r100_${M}_T${T}.jsonl becomes a pattern the PowerShell check
    can match against -- otherwise every looped output is invisible to it, which was
    this checker's third false positive."""
    # ${VAR:-default} resolves to its default for static purposes; an env override at
    # run time is the caller's business and is called out separately.
    prev = None
    while prev != val:
        prev = val
        # collapse each round: VAR="${VAR:-2500}" expands to a string that itself needs
        # collapsing, so doing this once up front is not enough
        val = re.sub(r"\$\{[A-Za-z_][A-Za-z0-9_]*:-([^}]*)\}", r"\1", val)
        for k, v in sorted(env.items(), key=lambda kv: -len(kv[0])):
            if v in ("<loop>", "<read>"):
                if glob_loops:
                    val = val.replace("${" + k + "}", "*").replace("$" + k, "*")
                continue
            val = val.replace("${" + k + "}", v).replace("$" + k, v)
    return re.sub(r"\*{2,}", "*", val)


def check_python_calls(name: str, code: str, env: dict[str, str]) -> tuple[set, set]:
    """Returns (inputs_referenced, outputs_written) as source-relative strings."""
    inputs, outputs = set(), set()
    for line in logical_lines(code):
        m = re.match(r"\s*python3?\s+(-m\s+)?(\S+)\s+(.*)$", line)
        if not m or line.lstrip().startswith("#"):
            continue
        modflag, target, rest = m.groups()
        if target.startswith("-"):
            continue
        if modflag:                       # python -m pkg.mod
            target = target.replace(".", "/") + ".py"
        if target == "-":                 # inline heredoc python, nothing to check
            continue
        py = WIN_SRC / target
        flags = set(re.findall(r"(--[a-zA-Z0-9_-]+)", rest))
        decl = declared_flags(py)
        if decl is None:
            note(name, "ERROR", f"invokes {target}, which does not exist")
            continue
        for f in sorted(flags - decl):
            note(name, "ERROR", f"{target} has no argument {f} "
                                f"(it declares: {', '.join(sorted(decl)[:6])} ...)")
        for f, dv in sorted(capping_defaults(py).items()):
            if f not in flags and target not in SUBSET_MAKERS:
                note(name, "ERROR",
                     f"{target} is called without {f}, and its default is {dv} -- the run "
                     f"will silently cover only {dv} rows and exit 0. A smoke-test default "
                     f"left in a generation script is how arm B of script 36 produced 20 "
                     f"rows instead of 400. Pass it explicitly.")
        for f, v in re.findall(r"(--[a-zA-Z0-9_-]+)\s+(\"[^\"]+\"|\S+)", rest):
            raw = v.strip('"')
            if raw.startswith("-"):
                continue
            if f in ("--output-jsonl", "--output-json", "--output", "--output-dir"):
                outputs.add(expand(raw, env, glob_loops=True))
            elif f in ("--input-jsonl", "--ir-jsonl", "--predicted-jsonl", "--input",
                       "--alignment-checkpoint", "--prior-checkpoint", "--lora-ir-dir",
                       "--lora-code-dir", "--retrieval-index", "--ids-from",
                       "--full-train-jsonl"):
                inputs.add(expand(raw, env, glob_loops=True))
        # THE UNDER-COVERAGE TRAP, checked precisely rather than by heuristic.
        # gen_code_from_predicted_ir.py iterates its --ir-jsonl, not its --input-jsonl.
        # So the run's effective n is the IR file's row count, and passing a 100-row IR
        # file while the script announces n=2500 produces 100 rows and exits 0. That is
        # bug #3 from the docstring, and it cost ~40 min of GPU before anyone noticed.
        if "gen_code_from_predicted_ir" in target:
            ir = next((expand(v.strip('"'), env, glob_loops=True)
                       for f, v in re.findall(r"(--ir-jsonl)\s+(\"[^\"]+\"|\S+)", rest)),
                      None)
            if ir:
                hits = resolve(ir)
                rows_n = [sum(1 for ln in p.open(encoding="utf-8", errors="replace")
                              if ln.strip()) for p in hits[:4] if p.is_file()]
                if rows_n:
                    eff = min(rows_n)
                    claims = [int(x) for x in re.findall(r"n=(\d{2,})", code)]
                    claims += [int(x) for x in re.findall(r"--limit\s+(\d{2,})", code)]
                    want = max(claims) if claims else None
                    note(name, "INFO",
                         f"effective n for {target} is {eff} -- it iterates "
                         f"--ir-jsonl ({ir}), NOT --input-jsonl")
                    if want and eff < want:
                        note(name, "ERROR",
                             f"UNDER-COVERAGE: this script announces n={want} but "
                             f"{target} will process only {eff} rows, because it "
                             f"iterates --ir-jsonl ({ir}, {eff} rows). It will exit 0 "
                             f"and write {eff}-row outputs. Re-run the step that "
                             f"PRODUCES the IR file at the larger n first.")

        # THE SLICE TRAP. --limit N against the full test set takes the FIRST N rows,
        # and docs SS9.2 measured that slice at ~10 pp optimistic (STEP N=1 Build: 79.0%
        # on the first 100, 67.0% on a seeded random 100, 70.0% on all 2,500). Any table
        # built this way is biased, and any comparison against a run that used the
        # seeded subset is confounded -- that is bug #2 from the docstring, where
        # configurations A and B shared 4 of 100 parts.
        lim = re.search(r"--limit\s+(\"[^\"]+\"|\$\{[^}]+\}|\S+)", rest)
        src = re.search(r"--input-jsonl\s+\"?(\S+?)\"?(?:\s|$)", rest)
        if lim and src:
            src_v = expand(src.group(1), env, glob_loops=True)
            lim_v = expand(lim.group(1).strip('"'), env)
            if src_v.endswith("/test.jsonl") and lim_v == "2500":
                note(name, "INFO",
                     f"{target} runs the full 2,500-row test set, so there is no slice "
                     f"bias -- but lowering it (e.g. B3_LIMIT=500) reintroduces one, "
                     f"because --limit takes the FIRST N rows.")
            elif src_v.endswith("/test.jsonl") and lim_v != "$LIMIT":
                note(name, "WARN",
                     f"{target} uses --limit {lim_v} on {src_v}: that is the FIRST "
                     f"{lim_v} rows, a slice docs SS9.2 measured ~10 pp optimistic. If "
                     f"this run will be compared against anything built from the seeded "
                     f"random subset, pre-filter with make_random_subset.py --ids-from "
                     f"outputs/geometry_nbest_random100/ir_step.jsonl.ids.txt instead.")

        # positional args to the repair scripts. Strip quotes BEFORE the .jsonl test:
        # "$W/x.jsonl" ends with '.jsonl"', not '.jsonl' -- this checker's fourth
        # false positive, and the one that hid two real PowerShell mismatches.
        if "repair_" in target:
            # Expand BEFORE testing the suffix: "$RAW" is a .jsonl but does not look
            # like one until the variable is substituted, so testing first silently
            # dropped it and the file it produces was reported as a missing input.
            pos = [expand(a.strip('"').strip("'"), env, glob_loops=True)
                   for a in rest.split()]
            pos = [a for a in pos if a.endswith(".jsonl")]
            if len(pos) >= 2:
                inputs.add(expand(pos[0], env, glob_loops=True))
                outputs.add(expand(pos[1], env, glob_loops=True))
    return inputs, outputs


def resolve(rel: str) -> list[Path]:
    """Existing paths matching rel, which may contain `*` from an unexpanded loop var."""
    try:
        if "*" not in rel:
            p = wsl(rel)
            return [p] if p.exists() else []
        parts = rel.split("/")
        stem = "/".join(p for p in parts if "*" not in p and parts.index(p) < parts.index(
            next(q for q in parts if "*" in q)))
        base = WSL_SRC / stem if stem else WSL_SRC
        pat = rel[len(stem) + 1:] if stem else rel
        return sorted(base.glob(pat))
    except (OSError, StopIteration, ValueError):
        return []


def matches(a: str, b: str) -> bool:
    """Do two possibly-globbed relative paths denote the same thing?"""
    ra = "^" + re.escape(a).replace(r"\*", ".*") + "$"
    rb = "^" + re.escape(b).replace(r"\*", ".*") + "$"
    return bool(re.match(ra, b) or re.match(rb, a))


def check_inputs_exist(name: str, inputs: set[str], outputs: set[str]) -> None:
    for rel in sorted(inputs):
        if any(matches(rel, o) for o in outputs):   # produced earlier in this script
            continue
        if re.search(r"\$[1-9]", rel):
            # A shell function's positional parameter. Its value is the caller's loop
            # variable, so the path cannot be resolved statically and reporting it as
            # absent is noise -- the fifth false positive this checker produced.
            continue
        hits = resolve(rel)
        if not hits:
            note(name, "ERROR", f"input does not exist in WSL: {rel}")
            continue
        for p in hits[:8]:
            if p.is_file() and p.suffix == ".jsonl":
                try:
                    n = sum(1 for ln in p.open(encoding="utf-8", errors="replace")
                            if ln.strip())
                    note(name, "INFO", f"input {p.name}: {n} rows")
                except OSError:
                    pass


def check_output_collisions(name: str, outputs: set[str], code: str,
                            env: dict[str, str]) -> None:
    """Existing outputs are only dangerous if the skip guard actually tests them.

    The first version flagged every pre-existing output as an ERROR, which fired on a
    run that was legitimately in progress -- three conditions complete at full length
    and a fourth mid-write. That is exactly the resume behaviour the guard exists for.
    So: resolve which path `[ -s "$X" ]` tests, and report row counts either way, so a
    truncated file is visibly different from a complete one.
    """
    guarded: set[str] = set()
    for m in re.finditer(r'\[\s*-s\s+"?\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?"?\s*\]', code):
        v = env.get(m.group(1))
        if v and v not in ("<loop>", "<read>"):
            guarded.add(expand(v, env, glob_loops=True))

    for rel in sorted(outputs):
        hits = [p for p in resolve(rel) if p.is_file() and p.stat().st_size > 0]
        if not hits:
            continue
        counts = []
        for p in hits[:6]:
            try:
                n = sum(1 for ln in p.open(encoding="utf-8", errors="replace")
                        if ln.strip())
            except OSError:
                n = -1
            counts.append(f"{p.name}({n})")
        is_guard = any(matches(rel, g) for g in guarded)
        if is_guard:
            note(name, "WARN",
                 f"the `[ -s ... ]` skip tests these and they already exist, so the run "
                 f"will SKIP them: {', '.join(counts)}. Check the row counts: a "
                 f"short file means a previous run was interrupted or under-covered, "
                 f"and skipping preserves the defect. Delete those to redo them.")
        else:
            note(name, "INFO",
                 f"intermediate output already present (not what the skip tests, so it "
                 f"will be rewritten): {', '.join(counts)}")


def heredoc_written_names(text: str) -> set[str]:
    """Basenames that an inline python heredoc appears to write.

    A blind spot the checker hit on itself: scripts that prepare inputs with an inline
    `python - <<PY` block write files the flag-scanner cannot see, because there is no
    --output-jsonl to read. Rather than treat every such script as broken, collect
    string literals ending in .json/.jsonl from heredoc bodies and turn f-string
    placeholders into globs. This proves the NAME is constructed, not that it is
    written -- so a match downgrades the finding to a caveat instead of clearing it.
    """
    names: set[str] = set()
    for body in re.findall(r"<<\s*'?[A-Za-z]+'?\s*\n(.*?)\n\s*[A-Za-z]+\s*$",
                           text, re.S | re.M):
        for lit in re.findall(r"[\"']([^\"'\n]*\.jsonl?)[\"']", body):
            names.add(re.sub(r"\{[^}]*\}", "*", lit).split("/")[-1])
    return names


def check_powershell_block(name: str, text: str, outputs: set[str]) -> None:
    blocks = re.findall(r"<<\s*'?EOF'?\s*\n(.*?)\n\s*EOF", text, re.S)
    if not blocks:
        note(name, "WARN", "no trailing instruction block found")
        return
    body = "\n".join(blocks)
    # F. is it actually PowerShell?
    for pat, why in [(r"^\s*for\s+\w+\s+in\s+.*;\s*do\s*$", "bash `for ... ; do`"),
                     (r"^\s*done\s*$", "bash `done`"),
                     (r"^\s*fi\s*$", "bash `fi`")]:
        if re.search(pat, body, re.M):
            note(name, "ERROR",
                 f"the printed block contains {why} -- pasting it into PowerShell "
                 f"fails with a parser error. Either run it in WSL or rewrite as "
                 f"PowerShell `foreach ($x in @(...)) {{ }}`")
    # D. do the referenced jsonl files correspond to things this script writes?
    refs = re.findall(r"-InputJsonl\s+\"?([^\"\s`]+)", body)
    for r in refs:
        if not re.search(r"[/\\]|\.jsonl", r):
            # Prose, not a path -- an instruction line reading "point -InputJsonl at the
            # local copies" made this checker report that the script never writes "at".
            continue
        # An UNQUOTED heredoc (<<EOF, not <<'EOF') needs every backslash doubled in
        # the source and the shell collapses them at print time. Collapse here too, or
        # the path arrives as ////wsl.localhost//Ubuntu// and matches nothing.
        r = r.replace("\\\\", "\\")   # one pass, exactly what the shell does
        tail = r.split("MIRAGE\\src\\")[-1].replace("\\", "/")
        tail = re.sub(r"\$\{?\w+\}?", "*", tail)
        heredoc = heredoc_written_names(text)
        base = tail.split("/")[-1]
        if not any(matches(tail, o) for o in outputs):
            if any(matches(base, h) for h in heredoc):
                note(name, "INFO",
                     f"PowerShell consumes {tail}; the name is constructed inside an "
                     f"inline python heredoc, so the write could not be verified "
                     f"statically. Confirm the file appears after the WSL run.")
            else:
                note(name, "ERROR",
                     f"PowerShell consumes {tail}, which this script never writes. "
                     f"Outputs are: {', '.join(sorted(outputs)[:4]) or '(none found)'} ...")
        elif not resolve(tail):
            note(name, "INFO", f"PowerShell input {tail} not on disk yet "
                               f"(expected -- the run produces it)")
    # E. do the OutputDirs collide with existing results?
    for d in re.findall(r"-OutputDir\s+\"?([^\"\s`]+)", body):
        tail = re.sub(r"\$\{?\w+\}?", "*", d.split("MIRAGE-V2\\")[-1]).replace("\\", "/")
        base = tail.split("/*")[0].rsplit("/", 1)[-1] if "*" in tail else None
        root = Path(r"C:\Workspace\Project\Paper\MIRAGE-V2") / tail.split("/")[0]
        if base and root.is_dir():
            hits = [p.name for p in root.iterdir() if p.is_dir() and p.name.startswith(base)]
            if hits:
                note(name, "WARN", f"PowerShell writes into existing dirs "
                                   f"({', '.join(sorted(hits)[:4])}) -- they will be overwritten")


def main(argv: list[str]) -> int:
    targets = argv[1:] or DEFAULT
    for rel in targets:
        name = Path(rel).name
        path = WIN_SRC / rel
        if not path.is_file():
            note(name, "ERROR", "script not found")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        # Variable analysis must not see heredoc bodies (PowerShell $m) or awk programs
        # ($NF); the call analysis must not see heredocs either, or the PowerShell block
        # would be parsed as shell.
        code = strip_awk(strip_comments(text, drop_heredocs=True))
        env = check_vars(name, code)
        inputs, outputs = check_python_calls(name, code, env)
        check_inputs_exist(name, inputs, outputs)
        check_output_collisions(name, outputs, code, env)
        check_powershell_block(name, text, outputs)

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    cur = None
    for script, sev, msg in sorted(problems, key=lambda p: (p[0], order[p[1]], p[2])):
        if script != cur:
            print(f"\n=== {script} ===")
            cur = script
        print(f"  [{sev:<5}] {msg}")

    errs = sum(1 for _, s, _ in problems if s == "ERROR")
    warns = sum(1 for _, s, _ in problems if s == "WARN")
    print(f"\n{errs} error(s), {warns} warning(s)")
    if errs:
        print("Do not start a long run until the errors are cleared.")
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
