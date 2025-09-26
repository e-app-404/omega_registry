---
id: ADR-0004
Title: "ADR-0004: Post-mirror push workflow and NAS mirror governance"
Date: 2025-09-25
Status: Proposed
Authors: Evert Appels
related: []
supersedes: []
tags: ["git", "lfs", "mirror", "nas", "github", "workflow", "adr", "policy", "governance"]
---

## Context

This ADR documents the conservative, safety-first workflow used to mirror and publish the Omega Registry repository to GitHub and to an on-prem NAS mirror. It records the decisions, commands, and responsibilities created during the migration and scrub work in September 2025. The goal is to provide a clear, repeatable process for pushing cleaned history, managing Git LFS, and mirroring to the NAS while minimizing the risk of leaking secrets or pushing oversized artifacts.

## Decision

We adopt GitHub as the primary authoritative remote and pin Git LFS to GitHub. The NAS host (Synology) remains an on-prem mirror used for backups and local access. Pushes should go to GitHub first; a key-gated GitHub Actions workflow mirrors main+tags to the NAS when a deploy key secret is set.

## Rationale

- GitHub provides reliable Git LFS hosting, integrated CI, and broader collaboration tools.
- Synology's server-side LFS support is brittle; mirroring ensures LFS objects remain on GitHub while the NAS holds a Git mirror for redundancy.
- A bootstrap-only `main` branch was pushed to GitHub during cleanup to avoid exposing historical secrets.
- A full history rewrite (replace-text) was used on a mirror clone to redact secrets from history. A scrubbed bundle and cleaned mirror were produced and archived in `_backups/`.

## Scope

This ADR covers:
  - The relationship between local clones, GitHub (primary), and the NAS mirror.
  - Commands used for pinning LFS, creating bootstrap branches, creating bundles, and performing history rewrites on mirror clones.
  - The GitHub Actions workflow used to push to the NAS.

## Workflow (high level)

1. Work locally and push to GitHub (primary). Developers should use the `github` remote for day-to-day pushes.
2. After merge to `main`, a key-gated GitHub Actions workflow mirrors `main` and tags to the NAS (if `NAS_SSH_KEY` secret is present).
3. If history needs scrubbing, operate on a mirror clone, create pre-scrub backups, run replace-text rules, validate scrubs in a worktree, and produce scrubbed bundles. Do not force-push directly from the main working clone.
4. Coordinate credential rotation before any force-push of scrubbed history to the central GitHub repo.

## Commands and examples

These commands are the exact steps used during the migration. Run them from a secure machine and keep backups.

1) Create a safety bundle of the current state (local repo)

  ```bash
  git bundle create _backups/omega_registry-pre-scrub.bundle --all
  ```

2) Create a cleaned mirror to work on (non-destructive)
  ```bash
  git clone --mirror /path/to/local/repo /tmp/omega_registry-filter-2
  ```
3) Create a second mirror for scrubbing
  ```bash
  git clone --mirror /tmp/omega_registry-filter-2 /tmp/omega_registry-scrub.git
  ```
4) Prepare replace-text rules (example patterns used)

  # file: /tmp/omega_registry_replace.txt
  # Replace GitHub-like tokens
  gh[o|p|s]_[A-Za-z0-9_]+ => REDACTED
  # Replace JSON fields
  "access_token"\s*:\s*"[^"]+" => "access_token":"REDACTED"
  "refresh_token"\s*:\s*"[^"]+" => "refresh_token":"REDACTED"
  "client_secret"\s*:\s*"[^"]+" => "client_secret":"REDACTED"
  # Replace cloudhook URLs (Nabu Casa)
  https://hooks.nabu.casa/[^\s"']+ => https://hooks.nabu.casa/REDACTED

5) Run the history rewrite on the bare scrub mirror
  ```bash
  cd /tmp/omega_registry-scrub.git
  git replace --delete --all || true
  git filter-repo --replace-text /tmp/omega_registry_replace.txt
  ```

6) Validate scrubbed working tree
  ```bash
  git clone /tmp/omega_registry-scrub.git /tmp/omega_registry-scrub-wt
  # search for residual tokens
  grep -R --line-number -E '(gho_|ghp_|ghs_|access_token|client_secret)' /tmp/omega_registry-scrub-wt || true
  ```

7) Create a scrubbed bundle to archive
  ```bash
  git -C /tmp/omega_registry-scrub.git bundle create /path/to/repo/_backups/omega_registry-scrubbed.bundle --all
  ```

