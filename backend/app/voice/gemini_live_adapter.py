"""Gemini Live WebSocket bridge with raw binary PCM streaming, server VAD, and allowlisted forensic tools."""

import asyncio
import base64
import binascii
import json
import logging
from contextlib import suppress
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types

from app.config import Settings
from app.dependencies import Actor
from app.voice.intent_schema import VoiceAudioEnd, VoiceAudioInput, VoiceTextInput
from app.voice.tool_dispatch import (
    TOOL_DECLARATIONS, VOICE_SYSTEM_INSTRUCTION, dispatch_voice_tool,
)

logger = logging.getLogger("tattva.voice.live")
_MAX_CALLS_PER_SESSION = 30
_MAX_INPUT_BYTES = 64 * 1024 * 1024


VOICE_METADATA = {
    "Aoede": {"gender": "female", "desc": "Female · Warm & Natural"},
    "Kore": {"gender": "female", "desc": "Female · Crisp & Clear"},
    "Puck": {"gender": "male", "desc": "Male · Energetic"},
    "Charon": {"gender": "male", "desc": "Male · Deep & Calm"},
    "Fenrir": {"gender": "male", "desc": "Male · Confident"},
}


def _live_config(voice_name: str = "Aoede", language: str = "auto") -> types.LiveConnectConfig:
    """Configures the Live connection with audio modality, server-side VAD, persona voice, and declared tools."""
    lang_directive = ""
    if language == "hindi":
        lang_directive = " Respond in fluent, natural Hindi (हिन्दी). Keep forensic terms precise."
    elif language == "hinglish":
        lang_directive = " Respond in conversational Hinglish (a natural mix of Hindi and English). Keep answers sharp, tactical, and engaging."
    elif language == "english":
        lang_directive = " Respond in sharp, authoritative, defense-grade English."
    else:
        lang_directive = " Automatically detect operator language (English, Hindi, or Hinglish) and mirror it fluently."

    gender = VOICE_METADATA.get(voice_name, {}).get("gender", "female")
    persona_note = f" You are speaking with the {voice_name} ({gender}) voice profile."
    full_instruction = VOICE_SYSTEM_INSTRUCTION + lang_directive + persona_note

    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
            )
        ),
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
                end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
                silence_duration_ms=1800,
            )
        ),
        system_instruction=types.Content(parts=[types.Part.from_text(text=full_instruction)]),
        tools=TOOL_DECLARATIONS,
    )


