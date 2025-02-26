from llama_index.core.evaluation import generate_question_context_pairs
from llama_index.llms.gemini import Gemini
import pickle
import os

from src.utils import load_api_key
from src.preprocessing_text import check_and_load_index, load_nodes

# Configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
API_KEY_PATH = os.path.join(BASE_DIR, "google_api_key.txt")
DATA_PATH = os.path.join(BASE_DIR, "data", "text")

api_key = load_api_key(API_KEY_PATH)
if not api_key:
    raise ValueError("Error: No se pudo cargar la API Key.")
os.environ["GOOGLE_API_KEY"] = api_key

llm = Gemini(model="models/gemini-2.0-flash-exp", api_key=api_key)  # problema que Gemini 2.0 peta!
nodes = load_nodes()
qa_file_path = os.path.join("evaluation", "q&a.pkl")


def qa_creation():
    """Verifica si existe un archivo de preguntas y respuestas, si no lo genera."""
    if os.path.exists(qa_file_path):
        print("Archivo de preguntas y respuestas encontrado. Cargando datos...")
        with open(qa_file_path, 'rb') as file:
            qa_dataset = pickle.load(file)
    else:
        print("Archivo de preguntas y respuestas no encontrado. Generando datos...")
        qa_dataset = generate_question_context_pairs(
            nodes=nodes,
            llm=llm,
            num_questions_per_chunk=1
        )
        # Guardar el archivo generado en formato pickle
        with open(qa_file_path, 'wb') as f:
            pickle.dump(qa_dataset, f)
        print("Archivo de preguntas y respuestas guardado en formato pickle en:", qa_file_path)
        with open(qa_file_path, 'rb') as file:
            qa_dataset = pickle.load(file)
    return qa_dataset



if __name__ == "__main__":
    qa_dataset = qa_creation()
