"""LangChain Tools for SteelVision Repair Agent"""

from typing import Dict, Any, Type, ClassVar, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from config import settings


class TaobaoSearchInput(BaseModel):
    defect_type: str = Field(description="缺陷类型，如'划痕'、'夹杂物'、'补丁'")


class SearchTaobaoTool(BaseTool):
    name: str = "search_taobao_materials"
    description: str = "搜索修复材料及DIY步骤。输入缺陷类型，返回推荐材料和修复步骤。"
    args_schema: Type[BaseModel] = TaobaoSearchInput

    DIY_STEPS_MAP: ClassVar[Dict[str, List[str]]] = {
        "划痕": [
            "1. 用清水和洗车液彻底清洁划痕区域，确保无尘无油。",
            "2. 使用2000目砂纸蘸水轻轻打磨划痕周边，使表面平整。",
            "3. 均匀涂抹划痕修复剂，等待15-20分钟自然干燥。",
            "4. 用抛光蜡配合超细纤维布进行圆周抛光，直至恢复光泽。",
            "5. 最后涂一层车漆保护剂，防止二次损伤。",
        ],
        "夹杂物": [
            "1. 使用高压水枪冲洗表面，去除松散杂质。",
            "2. 涂抹去污泥/清洗剂，用海绵均匀擦拭夹杂区域。",
            "3. 静置5分钟后用清水冲洗干净，检查是否残留。",
            "4. 若有锈迹，使用除锈剂处理并涂抹防锈底漆。",
            "5. 待完全干燥后喷涂匹配颜色的面漆。",
        ],
        "补丁": [
            "1. 用砂纸打磨补丁区域，使表面粗糙增加附着力。",
            "2. 清洁打磨区域，去除所有粉尘和油污。",
            "3. 均匀涂抹原子灰/腻子，用刮板刮平表面。",
            "4. 待腻子完全干燥后，用由粗到细的砂纸逐级打磨至光滑。",
            "5. 喷涂底漆后再喷面漆，最后打蜡抛光。",
        ],
    }
    DEFAULT_DIY_STEPS: ClassVar[List[str]] = [
        "1. 彻底清洁受损表面，确保无尘、无油、无水分。",
        "2. 根据缺陷类型选择合适的修复材料，按说明书调配。",
        "3. 均匀涂抹修复材料，用刮板或刷子刮平。",
        "4. 等待材料完全固化（参照产品说明的时间）。",
        "5. 用砂纸逐级打磨并抛光，恢复表面光洁度。",
    ]

    MATERIAL_SUGGESTIONS: ClassVar[Dict[str, List[str]]] = {
        "划痕": ["划痕修复剂", "抛光蜡", "超细纤维布", "汽车补漆笔"],
        "夹杂物": ["去污泥", "清洗剂", "除锈剂", "防锈底漆"],
        "补丁": ["汽车补漆笔", "砂纸", "原子灰", "喷漆罐"],
        "形变": ["钣金修复工具", "拉锤", "车身填料"],
        "裂纹": ["环氧树脂胶", "玻璃纤维布", "砂纸"],
    }

    def _run(self, defect_type: str) -> Dict[str, Any]:
        materials = self.MATERIAL_SUGGESTIONS.get(defect_type, ["通用修复材料", "汽车清洁剂", "多功能修复膏"])
        steps = self.DIY_STEPS_MAP.get(defect_type, self.DEFAULT_DIY_STEPS)
        mock_shops = ["车仆官方旗舰店", "3M汽车用品专营店", "固特异汽车养护店"]
        materials_list = []
        for i, mat in enumerate(materials[:3]):
            materials_list.append({
                "item": f"【正品】{mat} - {defect_type}专用",
                "shop": mock_shops[i],
                "link": f"https://s.taobao.com/search?q={mat.replace(' ', '+')}",
            })
        return {"materials_list": materials_list, "diy_steps": steps}

    async def _arun(self, defect_type: str) -> Dict[str, Any]:
        return self._run(defect_type)


class MapNavigationInput(BaseModel):
    query: str = Field(description="搜索关键词，如'汽修店'或'汽车修理厂'")


class MapNavigationTool(BaseTool):
    name: str = "find_nearby_repair_shops"
    description: str = "搜索附近汽修店。返回汽修店名称、地址、距离、导航链接。"
    args_schema: Type[BaseModel] = MapNavigationInput

    def _run(self, query: str) -> Dict[str, Any]:
        shops = [
            {"name": "诚信汽修服务中心", "address": "北京市朝阳区建国路88号", "distance": "2.5km",
             "navigation_link": "https://uri.amap.com/navigation?to=116.46,39.90,诚信汽修服务中心"},
            {"name": "专业汽车美容养护", "address": "北京市海淀区中关村大街15号", "distance": "3.1km",
             "navigation_link": "https://uri.amap.com/navigation?to=116.32,39.98,专业汽车美容养护"},
            {"name": "快速钣金喷漆中心", "address": "北京市丰台区西三环南路12号", "distance": "4.0km",
             "navigation_link": "https://uri.amap.com/navigation?to=116.30,39.86,快速钣金喷漆中心"},
        ]
        return {"repair_shops": shops}

    async def _arun(self, query: str) -> Dict[str, Any]:
        return self._run(query)
