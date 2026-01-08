import inspect
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

print("--- LlmResponse Field Info ---")
for name, field in LlmResponse.model_fields.items():
    print(f"{name}: {field.annotation}")

