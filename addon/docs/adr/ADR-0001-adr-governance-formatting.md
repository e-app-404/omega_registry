---
id: ADR-0001
title: "ADR-0001: ADR Governance, Redaction, and Formatting Policy"
date: 2025-09-21
status: Accepted
author:
  - "Evert Appels"
related: []
supersedes: []
last_updated: 2025-09-21
tags: ["governance", "formatting", "redaction", "tokens", "automation", "adr", "policy", "metadata"]
---

# ADR-0001: ADR Governance, Redaction, and Formatting Policy

## Table of Contents

1. Context
2. Decision
3. Lifecycle & Status Model
4. Identification, Slugs, and Filenames
5. Required Front-Matter (Schema v1)
6. Formatting Standards
7. Machine-Parseable Blocks
8. Enforcement
9. Token Block

## 1. Context

The project requires robust, machine-friendly governance for ADRs, including clear rules for redaction, definition, generation, and formatting. This ensures consistency, auditability, and automation for all architectural decisions.

## 2. Decision

- All ADRs must comply with a standardized structure, formatting, and machine-parseability requirements.
- Redaction, definition, and generation of ADRs must follow explicit, documented procedures.
- Token blocks and machine-parseable markers are mandatory for governance automation.

## 3. Lifecycle & Status Model

**Allowed `status` values (canonical):**

- `Draft` → `Proposed` → `Accepted` → (`Amended`)\* → `Deprecated` → `Superseded`
- Terminal: `Rejected`, `Withdrawn`

**Rules**

- Only `Draft` and `Proposed` may change text substantially without a superseding ADR.
- Moving from `Accepted` requires either `Amended`, `Deprecated`, or `Superseded` with links.

**Maintenance fields**

- `last_updated` (ISO-8601) MUST change on any edit.
- Optional: `last_reviewed` (ISO-8601) for periodic audits; ADRs older than 365 days SHOULD be reviewed.

## 4. Identification, Slugs, and Filenames

- **ID format**: `ADR-XXXX` (zero-padded, monotonically increasing).
- **Title format**: "ADR-XXXX: Short, Imperative Summary".
- **Slug**: derived from the short summary, kebab-case, ASCII only.
- **Filename**: `docs/ADR/ADR-XXXX-<slug>.md` (enforced by tooling).

## 5. Required Front-Matter (Schema v1)

Required keys: `title`, `date`, `status`, `author`, `related`, `supersedes`, `last_updated`

**YAML Formatting Rules**

- Use spaces only (no tabs) for YAML front-matter. Indent lists with two spaces per level.
- Required keys SHOULD appear in the order: `title`, `date`, `status`, `author`, `related`, `supersedes`, `last_updated`, `tags`.

## 6. Formatting Standards

- Use Markdown for all ADRs.
- Start with a YAML front-matter block containing required keys.
- Use clear section headers (`##`) for Context, Decision, Consequences, Enforcement, etc.
- Include a Table of Contents for ADRs longer than one page.

## 7. Machine-Parseable Blocks

- Every ADR that defines tokens, drift codes, or governance signals must include a fenced `TOKEN_BLOCK:` YAML code block at the end.
- CRTP markers, whitelists, and other governance signals must use fenced YAML/JSON blocks labeled with the marker type.

## 8. Enforcement

- Git hooks and CI must validate ADR structure, formatting, and presence of machine-parseable blocks.
- ADR index automation should extract metadata and token blocks for governance and reporting.

## 9. Token Block

```yaml
TOKEN_BLOCK:
  accepted:
    - ADR_FORMAT_OK
    - ADR_REDACTION_OK
    - ADR_GENERATION_OK
    - TOKEN_BLOCK_OK
  requires:
    - ADR_SCHEMA_V1
  drift:
    - DRIFT: adr_format_invalid
    - DRIFT: missing_token_block
    - DRIFT: adr_redaction_untracked
```

Last updated: 2025-09-21
