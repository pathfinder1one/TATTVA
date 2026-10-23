import asyncio
import json
import logging
from google import genai
from google.genai import types
from pymongo import AsyncMongoClient
from app.config import get_settings
from app.dependencies import Actor
from app.voice.gemini_live_adapter import _live_config
from app.voice.tool_dispatch import dispatch_voice_tool

logging.basicConfig(level=logging.INFO)

async def test_cross_case():
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key, http_options={"api_version": "v1alpha"})
    mongo = AsyncMongoClient(settings.mongodb_uri)
    db = mongo[settings.mongodb_database]
    actor = Actor(user_id="local-investigator", tenant_id="local-tenant")

    config = _live_config(voice_name="Aoede", language="auto")

    print("Connecting to Gemini Live WebSocket for Cross-Case Analysis test...")
    async with client.aio.live.connect(model=settings.gemini_live_model, config=config) as session:
        print("Connected! Sending prompt: 'charo cases ke beech me relation find karke batao, kya Vikramaditya ya murder knife ka pattern match ho raha hai?'")
        await session.send_realtime_input(
            text="Charo cases ke beech me relation find karke batao. Evidences aur suspects check karo, kya Vikramaditya multiple cases me hai aur knife ya weapon ka pattern do cases me match hota hai?"
        )

        async for response in session.receive():
            server_content = response.server_content
            if server_content is not None:
                model_turn = server_content.model_turn
                if model_turn is not None:
                    for part in model_turn.parts:
                        if part.text:
                            print(f"Gemini text: {part.text}")

            tool_call = response.tool_call
            if tool_call is not None:
                for call in tool_call.function_calls:
                    print(f"\n[TOOL CALL RECEIVED] Name: {call.name}, Args: {call.args}")
                    result = await dispatch_voice_tool(
                        name=call.name,
                        arguments=call.args or {},
                        database=db,
                        settings=settings,
                        actor=actor,
                        case_id="case_2024_023_golden_trident",
                    )
                    print(f"[TOOL EXECUTED] Returning result with {len(result.get('common_suspects', []))} common suspects and {len(result.get('weapon_pattern_matches', []))} weapon matches.")
                    
                    # Send tool response back to Gemini
                    await session.send(
                        input=types.LiveClientToolResponse(
                            function_responses=[
                                types.FunctionResponse(
                                    name=call.name,
                                    id=call.id,
                                    response={"result": result},
                                )
                            ]
                        )
                    )

            if server_content and server_content.turn_complete:
                print("\nTurn complete!")
                break

if __name__ == "__main__":
    asyncio.run(test_cross_case())
