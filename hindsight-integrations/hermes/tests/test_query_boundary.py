"""Drive automatic recall through the provider with the API's real BPE tokenizer."""

import logging

import hindsight_hermes as plugin
import pytest
import toktok
from conftest import FakeClient


@pytest.mark.parametrize("encoding", ["o200k_base", "cl100k_base", "o200k_harmony"])
@pytest.mark.parametrize("text", ["a " * 1000, "雪🙂x" * 700, "<|endoftext|>" * 150, "مرحبا naïve 東京 " * 150])
def test_long_input_reaches_recall_within_server_token_cap(provider, encoding, text):
    instance, fake = provider(
        {"recall_sync": True, "recall_max_input_chars": 2000, "recall_query_encoding": encoding},
        client=FakeClient(recall_texts=["remembered fact"]),
    )
    assert toktok.batch_count([text[:2000]], encoding, threads=1)[0] > 500
    assert "remembered fact" in instance.prefetch(text)
    sent = fake.recalls[0]["query"]
    assert text.startswith(sent)
    assert "\ufffd" not in sent
    assert 490 <= toktok.batch_count([sent], encoding, threads=1)[0] <= 500
    instance.shutdown()


def test_short_query_is_unchanged(provider):
    instance, fake = provider({"recall_sync": True})
    query = "What did we decide about the launch?"
    instance.prefetch(query)
    assert fake.recalls[0]["query"] == query
    instance.shutdown()


def test_background_prefetch_bounds_the_query(provider):
    instance, fake = provider(
        {"prefetch_waits_for_retain": False, "recall_max_input_chars": 2000},
        client=FakeClient(recall_texts=["remembered fact"]),
    )
    instance.queue_prefetch("雪🙂x" * 700)
    instance._prefetch_thread.join(5)
    assert not instance._prefetch_thread.is_alive()
    assert "remembered fact" in instance.prefetch("next turn")
    assert 490 <= toktok.batch_count([fake.recalls[0]["query"]], "o200k_base", threads=1)[0] <= 500
    instance.shutdown()


@pytest.mark.parametrize("value", [None, ""])
def test_empty_encoding_uses_default(provider, value):
    instance, fake = provider({"recall_sync": True, "recall_query_encoding": value})
    instance.prefetch("normal question")
    assert instance._recall_query_encoding == "o200k_base"
    assert fake.recalls[0]["query"] == "normal question"
    instance.shutdown()


def test_multibank_error_does_not_log_private_response(provider, caplog):
    from test_multibank import _fake_recall

    caplog.set_level(logging.DEBUG)
    instance, _ = provider({"recall_sync": True, "bank_id": "primary", "recall_additional_banks": ["vault"]})
    _fake_recall(instance, {"primary": ["safe fact"], "vault": RuntimeError("PRIVATE_QUERY_AND_CREDENTIAL")})
    assert "safe fact" in instance.prefetch("private question")
    # Exercise both the first outage and the subsequent cooldown-expired path.
    instance._extra_bank_down_until[("recall", "vault")] = 0
    instance.prefetch("private question")
    assert "error_type=RuntimeError" in caplog.text
    assert "PRIVATE_QUERY_AND_CREDENTIAL" not in caplog.text
    assert "private question" not in caplog.text
    instance.shutdown()


def test_character_limit_still_precedes_token_limit(provider):
    instance, fake = provider({"recall_sync": True, "recall_max_input_chars": 8})
    instance.prefetch("hello there and more")
    assert fake.recalls[0]["query"] == "hello th"
    instance.shutdown()


def test_token_cap_can_be_explicitly_disabled(provider):
    instance, fake = provider({"recall_sync": True, "recall_max_input_chars": 0, "recall_max_input_tokens": 0})
    query = "a " * 1000
    instance.prefetch(query)
    assert fake.recalls[0]["query"] == query
    instance.shutdown()


def test_automatic_reflect_uses_the_same_query_boundary(provider):
    instance, fake = provider(
        {"recall_sync": True, "recall_prefetch_method": "reflect", "recall_max_input_chars": 2000},
        client=FakeClient(reflect_text="evidence-based answer"),
    )
    assert "evidence-based answer" in instance.prefetch("a " * 1000)
    assert toktok.batch_count([fake.reflects[0]["query"]], "o200k_base", threads=1)[0] <= 500
    instance.shutdown()


def test_explicit_recall_tool_keeps_its_query_contract(provider):
    instance, fake = provider({"recall_max_input_tokens": 3})
    query = "the explicit focused tool query is unchanged"
    instance.handle_tool_call("hindsight_recall", {"query": query})
    assert fake.recalls[0]["query"] == query
    instance.shutdown()


def test_empty_query_does_not_call_server(provider, caplog):
    caplog.set_level(logging.INFO)
    instance, fake = provider({"recall_sync": True})
    assert instance.prefetch(" \n ") == ""
    assert fake.recalls == []
    assert "outcome=empty_query" in caplog.text
    instance.shutdown()


def test_failed_recall_logs_classification_without_private_exception(provider, monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    instance, _ = provider({"recall_sync": True})

    def fail(query: str) -> list:
        raise RuntimeError("PRIVATE_QUERY_AND_CREDENTIAL")

    monkeypatch.setattr(instance, "_recall", fail)
    assert instance.prefetch("private question") == ""
    assert "outcome=error error_type=RuntimeError" in caplog.text
    assert "PRIVATE_QUERY_AND_CREDENTIAL" not in caplog.text
    assert "private question" not in caplog.text
    instance.shutdown()


def test_empty_result_and_success_have_distinct_metadata(provider, caplog):
    caplog.set_level(logging.INFO)
    empty, _ = provider({"recall_sync": True})
    assert empty.prefetch("question") == ""
    assert "outcome=empty count=0" in caplog.text
    empty.shutdown()
    caplog.clear()
    found, _ = provider({"recall_sync": True}, client=FakeClient(recall_texts=["private remembered fact"]))
    assert "private remembered fact" in found.prefetch("question")
    assert "outcome=success count=1" in caplog.text
    assert "private remembered fact" not in caplog.text
    found.shutdown()


@pytest.mark.parametrize("config", [{"recall_max_input_tokens": -1}, {"recall_query_encoding": "model-name"}])
def test_invalid_boundary_config_is_rejected(config):
    instance = plugin.HindsightMemoryProvider()
    with pytest.raises(ValueError):
        instance._apply_recall_settings(config)
