"""The contract-drift test

Reads the ``openapi.json`` published in the GraphOWL repository. Refresh it when the API
description changes; this test then says whether the SDK still matches.
"""

from __future__ import annotations

import json
from pathlib import Path

from graphowl_ingest import CONTRACT_VERSION, REQUIRED_PATHS

CONTRACT = json.loads(
    (Path(__file__).resolve().parents[1] / "openapi.json").read_text(encoding="utf-8")
)


def test_the_sdk_is_pinned_to_the_contract_the_service_publishes() -> None:
    assert CONTRACT["info"]["version"] == CONTRACT_VERSION


def test_every_path_this_sdk_calls_is_still_declared() -> None:
    for path in REQUIRED_PATHS:
        assert path in CONTRACT["paths"]


def test_a_push_still_answers_207_and_a_batch_upload_202() -> None:
    """Both are 2xx, so a contract that swapped them would break the client
    silently — `push` treats 207 as per-item outcomes and `push_file` treats 202
    as a handle."""
    assert "207" in CONTRACT["paths"]["/ingest"]["post"]["responses"]
    assert "202" in CONTRACT["paths"]["/ingest/batch"]["post"]["responses"]
