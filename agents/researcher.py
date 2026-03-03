from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from config import settings, RESEARCHER_PROMPT
from tools.search_tool import search_web
from tools.visit_website import visit_website
from utils import logger
from typing import Dict, Any


class ResearcherAgent:
    """
    Researcher Agent - uses search_web + visit_website for hotel discovery.
    No Amadeus API here — Amadeus lives in the n8n verification layer only.
    """

    def __init__(self):
        self.model = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=settings.model_temperature,
            api_key=settings.groq_api_key
        )
        self.system_prompt = RESEARCHER_PROMPT
        self.tools = [search_web, visit_website]

        self.agent = create_react_agent(
            self.model,
            self.tools
        )

    def conduct_research(self, plan: str, query: str) -> Dict[str, Any]:
        try:
            logger.info("Researcher Agent: Starting research with search tools")

            research_prompt = f"""Research Plan:
{plan}

Original Query: {query}

Instructions:
- Use search_web to find hotels matching the query
- Use visit_website only if you need pricing details from a specific page
- Call search_web ONCE with a clear query like "best hotels in Paris under $2000 per night"
- Return top 5 hotels only in this EXACT format, nothing else:

- Hotel Name | ~$price/night | City, Country

Rules:
- NO numbered lists
- NO citations or sources
- NO TripAdvisor/Booking.com footnotes
- NO intro or closing text
- Just the 5 bullet lines"""

            response = self.agent.invoke(
                {
                    "messages": [
                        SystemMessage(content=self.system_prompt),
                        HumanMessage(content=research_prompt)
                    ]
                },
                config={"recursion_limit": 15}
            )

            findings = response["messages"][-1].content

            tool_calls = []
            for msg in response["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_calls.extend(msg.tool_calls)

            logger.info(f"Researcher Agent: Complete ({len(tool_calls)} tool calls)")

            return {
                "findings": findings,
                "tool_calls": tool_calls,
                "agent": "researcher",
                "success": True
            }

        except Exception as e:
            logger.error(f"Researcher Agent failed: {e}")
            return {
                "findings": f"Error during research: {str(e)}",
                "tool_calls": [],
                "agent": "researcher",
                "success": False,
                "error": str(e)
            }

    def __call__(self, plan: str, query: str) -> Dict[str, Any]:
        return self.conduct_research(plan, query)