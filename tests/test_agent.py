import asyncio

import pytest

from agent import RepairAgent, _build_llm_clients


@pytest.fixture
def agent():
    return RepairAgent()


def test_diy_for_scratch(agent):
    result = asyncio.run(agent.decide_and_advise(
        {"result_str": "划痕", "detected_classes": ["划痕"]}
    ))
    assert result["advice_type"] == "DIY"
    assert "划痕" in result["advice_content"]


def test_diy_for_inclusion(agent):
    result = asyncio.run(agent.decide_and_advise(
        {"result_str": "夹杂物", "detected_classes": ["夹杂物"]}
    ))
    assert result["advice_type"] == "DIY"
    assert "夹杂物" in result["advice_content"]


def test_no_defect(agent):
    result = asyncio.run(agent.decide_and_advise(
        {"result_str": "无缺陷", "detected_classes": []}
    ))
    assert "advice_type" in result


def test_parse_valid_json(agent):
    raw = '{"advice_type": "DIY", "advice_content": "用抛光蜡处理"}'
    result = agent._parse_agent_output(raw, "划痕", ["划痕"])
    assert result["advice_type"] == "DIY"
    assert "抛光蜡" in result["advice_content"]


def test_parse_json_with_markdown_wrapper(agent):
    raw = '```json\n{"advice_type": "AutoShop", "advice_content": "去修理厂"}\n```'
    result = agent._parse_agent_output(raw, "划痕", ["划痕"])
    assert result["advice_type"] == "AutoShop"
    assert "修理厂" in result["advice_content"]


def test_parse_invalid_falls_back(agent):
    raw = '乱七八糟的乱码输出'
    result = agent._parse_agent_output(raw, "裂纹", ["裂纹"])
    assert "advice_type" in result


def test_build_llm_clients_returns_list():
    clients = _build_llm_clients()
    assert isinstance(clients, list)


def test_build_llm_clients_has_required_keys():
    clients = _build_llm_clients()
    for c in clients:
        assert "name" in c
        assert "llm" in c
