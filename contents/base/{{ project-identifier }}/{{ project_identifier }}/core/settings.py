import chainlit as cl
from chainlit.input_widget import Select, Slider


async def get_settings():
    """
    Retrieves the chat settings.

    Returns:
        cl.ChatSettings: The chat settings object containing the selected values.
    """
    settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="OpenAI - Model",
                values=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1-mini"],
                initial_index=0,
            ),
            Slider(
                id="Temperature",
                label="OpenAI - Temperature",
                initial=0,
                min=0,
                max=1,
                step=0.1,
            ),
        ]
    ).send()
    return settings
