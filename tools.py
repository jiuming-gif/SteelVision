import hashlib
import time
from typing import Dict, Any, List, Optional

import httpx

from config import settings


class SearchTaobaoTool:
    """淘宝/电商材料搜索工具，支持真实 API 和 mock 回退"""

    # 按缺陷类型预设的修复步骤
    DIY_STEPS_MAP = {
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
    DEFAULT_DIY_STEPS = [
        "1. 彻底清洁受损表面，确保无尘、无油、无水分。",
        "2. 根据缺陷类型选择合适的修复材料，按说明书调配。",
        "3. 均匀涂抹修复材料，用刮板或刷子刮平。",
        "4. 等待材料完全固化（参照产品说明的时间）。",
        "5. 用砂纸逐级打磨并抛光，恢复表面光洁度。",
    ]

    async def search(
        self, defect_type: str, material_suggestions: List[str]
    ) -> Dict[str, Any]:
        """
        搜索修复材料。优先尝试真实淘宝 API，失败则返回上下文相关的 mock 数据。
        """
        # 尝试调用真实 API（如果配置了密钥）
        taobao_api_key = getattr(settings, "TAOBAO_API_KEY", "")
        if taobao_api_key and "YOUR_TAOBAO" not in taobao_api_key:
            try:
                return await self._search_real(defect_type, material_suggestions)
            except Exception as e:
                print(f"淘宝 API 调用失败，使用 mock 数据: {e}")

        return self._search_mock(defect_type, material_suggestions)

    async def _search_real(
        self, defect_type: str, material_suggestions: List[str]
    ) -> Dict[str, Any]:
        """真实淘宝/电商 API 搜索（需配置 TAOBAO_API_KEY）"""
        # 淘宝开放平台 API 端点 (需具体对接)
        # 这里使用通用搜索 API 模式
        keyword = "汽车 " + " ".join(material_suggestions[:3])
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            resp = await client.get(
                "https://eco.taobao.com/router/rest",
                params={
                    "method": "taobao.tbk.item.get",
                    "app_key": getattr(settings, "TAOBAO_API_KEY", ""),
                    "q": keyword,
                    "format": "json",
                },
            )
            # 解析真实结果...
            _ = resp  # 实际对接时实现解析逻辑
        # 回退到 mock
        return self._search_mock(defect_type, material_suggestions)

    def _search_mock(
        self, defect_type: str, material_suggestions: List[str]
    ) -> Dict[str, Any]:
        """生成上下文相关的 mock 搜索结果"""
        mock_shops = [
            ("车仆官方旗舰店", "https://s.taobao.com/search?q={}"),
            ("3M汽车用品专营店", "https://s.taobao.com/search?q={}"),
            ("固特异汽车养护店", "https://s.taobao.com/search?q={}"),
        ]
        materials_list = []
        for i, material in enumerate(material_suggestions[:3]):
            shop_name, link_tpl = mock_shops[i % len(mock_shops)]
            materials_list.append({
                "item": f"【正品】{material} - {defect_type}专用",
                "shop": shop_name,
                "link": link_tpl.format(material.replace(" ", "+")),
            })

        diy_steps = self.DIY_STEPS_MAP.get(defect_type, self.DEFAULT_DIY_STEPS)

        return {
            "materials_list": materials_list,
            "diy_steps": diy_steps,
        }


class MapNavigationTool:
    """地图导航工具，搜索附近汽修店，支持高德/百度地图 API 和 mock 回退"""

    # 模拟汽修店数据（按城市区域）
    MOCK_SHOPS = {
        "beijing": [
            {"name": "诚信汽修服务中心", "address": "北京市朝阳区建国路88号", "distance": "2.5km"},
            {"name": "专业汽车美容养护", "address": "北京市海淀区中关村大街15号", "distance": "3.1km"},
            {"name": "快速钣金喷漆中心", "address": "北京市丰台区西三环南路12号", "distance": "4.0km"},
        ],
        "default": [
            {"name": "诚信汽修服务中心", "address": "XX路YY号", "distance": "2.5km"},
            {"name": "专业汽车美容养护", "address": "AA街BB号", "distance": "3.1km"},
            {"name": "快速钣金喷漆中心", "address": "ZZ大道CC号", "distance": "4.0km"},
        ],
    }

    async def find_nearby_repair_shops(
        self, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        """
        搜索附近汽修店。优先尝试高德地图 API，失败则返回 mock 数据。
        """
        amap_key = getattr(settings, "AMAP_API_KEY", "")
        if amap_key and "YOUR_AMAP" not in amap_key:
            try:
                return await self._search_amap(latitude, longitude, amap_key)
            except Exception as e:
                print(f"高德地图 API 调用失败，使用 mock 数据: {e}")

        return self._search_mock(latitude, longitude)

    async def _search_amap(
        self, latitude: float, longitude: float, api_key: str
    ) -> Dict[str, Any]:
        """真实高德地图 POI 搜索"""
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            resp = await client.get(
                "https://restapi.amap.com/v3/place/around",
                params={
                    "key": api_key,
                    "location": f"{longitude},{latitude}",
                    "radius": 5000,
                    "keywords": "汽修|汽车修理|汽车美容",
                    "types": "汽车服务",
                    "offset": 5,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "1" and data.get("pois"):
                    shops = []
                    for poi in data["pois"][:3]:
                        name = poi.get("name", "未知")
                        address = poi.get("address", "未知地址")
                        distance = poi.get("distance", "未知")
                        if distance != "未知":
                            distance = f"{int(distance)}m" if int(distance) < 1000 else f"{int(distance)/1000:.1f}km"
                        shops.append({
                            "name": name,
                            "address": address,
                            "distance": distance,
                            "navigation_link": f"https://uri.amap.com/navigation?to={longitude},{latitude},{name}",
                        })
                    return {"repair_shops": shops}
        # 失败回退
        return self._search_mock(latitude, longitude)

    def _search_mock(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """生成基于坐标的 mock 结果"""
        # 尝试根据坐标判断城市（简化：北京范围）
        if 39.4 < latitude < 40.2 and 115.7 < longitude < 117.0:
            shops = self.MOCK_SHOPS["beijing"]
        else:
            shops = self.MOCK_SHOPS["default"]

        # 附加基于坐标的导航链接
        result_shops = []
        for shop in shops:
            shop_copy = dict(shop)
            shop_copy["navigation_link"] = (
                f"https://uri.amap.com/navigation?"
                f"from={longitude},{latitude}&to={shop['address']}"
            )
            result_shops.append(shop_copy)

        return {"repair_shops": result_shops}
