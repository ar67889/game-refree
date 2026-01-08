import inspect
from google.genai.types import FunctionCall

print("--- FunctionCall Fields ---")
# Check if it has pydantic fields or just attributes
if hasattr(FunctionCall, "model_fields"):
    print(FunctionCall.model_fields.keys())
else:
    print(dir(FunctionCall))

