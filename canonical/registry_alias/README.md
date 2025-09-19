# ALIAS OVERVIEW

---

**Canonical Output Notice:**

- The `canonical/registry_alias/` directory contains only pretty-printed or audit trail versions of the Omega Registry Master. These are not used in the pipeline and are strictly for human readability or historical reference.
- `omega_registry_master.pretty.json` is for human readability only and must not be used for programmatic or pipeline operations.
- All validation, analytics, diagnostics, audits, and post-processing scripts must operate on the canonical output (`omega_registry_master.json`) only.

The `canonical/alias/` directory contains alternative versions of the Omega Registry Master. These versions are not used in the current pipeline but are retained for audit trail and historical reference.

[omega_registry_master.pretty.json](canonical/alias/omega_registry_master.pretty.json) is a pretty-printed version of the Omega Registry Master, generated for easier human readability and debugging. It is not used in the pipeline but serves as a reference for developers and auditors.

Run the following command to generate the pretty-printed version:

```bash
python -m json.tool canonical/omega_registry_master.json > canonical/alias/omega_registry_master.pretty.json
```

This command formats the JSON file in a more readable way, making it easier to inspect the contents of the Omega Registry Master.