async def serve_live_session(
    websocket: WebSocket,
    settings: Settings,
    database: Any,
    actor: Actor,
    case_id: str,
    qdrant: Any = None,
) -> None:
    if not settings.gemini_live_configured:
        await websocket.close(code=1013, reason="Voice service is not configured.")
        return

    # Initialize Gemini client pinning v1alpha for bidirectional streaming WebSockets
    client = genai.Client(api_key=settings.gemini_api_key, http_options={"api_version": "v1alpha"})
    send_lock = asyncio.Lock()
    input_bytes = 0
    call_count = 0
    current_epoch = 0
    background_tasks: set[asyncio.Task] = set()

    async def send_json(payload: dict) -> None:
        async with send_lock:
            await websocket.send_json(payload)

    async def send_bytes(data: bytes) -> None:
        async with send_lock:
            await websocket.send_bytes(data)

    voice_name = websocket.query_params.get("voice", "Aoede")
    if voice_name not in VOICE_METADATA:
        voice_name = "Aoede"

    language = websocket.query_params.get("language", "auto")
    if language not in ("auto", "hindi", "english", "hinglish"):
        language = "auto"

    try:
        async with asyncio.timeout(settings.voice_max_session_seconds):
            async with client.aio.live.connect(
                model=settings.gemini_live_model, config=_live_config(voice_name, language)
            ) as session:
                await send_json({
                    "type": "ready",
                    "audio_input": "pcm_s16le_16000_mono",
                    "audio_output": "pcm_s16le_24000_mono",
                    "voice": voice_name,
                    "gender": VOICE_METADATA[voice_name]["gender"],
                    "language": language,
                    "case_id": case_id,
                })

                async def from_browser() -> None:
                    nonlocal input_bytes
                    while True:
                        msg = await websocket.receive()
                        if msg.get("type") == "websocket.disconnect":
                            break

                        # 1. Raw Binary PCM16 from AudioWorklet
                        raw_bytes = msg.get("bytes")
                        if raw_bytes:
                            input_bytes += len(raw_bytes)
                            if input_bytes > _MAX_INPUT_BYTES:
                                await send_json({"type": "error", "message": "Session audio limit reached."})
                                await websocket.close(code=1008)
                            try:
                                blob = types.Blob(data=raw_bytes, mime_type="audio/pcm;rate=16000")
                                await session.send_realtime_input(audio=blob)
                            except Exception as audio_err:
                                logger.debug(f"Audio frame dispatch skipped during state transition: {audio_err}")
                            continue

                        # 2. Text / JSON Control Frames
                        text = msg.get("text")
                        if text:
                            try:
                                payload = json.loads(text)
                                msg_type = payload.get("type") if isinstance(payload, dict) else None

                                if msg_type == "text":
                                    message = VoiceTextInput.model_validate(payload)
                                    await session.send_realtime_input(text=message.text)
                                elif msg_type == "audio":
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
                                elif msg_type == "audio_end":
                                    VoiceAudioEnd.model_validate(payload)
                                    await session.send_realtime_input(audio_stream_end=True)
                                elif msg_type == "ping":
                                    await send_json({"type": "pong"})
                            except Exception as err:
                                logger.debug(f"Non-fatal client payload error: {err}")

                async def from_model() -> None:
                    nonlocal call_count, current_epoch
                    async for response in session.receive():
                        server = getattr(response, "server_content", None)
                        if server is not None:
                            # 1. Server-side Barge-In Interruption
                            if getattr(server, "interrupted", False):
                                current_epoch += 1
                                logger.info(f"Barge-in triggered by operator. Advancing epoch to {current_epoch}.")
                                await send_json({
                                    "type": "barge_in",
                                    "epoch": current_epoch,
                                    "state": "LISTENING",
                                })
                                continue

                            # 2. Transcriptions
                            input_tx = getattr(server, "input_transcription", None)
                            output_tx = getattr(server, "output_transcription", None)
                            if input_tx and getattr(input_tx, "text", None):
                                await send_json({"type": "input_transcription", "text": input_tx.text})
                            if output_tx and getattr(output_tx, "text", None):
                                await send_json({"type": "output_transcription", "text": output_tx.text})

                            # 3. Model Audio Stream (prefixed with 4-byte epoch header)
                            turn = getattr(server, "model_turn", None)
                            for part in getattr(turn, "parts", []) if turn else []:
                                inline = getattr(part, "inline_data", None)
                                data = getattr(inline, "data", None) if inline else None
                                if data:
                                    epoch_header = current_epoch.to_bytes(4, byteorder="big")
                                    await send_bytes(epoch_header + data)
                                    await send_json({"type": "state", "state": "PLAYING"})

                            # 4. Turn Complete
                            if getattr(server, "turn_complete", False):
                                await send_json({"type": "state", "state": "LISTENING"})
                                await send_json({"type": "turn_complete"})

                        # 5. Native Forensic Tool Calling
                        tool_call = getattr(response, "tool_call", None)
                        if tool_call and getattr(tool_call, "function_calls", None):
                            await send_json({"type": "state", "state": "ANALYZING"})
                            function_responses = []
                            for fc in tool_call.function_calls:
                                call_count += 1
                                name = getattr(fc, "name", "")
                                args = getattr(fc, "args", {}) or {}

                                # Notify frontend action card (running)
                                await send_json({
                                    "type": "action_card",
                                    "tool": name,
                                    "status": "running",
                                    "args": dict(args),
                                })

                                if call_count > _MAX_CALLS_PER_SESSION:
                                    result = {"error": "session_tool_limit_reached"}
                                else:
                                    try:
                                        result = await dispatch_voice_tool(
                                            name=name,
                                            arguments=dict(args),
                                            database=database,
                                            settings=settings,
                                            actor=actor,
                                            case_id=case_id,
                                            qdrant=qdrant,
                                        )
                                    except Exception as exc:
                                        logger.exception(f"Voice tool '{name}' failed", extra={"tool_name": name})
                                        result = {"error": "tool_failed", "detail": str(exc)}

                                # Notify frontend action card (done)
                                await send_json({
                                    "type": "action_card",
                                    "tool": name,
                                    "status": "done",
                                    "result": result,
                                })

                                function_responses.append(types.FunctionResponse(
                                    name=name,
                                    id=getattr(fc, "id", None),
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
        logger.info("Voice WebSocket disconnected cleanly.")
        return
    except Exception as exc:
        logger.exception("Gemini Live session failed", extra={"case_id": case_id})
        with suppress(Exception):
            await send_json({"type": "error", "message": f"Voice session error: {str(exc)}"})
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
