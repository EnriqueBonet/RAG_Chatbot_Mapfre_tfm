import asyncio
import os
import sys
from typing import Any, Mapping

import aiohttp
from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.openai import OpenAILLMService
from pipecat.services.tavus import TavusVideoService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.services.elevenlabs import ElevenLabsTTSService, Language

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

async def main():
    async with aiohttp.ClientSession() as session:
        tavus = TavusVideoService(
            api_key=os.getenv("TAVUS_API_KEY"),
            replica_id=os.getenv("TAVUS_REPLICA_ID"),
            session=session,
        )

        # get persona, look up persona_name, set this as the bot name to ignore
        persona_name = await tavus.get_persona_name()
        room_url = await tavus.initialize()

        transport = DailyTransport(
            room_url=room_url,
            token=None,
            bot_name="Bot Valley TFM",
            params=DailyParams(
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                vad_audio_passthrough=True,
            ),
        )

        stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"), language="es-ES", sample_rate=16000)

        tts = ElevenLabsTTSService(
            api_key=os.getenv("E11_API_KEY"),
            voice_id="UOIqAnmS11Reiei1Ytkc",
            sample_rate=16000,
            params=ElevenLabsTTSService.InputParams(
                language=Language.ES
            )
        )

        llm = OpenAILLMService(model="gpt-4o-mini")
        

        messages = [
            {
                "role": "system",
                "content": "Eres un asistente llamado MAPPI que ayuda a resolver dudas sobre Polizas de coche en MAPFRE España, aseguradora lider. Se conciso y directo en tus preguntas y respuestas, ya que serás parte de una WebRTC Call en un call center.",
            }
        ]

        context = OpenAILLMContext(messages)
        context_aggregator = llm.create_context_aggregator(context)

        pipeline = Pipeline(
            [
                transport.input(),  # Transport user input
                stt,  # STT
                context_aggregator.user(),  # User responses
                llm,  # LLM
                tts,  # TTS
                tavus,  # Tavus output layer
                transport.output(),  # Transport bot output
                context_aggregator.assistant(),  # Assistant spoken responses
            ]
        )

        task = PipelineTask(
            pipeline,
            PipelineParams(
                # We just use 16000 because that's what Tavus is expecting and
                # we avoid resampling.
                audio_in_sample_rate=16000,
                audio_out_sample_rate=16000,
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=True,
                report_only_initial_ttfb=True,
            ),
        )

        @transport.event_handler("on_participant_joined")
        async def on_participant_joined(
            transport: DailyTransport, participant: Mapping[str, Any]
        ) -> None:
            # Ignore the Tavus replica's microphone
            if participant.get("info", {}).get("userName", "") == persona_name:
                logger.debug(f"Ignoring {participant['id']}'s microphone")
                await transport.update_subscriptions(
                    participant_settings={
                        participant["id"]: {
                            "media": {"microphone": "unsubscribed"},
                        }
                    }
                )

            if participant.get("info", {}).get("userName", "") != persona_name:
                # Kick off the conversation.
                messages.append(
                    {"role": "system", "content": "Introducete al usuario al empezar la conversación."}
                )
                await task.queue_frames([context_aggregator.user().get_context_frame()])

        @transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            await task.cancel()

        runner = PipelineRunner()

        await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())
