"""Gemini Live WebSocket bridge with bounded PCM input and allowlisted tools."""

import asyncio
import base64
import binascii
import json
import logging
from contextlib import suppress

from fastapi import WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types
from pydantic import ValidationError

from app.config import Settings
from app.dependencies import Actor
from app.voice.intent_schema import VoiceAudioEnd, VoiceAudioInput, VoiceTextInput
from app.voice.tool_dispatch import (
    TOOL_DECLARATIONS, VOICE_SYSTEM_INSTRUCTION, dispatch_voice_tool,
)

logger = logging.getLogger(__name__)
_MAX_CALLS_PER_SESSION = 20
_MAX_INPUT_BYTES = 32 * 1024 * 1024


def _live_config() -> dict:
    return {
        "response_modalities": ["AUDIO"],
        "input_audio_transcription": {},
        "output_audio_transcription": {},
        "system_instruction": VOICE_SYSTEM_INSTRUCTION,
        "tools": TOOL_DECLARATIONS,
    }


async def serve_live_session(
    websocket: WebSocket, settings: Settings, database, actor: Actor, case_id: str,
) -> None:
    if not settings.gemini_live_configured:
        await websocket.close(code=1013, reason="Voice service is not configured.")
        return
    client = genai.Client(api_key=settings.gemini_api_key)
    send_lock = asyncio.Lock()
    input_bytes = 0
    call_count = 0
    background_tasks: set[asyncio.Task] = set()

    async def send_json(payload: dict) -> None:
        async with send_lock:
            await websocket.send_json(payload)

    try:
        async with asyncio.timeout(settings.voice_max_session_seconds):
            async with client.aio.live.connect(
                model=settings.gemini_live_model, config=_live_config()
            ) as session:
                await send_json({"type": "ready", "audio_input": "pcm_s16le_16000_mono"})

                async def from_browser() -> None:
                    nonlocal input_bytes
                    while True:
                        raw = await websocket.receive_text()
                        if len(raw) > 70_000:
                            await send_json({"type": "error", "message": "Input frame is too large."})
                            await websocket.close(code=1009)
                            return
                        try:
                            payload = json.loads(raw)
                            message_type = payload.get("type") if isinstance(payload, dict) else None
                            if message_type == "text":
                                message = VoiceTextInput.model_validate(payload)
                                await session.send_realtime_input(text=message.text)
                            elif message_type == "audio":
                                message = VoiceAudioInput.model_validate(payload)
                                try:
                                    audio = base64.b64decode(message.data, validate=True)
                                except (binascii.Error, ValueError) as exc:
                                    raise ValueError("Audio frame is not valid base64.") from exc
                                if not audio or len(audio) % 2:
                                    raise ValueError("PCM audio must contain complete 16-bit samples.")
                                input_bytes += len(audio)
                                if input_bytes > _MAX_INPUT_BYTES:
                                    await send_json({"type": "error", "message": "Session audio limit reached."})
                                    await websocket.close(code=1008)
                                    return
                                await session.send_realtime_input(
                                    audio=types.Blob(data=audio, mime_type=message.mime_type)
                                )
                            elif message_type == "audio_end":
                                VoiceAudioEnd.model_validate(payload)
                                await session.send_realtime_input(audio_stream_end=True)
                            elif message_type == "error":
                                # Client-side errors do not grant a server operation.
                                await send_json({"type": "error", "message": "Client reported an audio input error."})
                            else:
                                raise ValueError("Unsupported voice message type.")
                        except (ValidationError, ValueError, json.JSONDecodeError):
                            await send_json({"type": "error", "message": "Voice message did not match the supported input format."})

                async def from_model() -> None:
                    nonlocal call_count
                    async for response in session.receive():
                        server = getattr(response, "server_content", None)
                        if server is not None:
                            input_tx = getattr(server, "input_transcription", None)
                            output_tx = getattr(server, "output_transcription", None)
                            if input_tx and getattr(input_tx, "text", None):
                                await send_json({"type": "input_transcription", "text": input_tx.text})
                            if output_tx and getattr(output_tx, "text", None):
                                await send_json({"type": "output_transcription", "text": output_tx.text})
                            turn = getattr(server, "model_turn", None)
                            for part in getattr(turn, "parts", []) if turn else []:
                                inline = getattr(part, "inline_data", None)
                                data = getattr(inline, "data", None) if inline else None
                                if data:
                                    encoded = base64.b64encode(data).decode("ascii") if isinstance(data, bytes) else data
                                    await send_json({"type": "audio", "data": encoded, "mime_type": getattr(inline, "mime_type", "audio/pcm;rate=24000")})
                            if getattr(server, "turn_complete", False):
                                await send_json({"type": "turn_complete"})
                        tool_call = getattr(response, "tool_call", None)
                        if tool_call:
                            function_responses = []
                            for function_call in getattr(tool_call, "function_calls", []):
                                call_count += 1
                                if call_count > _MAX_CALLS_PER_SESSION:
                                    result = {"error": "session_tool_limit_reached"}
                                else:
                                    name = getattr(function_call, "name", "")
                                    try:
                                        args = getattr(function_call, "args", {}) or {}
                                        result = await dispatch_voice_tool(
                                            name=name,
                                            arguments=dict(args),
                                            database=database,
                                            settings=settings,
                                            actor=actor,
                                            case_id=case_id,
                                        )
                                    except Exception:
                                        logger.exception("Voice tool failed", extra={"tool_name": name})
                                        result = {"error": "tool_unavailable_or_not_authorized"}
                                function_responses.append(types.FunctionResponse(
                                    name=getattr(function_call, "name", "unknown"),
                                    id=getattr(function_call, "id", None),
                                    response={"result": result},
                                ))
                            if function_responses:
                                await session.send_tool_response(function_responses=function_responses)

                client_task = asyncio.create_task(from_browser(), name="voice-client-input")
                model_task = asyncio.create_task(from_model(), name="voice-model-output")
                background_tasks.update({client_task, model_task})
                done, pending = await asyncio.wait(
                    {client_task, model_task}, return_when=asyncio.FIRST_COMPLETED
                )
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                for task in done:
                    exception = task.exception()
                    if exception and not isinstance(exception, WebSocketDisconnect):
                        raise exception
    except TimeoutError:
        with suppress(Exception):
            await send_json({"type": "error", "message": "Voice session time limit reached."})
            await websocket.close(code=1000)
    except WebSocketDisconnect:
        return
    except Exception:
        logger.exception("Gemini Live session failed", extra={"case_id": case_id})
        with suppress(Exception):
            await send_json({"type": "error", "message": "Voice session ended unexpectedly."})
            await websocket.close(code=1011)
    finally:
        for task in background_tasks:
            if not task.done():
                task.cancel()
        if background_tasks:
            await asyncio.gather(*background_tasks, return_exceptions=True)
        close = getattr(client.aio, "aclose", None)
        if close is not None:
            with suppress(Exception):
                await close()
