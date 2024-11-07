import os
from loguru import logger
import chainlit as cl
import openai

from typing import List  # noqa

from chainlit.server import app

import {{ project_identifier }}.utils.configuration as configuration
from {{ project_identifier }}.core.settings import get_settings
from {{ project_identifier }}.utils.chat_profiles import CHAT_PROFILES
from {{ project_identifier }}.core.core import process_response_for_references, select_agent

from llama_index.core.agent import ReActAgent  # noqa

from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.base.response.schema import StreamingResponse  # noqa

from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from phoenix.otel import register

is_phoenix_on = os.environ.get("PHOENIX_OBSERVABILITY", False)

if is_phoenix_on:
    tracer_provider = register(
        project_name="{{ project-identifier }}",
        endpoint="http://phoenix.phoenix:443/v1/traces",
    )
    LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)

configuration.configure_logging()

openai.api_key = os.getenv("OPENAI_API_KEY")

app_name = "{{ project-title }} Multi Step Agent"
index_path = os.path.join(os.path.dirname(__file__), "data", "indices")
storage_context = StorageContext.from_defaults(persist_dir=index_path)
index = load_index_from_storage(storage_context)


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Details on Ethylene & Propylene",
            message="What are some details I should know about Ethylene and Propylene?",
            icon="/public/images/366-300x300.jpg",
        ),
        cl.Starter(
            label="Infant Formula Preparation Chart",
            message="Can you please share instructions for Infant formula sample preparation procedure chart?",
            icon="/public/images/680-200x200.jpg",
        ),
        cl.Starter(
            label="Using TIC of Formaldehyde (10 nmol/mol)",
            message="How can I use Total ion chromatogram of formaldehyde at the concentration of 10 nmol/mol in SIM mode?",
            icon="/public/images/703-300x300.jpg",
        ),
        cl.Starter(
            label="Ammonia Analysis for Fuel Cells",
            message="What's the Ammonia Analysis in High-Purity Hydrogen for Fuel Cell Vehicles formula?",
            icon="/public/images/931-237x237.jpg",
        ),
        cl.Starter(
            label="Calibration Formulas & Calculations",
            message="Can you share some formulas or calculations for calibration procedures?",
            icon="/public/images/1053-200x200.jpg",
        ),
        cl.Starter(
            label="Methods for Methane Gas",
            message="What are some of the methods for methane gas?",
            icon="/public/images/442-400x400.jpg",
        ),
    ]


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """
    BEWARE OF DUMMY FUNCTIONALITY
    One of the strategies here to be implemented: https://docs.chainlit.io/authentication/overview
    Authenticates a user based on the provided username and password.

    Args:
        username (str): The username of the user.
        password (str): The password of the user.

    Returns:
        cl.User or None: If the authentication is successful, returns a `cl.User` object
        representing the authenticated user. Otherwise, returns `None`.
    """
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if (username, password) == ("admin", "admin"):
        return cl.User(identifier="admin", metadata={"role": "admin", "provider": "credentials"})
    else:
        return None


@cl.set_chat_profiles
async def chat_profile() -> List[cl.ChatProfile]:
    return [
        cl.ChatProfile(
            name=profile.get("name"),
            markdown_description=profile.get("markdown_description"),
            icon=profile.get("icon"),
        )
        for profile in CHAT_PROFILES.values()
    ]


@cl.on_settings_update
async def setup_agent(settings) -> None:
    logger.info(
        f"on_settings_update: Setup agent with following settings: {settings}",
    )
    chat_profile = cl.user_session.get("chat_profile")
    logger.info(f"on_settings_update: Starting chat with profile: {chat_profile}")
    await select_agent(chat_profile, settings)


@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")  # type: ReActAgent
    query_engine = cl.user_session.get("query_engine")
    is_operator = False

    msg = cl.Message(content="", author=cl.user_session.get("chat_profile"))

    if cl.user_session.get("chat_profile") == "{{ project-title }} Operator Persona":
        is_operator = True
        res = await cl.make_async(query_engine.query)(message.content)
    else:
        res = await cl.make_async(agent.stream_chat)(message.content)  # type: StreamingResponse

    logger.info(res)

    if not is_operator:
        for token in res.response_gen:
            await msg.stream_token(token)

    await msg.send()
    await process_response_for_references(res, is_operator)


@cl.on_chat_start
async def start():
    settings = await get_settings()
    chat_profile = cl.user_session.get("chat_profile")
    logger.info(f"on_chat_start: Starting chat with profile: {chat_profile}")
    await setup_agent(settings)


@app.get("/health/readiness")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
