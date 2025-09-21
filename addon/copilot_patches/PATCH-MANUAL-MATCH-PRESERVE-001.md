# 🧩 PATCH ID: PATCH-MANUAL-MATCH-PRESERVE-001

## OBJECTIVE

Prevent accidental overwriting of `manual_confirmed_matches.json` when no confirmed entries exist during a reconciliation run.

## CHANGES

1. **Preserve Logic**
   - When loading `manual_confirmed_matches.json`, store a backup in memory (`manual_confirmed_backup`) if file exists and is non-empty.
   - Before writing to disk, check:

     ```python
     if manual_confirmed:
         write as usual
     else:
         print("⚠️ Skipping overwrite: no confirmed matches to write.")
         skip writing to avoid flushing previous state.
     ```

2. **Optional Override**
   - Accept a `--force-overwrite` CLI flag (or config boolean) that allows flushing even if empty.

3. **Logging**
   - Emit warning when skip occurs and log it in `conversation_full_history.log`.

## EXPECTED RESULT

- Ensures `manual_confirmed_matches.json` is never blanked due to an empty run.
- All legitimate confirmations persist across reconciliation sessions unless explicitly cleared.

---

Please confirm patch implementation and readiness to rerun reconciliation safely.
