from dotenv import load_dotenv
import os
import logging
import sounddevice as sd

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation
from livekit.plugins import google
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from tools import (
    get_weather,
    search_web,
    send_email,
    control_volume,
    open_application,
    close_application,
    open_website,
    search_google,
    get_system_status,
    get_schedule,
    get_time_and_date,
    take_screenshot,
    get_latest_news_tool,
    book_movie_ticket_tool,
    shutdown_system,
    restart_system
)

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                api_key=os.getenv("GOOGLE_API_KEY"),
                voice="Aoede",
                temperature=0.8,
            ),
            tools=[
                # Web & Communication tools
                get_weather,
                search_web,
                send_email,
                # Desktop automation tools
                control_volume,
                open_application,
                close_application,
                open_website,
                search_google,
                get_system_status,
                get_schedule,
                get_time_and_date,
                take_screenshot,
                get_latest_news_tool,
                book_movie_ticket_tool,
                shutdown_system,
                restart_system
            ],
        )

    async def on_agent_started(self, session: AgentSession):
        await super().on_agent_started(session)
        logger.info("Nevira assistant started and ready")


async def entrypoint(ctx: agents.JobContext):
    # Configure audio devices
    input_device_index = os.getenv("AUDIO_INPUT_DEVICE_INDEX")
    input_device_name = os.getenv("AUDIO_INPUT_DEVICE_NAME")
    output_device_index = os.getenv("AUDIO_OUTPUT_DEVICE_INDEX")
    
    chosen_index = None
    out_idx = None
    
    # Input device selection
    if input_device_index:
        try:
            chosen_index = int(input_device_index)
            logger.info(f"Using audio input device index: {chosen_index}")
        except ValueError:
            logger.warning(f"Invalid AUDIO_INPUT_DEVICE_INDEX: {input_device_index}")
    elif input_device_name:
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if input_device_name.lower() in dev['name'].lower() and dev['max_input_channels'] > 0:
                chosen_index = i
                logger.info(f"Found input device matching '{input_device_name}': {dev['name']} (index {i})")
                break
    
    # Output device selection
    if output_device_index:
        try:
            out_idx = int(output_device_index)
            logger.info(f"Using audio output device index: {out_idx}")
        except ValueError:
            logger.warning(f"Invalid AUDIO_OUTPUT_DEVICE_INDEX: {output_device_index}")
    
    # Apply device settings
    if chosen_index is not None and out_idx is not None:
        sd.default.device = (chosen_index, out_idx)
        logger.info("Set sounddevice default input device to index %s and output to %s", chosen_index, out_idx)
    elif chosen_index is not None:
        sd.default.device = (chosen_index, sd.default.device[1])
        logger.info("Set sounddevice default input device to index %s", chosen_index)

    session = AgentSession()

    # Connect first to ensure the room is ready before starting the agent session
    await ctx.connect()

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            video_enabled=False,  # audio-only to reduce bandwidth & cutouts
            noise_cancellation=noise_cancellation.BVCTelephony(),
        ),
    )
    
    logger.info("Agent session started successfully")
    logger.info(f"Room participants: {[p.identity for p in ctx.room.remote_participants.values()]}")

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )

    # Keep the session alive to handle ongoing user interactions.
    # Without this, the process may exit after the initial reply and stop responding.
    try:
        while True:
            await agents.aio.sleep(1)
    except Exception:
        # On any fatal error, let the worker supervisor restart us.
        pass


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
