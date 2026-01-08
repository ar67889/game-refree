import inspect
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm  # Should work after pip install

print("--- Agent Init Signature ---")
print(inspect.signature(Agent.__init__))

print("\n--- LiteLlm Init Signature ---")
print(inspect.signature(LiteLlm.__init__))

print("\n--- LiteLlm Doc ---")
print(inspect.getdoc(LiteLlm))
