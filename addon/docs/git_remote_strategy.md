# Git Remote Strategy - Omega Registry Workspace

## Instructions

Please fill out the YAML (one per project) plus the diagnostics snippets’ outputs, so we can:

    •	Propose the remote topology (which remotes push vs fetch-only, and why)
    •	Drop in guardrails (validators, CI checks, size/symlink/nested-git gates)
    •	Provide NAS/Tailnet mirror settings (incl. Synology ACL notes)
    •	Generate a tailored .env.sample, workspace samples, and acceptance tests
    •	Specify merge & backup strategy (snapshot branches/tags) aligned with your ADR-0016 rules

⸻

## Requirements checklist

1. Repo basics
   • Purpose & runtime context (addon, registry, docs only, etc.)
   • Default branch, branching model (trunk, GitFlow, release branches)
   • Where it’s hosted now (GitHub/GitLab/Synology bare repo/path)

2. Remote topology & network
   • All remotes (URLs, which one is primary for push)
   • Will a NAS/Tailnet mirror be used? If yes: host/IP, path, shell restrictions (e.g., Synology git-shell)
   • Who pushes from where (LAN only? Tailnet allowed? fetch-only mirrors?)

3. Access & governance
   • Users/roles that need push/pull
   • Protected branches/tags requirements
   • Commit signing (required? GPG/Sigstore?)
   • PR requirements (reviewers, checks that must pass)

4. Files & storage
   • Expected large/binary artifacts (need Git LFS?)
   • Biggest files / size caps you want enforced
   • Any submodules / vendored repos
   • Symlinks expected or forbidden?

