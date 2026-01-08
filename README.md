# AI Game Referee - Rock-Paper-Scissors-Plus (Local LLM Edition)

This project is a CLI-based implementation of "Rock-Paper-Scissors-Plus" using the **Google ADK** (`google-adk`) and a **Local LLM** (Ollama/Gemma:2b).

It demonstrates how to build a robust, rule-abiding agent even with small, local language models by offloading logic to Python code and implementing strict input/output adapters.

## 🎮 Game Rules

1.  **3 Rounds Fixed**: The game always consists of exactly 3 rounds. It does not end early.
2.  **Valid Moves**: `ROCK`, `PAPER`, `SCISSORS`, `BOMB`.
3.  **The BOMB 💣**:
    *   Beats everything (Rock, Paper, and Scissors).
    *   **Single Use Only**: You can only use the BOMB **once** per match. Trying to use it a second time is an INVALID move and the round will not proceed until you pick a valid move.
4.  **Scoring**:
    *   **Win**: Winner gets +1 point.
    *   **Draw**: **BOTH** players get +1 point.
5.  **Game Over**: After 3 rounds, a scorecard is displayed, and the process exits.

## 🛠️ Prerequisites

*   **Python 3.10+**
*   **Ollama** installed and running locally.
    *   Download from [ollama.com](https://ollama.com/)
    *   Start the server: `ollama serve`
    *   Pull the model: `ollama pull gemma:2b`
*   **Google ADK**: `pip install google-adk`

## 🚀 How to Run

1.  Open your terminal (PowerShell or CMD on Windows).
2.  **Navigate** to the project directory:
    ```powershell
    cd path/to/project
    ```
3.  **Set Encoding** (Crucial for Windows to display emojis and UI correctly):
    ```powershell
    chcp 65001
    ```
4.  **Run the Agent**:
    ```powershell
    adk run .
    ```

## 🏗️ Architecture & Robustness

This agent uses a custom `LocalLlm` adapter (`local_llm.py`) to interface with Ollama (since ADK defaults to Gemini/Vertex). It includes several robustness layers to handle the limitations of smaller local models like `gemma:2b`:

*   **Turn Enforcement**: Prevents the LLM from auto-playing multiple rounds at once.
*   **Input Override**: If you type "BOMB", the system forces the move to be "BOMB", fixing cases where the model hallucinates "ROCK".
*   **Fallback Logic**: If the model chats instead of calling the game tool, the system detects your move keyword and force-executes the game logic.
*   **Strict State**: All game rules (scores, history, round limits) are enforced by Python code in `agent.py`, ensuring fair play.
