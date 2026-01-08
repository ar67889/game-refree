import importlib
import inspect

modules_to_check = [
    'google.adk.models.lite_llm',
    'google.adk.models.gemma_llm',
    'google.adk.models.registry'
]

for mod_name in modules_to_check:
    print(f"\n--- Checking {mod_name} ---")
    try:
        mod = importlib.import_module(mod_name)
        print(f"Dir: {dir(mod)}")
        for name, obj in inspect.getmembers(mod):
            if inspect.isclass(obj) and obj.__module__ == mod_name:
                print(f"Class: {name}")
                print(f"Init: {inspect.signature(obj.__init__)}")
    except ImportError as e:
        print(f"Failed to import {mod_name}: {e}")