5. Workspace & paths
   • Any absolute paths hard-coded (e.g., /config, /data, /n/ha) that should be parametric or intentionally literal (containers often require literal /config//data)
   • Do you want an .env.sample and validators like we added to HA?

6. CI/CD & automation
   • Existing CI (GitHub Actions, etc.) and what must run on PRs
   • Build/release packaging (tags/semver), changelog policy, artifact publishing

7. NAS specifics (if mirroring)
   • Bare repo path on NAS (e.g., /volume1/git-mirrors/<name>.git)
   • Ownership/ACL expectations (gituser:users, g+rx on parents)
   • Whether Synology Git package wrappers are in play (fetch-only advisories, etc.)

8. Backup & recovery
   • Mirror/backup cadence (push on every main? nightly? tags only?)
   • Snapshot/backup branches/tags you want (e.g., backup/<name>-<ts>)

⸻

## Quick diagnostics (commands)

```bash
git remote -v
git rev-parse --abbrev-ref HEAD
git config --get init.defaultBranch || true
git branch -r | sed -n '1,50p'
git lfs env 2>/dev/null | sed -n '1,80p' || echo "no-git-lfs"
git submodule status 2>/dev/null || echo "no-submodules"
git config --list | grep -E 'user.signingkey|commit.gpgsign|tag.gpgsign' || true
# size & risk checks
git ls-files -z | xargs -0 -I{} sh -c 'test -f "{}" && wc -c < "{}" | awk -v f="{}" "{print \$1, f}"' \
  | sort -nr | head -20
# symlinks & nested repos
find . -type l | sed -n '1,120p'
find . -type d -name .git -not -path "./.git" | sed -n '1,120p'
# path policy probes
grep -R -n --exclude-dir=".git" -E '/config|/data|/n/ha' . | sed -n '1,120p' || true
# CI presence
ls -la .github/workflows 2>/dev/null || echo "no-ci"
```

⸻

## Omega Registry Workspace Config Info

```yaml
project: "Omega Registry (BB8 Addon)"
purpose: "addon & registry (primary: addon)"
default_branch: "main"
branch_model: "trunk"
remotes:
  primary_push: "ssh://gituser@ds220plus.reverse-beta.ts.net/volume1/git/omega_registry.git"
  additional:
    - name: "origin"
      url: "ssh://gituser@ds220plus.reverse-beta.ts.net/volume1/git/omega_registry.git"
      push: true
    - name: "github"
      url: "https://github.com/e-app-404/omega_registry.git"
      push: true
network:
  lan_ip: "192.168.0.104"
  tailnet_ip: "100.x.y.z"
  synology_git_shell_wrapped: true
governance:
  protected_branches: ["main", "chore/restructure-to-addon"]
  commit_signing_required: false
  pr_checks_required: ["validate-adrs", "ruff"]
files:
  expects_large_binaries: true
  git_lfs_needed: true
  allows_symlinks: false
paths:
  uses_container_literals: true
  must_parameterize_host_paths: true
ci_cd:
  platform: "github-actions"
  release_tags: "semver"
nas_mirror:
  path: "/volume1/git-mirrors/omega_registry.git"
  owner: "gituser:users"
  parents_g_rx: true
backup_policy:
  push_to_mirror_on: ["main"]
  create_backup_tags: true
```

## Diagnostics Output

```json
{
  "git -C /Users/evertappels/Projects/omega_registry remote -v": {
    "rc": 0,
    "stdout": "github\thttps://github.com/e-app-404/omega_registry.git (fetch)\ngithub\thttps://github.com/e-app-404/omega_registry.git (push)\norigin\tssh://gituser@ds220plus.reverse-beta.ts.net/volume1/git/omega_registry.git (fetch)\norigin\tssh://gituser@ds220plus.reverse-beta.ts.net/volume1/git/omega_registry.git (push)",
    "stderr": ""
  },
  "git -C /Users/evertappels/Projects/omega_registry rev-parse --abbrev-ref HEAD": {
    "rc": 0,
    "stdout": "chore/restructure-to-addon",
    "stderr": ""
  },
  "git -C /Users/evertappels/Projects/omega_registry config --get init.defaultBranch": {
    "rc": 0,
    "stdout": "main",
    "stderr": ""
  },
  "git -C /Users/evertappels/Projects/omega_registry branch -r": {
    "rc": 0,
    "stdout": "",
    "stderr": ""
  },
  "git -C /Users/evertappels/Projects/omega_registry lfs env": {
    "rc": 0,
    "stdout": "git-lfs/3.7.0 (GitHub; darwin arm64; go 1.24.4)\ngit version 2.39.5 (Apple Git-154)\n\nEndpoint=https://ds220plus.reverse-beta.ts.net/volume1/git/omega_registry.git/info/lfs (auth=none)\n  SSH=gituser@ds220plus.reverse-beta.ts.net:/volume1/git/omega_registry.git\nEndpoint (github)=https://github.com/e-app-404/omega_registry.git/info/lfs (auth=none)\nLocalWorkingDir=/Users/evertappels/Projects/omega_registry\nLocalGitDir=/Users/evertappels/Projects/omega_registry/.git\nLocalGitStorageDir=/Users/evertappels/Projects/omega_registry/.git\nLocalMediaDir=/Users/evertappels/Projects/omega_registry/.git/lfs/objects\nLocalReferenceDirs=\nTempDir=/Users/evertappels/Projects/omega_registry/.git/lfs/tmp\nConcurrentTransfers=8\nTusTransfers=false\nBasicTransfersOnly=false\nSkipDownloadErrors=false\nFetchRecentAlways=false\nFetchRecentRefsDays=7\nFetchRecentCommitsDays=0\nFetchRecentRefsIncludeRemotes=true\nPruneOffsetDays=3\nPruneVerifyRemoteAlways=false\nPruneVerifyUnreachableAlways=false\nPruneRemoteName=origin\nLfsStorageDir=/Users/evertappels/Projects/omega_registry/.git/lfs\nAccessDownload=none\nAccessUpload=none\nDownloadTransfers=basic,lfs-standalone-file,ssh\nUploadTransfers=basic,lfs-standalone-file,ssh\nGIT_EXEC_PATH=/Applications/Xcode.app/Contents/Developer/usr/libexec/git-core\ngit config filter.lfs.process = \"git-lfs filter-process\"\ngit config filter.lfs.smudge = \"git-lfs smudge -- %f\"\ngit config filter.lfs.clean = \"git-lfs clean -- %f\"",
    "stderr": ""
  },
  "git -C /Users/evertappels/Projects/omega_registry submodule status": {
    "rc": 0,
    "stdout": "",
    "stderr": ""
  },
  "git -C /Users/evertappels/Projects/omega_registry config --list": {
    "rc": 0,
    "stdout": "credential.helper=osxkeychain\ninit.defaultbranch=main\ncredential.helper=osxkeychain\nuser.email=evert.app@proton.me\nuser.name=Evert Appels\nfilter.lfs.clean=git-lfs clean -- %f\nfilter.lfs.smudge=git-lfs smudge -- %f\nfilter.lfs.process=git-lfs filter-process\nfilter.lfs.required=true\ncore.repositoryformatversion=0\ncore.filemode=true\ncore.bare=false\ncore.logallrefupdates=true\ncore.ignorecase=true\ncore.precomposeunicode=true\nremote.github.url=https://github.com/e-app-404/omega_registry.git\nremote.github.fetch=+refs/heads/*:refs/remotes/github/*\nlfs.repositoryformatversion=0\nremote.origin.url=ssh://gituser@ds220plus.reverse-beta.ts.net/volume1/git/omega_registry.git\nremote.origin.fetch=+refs/heads/*:refs/remotes/origin/*",
    "stderr": ""
  },
  "largest_files": [
    [5615054, "addon/canonical/logs/diagnostics/trace_overlay.omega.json"],
    [4766716, "addon/output/pre_reboot_entities.combined.json"],
    [
      3679607,
      "addon/output/migration_diagnostics/pre_reboot_entities_by_source.json"
    ],
    [
      3679607,
      "addon/output/fingerprinting_run/pre_reboot_entities_by_source.json"
    ],
    [
      3000064,
      "addon/output/alpha_tier/alpha_cluster_schema_validation_report.json"
    ],
    [2674701, "addon/input/pre-reboot.ha_registries/core.entity_registry"],
    [
      2674701,
      "addon/canonical/enrichment_sources/ha_registries/pre-reboot/core.entity_registry"
    ],
    [2228610, "addon/output/alpha_tier/cluster_assignment_trace.json"],
    [
      2005009,
      "addon/canonical/logs/audit/join_path/join_path_audit.pretty.json"
    ],
    [
      1788294,
      "addon/canonical/logs/audit/contract_compliance/contract_compliance_report.pretty.json"
    ],
    [1770546, "addon/output/mappings/entity_id_migration_map.rosetta.v5.json"],
    [1770546, "addon/input/mappings/entity_id_migration_map.rosetta.v5.json"],
    [1622911, "addon/canonical/omega_registry_master.json"],
    [1599960, "addon/canonical/logs/audit/join_path/join_path_audit.json"],
    [1590038, "addon/output/omega_registry_master.json"],
    [
      1416207,
      "addon/canonical/logs/audit/contract_compliance/contract_compliance_report.json"
    ],
    [1393500, "addon/input/storage_0720/core.entity_registry"],
    [1390263, "addon/input/core.entity_registry"],
    [1318371, "addon/output/debug_join_graph_omega_registry.jsonl"],
    [1292516, "addon/input/post-reboot.ha_registries/core.entity_registry"]
  ],
  "symlinks": "/Users/evertappels/Projects/omega_registry/.venv\n/Users/evertappels/Projects/omega_registry/addon/output/debug/venv/bin/python3\n/Users/evertappels/Projects/omega_registry/addon/output/debug/venv/bin/python\n/Users/evertappels/Projects/omega_registry/addon/output/debug/venv/bin/python3.13\n/Users/evertappels/Projects/omega_registry/addon/.venv/bin/python3\n/Users/evertappels/Projects/omega_registry/addon/.venv/bin/python\n/Users/evertappels/Projects/omega_registry/addon/.venv/bin/python3.13\n/Users/evertappels/Projects/omega_registry/addon/.indexvenv/bin/python3\n/Users/evertappels/Projects/omega_registry/addon/.indexvenv/bin/python\n/Users/evertappels/Projects/omega_registry/addon/.indexvenv/bin/python3.13\n/Users/evertappels/Projects/omega_registry/venv/bin/python3\n/Users/evertappels/Projects/omega_registry/venv/bin/python\n/Users/evertappels/Projects/omega_registry/venv/bin/python3.13",
  "nested_git": "",
  "ci": "total 8\ndrwxr-xr-x@ 3 evertappels  staff    96 Sep 22 01:37 .\ndrwxr-xr-x@ 3 evertappels  staff    96 Sep 22 01:37 ..\n-rw-r--r--@ 1 evertappels  staff  1136 Sep 22 12:23 validate-adrs.yml"
}
```

⸻

## Decision

### Overview

Omega Registry — GitHub-primary, NAS mirror (main + tags)

### Why

- GitHub provides stable Git LFS hosting and integrated CI (we require "validate-adrs" and "ruff").
- Synology's git-shell and server-side hook support for LFS is brittle; mirroring keeps on-prem durability without relying on Synology for LFS storage.
- Pin LFS to GitHub so LFS objects are consistently stored on GitHub even if someone pushes to the NAS.

### Net effect

- Developers push to GitHub by default.
- CI or a manual job mirrors main + tags to the NAS for on-prem backup.
- LFS is stable and uniform (no Synology LFS surprises).

### Minimal, safe changes (summary)

- Keep the existing Synology `origin`, but restrict its push refs to main and tags (or make it fetch-only).
- Use `github` as the primary push remote.
- Add a `.lfsconfig` to pin LFS storage to GitHub.

### Commands (run from repository root)

```bash
git lfs install
cat > .lfsconfig <<'CFG'
[lfs]
    url = https://github.com/e-app-404/omega_registry.git/info/lfs
CFG
git add .lfsconfig
git commit -m "lfs: pin LFS storage to GitHub"

git remote set-url github https://github.com/e-app-404/omega_registry.git
git push -u github HEAD:main
git push github --tags

git config remote.origin.push "+refs/heads/main:refs/heads/main"
git config --add remote.origin.push "+refs/tags/*:refs/tags/*"
```

### Optional: CI mirror (GitHub Actions)

Add `.github/workflows/mirror-to-nas.yml` with the following job to mirror main+tags to your NAS:

```yaml
name: Mirror main+tags to NAS
on:
  push:
    branches: [main]
    tags: ["*"]
jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Push to NAS
        env:
          NAS_URL: ssh://gituser@ds220plus.reverse-beta.ts.net/volume1/git/omega_registry.git
          GIT_SSH_COMMAND: ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10
        run: |
          git remote add nas "$NAS_URL" || true
          git push nas main --tags
```

Keep the size/symlink guard (from HA) enabled in CI to prevent accidental commits of venvs or large artifacts.

⸻

## Setup Block

```
set -euo pipefail
cd "$HOME/Projects/omega_registry"

git lfs install

cat > .lfsconfig <<'CFG'
[lfs]
        url = https://github.com/e-app-404/omega_registry.git/info/lfs
CFG
git add .lfsconfig
git commit -m "lfs: pin LFS storage to GitHub" || true

git remote set-url github https://github.com/e-app-404/omega_registry.git
git remote set-url origin ssh://gituser@ds220plus.reverse-beta.ts.net/volume1/git/omega_registry.git

git push -u github HEAD:main
git push github --tags

git config --unset-all remote.origin.push || true
git config --add remote.origin.push +refs/heads/main:refs/heads/main
git config --add remote.origin.push +refs/tags/*:refs/tags/*

mkdir -p .github/workflows
cat > .github/workflows/mirror-to-nas.yml <<'YML'
name: Mirror main+tags to NAS
on:
  push:
    branches: [main]
    tags: ["*"]
jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Push to NAS
        env:
          NAS_URL: ssh://gituser@ds220plus.reverse-beta.ts.net/volume1/git/omega_registry.git
          GIT_SSH_COMMAND: ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10
        run: |
          git remote add nas "$NAS_URL" || true
          git push nas main --tags
YML
git add .github/workflows/mirror-to-nas.yml
git commit -m "ci: mirror main+tags to NAS" || true
git push -u github HEAD:main
```

## Setup Block v2

```
#!/usr/bin/env bash
set -euo pipefail

# 0) Ensure repo + create safety backup bundle
git rev-parse --is-inside-work-tree >/dev/null
cd "$(git rev-parse --show-toplevel)"
git bundle create ../omega_registry-before-lfs-pin.bundle --all

# 1) Work on a feature branch (no direct main changes)
BRANCH="chore/lfs-pin-and-mirror"
if git show-ref --quiet "refs/heads/$BRANCH"; then
  git switch "$BRANCH"
else
  git switch -c "$BRANCH"
fi

# 2) Pin LFS to GitHub (local install to avoid global side-effects)
git lfs install --local

mkdir -p .github/workflows

cat > .lfsconfig <<'CFG'
[lfs]
  url = https://github.com/e-app-404/omega_registry.git/info/lfs
CFG

# Append LFS defaults if not already present
if ! grep -q "BEGIN LFS DEFAULTS" .gitattributes 2>/dev/null; then
  cat >> .gitattributes <<'ATTR'
# ----- BEGIN LFS DEFAULTS -----
*.json filter=lfs diff=lfs merge=lfs -text
*.jsonl filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
*.tar.gz filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
# ----- END LFS DEFAULTS -----
ATTR
fi

# 3) Ensure remotes (idempotent)
git remote add github https://github.com/e-app-404/omega_registry.git 2>/dev/null || true
git remote set-url github https://github.com/e-app-404/omega_registry.git

git remote add origin ssh://gituser@ds220plus.reverse-beta.ts.net/volume1/git/omega_registry.git 2>/dev/null || true
git remote set-url origin ssh://gituser@ds220plus.reverse-beta.ts.net/volume1/git/omega_registry.git

# Limit what we push to NAS-origin from this clone (main + tags only)
git config --unset-all remote.origin.push || true
git config --add remote.origin.push "+refs/heads/main:refs/heads/main"
git config --add remote.origin.push "+refs/tags/*:refs/tags/*"

# 4) CI workflow: mirror main + tags to NAS when a deploy key secret is present
cat > .github/workflows/mirror-to-nas.yml <<'YML'
name: Mirror main + tags to NAS
on:
  push:
    branches: [ main ]
  workflow_dispatch:
jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Load NAS deploy key
        if: ${{ secrets.NAS_SSH_KEY }}
        uses: webfactory/ssh-agent@v0.8.0
        with:
          ssh-private-key: ${{ secrets.NAS_SSH_KEY }}
      - name: Push to NAS
        if: ${{ secrets.NAS_SSH_KEY }}
        env:
          NAS_URL: ssh://gituser@ds220plus.reverse-beta.ts.net/volume1/git/omega_registry.git
          GIT_SSH_COMMAND: ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10
        run: |
          git remote add nas "$NAS_URL" || true
          git push nas main --tags
          echo "Pushed main + tags to NAS"
          git ls-remote nas refs/heads/main refs/tags/* | sed -n '1,50p' || true
      - name: Preflight: check NAS reachability
        if: ${{ secrets.NAS_SSH_KEY }}
        env:
          GIT_SSH_COMMAND: ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10
        run: |
          ssh -o BatchMode=yes gituser@ds220plus.reverse-beta.ts.net 'echo OK_NAS'
      - name: Note if disabled
        if: ${{ !secrets.NAS_SSH_KEY }}
        run: echo "NAS mirror disabled (missing NAS_SSH_KEY secret). Workflow exited cleanly."
YML

# 5) Commit only if something changed, then push feature branch to GitHub
git add .lfsconfig .gitattributes .github/workflows/mirror-to-nas.yml || true
# ensure .gitattributes explicitly staged before commit
git add .gitattributes || true
if [ -n "$(git status --porcelain)" ]; then
  git commit -m "chore(omega): pin LFS to GitHub; add defaults; NAS mirror workflow (key-gated)"
else
  echo "No changes to commit."
fi

# verify github remote reachable before pushing branch
if git ls-remote --exit-code github HEAD >/dev/null 2>&1; then
  git push -u github "$BRANCH"
  echo "✅ Done. Branch '$BRANCH' pushed to GitHub. Open a PR to merge into main."
  echo "ℹ️ After merge, set repo secret NAS_SSH_KEY (private deploy key with write access to the NAS bare repo) to enable mirroring."
else
  echo "❌ Cannot reach 'github' remote (git ls-remote failed). Branch not pushed. Check network / remote URL." >&2
fi
```
