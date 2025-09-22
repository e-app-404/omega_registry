Contributing
=============

This repository uses machine-parseable ADRs and a small set of repository tools. A few notes to get contributors up and running quickly.

Required tooling
-----------------
- yq (mikefarah/yq) v4.x is required for ADR validation and index generation. The project CI pins `yq` to a specific v4 release to ensure deterministic parsing.

Install (macOS, Homebrew)

```bash
# Install the mikefarah/yq v4 binary via Homebrew (if available) or download the release binary:
brew install yq
```

Install (manual binary)

```bash
# Download the pinned binary used in CI (example for macOS arm64):
curl -L -o ~/bin/yq "https://github.com/mikefarah/yq/releases/download/v4.30.8/yq_darwin_arm64"
chmod +x ~/bin/yq
# Ensure ~/bin is on your PATH
```

Local usage
-----------
- Validate ADRs locally:

```bash
bash ops/ADR/validate_adrs.sh
```

- Generate ADR index (updates `addon/docs/ADR/INDEX.md`):

```bash
bash ops/ADR/generate_adr_index.sh
```

CI
--
The repository has a GitHub Actions workflow that validates ADRs on pull requests. The workflow installs a pinned `yq` binary to ensure consistent parsing across environments.

If the validator complains about `yq` lexer messages locally, install the pinned `yq` binary above or run the validator script which will download a pinned `yq` temporarily.
