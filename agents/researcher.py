from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from config import settings, RESEARCHER_PROMPT
from tools import search_web, search_hotels_amadeus  # ← replaced visit_website + search_hotels
from utils import logger
from typing import Dict, Any


class ResearcherAgent:
    """
    Researcher Agent - executes hotel research using Amadeus API + web search.
    Limited to top 5 results for speed and token efficiency.
    """

    def __init__(self):
        self.model = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",  # ← 30K TPM free
            temperature=settings.model_temperature,
            api_key=settings.groq_api_key
        )
        self.system_prompt = RESEARCHER_PROMPT
        self.tools = [search_hotels_amadeus]  

        # Cap iterations to prevent runaway loops + token overflow
        self.agent = create_react_agent(
            self.model,
            self.tools,
            
        )

    def conduct_research(self, plan: str, query: str) -> Dict[str, Any]:
        try:
            logger.info("Researcher Agent: Starting research")

            research_prompt = f"""Research Plan:
{plan}

Original Query: {query}

Use search_hotels_amadeus for real-time hotel prices and availability.
Use search_web only if you need additional context (reviews, area info).
Return top 5 results only. Be concise."""

            response = self.agent.invoke({
                "messages": [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=research_prompt)
                ]
            }, config={"recursion_limit": 30})

            findings = response["messages"][-1].content

            tool_calls = []
            for msg in response["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_calls.extend(msg.tool_calls)

            logger.info(f"Researcher Agent: Research complete ({len(tool_calls)} tool calls)")

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