"""Simple test to check API key and model."""
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

print("Testing Gemini API...")
print()

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage

    # Try the experimental model that was working before (just had quota issues)
    print("Testing with gemini-2.5-flash-lite...")
    llm = ChatGoogleGenerativeAI(
        google_api_key="AIzaSyDDdXaMgLiq4GpfxlKZhUpw4ssKN3-Nyto",
        model="gemini-2.5-flash-lite",
        temperature=0,
        convert_system_message_to_human=True
    )

    print("[OK] LLM instance created")
    print("[OK] Sending test query...")

    response = llm.invoke([HumanMessage(content="Respond with exactly: OK")])

    print(f"\n[SUCCESS] Gemini responded: {response.content}\n")
    print("Gemini API is working!")

except Exception as e:
    error_msg = str(e)
    print(f"\n[ERROR] {error_msg}\n")

    if "quota" in error_msg.lower():
        print("DIAGNOSIS: API key has exceeded its quota.")
        print("The integration is working correctly, but the free tier quota is exhausted.")
        print()
        print("Solutions:")
        print("1. Wait for quota to reset (usually per minute or per day)")
        print("2. Check your quota at: https://ai.dev/usage")
        print("3. Upgrade to paid tier for higher quotas")
        print("4. Try a different Google API key")
    elif "not found" in error_msg.lower():
        print("DIAGNOSIS: Model name is incorrect or not available for this API key.")
        print("The model 'gemini-2.0-flash-exp' may not be accessible.")
    else:
        import traceback
        traceback.print_exc()

    sys.exit(1)
