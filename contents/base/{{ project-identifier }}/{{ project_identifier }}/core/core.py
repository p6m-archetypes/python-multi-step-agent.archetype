import os
from loguru import logger
import chainlit as cl
import openai
from datetime import datetime

from typing import List  # noqa


import {{ project_identifier }}.utils.configuration as configuration
from {{ project_identifier }}.utils.common import process_response_metadata_list, find_profile_data

from llama_index.core import Settings
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool, QueryEngineTool
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.callbacks import CallbackManager
from llama_index.core.base.response.schema import StreamingResponse  # noqa
from llama_index.llms.openai import OpenAI
from llama_index.tools.tavily_research import TavilyToolSpec
from llama_index.embeddings.openai import OpenAIEmbedding

configuration.configure_logging()
openai.api_key = os.getenv("OPENAI_API_KEY")

app_name = "{{ project-title }} Multi Step Agent"
index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "indices")
storage_context = StorageContext.from_defaults(persist_dir=index_path)
index = load_index_from_storage(storage_context)


@cl.step(type="tool", name="References")
async def references_tool(references):
    """
    Generates a formatted string of references with their details.

    Args:
        references (list): A list of dictionaries, where each dictionary contains
            information about a reference, including 'score', 'path', 'page_numbers',
            and 'images'.

    Returns:
        str: A formatted string containing the details of each reference.
    """
    paragraph = "#### Sources:\n"
    for reference in references:
        paragraph += f"**Score:** {reference['score']}\n"
        paragraph += f"**File:** {reference['path'].replace('./data/documents/', '')}\n"
        paragraph += f"**Page:** {', '.join(reference['page_numbers'])}\n"
        if reference["images"]:
            paragraph += "**Images:**\n"
            paragraph += "\n".join([f"{img['path'].replace('./data/images/', '')}" for img in reference["images"]])
        paragraph += "\n\n"

    await cl.sleep(1)
    return paragraph


async def process_response_for_references(response: StreamingResponse, is_operator: bool = False):
    """
    Processes a response for references and sends a message.

    This function processes the metadata of the response's source nodes, creates
    elements based on the type of the response (e.g., Pdf, Image), and sends a
    message with the processed content and elements.

    Args:
        response (StreamingResponse): The response object containing source nodes.
        is_operator (bool, optional): Flag indicating if the user is an operator. Defaults to False.

    Returns:
        None
    """
    msg = cl.Message(content="", author=cl.user_session.get("chat_profile"))
    if response.source_nodes:
        response = process_response_metadata_list(response.source_nodes)
        elements = []
        for r in response:
            if r["type"] == "Pdf":
                elements.append(cl.Pdf(name=r["name"], display="inline", path=r["path"], page=r["page_numbers"][0]))
            if r["images"]:
                for img in r["images"]:
                    elements.append(cl.Image(name=img["name"], display="inline", path=img["path"], size="small"))
            if is_operator:
                if msg.content:
                    msg.content = f'{msg.content}\n\n{r["text"]}'
                else:
                    msg.content = r["text"]

        msg.elements = elements
        await references_tool(response)
    await msg.send()


async def user_message_from_token_list(token_list: List[str]):
    """
    Creates and sends a user message from a list of tokens.

    This function constructs a message object with an empty content and the current user's chat profile as the author.
    It then streams each token from the provided token list into the message content and sends the message.

    Args:
        token_list (List[str]): A list of string tokens to be included in the message content.

    Returns:
        None
    """
    msg = cl.Message(content="", author=cl.user_session.get("chat_profile"))
    for token in token_list:
        await msg.stream_token(token)
    await msg.send()


async def select_agent(chat_profile, settings) -> None:
    """
    Selects and initializes an agent based on the provided chat profile and settings.

    Args:
        chat_profile (dict): The chat profile data used to customize the agent.
        settings (dict): A dictionary containing configuration settings for the agent, including:
            - "Model": The model name to be used by the OpenAI API.
            - "Temperature": The temperature setting for the OpenAI model.

    Returns:
        None
    """
    model = settings["Model"]
    temperature = settings["Temperature"]

    def add(x: int, y: int) -> int:
        """Useful function to add two numbers."""
        return x + y

    def multiply(x: int, y: int) -> int:
        """Useful function to multiply two numbers."""
        return x * y

    tavily_tool_spec = TavilyToolSpec(
        api_key=os.environ.get("TAVILY_API_KEY"),
    )

    profile = await find_profile_data(chat_profile)

    llm = OpenAI(
        model=model, temperature=temperature, max_tokens=2048, streaming=True, system_prompt=profile.get("prompt")
    )

    Settings.llm = llm
    embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    Settings.embed_model = embed_model

    Settings.callback_manager = CallbackManager([cl.LlamaIndexCallbackHandler()])

    query_engine = index.as_query_engine(
        similarity_top_k=5,
        streaming=True,
        llm=llm,
        embed_model=embed_model,
        response_mode="compact",
        verbose=True,
        system_prompt=profile.get("prompt"),
    )

    multiply_tool = FunctionTool.from_defaults(fn=multiply)

    add_tool = FunctionTool.from_defaults(fn=add)

    ybor_tool = QueryEngineTool.from_defaults(
        query_engine,
        name="Search",
        description="Useful for answering questions. Do not use if questions are about you. Try not to condense the question and provide a detailed answer.",
    )

    tl = tavily_tool_spec.to_tool_list()[0]

    current_date = datetime.now().strftime("%Y-%m-%d")

    search_tool = FunctionTool.from_defaults(
        fn=tl.fn,
        async_fn=tl.async_fn,
        name="Web",
        description=f"Useful when 'web, google' keywords are mentioned. Today's data is {current_date}",
    )

    agent = ReActAgent.from_tools(
        [multiply_tool, add_tool, ybor_tool, search_tool],
        verbose=True,
        llm=llm,
        context=profile.get("prompt"),
    )

    cl.user_session.set("agent", agent)
    cl.user_session.set("query_engine", query_engine)


def execute():
    """
    Dummy function
    """
    logger.info("Executing")
    return True
