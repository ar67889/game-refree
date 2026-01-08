import inspect
from google.adk.models.base_llm import BaseLlm

print("--- BaseLlm Interface ---")
print(inspect.getdoc(BaseLlm))
print("\n--- Methods ---")
for name, member in inspect.getmembers(BaseLlm):
    if not name.startswith("__"):
        print(f"{name}: {inspect.signature(member) if callable(member) else 'property'}")
