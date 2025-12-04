from dotenv import load_dotenv
from datetime import datetime
import os
import json
import asyncio
import logging
import sounddevice as sd
from typing import Any, Dict, List, cast

from dotenv import load_dotenv
load_dotenv()

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.agents.llm.chat_context import ChatMessage
from livekit.plugins import noise_cancellation
from livekit.plugins import google
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from tools import (
    get_weather,
    search_web,
    send_email,
    open_email_composer,
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
    restart_system,
    # Automation tools
    add_task,
    list_tasks,
    complete_task,
    delete_task,
    organize_downloads,
    find_duplicates,
    clean_temp,
    get_clipboard,
    set_clipboard,
    generate_password,
    word_count,
    check_internet,
    get_network_stats,
    list_processes,
    kill_process,
    get_disk_usage,
    # File operations tools
    list_files_tool,
    rename_files_tool,
    move_files_tool,
    organize_folder_tool,
    analyze_file_tool,
    find_large_files_tool,
    find_duplicates_tool,
    undo_last_operation_tool,
    # Email contact management tools
    add_contact_tool,
    update_contact_tool,
    delete_contact_tool,
    list_contacts_tool
)

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Assistant(Agent):
    def __init__(self) -> None:
        # Cast the env var to str for the type checker; also keep a runtime check
        google_api_key = cast(str, os.getenv("GOOGLE_API_KEY"))
        if not google_api_key:
            logger.warning("GOOGLE_API_KEY is not set; RealtimeModel may fail at runtime.")

        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                api_key=google_api_key,
                voice="Aoede",
                temperature=0.8,
            ),
            tools=[
                # Web & Communication tools
                get_weather,
                search_web,
                send_email,
                open_email_composer,
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
                restart_system,
                # Task Management
                add_task,
                list_tasks,
                complete_task,
                delete_task,
                # File Organization
                organize_downloads,
                find_duplicates,
                clean_temp,
                # File Operations
                list_files_tool,
                rename_files_tool,
                move_files_tool,
                organize_folder_tool,
                analyze_file_tool,
                find_large_files_tool,
                find_duplicates_tool,
                undo_last_operation_tool,
                # Email Contact Management
                add_contact_tool,
                update_contact_tool,
                delete_contact_tool,
                list_contacts_tool,
                # Clipboard Operations
                get_clipboard,
                set_clipboard,
                # Utilities
                generate_password,
                word_count,
                # Network & System
                check_internet,
                get_network_stats,
                list_processes,
                kill_process,
                get_disk_usage
            ],
        )

    async def on_agent_started(self, session: AgentSession):  # type: ignore[override]
        await super().on_agent_started(session)  # type: ignore[attr-defined]




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
        # Tell type checker devices is a list of dicts
        devices = cast(List[Dict[str, Any]], sd.query_devices())
        for i, dev in enumerate(devices):
            dev = cast(Dict[str, Any], dev)
            name = (dev.get("name") or "").lower()
            max_inputs = dev.get("max_input_channels") or 0
            if input_device_name.lower() in name and max_inputs > 0:
                chosen_index = i
                logger.info(f"Found input device matching '{input_device_name}': {dev.get('name')} (index {i})")
                break
    
    # Output device selection
    if output_device_index:
        try:
            out_idx = int(output_device_index)
            logger.info(f"Using audio output device index: {out_idx}")
        except ValueError:
            logger.warning(f"Invalid AUDIO_OUTPUT_DEVICE_INDEX: {output_device_index}")
    
    # Apply device settings (cast assignments to Any to satisfy Pylance)
    if chosen_index is not None and out_idx is not None:
        sd.default.device = cast(Any, (chosen_index, out_idx))
        logger.info("Set sounddevice default input device to index %s and output to %s", chosen_index, out_idx)
    elif chosen_index is not None:
        # keep existing output index from sd.default.device[1] at runtime
        sd.default.device = cast(Any, (chosen_index, sd.default.device[1]))
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

    async def send_chat_message(message: str, images: list[dict] | None = None) -> None:
        """Push assistant responses to the UI chat."""
        if not message:
            return
        payload = {
            "type": "assistant_message",
            "message": message,
            "text": message,
            "images": images or [],
            "timestamp": datetime.utcnow().isoformat(),
        }
        try:
            await ctx.room.local_participant.publish_data(
                json.dumps(payload).encode("utf-8"),
                reliable=True,
            )
        except Exception as exc:
            logger.warning("Failed to send chat update: %s", exc)

    speech_buffers: Dict[str, List[str]] = {}

    def handle_speech_created(event) -> None:
        handle = event.speech_handle
        speech_buffers[handle.id] = []

        def on_item_added(item):
            if isinstance(item, ChatMessage) and item.role == "assistant":
                text = (item.text_content or "").strip()
                if text:
                    speech_buffers[handle.id].append(text)

        def on_done(_handle):
            handle._remove_item_added_callback(on_item_added)
            handle.remove_done_callback(on_done)
            combined = "\n".join(speech_buffers.pop(handle.id, [])).strip()
            if combined:
                asyncio.create_task(send_chat_message(combined))

        handle._add_item_added_callback(on_item_added)
        handle.add_done_callback(on_done)

    session.on("speech_created", handle_speech_created)

    def handle_data_packet(packet) -> None:
        try:
            payload = json.loads(packet.data.decode("utf-8"))
        except Exception:
            logger.warning("Received malformed data packet")
            return

        if payload.get("type") != "user_command":
            return

        text = (payload.get("text") or payload.get("message") or "").strip()
        if not text:
            return

        async def process_text_request():
            try:
                await session.generate_reply(instructions=text)
            except Exception as exc:
                logger.error("Failed to process chat command: %s", exc)
                await send_chat_message(
                    "I ran into an unexpected issue while responding. Please try again."
                )

        asyncio.create_task(process_text_request())

    ctx.room.on("data_received", handle_data_packet)

    # After all handlers are registered and the room is ready, send an initial greeting
    # so that whenever a user connects to the room, the assistant starts participating.
    try:
        await session.generate_reply(
            instructions=SESSION_INSTRUCTION,
        )
    except Exception as exc:
        logger.error("Failed to send initial greeting: %s", exc)

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
