# Zoho incoming webhook: deployment gates

This receiver is not a replacement for the OAuth email CLI. All upstream files,
including its complete skill and MIT copyright, are preserved.

## Supported delivery

Uses the installed OpenClaw documented authenticated POST /hooks/agent contract:
Authorization: Bearer (dedicated hooks.token), Idempotency-Key, fixed agentId
jlp-support (Claire), sessionMode isolated, deliver false. A durable admitted row contains the
returned runId. HTTP 200 means admission, NOT completed intake or customer delivery.
No logger/file watcher is presented as delivery. Subject, sender and mail body
are never forwarded. Account/message IDs are metadata, not instructions.

The target Claire reader MUST have separately enforced read-only tool permissions
(no email/message send, exec, or write-capable integrations). A prompt instruction
or deliver:false does not restrict tools. Do not enable against an unrestricted
Claire agent. hooks.allowedAgentIds must permit ONLY jlp-support for this endpoint;
keep hooks.allowRequestSessionKey false and use a dedicated strong hook token.
These are rollout prerequisites, not configuration changes made by this PR.

## Explicit secret enrollment

Official contract: https://www.zoho.com/mail/help/dev-platform/webhook.html
Zoho provides x-hook-secret only on the initial registration POST. Do NOT expose
a first-use secret learning endpoint to the Internet. Register through a temporary
operator-controlled capture endpoint protected by a one-time unguessable URL and
network access restriction; obtain the first secret privately, validate the
registration signature against the exact raw bytes, pin it locally, then remove
the temporary capture path. Configure the final route with that pinned secret
before opening ingress. This program never trusts or stores x-hook-secret headers.
If Zoho needs a new registration POST, repeat the controlled enrollment procedure;
unsigned registration requests intentionally fail closed here. Do not put secrets
in repository files, logs, command-line arguments or this document.

The signature is the Base64 digest of HMAC-SHA256 over the FULL raw body, with no
sha256= prefix. Native payload uses zuid, messageId and folderId (not snake_case).
Route /zoho/<account> selects a preconfigured secret and pins the payload zuid.
Pin the verified Zoho REST account_id as well as zuid for each route; these are
different identifiers. Use distinct secrets/routes for two accounts. The account_id
is the durable ledger identity and is forwarded to Claire; route labels are not
account IDs. Never change account_id to reset processing history. All recipient aliases naturally
share account+message identity; do not filter on sender or alias address. Configure
the Zoho Mail condition for all incoming mail, not a selected recipient alias.
Do not enable Limited Data List unless a controlled validation confirms messageId
and zuid are present; the documented limited fields do not include those IDs.

## Durable processing and topology — BLOCKED until ownership is resolved

SQLite coordinates workers using the SAME local database, not Thumbo and AWS.
Do not activate independent receivers/workers or a delivering poller on both
hosts. This implementation intentionally requires explicit single-active and
non-delivering-polling attestations. It does not alter, disable or integrate the
existing polling/Claire intake. Existing delivering polling MUST remain untouched
until an operator-approved cutover or shared durable dedupe integration exists.
Deployment of files to both hosts is distinct from activation: keep one standby.
Both serve and worker fail closed by default. deployment_role must be active,
active_host must exactly equal this machine's hostname, and
read_only_policy_verified must be true before either starts. Configure the standby
with deployment_role standby and the SAME designated active_host as the active
host. These are startup interlocks and operator attestations, NOT a distributed
lease, a remote fencing check, or enforcement of Gateway tool permissions.
Never configure each host as its own active_host. Do not change role/host while
processes run: stop and prove old ingress/worker fenced before any promotion.
To preserve active delivering polling and enable webhooks simultaneously requires
a shared intake ledger/ownership mechanism integrated with that existing poller;
this PR alone cannot guarantee cross-host or poll/webhook exactly-once intake.

Rows are keyed permanently by account+message, independent of folder, timestamp,
body or alias. There is no automatic dedupe expiry. Receiver acknowledges only
after durable enqueue. Worker atomically commits sending before network I/O.
Transport, HTTP and invalid receipt failures become uncertain, never automatic
retry; crashed sending rows also remain held. Inspect Gateway receipt/run evidence
privately before any manual reconciliation. Never reset a held row speculatively.
Idempotency-Key is defense in depth, not durable exactly-once across Gateway
restart. Monitor pending/sending/uncertain rows without dumping mail or tokens.
Back up the database and preserve it on rollback; rollback must not replay rows.

## Local operation (only after above gates)

Use an owner-only config file outside the checkout (chmod 600), owner-only state
directory, persistent db_path, loopback listener and operator-managed TLS proxy.
No live services, cron, ingress or polling are modified by this PR.

Config shape (values below are illustrative, not deployable credentials):

    {
      "deployment_role": "standby",
      "active_host": "<one designated exact hostname on both hosts>",
      "read_only_policy_verified": false,
      "processing_owner": "single-active",
      "polling_mode": "non-delivering",
      "db_path": "/private/state/zoho-events.sqlite",
      "port": 8787,
      "hook_url": "http://127.0.0.1:18789/hooks/agent",
      "hook_token": "<dedicated long random hook token>",
      "accounts": {
        "primary": {"account_id": "<verified Zoho REST account ID>", "zuid": "<pinned zuid>", "secret": "<pre-enrolled secret>"},
        "secondary": {"account_id": "<second verified REST account ID>", "zuid": "<different pinned zuid>", "secret": "<different secret>"}
      }
    }

The example intentionally refuses startup. Only after all gates pass, explicitly
select active on ONE host and attest the enforced read-only policy. Run separate
processes with the SAME config/db:

    python scripts/zoho_webhook_handler.py serve --config /private/zoho.json
    python scripts/zoho_webhook_handler.py worker --config /private/zoho.json

Run synthetic local tests: python -m pytest -q tests
Live registration, target agent tool policy, all-alias Zoho rules, Gateway receipt
and final intake, and host ownership remain deployment acceptance checks. Do not
send customer test mail, retry held real messages, or claim these are verified.

## Minimal safe rollout on Thumbo and the existing AWS host

1. Install the identical reviewed revision on BOTH hosts, with standby configs,
   services stopped and ingress closed. Leave current polling/intake unchanged.
2. Privately verify two account_id/zuid mappings, all aliases, pinned secrets,
   protected enrollment, owner-only persistent storage, and the actual installed
   /hooks/agent contract. Enforce and test the jlp-support read-only tool policy
   (including delegated agents and inherited integration tools); an attestation
   alone does not establish it. This PR does not modify that agent's policy.
3. Use isolated synthetic IDs and a permitted read-only test target to verify
   real Gateway admission AND final intake, without customer mail or sending.
   Local mocked receipts are not this proof. Verify proxy body/header/time limits.
4. Schedule an approved cutover. Fence existing delivering polling and any other
   webhook owner, establish the old poller's processed-message boundary/import
   into the new ledger, and account for queued/delayed events. If no trustworthy
   ledger/boundary is available, keep webhook workers stopped: the standalone
   ledger cannot distinguish already-processed customer mail.
5. Activate ingress/worker on the designated host only. Keep the other standby.
   Monitor admission separately from completed processing; inspect held rows
   privately and never reset them blindly.
6. For failover, fence and stop the former active host, back up and transfer the
   complete SQLite database while quiescent, validate its event/receipt states,
   then change the single active_host designation on both hosts. If fencing or
   ledger transfer cannot be proved, do not promote. Never restore a stale empty
   ledger or restart delivering polling as an automatic rollback.
