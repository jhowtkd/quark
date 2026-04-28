from app.services.oasis_profile_generator import OasisProfileGenerator
from app.services.simulation_config_generator import SimulationConfigGenerator


def test_profile_progress_message_is_portuguese_without_cjk() -> None:
    generator = OasisProfileGenerator()

    message = generator._format_profile_progress_message(2, 56, "Luiz Gustavo Martins e Sousa", "Person")

    assert message == "Concluído 2/56: Luiz Gustavo Martins e Sousa (Person)"
    assert "已完成" not in message
    assert "（" not in message
    assert "）" not in message


def test_extract_json_payload_handles_think_tags_for_simulation_config() -> None:
    generator = SimulationConfigGenerator()

    payload = generator._extract_json_payload(
        """<think>reasoning</think>\n```json\n{\"reasoning\":\"ok\"}\n```"""
    )

    assert payload == '{"reasoning":"ok"}'


def test_normalize_reasoning_text_replaces_cjk_with_portuguese_fallback() -> None:
    generator = SimulationConfigGenerator()

    normalized = generator._normalize_reasoning_text(
        "目标群体为健身爱好者，晚间活跃度更高。",
        fallback="Configuração ajustada ao público e ao ritmo esperado da discussão.",
    )

    assert normalized == "Configuração ajustada ao público e ao ritmo esperado da discussão."
