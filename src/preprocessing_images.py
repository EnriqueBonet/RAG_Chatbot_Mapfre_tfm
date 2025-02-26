import os
from pydantic import BaseModel, Field
from llama_index.multi_modal_llms.gemini import GeminiMultiModal
from llama_index.core.program import MultiModalLLMCompletionProgram
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core import SimpleDirectoryReader
from src.utils import load_api_key

# Configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API_KEY_PATH = os.path.join(BASE_DIR, "google_api_key.txt")

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


# Clase de datos para la información del vehículo
class VehicleInfo(BaseModel):
    """Modelo de datos para información extraída del vehículo."""
    matricula: str = Field(description="Número de matrícula del vehículo")
    año_matricula: int = Field(description="Año de matriculación")
    modelo: str = Field(description="Marca y modelo del vehículo")
    color: str = Field(description="Color del vehículo")

prompt_template_str = """\
    ¿Puedes resumir lo que se muestra en la imagen\
    y devolverlo en formato .json?\
"""


def pydantic_gemini(
    model_name="models/gemini-2.0-flash-exp", output_class=VehicleInfo, image_documents=None, prompt_template_str=prompt_template_str
):
    gemini_llm = GeminiMultiModal(model_name=model_name)

    llm_program = MultiModalLLMCompletionProgram.from_defaults(
        output_parser=PydanticOutputParser(output_class),
        image_documents=image_documents,
        prompt_template_str=prompt_template_str,
        multi_modal_llm=gemini_llm,
        verbose=True,
    )

    response = llm_program()
    response_text = str(response)  # Fallback si no tiene un método json

    return response_text


if __name__ == "__main__":
    google_image_documents = SimpleDirectoryReader(
    "/Users/mmolinaalvarez/Desktop/tfm_valley_2025_g3/data/images"
    ).load_data()
    pydantic_response = pydantic_gemini(image_documents=google_image_documents)
    print(pydantic_response)