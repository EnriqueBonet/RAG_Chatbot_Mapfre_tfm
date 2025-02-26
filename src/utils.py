# Cargar API KEY
def load_api_key(file_path: str) -> str:
    try:
        with open(file_path, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        print("Error: No se encontró el archivo con la API Key.")
        return ""
    

