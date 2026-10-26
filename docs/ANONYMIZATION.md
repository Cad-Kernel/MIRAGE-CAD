# Anonymous-copy conventions

Identified personal names, usernames, workstation names and machine-specific prefixes are neutralized
in the distributed working tree. Python code keeps the same non-string AST where the original parses;
JSON/JSONL numeric/boolean/null values and CSV numeric cells are checked unchanged. PNG text/EXIF chunks
are removed without changing IDAT bytes; STEP DATA numeric tokens are checked unchanged. Binary array
payloads are copied only after inspecting their containers for the requested identity tokens.

Path tokens include `__RUN_SOURCE_ROOT__`, `__RUN_ROOT__`, `__DEV_ROOT__`, `__REPO_ROOT__`,
`__EVIDENCE_SOURCE_ROOT__`, `__FLLUMA_ROOT__`, `__USER_HOME__`, `__LOCAL_WORKSPACE__` and
`__TEMP_RUN_ROOT__`. They are provenance/configuration markers, not claims that these files are present.
The materializer creates a separate local source copy; configure omitted resources yourself.

Original SHA256 values, old archive object names and historical seal fields remain original identifiers.
They do not validate the anonymized bytes. `evidence/provenance.jsonl` and `bundle_manifest.jsonl` provide
the original-to-distributed relationship and current integrity authority. Old manifests are not silently
re-sealed. Some historical hash guards will intentionally reject altered paths/source bytes; no such
failure should be bypassed and described as an exact historical reproduction.

Copyright/license notices for third-party work are retained. Private source-path mappings, editorial
letters and repository backups stay outside this tree. Text/container checks are scoped checks, not a
proof against inference from scientific content or a substitute for final anonymous-access review.

The local Git database was replaced by a fresh database containing one anonymous root commit. No old
commits or remote-tracking references were copied into it. Its previous database is backed up privately
outside the release, not inside this repository. No remote push or hosting-service history cleanup was
performed. Fetching the old remote can restore old identifying objects locally. See `GIT_HISTORY.md`.

Original scientific source/checkpoint/manifest hashes remain historical identifiers; replacing Git
history does not make an unresolved historical experiment strictly matched or fully reproducible.
