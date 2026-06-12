"""SteelVision Repair Agent — LangChain multi-LLM Agent with fallback"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple

from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

from config import settings
from tools import SearchTaobaoTool, MapNavigationTool


def _build_llm_clients() -> list:
    """Build available LLM clients, ordered by priority"""
    clients = []

    if settings.DEEPSEEK_API_KEY and "YOUR_DEEPSEEK" not in settings.DEEPSEEK_API_KEY:
        clients.append({
            "name": "deepseek",
            "llm": ChatOpenAI(
                model=getattr(settings, "DEEPSEEK_MODEL", "deepseek-chat"),
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL.rstrip("/"),
                temperature=0.3,
            ),
        })

    if settings.KIMI_API_KEY and "YOUR_KIMI" not in settings.KIMI_API_KEY:
        clients.append({
            "name": "kimi",
            "llm": ChatOpenAI(
                model=getattr(settings, "KIMI_MODEL", "moonshot-v1-8k"),
                api_key=settings.KIMI_API_KEY,
                base_url=settings.KIMI_BASE_URL.rstrip("/"),
                temperature=0.3,
            ),
        })

    if settings.DOUBAO_API_KEY and "YOUR_DOUBAO" not in settings.DOUBAO_API_KEY:
        clients.append({
            "name": "doubao",
            "llm": ChatOpenAI(
                model=getattr(settings, "DOUBAO_MODEL", "doubao-pro-32k"),
                api_key=settings.DOUBAO_API_KEY,
                base_url=settings.DOUBAO_BASE_URL.rstrip("/"),
                temperature=0.3,
            ),
        })

    if settings.GEMINI_API_KEY and "YOUR_GEMINI" not in settings.GEMINI_API_KEY:
        clients.append({
            "name": "gemini",
            "llm": ChatGoogleGenerativeAI(
                model=getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash"),
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.3,
            ),
        })

    return clients


SYSTEM_PROMPT = """你是一个车辆零部件缺陷检测维修专家。
根据检测到的缺陷信息，判断应该 DIY 自行修复还是前往专业汽修店。

决策规则：
- 轻微划痕、小夹杂物、小补丁 → DIY
- 严重形变、裂纹、大面积损伤 → AutoShop
- 无法确定 → AutoShop

可用工具：
- search_taobao_materials: 搜索修复材料和DIY步骤（DIY 时使用）
- find_nearby_repair_shops: 搜索附近汽修店（AutoShop 时使用）

最终返回 JSON 格式：
{"advice_type": "DIY或AutoShop", "advice_content": "完整建议内容（含材料/步骤或店铺信息）"}
"""


class RepairAgent:
    """智能维修决策 Agent，多 LLM 自动降级，LangChain Tool calling"""

    def __init__(self):
        self.tools: list = [SearchTaobaoTool(), MapNavigationTool()]
        self.llm_clients = _build_llm_clients()
        if not self.llm_clients:
            print("Warning: 未配置有效的 LLM API Key，AI Agent 将使用规则引擎回退。")

    async def decide_and_advise(
        self,
        detection_result: Dict[str, Any],
        user_location: Tuple[float, float] = (39.9042, 116.4074),
    ) -> Dict[str, Any]:
        """根据 CV 检测结果，决定维修方案并生成建议"""
        defect_description = detection_result.get("result_str", "未知缺陷")
        detected_classes = detection_result.get("detected_classes", [])

        if not self.llm_clients:
            return self._rule_based_result(defect_description, detected_classes)

        for client_info in self.llm_clients:
            try:
                return await self._agent_decide(client_info, defect_description, detected_classes, user_location)
            except Exception as e:
                print(f"{client_info['name']} 调用失败，尝试下一个: {e}")
                continue

        print("所有 LLM 调用失败，回退到规则引擎")
        return self._rule_based_result(defect_description, detected_classes)

    async def _agent_decide(
        self,
        client_info: dict,
        defect_description: str,
        detected_classes: list,
        user_location: Tuple[float, float],
    ) -> Dict[str, Any]:
        """使用 LangChain Agent 进行决策"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", (
                f"检测到的缺陷：{defect_description}\n"
                f"缺陷类别列表：{', '.join(detected_classes) if detected_classes else '无'}\n"
                f"用户位置坐标：({user_location[0]}, {user_location[1]})\n"
                f"请判断应该 DIY 还是去汽修店，并给出具体建议。"
            )),
        ])

        agent = create_tool_calling_agent(client_info["llm"], self.tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, tools=self.tools, verbose=False,
            handle_parsing_errors=True, max_iterations=3,
        )

        result = await agent_executor.ainvoke({
            "input": f"检测到 {defect_description}，请给出维修建议。",
        })

        output = result.get("output", "")
        return self._parse_agent_output(output, defect_description, detected_classes)

    def _parse_agent_output(self, raw: str, defect_description: str, detected_classes: list) -> Dict[str, Any]:
        """解析 Agent 输出，提取 JSON 决策"""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r'\{[^{}]*"advice_type"[^{}]*\}', raw, re.DOTALL)
            try:
                data = json.loads(m.group()) if m else {}
            except json.JSONDecodeError:
                data = {}

        advice_type = data.get("advice_type", "AutoShop")
        advice_content = data.get("advice_content", "")

        if not advice_content:
            if advice_type == "DIY":
                advice_content = f"检测到 {defect_description}，建议尝试DIY修复。请使用搜索工具查找合适的修复材料。"
            else:
                advice_content = f"检测到 {defect_description}，建议前往专业汽修店进行修复。请使用地图工具搜索附近的修理厂。"

        return {"advice_type": advice_type, "advice_content": advice_content}

    def _rule_based_result(self, defect_description: str, detected_classes: list) -> Dict[str, Any]:
        """规则引擎回退 — 不依赖 LLM"""
        severe_keywords = ["形变", "裂纹", "大面积", "严重"]
        is_severe = any(kw in cls for cls in detected_classes for kw in severe_keywords)

        if is_severe:
            return {
                "advice_type": "AutoShop",
                "advice_content": (
                    f"检测到 {defect_description}，属于较严重的缺陷，建议前往专业汽修店修复。\n\n"
                    "推荐汽修店:\n"
                    "- 诚信汽修服务中心 (地址: 北京市朝阳区建国路88号, 距离: 2.5km)\n"
                    "- 专业汽车美容养护 (地址: 北京市海淀区中关村大街15号, 距离: 3.1km)\n"
                    "- 快速钣金喷漆中心 (地址: 北京市丰台区西三环南路12号, 距离: 4.0km)"
                ),
            }
        else:
            taobao = SearchTaobaoTool()
            result = taobao._run(defect_description)
            materials = "\n".join(f"- {m['item']} (店铺: {m['shop']})" for m in result["materials_list"])
            steps = "\n".join(result["diy_steps"])
            return {
                "advice_type": "DIY",
                "advice_content": (
                    f"检测到 {defect_description}，建议您尝试DIY修复。\n\n"
                    f"**推荐材料**:\n{materials}\n\n"
                    f"**详细修复步骤**:\n{steps}"
                ),
            }
