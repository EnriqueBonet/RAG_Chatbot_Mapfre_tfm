import nest_asyncio
import asyncio

nest_asyncio.apply()

from llama_index.llms.gemini import Gemini
from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator,BatchEvalRunner
from src.evaluation.qa import qa_creation


import os
import pandas as pd
import random

from src.utils import load_api_key
from src.preprocessing_text import check_and_load_index, load_nodes



# Configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",".."))
API_KEY_PATH = os.path.join(BASE_DIR, "google_api_key.txt")
DATA_PATH = os.path.join(BASE_DIR, "data", "text")

api_key = load_api_key(API_KEY_PATH)
if not api_key:
    raise ValueError("Error: No se pudo cargar la API Key.")
os.environ["GOOGLE_API_KEY"] = api_key

llm = Gemini(model="models/gemini-2.0-flash-exp", api_key=api_key) # problema que Gemini 2.0 peta!
nodes = load_nodes()
vector_index = check_and_load_index()
query_engine = vector_index.as_query_engine()

CSV_FILENAME = (BASE_DIR, "evaluation", "batch_evaluation_results.csv")
SCORES_CSV_FILENAME = (BASE_DIR, "evaluation", "model_scores.csv")


async def evaluate_models():
    CSV_FILENAME = CSV_FILENAME
    SCORES_CSV_FILENAME = SCORES_CSV_FILENAME

    models = {
        "pro1_5": Gemini(model="models/gemini-1.5-pro", api_key=api_key, temperature=0),
        "flash1_5": Gemini(model="models/gemini-1.5-flash", api_key=api_key, temperature=0),
        "flash2": Gemini(model="models/gemini-2.0-flash-exp", api_key=api_key, temperature=0)
    }

    selected_queries = random.sample(list(qa_dataset.queries.values()), min(10, len(qa_dataset.queries)))
    evaluators_per_model = {
        model_name: {
            "faithfulness": FaithfulnessEvaluator(llm=model),
            "relevancy": RelevancyEvaluator(llm=model)
        }
        for model_name, model in models.items()
    }

    all_results = []
    model_scores = []

    for model_name, evaluators in evaluators_per_model.items():
        print(f"Evaluando modelo: {model_name}")
        runner = BatchEvalRunner(evaluators, workers=8)
        eval_results = await runner.aevaluate_queries(query_engine, queries=selected_queries)

        faithfulness_score = sum(result.passing for result in eval_results["faithfulness"]) / len(eval_results["faithfulness"])
        relevancy_score = sum(result.passing for result in eval_results["relevancy"]) / len(eval_results["relevancy"])

        model_scores.append({
            "Model": model_name,
            "Faithfulness Score": faithfulness_score,
            "Relevancy Score": relevancy_score
        })

        for query, eval_data in eval_results.items():
            row = {"Model": model_name, "Query": query}
            if isinstance(eval_data, list):
                eval_data = {evaluator_name: result for evaluator_name, result in zip(evaluators.keys(), eval_data)}
            for eval_name, eval_result in eval_data.items():
                row[eval_name] = eval_result.passing  
            all_results.append(row)

    df_results = pd.DataFrame(all_results)
    df_results.to_csv(CSV_FILENAME, index=False, encoding="utf-8")
    print(f"✅ Resultados guardados en {CSV_FILENAME}")

    df_scores = pd.DataFrame(model_scores)
    df_scores.to_csv(SCORES_CSV_FILENAME, index=False, encoding="utf-8")
    print(f"✅ Scores guardados en {SCORES_CSV_FILENAME}")

    print("🔹 Resultados por consulta:")
    print(df_results)
    print("\n🔹 Scores por modelo:")
    print(df_scores)

if __name__ == "__main__":
    qa_dataset = qa_creation()
    asyncio.run(evaluate_models())

