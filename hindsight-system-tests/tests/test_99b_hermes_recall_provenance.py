"""A retained source survives the public API/SDK/Hermes rendering boundary.

The provider tests cover multi-bank retrieval and default-format compatibility.
This story guards the seam those fake responses cannot: actual SDK source fields
returned by a real server remain usable after Hermes formats the recalled fact.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from hindsight_system_tests.payloads import consolidation, extracted, fact

pytestmark = pytest.mark.asyncio


async def test_recalled_source_can_identify_its_retained_document(client, llm, bank_id, settled):
    note = "Alice decided to keep the blue prototype after the design review."
    document = "design-review"
    llm.on_step("extract_facts", contains="blue prototype").returns(extracted(fact(note, who="Alice")))
    llm.on_step("consolidate").returns(consolidation())
    await client.aretain(bank_id=bank_id, content=note, document_id=document)
    await settled(bank_id)
    recalled = await client.arecall(
        bank_id=bank_id, query="Alice blue prototype decision", types=["world"], budget="low"
    )
    assert recalled.results, "the source must exist for the provenance assertion to mean anything"
    matching = [r for r in recalled.results if r.document_id == document]
    assert matching, "the public SDK response must identify the retained document"

    # Load the pure production formatter without importing or faking Hermes core.
    path = Path(__file__).resolve().parents[2] / "hindsight-integrations/hermes/provenance.py"
    spec = importlib.util.spec_from_file_location("hermes_provenance_system_story", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        rendered = json.loads(module.with_provenance(matching[0], bank_id).render())
    finally:
        sys.modules.pop(spec.name, None)

    assert rendered["text"] == matching[0].text
    assert rendered["source"]["bank_id"] == bank_id
    assert rendered["source"]["document_id"] == document
    assert rendered["source"]["memory_id"] == matching[0].id
    assert rendered["source"]["fact_type"] == matching[0].type
    for name in ("occurred_start", "occurred_end", "mentioned_at"):
        value = getattr(matching[0], name)
        assert rendered["source"][name] == (value.isoformat() if hasattr(value, "isoformat") else value)
    originals = await client.documents.list_documents(bank_id)
    assert document in [d.id for d in originals.items]
