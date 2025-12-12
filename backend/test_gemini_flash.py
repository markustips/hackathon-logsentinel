"""Test Gemini 1.5 Flash integration."""
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

print("Testing gemini-2.5-flash-lite Flash integration...")

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage

    # Use gemini-1.5-flash model (stable, better quota)
    llm = ChatGoogleGenerativeAI(
        google_api_key="AIzaSyDDdXaMgLiq4GpfxlKZhUpw4ssKN3-Nyto",
        model="gemini-2.5-flash-lite",
        temperature=0,
        convert_system_message_to_human=True
    )

    print("[OK] Created gemini-2.5-flash-lite Flash LLM instance")
    print("[OK] Testing simple query...")

    response = llm.invoke([HumanMessage(content="Say 'Hello from Gemini 1.5 Flash!' and nothing else.")])

    print(f"\n[SUCCESS] Gemini responded: {response.content}\n")
    print("gemini-2.5-flash-lite is working perfectly!")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
