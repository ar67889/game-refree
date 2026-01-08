# AI Game Referee - Rock-Paper-Scissors-Plus

This project is a CLI-based implementation of "Rock-Paper-Scissors-Plus" using Python and the Google Gen AI SDK. It features a special "Bomb" move and uses a Function Calling (Tool) approach to enforce game rules and state.

## State Model

The state is tracked using a local dictionary to ensure strict rule enforcement (best of 3, 1 bomb limit).

**State Object:**
*   `current_round` (Integer, 0-3): Tracks the current round number.
*   `user_score` (Integer): The user's number of wins.
*   `bot_score` (Integer): The bot's number of wins.
*   `user_bomb_used` (Boolean): Tracks if the user has used their single "Bomb".
*   `bot_bomb_used` (Boolean): Tracks if the bot has used its single "Bomb".
*   `game_over` (Boolean): Flag to indicate if the game has finished.

## Why this design?
This ensures strict enforcement of the "one bomb per game" rule and "best of 3" limit programmatically, preventing the LLM from losing count or "hallucinating" a score change.

## Setup
1.  Install the SDK: `pip install google-generativeai`
2.  Set your API key: `set GOOGLE_API_KEY=your_key_here` (Windows) or `export GOOGLE_API_KEY=your_key_here` (Linux/Mac)
3.  Run the game: `python game_referee.py`
