# Timeout triage

Runbook ID: `RB-TIMEOUT`

Use when an operation exceeds its deadline or a completion event is absent.

1. Confirm the request and completion identifiers match.
2. Compare elapsed time with the configured deadline.
3. Inspect queue depth, downstream availability, and retry count.
4. Capture the first timeout and the immediately preceding state transition.
5. Retry only when the operation is documented as idempotent.

Do not infer a hardware root cause from a timeout alone. Route mixed evidence to
manual review.

