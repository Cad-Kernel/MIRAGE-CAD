# Local history replacement and publication boundary

The local source repository has one parentless commit authored and committed as `Anonymous Authors`
with `anonymous@example.invalid`. It contains the full sanitized working tree, including revision
evidence and the original training-source snapshots. The previous local `.git` database, branches,
remote-tracking references, reflogs and unreachable objects are not part of the new database.

A complete verified backup of the old database is retained outside the distributed tree for private
recovery. Do not publish that backup. Scientific files and numerical results are unchanged by the Git
operation. Repository documentation and the current anonymous-copy inventory were updated; historical
source hashes and scientific provenance were not rewritten.

The existing remote URL is retained only for a later explicit publication decision. No fetch, push,
remote branch replacement, repository deletion or hosting-service cleanup was performed. Therefore an
old hosted branch, tag, pull request, fork, cached commit page or other retained copy may still reveal
old content. A local root commit is not evidence that these hosted copies have been removed. Fetching
or pulling the old remote may import its old commits again.

The private completion receipt records verification of one stored commit, no parents, only the local
`main` reference, failure to resolve the old commit IDs, a clean working tree, and `git fsck` success.
The ordinary artifact verifier checks distributed-file hashes and raw result rows; it does not contact
the hosting service or prove remote anonymity. ZIP exports omit `.git` entirely.
