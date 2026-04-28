from app.services.zep_graph_memory_updater import AgentActivity, ZepGraphMemoryUpdater


def _activity(content: str) -> AgentActivity:
    return AgentActivity(
        platform="reddit",
        agent_id=1,
        agent_name="agent",
        action_type="CREATE_POST",
        action_args={"content": content},
        round_num=1,
        timestamp="2026-01-01T00:00:00",
    )


def test_build_payload_batches_respects_max_text_size() -> None:
    updater = object.__new__(ZepGraphMemoryUpdater)
    updater.MAX_TEXT_PAYLOAD_CHARS = 100

    activities = [_activity("a" * 60), _activity("b" * 60), _activity("c" * 60)]

    payloads = updater._build_payload_batches(activities)

    assert len(payloads) >= 2
    assert all(len(payload) <= 100 for payload in payloads)


def test_build_payload_batches_truncates_single_oversized_activity() -> None:
    updater = object.__new__(ZepGraphMemoryUpdater)
    updater.MAX_TEXT_PAYLOAD_CHARS = 80

    payloads = updater._build_payload_batches([_activity("x" * 300)])

    assert len(payloads) == 1
    assert len(payloads[0]) <= 80
