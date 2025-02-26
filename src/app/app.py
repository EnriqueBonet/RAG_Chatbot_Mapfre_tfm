from llama_index.core import (
        Settings
)
import shutil
import asyncio
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.core.memory import ChatMemoryBuffer
from pathlib import Path

import chainlit as cl
from llama_index.core import SimpleDirectoryReader
from src.preprocessing_text import check_and_load_index
from src.preprocessing_images import pydantic_gemini
from src.prompt import system_prompt
from src.utils import load_api_key
import os

from llama_index.core.query_engine.retriever_query_engine import RetrieverQueryEngine
from llama_index.core.callbacks import CallbackManager




# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY_PATH = os.path.join(BASE_DIR, "google_api_key.txt")
IMAGE_PATH = os.path.join(BASE_DIR, "data", "images")


# Load the API key
api_key = os.getenv("GOOGLE_API_KEY")
# Si no está en la variable de entorno, intenta cargarla desde el archivo
if not api_key:
    api_key = load_api_key(API_KEY_PATH)
# Si sigue sin existir, lanza un error
if not api_key:
    raise ValueError("Error: No se pudo cargar la API Key.")
# Configurar la API Key en las variables de entorno
os.environ["GOOGLE_API_KEY"] = api_key


index = check_and_load_index()

system_prompt = system_prompt

# Delete all contents inside the directory
images_directory_path = Path('data/images')
for item in images_directory_path.iterdir():
    if item.is_dir():
        shutil.rmtree(item)
    else:
        item.unlink()

print(f"All contents inside {images_directory_path} have been deleted.")

@cl.on_chat_start
async def start(): 
    Settings.llm = Gemini(model="models/gemini-2.0-flash-exp",
                      api_key=api_key,
                      temperature=0.3,
                      max_tokens=1024,               
                      context_window=4096,
                    )

    Settings.embed_model = GeminiEmbedding(model_name="models/text-embedding-004", api_key=api_key)
    service_context = Settings.callback_manager = CallbackManager([cl.LlamaIndexCallbackHandler()])
    memory = ChatMemoryBuffer.from_defaults(token_limit=20000)
    chat_engine = index.as_chat_engine(
        top_k=5,
        memory=memory,
        chat_mode= "context",
        llm=Settings.llm,
        embed_model=Settings.embed_model,
        service_context=service_context,
        system_prompt=system_prompt) 
    
    cl.user_session.set("chat_engine", chat_engine)
    await asyncio.sleep(1.5)
    await cl.Message(author="MAPPI", content="¡Bienvenido! Soy MAPPI, un asistente virtual de Mapfre para resolver tus dudas sobre nuestros productos de auto y ayudar a la contratación.").send()

@cl.on_message
async def main(message: cl.Message):

    chat_engine = cl.user_session.get("chat_engine")

    msg = cl.Message(content="", author="MAPPI")

    if not message.elements:
        response = await cl.make_async(chat_engine.stream_chat)(message.content)
        msg = cl.Message(content="")

        for token in response.response_gen:
            await msg.stream_token(token=token)

        await msg.send()
    
    else:
    # Procesar exclusivamente imágenes
        images = [file for file in message.elements if "image" in file.mime]

        for image in images:
            next_image_dir = Path(IMAGE_PATH)
            file_path = next_image_dir.joinpath(image.name)
            with open(image.path, "rb") as temp_file:
                image_content = temp_file.read()
            with open(file_path, "wb") as f:
                f.write(image_content)


        print(next_image_dir)
        google_image_documents = SimpleDirectoryReader(next_image_dir).load_data()
        print(f"Loaded {len(google_image_documents)} docs")
        print(message.content)

        text_image = pydantic_gemini(image_documents=google_image_documents)

        response = await cl.make_async(chat_engine.stream_chat)(text_image)
        response_message = cl.Message(content="")

        for token in response.response_gen:
            await response_message.stream_token(token=token)

        await response_message.send()
