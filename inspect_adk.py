import google.adk.models
import pkgutil
import inspect

print("--- ADK Models Inspection ---")
if hasattr(google.adk.models, '__path__'):
    for importer, modname, ispkg in pkgutil.iter_modules(google.adk.models.__path__):
        print(f"Module: {modname}")
else:
    print("google.adk.models has no __path__")

print("\nClasses in google.adk.models:")
for name, obj in inspect.getmembers(google.adk.models):
    if inspect.isclass(obj):
        print(f"Class: {name}")

try:
    from google.adk.models import Model
    print("\nModel Interface:")
    print(dir(Model))
except ImportError:
    print("\nCould not import Model from google.adk.models")
