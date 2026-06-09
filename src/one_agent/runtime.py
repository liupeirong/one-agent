"""LLM invocation runtime for one-agent."""

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
_MCP_AGENT_EXECUTION_TIMEOUT_SECONDS = 120.0


def invoke(
    *,
    config: Config,
    prompt: str,
    system_instructions: str | None = None,
    mcp_servers: Sequence[McpServer] | None = None,
) -> str:
    """Run a single-shot LLM (or LangGraph agent) invocation.

    Builds a ChatOpenAI model from *config*. When *mcp_servers* is empty
    or ``None``, the model is invoked directly with *prompt* (and an
    optional preceding system message carrying *system_instructions*).
    When *mcp_servers* is non-empty, their tools are listed and a
    LangGraph ReAct agent is run to completion — both within a single
    event loop so adapter sessions stay alive for the whole run and no
    orphaned child processes are left behind.
    """
    llm = _build_chat_model(config)

    if mcp_servers:
        return asyncio.run(
            _arun_with_mcp(llm, prompt, system_instructions, tuple(mcp_servers))
        )

    if system_instructions:
        messages: list[tuple[str, str]] = [
            ("system", system_instructions),
            ("human", prompt),
        ]
        result = llm.invoke(messages)
    else:
        result = llm.invoke(prompt)
    return str(result.content)


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


async def _arun_with_mcp(
    llm: ChatOpenAI,
    prompt: str,
    system_instructions: str | None,
    servers: tuple[McpServer, ...],
) -> str:
    """List MCP tools and run the ReAct agent inside a single event loop."""
    connections = {server.name: to_stdio_connection(server) for server in servers}
    async with MultiServerMCPClient(connections) as client:
        tools: list[BaseTool] = await asyncio.wait_for(
            client.get_tools(),
            timeout=_MCP_TOOL_LISTING_TIMEOUT_SECONDS,
        )
        agent = create_agent(
            llm, list(tools), system_prompt=system_instructions or None
        )
        state = await asyncio.wait_for(
            agent.ainvoke({"messages": [("user", prompt)]}),
            timeout=_MCP_AGENT_EXECUTION_TIMEOUT_SECONDS,
        )
        messages = state.get("messages", []) if isinstance(state, dict) else []

    if not messages:
        return ""
    final = messages[-1]
    content = getattr(final, "content", final)
    return str(content)
