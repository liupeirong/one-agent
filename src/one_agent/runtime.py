"""Agent invocation runtime for one-agent."""

import asyncio
from typing import Sequence

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from one_agent.config import Config
from one_agent.mcp_config import McpServer
from one_agent.mcp_servers import to_stdio_connection

# Maximum time we will wait for selected MCP servers to start and list their
# tools before failing the run. Keeps a misconfigured or hung server from
# blocking the console indefinitely (and from being orphaned if the user
# escapes with a hard kill).
_MCP_TOOL_LISTING_TIMEOUT_SECONDS = 30.0
_AGENT_EXECUTION_TIMEOUT_SECONDS = 120.0


def invoke(
    *,
    config: Config,
    prompt: str,
    system_instructions: str | None = None,
    mcp_servers: Sequence[McpServer] | None = None,
) -> str:
    """Run a single-shot LangChain agent invocation.

    Builds a ChatOpenAI model from *config* and always runs the agent on
    the async path inside a fresh event loop. When *mcp_servers* is
    non-empty, tools exposed by the selected servers are added to the
    agent; otherwise the agent runs with an empty tool list.
    """
    llm = _build_chat_model(config)
    servers = tuple(mcp_servers or ())
    return asyncio.run(_arun_agent(llm, prompt, system_instructions, servers))


def _build_chat_model(config: Config) -> ChatOpenAI:
    """Construct a ChatOpenAI client with API key or Entra ID credential."""
    model_kwargs: dict[str, object] = {}
    if config.openai_api_key:
        model_kwargs["api_key"] = config.openai_api_key
    else:
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )
        model_kwargs["api_key"] = token_provider

    return ChatOpenAI(
        model=config.openai_model,
        base_url=config.openai_base_url,
        **model_kwargs,
    )


async def _arun_agent(
    llm: ChatOpenAI,
    prompt: str,
    system_instructions: str | None,
    servers: tuple[McpServer, ...],
) -> str:
    """Run the agent inside a single event loop, optionally with MCP tools."""
    if not servers:
        state = await _ainvoke_agent(
            llm=llm,
            tools=[],
            prompt=prompt,
            system_instructions=system_instructions,
        )
        return _extract_final_message(state)

    connections = {server.name: to_stdio_connection(server) for server in servers}
    async with MultiServerMCPClient(connections) as client:
        tools: list[BaseTool] = await asyncio.wait_for(
            client.get_tools(),
            timeout=_MCP_TOOL_LISTING_TIMEOUT_SECONDS,
        )
        state = await _ainvoke_agent(
            llm=llm,
            tools=tools,
            prompt=prompt,
            system_instructions=system_instructions,
        )
    return _extract_final_message(state)


async def _ainvoke_agent(
    *,
    llm: ChatOpenAI,
    tools: list[BaseTool],
    prompt: str,
    system_instructions: str | None,
) -> dict:
    """Create and execute a LangChain agent with provided tools and prompt."""
    agent = create_agent(llm, tools, system_prompt=system_instructions or None)
    state = await asyncio.wait_for(
        agent.ainvoke({"messages": [("user", prompt)]}),
        timeout=_AGENT_EXECUTION_TIMEOUT_SECONDS,
    )
    return state if isinstance(state, dict) else {}


def _extract_final_message(state: object) -> str:
    """Extract final content string from a LangChain agent state payload."""
    messages = state.get("messages", []) if isinstance(state, dict) else []
    if not messages:
        return ""
    final = messages[-1]
    content = getattr(final, "content", final)
    return str(content)
