# Firmware compatibility triage

Runbook ID: `RB-FW`

Use when logs explicitly show incompatible firmware, API, schema, or image
versions.

1. Record expected and observed versions.
2. Verify the compatibility matrix and image provenance.
3. Check whether activation completed and whether rollback is supported.
4. Preserve hashes/signatures if present.
5. Do not recommend flashing or rollback unless the evidence and platform
   procedure support it.

