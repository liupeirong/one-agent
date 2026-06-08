"""LLM invocation runtime for one-agent."""

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_openai import ChatOpenAI

from one_agent.config import Config


def invoke(
    *, config: Config, prompt: str, system_instructions: str | None = None
) -> str:
    """Run a single-shot LLM invocation and return the final answer.

    Builds a ChatOpenAI model from *config* and sends *prompt* as a single
    human message. When *system_instructions* is provided and non-empty, it
    is sent as a preceding system message so loaded skill context guides
    the model. Returns the model's text response.
    """
    model_kwargs: dict[str, str] = {}
    if config.openai_api_key:
        model_kwargs["api_key"] = config.openai_api_key
    else:
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )
        model_kwargs["api_key"] = token_provider

    llm = ChatOpenAI(
        model=config.openai_model,
        base_url=config.openai_base_url,
        **model_kwargs,
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
