# GraphOWL ingestion SDK for Python

Push entities, relationships and extracted claims into [GraphOWL](https://github.com/graphowl/graphowl) from anything you can write Python against: a script, a scheduler job, a notebook.

- **No runtime dependencies.** Standard library only, so it never fights the packages already pinned in your environment.
- **Safe to retry.** Every push carries an idempotency key and a retry reuses it. `429` and `5xx` responses are retried with capped exponential backoff and jitter; nothing else is.
- **Partial success is reported, not hidden.** A push of up to 1,000 items returns a verdict per item; one bad row does not discard the rest.
- **Any size.** Larger inputs go up as a JSONL or CSV file and are processed as a job you can poll.

Status: **early access**, version 0.1.0. The API may change before 1.0; see the [changelog](https://github.com/graphowl/graphowl/blob/main/CHANGELOG.md).

## Install

```bash
pip install .      # from a checkout; not yet published to PyPI
```

Requires Python 3.10 or newer.

## Push

```python
from graph_owl_sdk import GraphOwlClient, IngestBuilder

client = GraphOwlClient(base_url="https://your-graphowl-host", token=TOKEN)

request = (
    IngestBuilder()
    .entity("service", "payments")
    .entity("database", "core", parent_fqn="payments")
    .entity("schema", "public", parent_fqn="payments.core")
    .entity("table", "orders", parent_fqn="payments.core.public")
    .build()
)
result = client.push(request)      # batching, keys and retries handled
```

A file, when there are more rows than one request can carry:

```python
handle = client.push_file(open("export.jsonl").read(), "jsonl")
job = client.await_job(handle["id"])
print(job["state"], job["accepted"], job["failures"][:5])
```

A job ends as `succeeded`, `failed`, or **`partial`**: some rows landed and some did not. `partial` is not a failure; read `failures` for the rows to fix.

## What your code should branch on

Errors are [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem documents.

| Status | Meaning | What to do |
|---|---|---|
| `207` | per-item outcomes | read `results`; some may have failed |
| `400` | the request is wrong | fix the code; do not retry |
| `409` | an idempotency key was reused for different content | fix the key generation |
| `429`, `5xx` | not now | retry with backoff; the SDK does |

Keys expire after 24 hours; a replay after that is a new request.

## Scoping

A push says what it is *about*, not what it is *not*. GraphOWL does not delete what your push omitted: "absent from this file" and "deleted at the source" are different facts, and only your adapter can tell them apart.

## Authenticate as a service

An adapter authenticates as itself, not as a person: create a service account in your identity provider with a client-credentials grant, grant it write access to the subtree it owns and nothing else, and pass its token as `token=`.

## Example

[`examples/csv_adapter.py`](examples/csv_adapter.py) is a complete adapter in one file: it reads a CSV of tables, builds the hierarchy, pushes it and reports what landed. It uses only the SDK's published surface, and a test asserts that.

```bash
python examples/csv_adapter.py --base-url https://your-graphowl-host examples/tables.csv
```

## Tests

```bash
pip install pytest
pytest
```

The tests run offline. `openapi.json` is a copy of the API description published in the GraphOWL repository; one test checks that every route this SDK calls is still declared there.

## Licence

[Apache-2.0](LICENSE). The GraphOWL name and logos are not covered by it; see the [brand terms](https://github.com/graphowl/graphowl/blob/main/brand/README.md).
