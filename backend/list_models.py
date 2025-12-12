"""List available Gemini models."""
import sys
import google.generativeai as genai

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

print("Checking available Gemini models for your API key...")
print()

try:
    genai.configure(api_key="AIzaSyDDdXaMgLiq4GpfxlKZhUpw4ssKN3-Nyto")

    print("Available models:")
    print("-" * 80)

    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"Model: {model.name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Description: {model.description}")
            print(f"  Supported: {', '.join(model.supported_generation_methods)}")
            print()

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
