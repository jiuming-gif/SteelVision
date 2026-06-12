import asyncio
import json
import re
from typing import Dict, Any, List, Tuple, Optional

import httpx

from tools import SearchTaobaoTool, MapNavigationTool
from config import settings


class LLMClient:
    """真实的 LLM API 客户端，支持 OpenAI 兼容接口（DeepSeek / Kimi / Doubao）"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> str:
        """调用 OpenAI 兼容的 chat/completions 接口"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            if resp.status_code != 200:
                raise RuntimeError(f"LLM API 调用失败 ({resp.status_code}): {resp.text[:500]}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]


class GeminiClient:
    """Google Gemini API 客户端（原生 Gemini API 格式，非 OpenAI 兼容）"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> str:
        """调用 Gemini generateContent 接口"""
        import httpx
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            resp = await client.post(
                f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API 调用失败 ({resp.status_code}): {resp.text[:500]}")
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini 返回空响应")
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            return "".join(p.get("text", "") for p in parts)


class RepairAgent:
    """智能维修决策 Agent，集成 LLM 进行缺陷严重度评估和维修方案推荐"""

    # 缺陷类型 → 推荐材料映射
    MATERIAL_SUGGESTIONS = {
        "划痕": ["划痕修复剂", "抛光蜡", "超细纤维布", "汽车补漆笔"],
        "夹杂物": ["去污泥", "清洗剂", "除锈剂", "防锈底漆"],
        "补丁": ["汽车补漆笔", "砂纸", "原子灰", "喷漆罐"],
        "形变": ["钣金修复工具", "拉锤", "车身填料"],
        "裂纹": ["环氧树脂胶", "玻璃纤维布", "砂纸"],
    }

    def __init__(self):
        self.taobao_tool = SearchTaobaoTool()
        self.map_tool = MapNavigationTool()

        # 初始化 LLM 客户端
        self.llm_clients: Dict[str, LLMClient] = {}
        if settings.DEEPSEEK_API_KEY and "YOUR_DEEPSEEK_API_KEY" not in settings.DEEPSEEK_API_KEY:
            self.llm_clients["deepseek"] = LLMClient(
                settings.DEEPSEEK_API_KEY,
                settings.DEEPSEEK_BASE_URL,
                getattr(settings, "DEEPSEEK_MODEL", "deepseek-chat"),
            )
        if settings.KIMI_API_KEY and "YOUR_KIMI_API_KEY" not in settings.KIMI_API_KEY:
            self.llm_clients["kimi"] = LLMClient(
                settings.KIMI_API_KEY,
                settings.KIMI_BASE_URL,
                getattr(settings, "KIMI_MODEL", "moonshot-v1-8k"),
            )
        if settings.DOUBAO_API_KEY and "YOUR_DOUBAO_API_KEY" not in settings.DOUBAO_API_KEY:
            self.llm_clients["doubao"] = LLMClient(
                settings.DOUBAO_API_KEY,
                settings.DOUBAO_BASE_URL,
                getattr(settings, "DOUBAO_MODEL", "doubao-pro-32k"),
            )
        if settings.GEMINI_API_KEY and "YOUR_GEMINI" not in settings.GEMINI_API_KEY:
            self.llm_clients["gemini"] = GeminiClient(
                settings.GEMINI_API_KEY,
                getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash"),
            )

        if not self.llm_clients:
            print("Warning: 未配置有效的 LLM API Key，AI Agent 将使用规则引擎回退。")

    def _primary_llm(self) -> Optional[LLMClient]:
        """返回第一个可用的 LLM 客户端"""
        if self.llm_clients:
            return next(iter(self.llm_clients.values()))
        return None

    async def decide_and_advise(
        self,
        detection_result: Dict[str, Any],
        user_location: Tuple[float, float] = (39.9042, 116.4074),
    ) -> Dict[str, Any]:
        """根据 CV 检测结果，决定维修方案并生成建议"""
        defect_description = detection_result.get("result_str", "未知缺陷")
        detected_classes = detection_result.get("detected_classes", [])

        # 尝试用 LLM 决策
        llm = self._primary_llm()
        if llm:
            try:
                decision = await self._llm_decide(llm, defect_description, detected_classes)
            except Exception as e:
                print(f"LLM 调用失败，回退到规则引擎: {e}")
                decision = self._rule_based_decide(detected_classes)
        else:
            decision = self._rule_based_decide(detected_classes)

        # 构建建议内容
        advice_type = decision["advice_type"]
        if advice_type == "DIY":
            materials = self._suggest_materials(defect_description)
            taobao_results = await self.taobao_tool.search(defect_description, materials)
            advice_content = self._format_diy_advice(defect_description, taobao_results)
        else:
            latitude, longitude = user_location
            repair_shops = await self.map_tool.find_nearby_repair_shops(latitude, longitude)
            advice_content = self._format_autoshop_advice(defect_description, repair_shops)

        return {"advice_type": advice_type, "advice_content": advice_content}

    async def _llm_decide(
        self, llm: LLMClient, defect_description: str, detected_classes: List[str]
    ) -> Dict[str, str]:
        """使用 LLM 进行结构化决策"""
        system_prompt = (
            "你是一个车辆零部件缺陷检测维修专家。"
            "根据检测到的缺陷信息，判断应该 DIY 自行修复还是前往专业汽修店。"
            "请严格返回 JSON 格式，不要包含其他内容。"
        )
        prompt = (
            f"检测到的缺陷：{defect_description}\n"
            f"缺陷类别列表：{', '.join(detected_classes) if detected_classes else '无'}\n\n"
            f'请返回 JSON: {{"decision": "DIY或AutoShop", "severity": "轻微或中等或严重", "reason": "判断理由"}}'
        )

        raw = await llm.generate_response(prompt=prompt, system_prompt=system_prompt, temperature=0.3)
        return self._parse_llm_decision(raw)

    def _parse_llm_decision(self, raw: str) -> Dict[str, str]:
        """解析 LLM 返回的 JSON，失败则回退为规则引擎"""
        try:
            # 尝试直接解析
            data = json.loads(raw)
        except json.JSONDecodeError:
            # 尝试用正则提取 JSON 块
            m = re.search(r'\{[^{}]*"decision"[^{}]*\}', raw, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group())
                except json.JSONDecodeError:
                    data = {}
            else:
                data = {}

        decision = data.get("decision", "AutoShop")
        severity = data.get("severity", "中等")

        if "DIY" in decision:
            advice_type = "DIY"
        else:
            advice_type = "AutoShop"

        return {"advice_type": advice_type, "severity": severity}

    def _rule_based_decide(self, detected_classes: List[str]) -> Dict[str, str]:
        """规则引擎回退：根据缺陷类别判断严重程度"""
        severe_keywords = ["形变", "裂纹", "大面积", "严重"]
        mild_keywords = ["划痕", "夹杂物", "补丁"]

        is_severe = any(kw in cls for cls in detected_classes for kw in severe_keywords)
        is_mild = any(kw in cls for cls in detected_classes for kw in mild_keywords)

        if is_severe:
            return {"advice_type": "AutoShop", "severity": "严重"}
        elif is_mild:
            return {"advice_type": "DIY", "severity": "轻微"}
        else:
            return {"advice_type": "AutoShop", "severity": "中等"}

    def _suggest_materials(self, defect_description: str) -> List[str]:
        """根据缺陷描述匹配推荐材料"""
        for keyword, materials in self.MATERIAL_SUGGESTIONS.items():
            if keyword in defect_description:
                return materials
        return ["通用修复材料", "汽车清洁剂", "多功能修复膏"]

    def _format_diy_advice(self, defect_description: str, taobao_results: Dict[str, Any]) -> str:
        materials_list_str = "\n".join(
            f"- {m['item']} (店铺: {m['shop']}, 链接: {m['link']})"
            for m in taobao_results["materials_list"]
        )
        diy_steps_str = "\n".join(
            f"{idx + 1}. {step}" for idx, step in enumerate(taobao_results["diy_steps"])
        )
        return (
            f"**DIY修复建议**\n"
            f"检测到 {defect_description}，建议您尝试DIY修复。\n\n"
            f"**推荐材料及购买链接**:\n{materials_list_str}\n\n"
            f"**详细修复步骤**:\n{diy_steps_str}"
        )

    def _format_autoshop_advice(self, defect_description: str, repair_shops: Dict[str, Any]) -> str:
        shops_list_str = "\n".join(
            f"- {s['name']} (地址: {s['address']}, 距离: {s['distance']}, 导航: {s['navigation_link']})"
            for s in repair_shops["repair_shops"]
        )
        return (
            f"**汽修店专业修复建议**\n"
            f"检测到 {defect_description}，建议您前往专业汽修店进行修复。\n\n"
            f"**推荐汽修店**:\n{shops_list_str}"
        )
