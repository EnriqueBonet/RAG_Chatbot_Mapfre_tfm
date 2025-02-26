from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings
)
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini
import os
from src.utils import load_api_key
import pickle

# Configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API_KEY_PATH = os.path.join(BASE_DIR, "google_api_key.txt")
DATA_PATH = os.path.join(BASE_DIR, "data", "text")
EMBEDDINGS_STORAGE = os.path.join(BASE_DIR, "RAG", "embeddings")
NODES_STORAGE = os.path.join(BASE_DIR, "RAG", "nodes", "nodes.pkl") 


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


# Configure GeminiEmbedding
EMBEDDING_MODEL = GeminiEmbedding(model_name="models/text-embedding-004", api_key=api_key)
LLM_MODEL = Gemini(model="models/gemini-2.0-flash-exp", api_key=api_key)
NODE_PARSER = SemanticSplitterNodeParser(
        buffer_size=1,
        breakpoint_percentile_threshold=95,
        embed_model=EMBEDDING_MODEL,
        chunk_size=512,
    )
Settings.llm = LLM_MODEL
Settings.embed_model = EMBEDDING_MODEL
#Settings.chunk_size = chunk_size
#Settings.chunk_overlap = chunk_size // 5
Settings.node_parser = NODE_PARSER


# Función cargar y limpiar documentos
def load_and_clean_documents(DATA_PATH):
    reader = SimpleDirectoryReader(input_dir=DATA_PATH, recursive=True)
    documents = reader.load_data()
    return documents


def create_index():
    storage_path = EMBEDDINGS_STORAGE
    documents = load_and_clean_documents(DATA_PATH)

    nodes= NODE_PARSER.get_nodes_from_documents(documents)
    with open(NODES_STORAGE, "wb") as f:
        pickle.dump(nodes, f)

    # Create the vector index with the settings
    vector_index = VectorStoreIndex(nodes, embed_model=EMBEDDING_MODEL)
    vector_index.storage_context.persist(persist_dir=storage_path)


def load_nodes():
    # Cargar nodos desde un archivo
    if os.path.exists(NODES_STORAGE):
        with open(NODES_STORAGE, "rb") as f:
            return pickle.load(f)
    else:
        raise FileNotFoundError("El archivo de nodos no existe. Asegúrate de crear el índice primero.")


def check_and_load_index():
    """
    Comprueba si se ha creado previamente el índice y, si es el caso, recupera los archivos indexados
    necesarios para cargar el índice. Si no, llama a la función create_index para crearlo.
    """
    storage_path = EMBEDDINGS_STORAGE

    # Verifica si el archivo docstore.json existe en el directorio de almacenamiento
    docstore_path = os.path.join(storage_path, "docstore.json")
    if not os.path.exists(docstore_path):
        print("Índice persistido no encontrado, creando el índice.")
        create_index()
    else:
        print("Índice persistido encontrado, cargando el índice.")

    # Cargar el índice desde el almacenamiento
    storage_context = StorageContext.from_defaults(persist_dir=storage_path)
    index = load_index_from_storage(storage_context)
    
    return index


if __name__ == "__main__":
    index = check_and_load_index()
    print("Índice cargado exitosamente:", index)