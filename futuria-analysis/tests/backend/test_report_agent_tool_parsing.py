from app.services.report_agent import ReportAgent


def test_parse_tool_calls_handles_wrapping_json():
    agent = object.__new__(ReportAgent)
    agent.VALID_TOOL_NAMES = {"insight_forge", "panorama_search", "quick_search", "interview_agents"}

    # format: <tool_call>{JSON}</tool_call>
    text = '<tool_call>{"name": "insight_forge", "parameters": {"query": "test"}}</tool_call>'
    calls = agent._parse_tool_calls(text)
    assert len(calls) == 1
    assert calls[0]["name"] == "insight_forge"


def test_parse_tool_calls_handles_lowercase_tool_name():
    agent = object.__new__(ReportAgent)
    agent.VALID_TOOL_NAMES = {"insight_forge", "panorama_search", "quick_search", "interview_agents"}

    # Model sometimes uses lowercase "tool_name" instead of "name"
    text = '<tool_call>{"tool_name": "insight_forge", "parameters": {"query": "test"}}</tool_call>'
    calls = agent._parse_tool_calls(text)
    assert len(calls) == 1
    assert calls[0]["name"] == "insight_forge"


def test_parse_tool_calls_handles_forge_mistype():
    agent = object.__new__(ReportAgent)
    agent.VALID_TOOL_NAMES = {"insight_forge", "panorama_search", "quick_search", "interview_agents"}

    # Model typed "insight_forage" instead of "insight_forge" - fuzzy match
    text = '<tool_call>{"name": "insight_forage", "parameters": {"query": "test"}}</tool_call>'
    calls = agent._parse_tool_calls(text)
    # Fuzzy match should correct the typo
    assert len(calls) == 1
    assert calls[0]["name"] == "insight_forge"