8) Push scrubbed refs to GitHub (only after credential rotation and with authorization)

  ```bash
  git -C /tmp/omega_registry-scrub.git push --force https://github.com/<org>/<repo>.git 'refs/heads/*:refs/heads/*'
  git -C /tmp/omega_registry-scrub.git push --force https://github.com/<org>/<repo>.git --tags
  ```

9) Bootstrap minimal branch (safe small push used earlier)
  ```
  # create an orphan and commit only minimal files
  git checkout --orphan bootstrap-main
  git rm -rf --cached .
  git add .github/workflows/mirror-to-nas.yml addon/docs/git_remote_strategy.md copilot_patches/phase-1
  git commit -m "chore(bootstrap): minimal workflow + docs"
  git push -u github bootstrap-main:main --force
  ```
## Git LFS policy

- Pin LFS to GitHub by adding `.lfsconfig` at the repo root:

  [lfs]
    url = `https://github.com/e-app-404/omega_registry.git/info/lfs`

- Add `.gitattributes` defaults for large JSON, JSONL, and binary artifacts to ensure large outputs are tracked with LFS.

## GitHub Actions: Mirror workflow

The key-gated workflow is located at `.github/workflows/mirror-to-nas.yml` and is configured to:

- Run on push to `main` (and optionally on push tags).
- Fetch full history (fetch-depth: 0) to ensure tags and all refs are present.
- Use a repository secret `NAS_SSH_KEY` containing a deploy key (private key) that can write to the on-prem NAS bare repository.
- Preflight SSH reachability checks before pushing.
- Push `main` and tags to the NAS remote.

If `NAS_SSH_KEY` is not present in the repository secrets, the job exits cleanly and logs that the NAS mirror is disabled.

## Roles & responsibilities

- Developers: Push changes to GitHub. Avoid pushing large runtime artifacts or credentials. Use LFS for large files.
- Maintainers (Ops):
  - Manage the `NAS_SSH_KEY` secret in GitHub (deploy key with limited write access, rotated periodically).
  - Rotate any credentials found in historical commits prior to a force-push of scrubbed history.
  - Validate scrubbed bundles and keep backups in `_backups/` until final confirmation.

## Risks & mitigations

- Risk: Credentials might remain in forks or external clones even after a scrub. Mitigation: rotate any exposed credentials immediately and notify impacted services.
- Risk: LFS objects may be missing on the NAS. Mitigation: Pin LFS to GitHub so objects remain available on GitHub; NAS remains a Git mirror only (no LFS hosting expectation).
- Risk: Accidental push of runtime venvs or HA storage. Mitigation: CI guards (size check, symlink forbids) and `.gitignore`/workspace excludes.

## Audit & rollback

- All destructive operations were performed on mirror clones; pre-scrub and scrubbed bundles were stored in `_backups/`.
- To rollback to pre-scrub state, restore from the pre-scrub bundle and push to a protected review branch for analysis.

## Appendix: key artifacts generated during migration

- `_backups/omega_registry-pre-scrub.bundle` — original bundle (~171MB)
- `_backups/omega_registry-cleaned-mirror.bundle` — cleaned mirror (~3.3MB)
- `_backups/omega_registry-scrubbed.bundle` — final scrubbed bundle (~3.3MB)
- `.github/workflows/mirror-to-nas.yml` — key-gated NAS mirror workflow
- `addon/docs/git_remote_strategy.md` — remote topology and LFS pin guidance

## Assumptions & Preconditions (visible & explicit)

These assumptions were made during the migration and must be validated before any destructive operation (force-push) is attempted. If any assumption is false, stop and escalate.

- The scrub and rewrite tools are available on the machine performing the operation (for example, `git-filter-repo` or an approved history-rewrite binary). Confirm with `git filter-repo --version` or equivalent.
- A recent, offline backup bundle exists and is retained in `_backups/` (for example: `_backups/omega_registry-pre-scrub.bundle`). Do not delete it.
- The person performing the push has repository admin privileges on GitHub and permission to force-push branches (or an agreed escalation path exists).
- Credential rotation (all tokens, secrets, deploy keys) will be performed prior to pushing scrubbed history to any public remote. This requires coordination with service owners and must be completed before Step 8 (Push scrubbed refs) above.
- Git LFS objects are expected to remain hosted on GitHub; the NAS is treated as a Git mirror only and is not relied on to serve LFS objects to clients.
- The scrub is accepted to leave redaction placeholders like `REDACTED` in files; this is intentional. If the true secret must be replaced with a runtime secret retrieval mechanism, that is a separate engineering change.

