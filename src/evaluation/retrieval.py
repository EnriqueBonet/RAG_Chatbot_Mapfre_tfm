import nest_asyncio
import asyncio

nest_asyncio.apply()

from llama_index.core.evaluation import RetrieverEvaluator
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
import pickle

import os
import pandas as pd

from src.utils import load_api_key
from src.preprocessing_text import check_and_load_index, load_nodes
from src.evaluation.qa import qa_creation


# Configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
API_KEY_PATH = os.path.join(BASE_DIR, "google_api_key.txt")

api_key = load_api_key(API_KEY_PATH)
if not api_key:
    raise ValueError("Error: No se pudo cargar la API Key.")
os.environ["GOOGLE_API_KEY"] = api_key

llm = Gemini(model="models/gemini-2.0-flash-exp", api_key=api_key)
nodes = load_nodes()
vector_index = check_and_load_index()
qa_file_path = os.path.join("evaluation", "q&a.pkl")
output_path = os.path.join("evaluation", "retrieval_eval.csv")



qa_dataset = qa_creation()
retriever = vector_index.as_retriever(similarity_top_k=2)    
retriever_evaluator = RetrieverEvaluator.from_metric_names(["mrr", "hit_rate"], retriever=retriever)



def split_queries(queries, chunk_size):
    """Divide un diccionario de queries en fragmentos más pequeños."""
    query_items = list(queries.items())
    return [dict(query_items[i:i + chunk_size]) for i in range(0, len(query_items), chunk_size)]

async def evaluate_dataset_in_chunks(retriever_evaluator, qa_dataset, chunk_size=5, workers=2):
    """Evalúa el dataset en fragmentos y une los resultados."""
    query_chunks = split_queries(qa_dataset.queries, chunk_size)
    eval_results = []
    
    async def evaluate_chunk(chunk):
        chunk_dataset = qa_dataset.model_copy(update={"queries": chunk})
        try:
            return await retriever_evaluator.aevaluate_dataset(chunk_dataset, workers=workers)
        except Exception as e:
            print(f"Error evaluando un chunk: {e}")
            return []

    tasks = [evaluate_chunk(chunk) for chunk in query_chunks]
    chunk_results = await asyncio.gather(*tasks)

    for result in chunk_results:
        eval_results.extend(result)

    return eval_results

def display_results(name, final_results):
    """Display results from evaluate."""
    metric_dicts = [result.metric_vals_dict for result in final_results]
    full_df = pd.DataFrame(metric_dicts)
    hit_rate = full_df["hit_rate"].mean()
    mrr = full_df["mrr"].mean()
    metric_df = pd.DataFrame({"Retriever Name": [name], "Hit Rate": [hit_rate], "MRR": [mrr]})

    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        if name in existing_df["Retriever Name"].values:
            print(f"Resultados para '{name}' ya existen. No se repetirán.")
            return existing_df
        updated_df = pd.concat([existing_df, metric_df], ignore_index=True)
    else:
        updated_df = metric_df

    updated_df.to_csv(output_path, index=False)
    print(f"Resultados guardados en {output_path}")
    return updated_df

async def main():
    retriever_name = "Gemini Embedding Retriever"
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        if retriever_name in existing_df["Retriever Name"].values:
            print(f"Evaluación ya realizada para {retriever_name}. Cargando resultados previos.")
            return existing_df
    eval_results = await evaluate_dataset_in_chunks(retriever_evaluator, qa_dataset, chunk_size=10, workers=1)
    print(f"Evaluación completada con {len(eval_results)} resultados.")
    return eval_results

if __name__ == "__main__":
    final_results = asyncio.run(main())

    if isinstance(final_results, pd.DataFrame):
        print(final_results)
    else:
        print(display_results("Gemini Embedding Retriever", final_results))
