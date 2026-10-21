"""Strict browser-to-voice-gateway message contract."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VoiceTextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["text"]
    text: str = Field(min_length=1, max_length=4000)


class VoiceAudioInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["audio"]
    data: str = Field(min_length=4, max_length=65536)
    mime_type: Literal["audio/pcm;rate=16000"]


class VoiceAudioEnd(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["audio_end"]


class VoiceClientError(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["error"]
    message: str = Field(min_length=1, max_length=500)