If you are uncertain about any of the above, do not proceed with a forced push. Use a review branch instead (see "Safe push alternative" below).

## Hardened checks & pre-push checklist

Run these checks and mark them green before syncing scrubbed refs to GitHub.

1) Validate tool availability

```bash
command -v git >/dev/null || { echo "git missing"; exit 1; }
command -v git-filter-repo >/dev/null || echo "git-filter-repo not found; ensure you have an approved rewrite tool"
git lfs env || true
```

2) Confirm and inspect backups (do not proceed if missing)

```bash
ls -lh _backups/omega_registry-pre-scrub.bundle
ls -lh _backups/omega_registry-scrubbed.bundle
```

3) Sanity-check for large files (local working tree)

```bash
git ls-files -z | xargs -0 -I{} sh -c 'test -f "{}" && wc -c < "{}" | awk -v f="{}" "{print \$1, f}"' | sort -nr | head -n 50
```

4) Run repository scans for token-like patterns in the scrubbed working-tree (repeat with several regexes)

```bash
grep -R --line-number -I -E "(gho_[A-Za-z0-9_]{36}|ghp_[A-Za-z0-9_]{36}|access_token|refresh_token|client_secret|password|nabu.casa)" /tmp/omega_registry-scrub-wt || true
```

5) Confirm GitHub push-protection checks and secret-scanning findings have been addressed for any flagged commit. Use the GitHub UI and your organization's security process.

6) Validate LFS pointers in the scrubbed mirror (confirm expected objects are present on GitHub after a dry push to a review ref)

```bash
# Example: push only refs/heads/main -> refs/heads/scrubbed-main-review (see safe alternative)
git -C /tmp/omega_registry-scrub.git push --force https://github.com/<org>/<repo>.git refs/heads/main:refs/heads/scrubbed-main-review
# Then inspect repo on GitHub to ensure LFS pointers exist and web UI doesn't show missing objects
```

7) Final sign-off: at least two maintainers (ops + security) must sign off in a comment on the review branch or in an internal ticket before the final force-push to core refs.

## Safe push alternative (recommended intermediate step)

Never force-push scrubbed history straight to `main` immediately. Instead, push scrubbed refs to a review branch and use that branch for human and CI validation.

```bash
# push scrubbed main to a review branch on GitHub to allow validation without touching protected refs
git -C /tmp/omega_registry-scrub.git push --force https://github.com/<org>/<repo>.git refs/heads/main:refs/heads/scrubbed-main-review
git -C /tmp/omega_registry-scrub.git push --force https://github.com/<org>/<repo>.git --tags
```

Use the review branch for:
- Running CI (validate-adrs, lint, size-checks)
- Running secret-scan tools (GitHub secret scanning, internal SAST)
- Letting other maintainers inspect the scrubbed tree and confirm redactions

After review and rotations, if everything is green, escalate to an admin to perform the replace of `main` (or merge the review branch according to your governance policy).

## Notes about limitations and residual risks (be explicit)

- Historical secrets may persist in forks, previously cloned mirrors, or third-party mirrors. Rotating secrets is the only reliable mitigation for secrets already leaked.
- Replace-text rewrites are pattern-based and may miss atypical encodings (base64-wrapped tokens, partial strings across binary blobs). Confirm with multiple regexes and manual inspection when in doubt.
- LFS objects referenced prior to the scrub that were never pushed to GitHub (for example, stored only on the NAS or local developer machines) may no longer be available after the history rewrite if you rely on the NAS for LFS. This is why we pin LFS to GitHub and avoid relying on Synology for LFS object storage.

## Minimal acceptance criteria for final push

- `scrubbed-main-review` branch present on GitHub and visible to maintainers.
- CI run on `scrubbed-main-review` completes successfully (validate-adrs + size checks + ruff or similar).
- No secret-scan alerts remaining for the commits in the `scrubbed-main-review` branch.
- Ops confirms credentials rotated for all services flagged in pre-scan.
- Backups (`_backups/`) verified and retained.

Once the above are satisfied, a privileged maintainer can replace `main` with the scrubbed history as agreed by governance.

