import logging
import random
import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import aiohttp

# Monkey-patch aiohttp because google-genai expects ClientConnectorDNSError which is missing in recent aiohttp versions
if not hasattr(aiohttp, 'ClientConnectorDNSError'):
    aiohttp.ClientConnectorDNSError = aiohttp.ClientConnectorError

from google.adk.agents import Agent
# from google.adk.tools import Tool # Tool decorator/class not needed in this version

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- State Management ---
# Since no database is allowed, we use a global state dictionary or closure.
# We avoid hardcoded API keys by relying on ADC (which ADK uses by default).

@dataclass
class GameState:
    user_score: int = 0
    bot_score: int = 0
    current_round: int = 1
    user_bomb_used: bool = False
    bot_bomb_used: bool = False
    game_over: bool = False
    round_history: list[str] = field(default_factory=list)
    history: list[Dict[str, Any]] = field(default_factory=list) # Keep original history for results

    def to_dict(self):
        return {
            "current_round": self.current_round,
            "user_score": self.user_score,
            "bot_score": self.bot_score,
            "game_over": self.game_over,
            "round_history": self.round_history,
            "last_result": self.history[-1] if self.history else "No history yet",
        }

# Global state instance
game_state = GameState()

MOVES = ["ROCK", "PAPER", "SCISSORS", "BOMB"]

def manage_game_state(user_move: str, bot_move: str = None) -> Dict[str, Any]:
    """
    Updates the game state based on moves. Validates rules (1 bomb limit, best of 3).
    
    Args:
        user_move: The user's move (ROCK, PAPER, SCISSORS, BOMB).
        bot_move: The bot's move (ROCK, PAPER, SCISSORS, BOMB).
        
    Returns:
        Current game status, winner of the round, and total scores.
    """
    if not user_move:
        return {"error": "User move required."}
    
    if not bot_move:
        bot_move = random.choice(["ROCK", "PAPER", "SCISSORS"])

    user_move = user_move.upper()
    bot_move = bot_move.upper()
    
    if game_state.game_over:
        # Graceful exit with detailed report ensuring requirements are met
        final_winner = "DRAW"
        if game_state.user_score > game_state.bot_score:
            final_winner = "USER WINS"
        elif game_state.bot_score > game_state.user_score:
            final_winner = "BOT WINS"
            
        print("\n" + "="*30)
        print("       GAME OVER")
        print("="*30)
        print(f"Final Score:")
        print(f"User: {game_state.user_score}")
        print(f"Bot:  {game_state.bot_score}")
        print(f"Result: {final_winner}")
        print("="*30 + "\n", flush=True)
        os._exit(0)

    # Validation
    if user_move not in MOVES:
        return {"error": f"Invalid move {user_move}. Valid moves: {MOVES}"}
    if bot_move not in MOVES:
        bot_move = random.choice(["ROCK", "PAPER", "SCISSORS"])

    # Bomb Logic
    user_bomb_active = False
    bot_bomb_active = False
    
    if user_move == "BOMB":
        if game_state.user_bomb_used:
            print(f"\n[Referee]: INVALID MOVE! You already used your BOMB. Please choose ROCK, PAPER, or SCISSORS.\n", flush=True)
            return {
                "message": "You already used your BOMB! It can only be used once per match.",
                "valid_moves": ["ROCK", "PAPER", "SCISSORS"],
                "state": game_state.to_dict()
            }
        game_state.user_bomb_used = True
        user_bomb_active = True
        
    if bot_move == "BOMB":
        if game_state.bot_bomb_used:
            bot_move = "ROCK" # Fallback
        else:
            game_state.bot_bomb_used = True
            bot_bomb_active = True

    # Determine Winner
    winner = None
    msg = ""
    
    result_str = "DRAW" # For print statement

    if user_move == bot_move:
        winner = "DRAW"
        msg = f"Draw! Both chose {user_move}."
        game_state.round_history.append(f"Round {game_state.current_round}: Draw ({user_move})")
        # Rule Change: Each gets a point on Draw
        game_state.user_score += 1
        game_state.bot_score += 1
        result_str = "DRAW"
    elif user_bomb_active:
        winner = "USER"
        game_state.user_score += 1
        msg = f"User BOMB destroys {bot_move}!"
        game_state.round_history.append(f"Round {game_state.current_round}: User wins (BOMB beats {bot_move})")
        result_str = "USER WINS"
    elif bot_bomb_active:
        winner = "BOT"
        game_state.bot_score += 1
        msg = f"Bot BOMB destroys {user_move}!"
        game_state.round_history.append(f"Round {game_state.current_round}: Bot wins (BOMB beats {user_move})")
        result_str = "BOT WINS"
    elif (user_move == "ROCK" and bot_move == "SCISSORS") or \
         (user_move == "SCISSORS" and bot_move == "PAPER") or \
         (user_move == "PAPER" and bot_move == "ROCK"):
        winner = "USER"
        game_state.user_score += 1
        msg = f"{user_move} beats {bot_move}!"
        game_state.round_history.append(f"Round {game_state.current_round}: User wins ({user_move} beats {bot_move})")
        result_str = "USER WINS"
    else:
        winner = "BOT"
        game_state.bot_score += 1
        msg = f"{bot_move} beats {user_move}!"
        game_state.round_history.append(f"Round {game_state.current_round}: Bot wins ({bot_move} beats {user_move})")
        result_str = "BOT WINS"

    # Print Round Summary to Console (Ensures user sees it even if LLM is chat-blocked)
    print(f"\n[Referee]: Round {game_state.current_round} Complete!")
    print(f"   You: {user_move}")
    print(f"   Bot: {bot_move}")
    print(f"   Winner: {result_str}")
    print(f"   Score: User {game_state.user_score} - {game_state.bot_score} Bot\n", flush=True)

    # Round Update
    game_state.current_round += 1
    
    # Check Game Over Conditions
    # User requested fixed 3 rounds (not Best of 3)
    if game_state.current_round > 3:
        game_state.game_over = True
        
        # Immediate Exit if Game Over occurred this turn
        final_winner = "DRAW"
        if game_state.user_score > game_state.bot_score:
            final_winner = "USER WINS"
        elif game_state.bot_score > game_state.user_score:
            final_winner = "BOT WINS"
            
        print("\n" + "="*33)
        print("          GAME OVER")
        print("="*33)
        print(f"Final Score:")
        print(f"User: {game_state.user_score}")
        print(f"Bot:  {game_state.bot_score}")
        print(f"Result: {final_winner}")
        print("="*33 + "\n", flush=True)
        os._exit(0)

    result = {
        "message": msg,
        "round_winner": winner,
        "user_score": game_state.user_score,
        "bot_score": game_state.bot_score,
        "round": game_state.current_round - 1,
        "game_over": game_state.game_over
    }
    game_state.history.append(result)
    return result

