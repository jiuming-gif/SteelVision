import asyncio

from tools import SearchTaobaoTool, MapNavigationTool


def test_search_taobao_has_name():
    tool = SearchTaobaoTool()
    assert tool.name == "search_taobao_materials"


def test_search_scratch():
    tool = SearchTaobaoTool()
    result = tool._run("划痕")
    assert "materials_list" in result
    assert "diy_steps" in result
    materials = [m["item"] for m in result["materials_list"]]
    assert any("抛光蜡" in m for m in materials)


def test_search_unknown_defect():
    tool = SearchTaobaoTool()
    result = tool._run("未知")
    assert "materials_list" in result
    assert "diy_steps" in result


def test_search_patch():
    tool = SearchTaobaoTool()
    result = tool._run("补丁")
    materials = [m["item"] for m in result["materials_list"]]
    assert any("补漆笔" in m or "砂纸" in m for m in materials)


def test_search_arun_same_as_run():
    tool = SearchTaobaoTool()
    sync_result = tool._run("划痕")
    async_result = asyncio.run(tool._arun("划痕"))
    assert sync_result == async_result


def test_map_has_name():
    tool = MapNavigationTool()
    assert tool.name == "find_nearby_repair_shops"


def test_find_shops():
    tool = MapNavigationTool()
    result = tool._run("汽修店")
    shops = result["repair_shops"]
    assert len(shops) == 3
    for shop in shops:
        assert "name" in shop
        assert "address" in shop
        assert "navigation_link" in shop


def test_map_arun_same_as_run():
    tool = MapNavigationTool()
    sync_result = tool._run("汽修店")
    async_result = asyncio.run(tool._arun("汽修店"))
    assert sync_result == async_result
