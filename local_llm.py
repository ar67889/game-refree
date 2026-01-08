from google.genai.types import Content, Part, FunctionCall
import json
import re
import logging
import aiohttp
import uuid
import ast
import random
from typing import AsyncGenerator, Any

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

logger = logging.getLogger(__name__)

class LocalLlm(BaseLlm):
    """
    Adapter for Local LLMs (via Ollama/OpenAI API).
    Assumes standard OpenAI chat/completions API at base_url.
    """
    model_name: str = "gemma:2b" # Default to a small model common in Ollama
    base_url: str = "http://localhost:11434/v1"
    api_key: str = "ollama"

    def __init__(self, model_name: str = "gemma:2b", base_url: str = "http://localhost:11434/v1", **data):
        # Pass 'model' to BaseLlm as it is a required Pydantic field
        data["model"] = model_name
        super().__init__(**data)
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        
        # Debugging: Print request structure to find System Prompt
        # logger.info(f"LlmRequest Config: {llm_request.config}")

        # Convert ADK contents to OpenAI messages
        messages = []

        # System Instruction
        if llm_request.config and hasattr(llm_request.config, "system_instruction"):
            sys_inst = llm_request.config.system_instruction
            if sys_inst:
                if hasattr(sys_inst, "parts"):
                   sys_text = "\n".join([p.text for p in sys_inst.parts if p.text])
                   messages.append({"role": "system", "content": sys_text})
                else:
                   messages.append({"role": "system", "content": str(sys_inst)})
        
        for content in llm_request.contents:
            role = "user"
            if hasattr(content, "role") and content.role:
                role = content.role
                if role == "model": role = "assistant"
            
            # Handle text parts
            parts_text = []
            tool_calls = []
            
            if hasattr(content, "parts"):
                for part in content.parts:
                    # Text
                    if hasattr(part, "text") and part.text:
                        parts_text.append(part.text)
                    
                    # Tool Call (from Model history)
                    if hasattr(part, "function_call") and part.function_call:
                        # OpenAI format for tool calls
                        fc = part.function_call
                        # Use ID if present, otherwise generate one (though normally ADK keeps it)
                        call_id = fc.id if hasattr(fc, "id") and fc.id else f"call_{uuid.uuid4()}"
                        tool_calls.append({
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": fc.name,
                                "arguments": json.dumps(fc.args) if fc.args else "{}"
                            }
                        })
                    
                    # Tool Response (from User/Tool history)
                    if hasattr(part, "function_response") and part.function_response:
                        fr = part.function_response
                        # OpenAI tool response
                        messages.append({
                            "role": "tool",
                            "tool_call_id": fr.id, # Must match the call ID
                            "content": json.dumps(fr.response) if fr.response else "{}"
                        })
                        # Continue to next part, don't add as text
                        continue

            text_content = "\n".join(parts_text)
            
            # Construct message
            if tool_calls:
                msg = {
                    "role": role,
                    "content": text_content if text_content else None,
                    "tool_calls": tool_calls
                }
                messages.append(msg)
            elif text_content: # Only add if there is text and no tool calls (standard msg) or if mixed (handled above?)
                # If mixed text and tool calls, OpenAI allows content + tool_calls.
                # If we processed tool_calls above, we already added msg.
                # If we processed function_response, we added msg.
                # So here check if we need to add a standard text message
                # If we had function_response, valid inputs loop continues.
                # If we had tool_calls, we added msg.
                # If we only have text, add it.
                messages.append({"role": role, "content": text_content})


        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream
        }

        # Loop Prevention: If the last message was a Tool Result, preventing an immediate follow-up Tool Call
        # allows us to stop 'auto-play' loops where the model simulates the user.
        last_role = messages[-1]["role"] if messages else "system"
        allow_tools = (last_role != "tool")
        
        # logger.info(f"Last Role: {last_role}, Allow Tools: {allow_tools}")

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        url = f"{self.base_url}/chat/completions"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        logger.error(f"Local LLM Error {resp.status}: {err_text}")
                        yield LlmResponse(content=Content(parts=[Part(text=f"Error: {err_text}")]))
                        return

                    if stream:
                        full_content = ""
                        async for line in resp.content:
                            if line:
                                line = line.decode('utf-8').strip()
                                if line.startswith("data: ") and line != "data: [DONE]":
                                    json_str = line[6:]
                                    try:
                                        chunk = json.loads(json_str)
                                        delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                        if delta:
                                            full_content += delta
                                    except:
                                        pass
                        
                        content_to_yield = self._parse_response(full_content, allow_tools=allow_tools)

                        # Fallback: If User provided a move but Model didn't call tool (just chatted), FORCE a tool call.
                        if allow_tools and not content_to_yield.parts[0].function_call:
                            last_user_msg = messages[-1]["content"].upper() if messages else ""
                            match = re.search(r'\b(ROCK|PAPER|SCISSORS|BOMB)\b', last_user_msg)
                            if match:
                                user_move = match.group(1)
                                bot_move = random.choice(["ROCK", "PAPER", "SCISSORS"])
                                call_id = f"call_{uuid.uuid4()}"
                                logger.info(f"Fallback: Forcing Tool Call for '{user_move}' vs '{bot_move}'")
                                content_to_yield = Content(role="model", parts=[Part(
                                    function_call=FunctionCall(
                                        id=call_id, 
                                        name="manage_game_state", 
                                        args={"user_move": user_move, "bot_move": bot_move}
                                    )
                                )])

                        yield LlmResponse(content=content_to_yield, turn_complete=True)

                    else:
                        result = await resp.json()
                        content_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        content_to_yield = self._parse_response(content_text, allow_tools=allow_tools)
                        
                        # Fallback (Non-Streaming)
                        if allow_tools and not content_to_yield.parts[0].function_call:
                            last_user_msg = messages[-1]["content"].upper() if messages else ""
                            # Fix: Support SCISSOR (singular)
                            match = re.search(r'\b(ROCK|PAPER|SCISSORS?|BOMB)\b', last_user_msg)
                            if match:
                                user_move = match.group(1)
                                if "SCISSOR" in user_move: user_move = "SCISSORS" # Normalize
                                
                                bot_move = random.choice(["ROCK", "PAPER", "SCISSORS"])
                                call_id = f"call_{uuid.uuid4()}"
                                logger.info(f"Fallback: Forcing Tool Call for '{user_move}' vs '{bot_move}'")
                                content_to_yield = Content(role="model", parts=[Part(
                                    function_call=FunctionCall(
                                        id=call_id, 
                                        name="manage_game_state", 
                                        args={"user_move": user_move, "bot_move": bot_move}
                                    )
                                )])
                        
                        # OVERRIDE: If user typed BOMB, force it (fixing model hallucination of ROCK)
                        if allow_tools and content_to_yield.parts[0].function_call:
                            fc = content_to_yield.parts[0].function_call
                            if fc.name == "manage_game_state":
                                last_user_msg = messages[-1]["content"].upper() if messages else ""
                                if "BOMB" in last_user_msg:
                                    fc.args["user_move"] = "BOMB"
                                elif "ROCK" in last_user_msg: fc.args["user_move"] = "ROCK"
                                elif "PAPER" in last_user_msg: fc.args["user_move"] = "PAPER"
                                elif "SCISSOR" in last_user_msg: fc.args["user_move"] = "SCISSORS" # Fix override too

                        yield LlmResponse(content=content_to_yield, turn_complete=True)

            except Exception as e:
                logger.error(f"Connection failed: {e}")
                yield LlmResponse(content=Content(parts=[Part(text=f"Error connecting to Local LLM ({url}): {e}")]))

    def _parse_response(self, text: str, allow_tools: bool = True) -> Content:
        """Parses text for JSON tool calls, handling JSON, Python dicts, and chatty formats."""
        text = text.strip()
        
        if not allow_tools:
            # If we are blocking tools (to prevent loops), return text only.
            # But if the text is just a JSON blob, we should properly replace it with a prompt.
            if "tool_call" in text or text.strip().startswith("{"):
                return Content(role="model", parts=[Part(text="Round complete. Waiting for your next move...")])
            return Content(role="model", parts=[Part(text=text)])

        # 0. Try evaluating as a Python literal (handles {'tool_call': ...} single quotes)
        if text.startswith("{") and "tool_call" in text:
            try:
                data = ast.literal_eval(text)
                # ... (rest of function as is, just wrapped in if allow_tools)
                if isinstance(data, dict) and "tool_call" in data:
                    tool_name = data["tool_call"]
                    args = data.get("args", {})
                    call_id = f"call_{uuid.uuid4()}"
                    logger.info(f"Detected Tool Call (AST): {tool_name} {args} id={call_id}")
                    return Content(role="model", parts=[Part(
                        function_call=FunctionCall(id=call_id, name=tool_name, args=args)
                    )])
            except:
                pass

        try:
            # 1. Look for strict JSON block
            json_match = re.search(r'\{.*"tool_call".*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    data = json.loads(json_str)
                    if "tool_call" in data:
                        tool_name = data["tool_call"]
                        args = data.get("args", {})
                        call_id = f"call_{uuid.uuid4()}"
                        logger.info(f"Detected Tool Call (JSON): {tool_name} {args} id={call_id}")
                        return Content(role="model", parts=[Part(
                            function_call=FunctionCall(id=call_id, name=tool_name, args=args)
                        )])
                except json.JSONDecodeError:
                    pass
            
            # 2. Look for chatty format: **tool_call:** name ... **args:** {json}
            if "**tool_call" in text:
                tc_match = re.search(r'\*\*tool_call\W*\*\*\W*["\']?(\w+)["\']?', text)
                if tc_match:
                    tool_name = tc_match.group(1)
                    args = {}
                    args_match = re.search(r'\*\*args\W*\*\*\W*(\{.*?\})', text, re.DOTALL)
                    if args_match:
                        try:
                            args = json.loads(args_match.group(1))
                        except:
                            pass
                    
                    call_id = f"call_{uuid.uuid4()}"
                    logger.info(f"Detected Tool Call (Regex): {tool_name} {args} id={call_id}")
                    return Content(role="model", parts=[Part(
                        function_call=FunctionCall(id=call_id, name=tool_name, args=args)
                    )])

            # 3. Look for lazy comma format: "tool_name", {args}
            comma_match = re.search(r'["\'](\w+)["\'],\s*(\{.*?\})', text, re.DOTALL)
            if comma_match:
                tool_name = comma_match.group(1)
                try:
                    # Try JSON first
                    args = json.loads(comma_match.group(2))
                except:
                    # Try AST for single quotes in args
                    try:
                        args = ast.literal_eval(comma_match.group(2))
                    except:
                        args = {} # Fail
                
                if args:
                    call_id = f"call_{uuid.uuid4()}"
                    logger.info(f"Detected Tool Call (Comma): {tool_name} {args} id={call_id}")
                    return Content(role="model", parts=[Part(
                        function_call=FunctionCall(id=call_id, name=tool_name, args=args)
                    )])

        except Exception as e:
            logger.warning(f"Failed to parse potential tool call: {e}")
        
        return Content(role="model", parts=[Part(text=text)])

