import inspect
try:
    from google.adk.models.lite_llm import LiteLLM
    print("LiteLLM found.")
    print(inspect.signature(LiteLLM.__init__))
    print(inspect.getdoc(LiteLLM))
except ImportError:
    print("Could not import LiteLLM from google.adk.models.lite_llm")
    # Try finding where it is
    import google.adk.models
    print(dir(google.adk.models))
