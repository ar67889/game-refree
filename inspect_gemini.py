import inspect
from google.adk.models.google_llm import Gemini

print("--- Gemini Class Methods ---")
for name, member in inspect.getmembers(Gemini):
    if not name.startswith("_") or name == "__call__":
        print(f"{name}: {inspect.signature(member) if callable(member) else 'property'}")

print("\n--- Gemini.generate_content_async Source (First 10 lines) ---")
try:
    src = inspect.getsource(Gemini.generate_content_async)
    print("\n".join(src.splitlines()[:20]))
except Exception as e:
    print(f"Could not get source: {e}")
