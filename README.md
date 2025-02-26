🚀 Multimodal RAG Chatbot for MAPFRE | Master's Thesis Project
------------------------------------------------------------------------------
📌 Project Overview

This project is a Master’s Thesis focused on developing a multimodal chatbot using Retrieval-Augmented Generation (RAG) for MAPFRE. The chatbot runs on Chainlit and provides an enhanced user experience for both new and existing clients seeking information about car insurance.

Additionally, a voice-enabled avatar has been developed, allowing users to interact via voice commands. However, this feature is separate from the RAG-based retrieval system.


🎯 Objectives
The chatbot is designed to improve the user experience for both:
✅ New customers looking to purchase car insurance.
✅ Existing customers who have questions about their current policy or potential rate optimizations.

🔍 Key Features:
🗣️ Voice Interaction via an AI-driven avatar.
📄 RAG-based chatbot that retrieves and generates insurance-related responses.
📸 Image processing capabilities:
Users can upload car images, and the chatbot will extract license plate information, vehicle model, registration year, color, and more.

📂 Project Structure

📦 MAPFRE_RAG_Chatbot
 ┣ 📂 src/                    # Main source code
 ┃ ┣ 📜 app.py                # Main chatbot script
 ┃ ┣ 📜 avatar.py             # Voice-enabled avatar module
 ┃ ┣ 📂 chatbot/              # Core chatbot logic
 ┃ ┣ 📂 llm/                  # Large Language Model integration
 ┃ ┣ 📂 processing/           # Data preprocessing (text & images)
 ┃ ┃ ┣ 📜 preprocessing_images.py
 ┃ ┃ ┣ 📜 preprocessing_text.py
 ┃ ┣ 📂 rag/                  # Retrieval-Augmented Generation module
 ┃ ┃ ┣ 📂 embeddings/
 ┃ ┃ ┣ 📂 nodes/
 ┃ ┃ ┗ 📜 rag_pipeline.py
 ┃ ┣ 📜 prompt.py             # Prompt engineering module
 ┃ ┣ 📜 utils.py              # Utility functions
 ┃ ┣ 📜 voice_text.py         # Voice-to-text and text-to-voice conversion
 ┣ 📂 data/                   # Data storage
 ┃ ┣ 📂 embeddings/           # Precomputed embeddings (excluded from GitHub)
 ┃ ┣ 📂 evaluation/           # Model evaluation data
 ┣ 📂 public/                 # Static files and example assets
 ┣ 📜 .gitignore              # Ignored files and directories
 ┣ 📜 Dockerfile              # Deployment configuration
 ┣ 📜 pyproject.toml          # Poetry configuration
 ┣ 📜 README.md               # Documentation
 ┣ 📜 requirements.txt        # Python dependencies
 ┗ 📜 chainlit.md             # Chainlit usage guide

🔧 Installation & Setup

1️⃣ Prerequisites

Before you can start using the RAG Bot, make sure you have the following prerequisites installed on your system:

- Python 3.12 or higher

2️⃣ Installation

1. Clone this repository to your local machine.
    ```bash
    git clone https://github.com/ssillerom/tfm_valley_2025_g3.git
    cd RAG_CHATBOT
    ```

2. Install dependencies 
    ```bash
    poetry install
    ```

3. Access the enviroment:
    ```bash
    poetry env activate
    ```

4. Configure the GOOGLE API KEY
    - Create a google_api_key.txt file
    - Paste your API key into the file.


5. Run
    ```bash
    chainlit run app.py -w
    ```