# --- Agent Definition ---

SYSTEM_PROMPT = """
You are the AI Referee for Rock-Paper-Scissors-Plus.
Rules:
1. Standard RPS rules.
2. BOMB beats everything but can be used only ONCE per game.
3. Best of 3 rounds.

Instructions:
- The user has provided their move. DO NOT greet. DO NOT ask for the move again if provided.
- Inform the user that Valid moves are ROCK, PAPER, SCISSORS, BOMB (once).
- You MUST call the "manage_game_state" tool to process the turn.
- DO NOT simulate the game in text. DO NOT announce the winner yourself.
- OUTPUT JSON ONLY.
- Example: { "tool_call": "manage_game_state", "args": { "user_move": "ROCK", "bot_move": "SCISSORS" } }

- The ONLY available tool is "manage_game_state". DO NOT use "set_game_state" or any other name.
- Example: { "tool_call": "manage_game_state", "args": { "user_move": "ROCK", "bot_move": "PAPER" } }
- Do not properly calculate the winner yourself. Use the tool.
- If game_over is True, congratulate/console and stop.
"""

# Tool Registration
state_tool = manage_game_state

# Import LocalLlm adapter
try:
    from local_llm import LocalLlm
    print("Using Local LLM (Ollama)")
    # User can change model_name to "llama3" or whatever they have installed
    llm_instance = LocalLlm(model_name="gemma:2b")
except ImportError:
    print("LocalLlm not found, falling back to Vertex")
    llm_instance = "gemini-1.5-flash-001"

game_agent = Agent(
    name="game_referee",
    instruction=SYSTEM_PROMPT,
    model=llm_instance,

    tools=[state_tool]
)

# For 'adk run', we expose the agent object.
# The variable name expected is 'root_agent'.
root_agent = game_agent

if __name__ == "__main__":
    print("--- ADK Game Referee (Main File) ---")
    print("This file contains the ADK Agent definition.")
    print("To run this successfully with the full runtime, use:")
    print("    adk run game_referee:agent")
    print("(Or just `adk run` if configured in pyproject.toml / yaml, but default usage might expect `agent.py`)")
    print("Validating structure...")
    # Minimal check
    print(f"Agent Configured: {agent.name}")
