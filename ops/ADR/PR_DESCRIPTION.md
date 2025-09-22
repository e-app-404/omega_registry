Title: chore(ADR): consolidate ADR tooling, add CI validation and index

Body:
This PR adapts ADR ops scripts for repository-root usage, adds ADR validation CI that pins mikefarah/yq v4, generates an ADR INDEX.md, and adds CONTRIBUTING notes regarding yq installation and usage.

Changes:
- ops/ADR/validate_adrs.sh: make repo-root-aware, add front-matter normalization, use pinned mikefarah/yq v4 when necessary, add run_yq helper to suppress benign stderr, validate TOKEN_BLOCK.
- ops/ADR/generate_adr_index.sh: generate addon/docs/ADR/INDEX.md (now committed).
- ops/ADR/consolidate_adr0001.sh: add usage/help text.
- .github/workflows/validate-adrs.yml: CI to install pinned yq and run ADR validator; includes a self-test step asserting pinned yq version.
- CONTRIBUTING.md: docs for installing and using mikefarah/yq to ensure consistent local validation.

Notes:
- The script will download a pinned `yq` binary at runtime only when the local `yq` isn't the expected mikefarah v4 build; the binary is stored in a temp dir and cleaned up after the script runs.
- CI is configured to pin `yq` to v4.30.8 for consistent behavior.

If you want me to open the PR on your remote, provide the repo host with pull-request API access or run `gh pr create` locally in an environment authenticated to the host.