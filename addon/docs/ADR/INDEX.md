# ADR Index

_Generated: 2025-09-22T00:37:24+0000_

| ADR        | Title                                   | Status     | Date       | Author                | Related         | Supersedes         | Last Updated | Token Block | Machine Block |
|------------|-----------------------------------------|------------|------------|-----------------------|-----------------|--------------------|--------------|-------------|--------------|
| [ADR-000x-template.md](ADR-000x-template.md) | ADR-000x: Example Policy | Draft | 2025-08-27 |  |  |  | 2025-09-05 | - | - |
| [ADR-0001-adr-governance-formatting.md](ADR-0001-adr-governance-formatting.md) | ADR-0001: ADR Governance, Redaction, and Formatting Policy | Accepted | 2025-09-21 | Evert Appels |  |  | 2025-09-21 | TOKEN_BLOCK: accepted: - ADR_FORMAT_OK - ADR_REDACTION_OK - ADR_GENERATION_OK - TOKEN_BLOCK_OK requires: - ADR_SCHEMA_V1 drift: - DRIFT: adr_format_invalid - DRIFT: missing_token_block - DRIFT: adr_redaction_untracked | - |
| [ADR-0002-automation-and-migration-governance.md](ADR-0002-automation-and-migration-governance.md) | ADR-0002: Automation & Migration Governance | Accepted | 2025-09-22 | Evert Appels | ADR-0001 |  | 2025-09-22 | TOKEN_BLOCK: accepted: - ADR_AUTOMATION_OK - ADR_MIGRATION_SAFE requires: - ADR-0001 produces: - MIGRATION_REPORT_JSON drift: - DRIFT: automation_disabled - DRIFT: missing_backups | - |
| [ADR-0003-workspace-shape-io-strategy.md](ADR-0003-workspace-shape-io-strategy.md) | ADR-0003: Workspace Shape and I/O Strategy | Accepted | 2025-09-22 | Evert Appels | ADR-0001,ADR-0002 |  | 2025-09-22 | TOKEN_BLOCK: accepted: - ADR_WORKSPACE_IO_OK - ADR_AUTOMATION_OK requires: - ADR-0001 - ADR-0002 produces: - IMPORT_SAFETY_REPORT drift: - DRIFT: import_time_io_detected - DRIFT: scripts_unimportable | - |
