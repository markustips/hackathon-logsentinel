"""Test all imports to verify they work."""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

try:
    print("✓ Importing config...")
    from config import get_settings

    print("✓ Importing models...")
    from models import LogFile, LogRecord, Anomaly

    print("✓ Importing database...")
    from database import create_db_and_tables, get_session

    print("✓ Importing services.parser...")
    from services.parser import LogParser

    print("✓ Importing services.indexer...")
    from services.indexer import LogIndexer

    print("✓ Importing services.anomaly...")
    from services.anomaly import AnomalyDetector

    print("✓ Importing services.mitre...")
    from services.mitre import MitreMapper

    print("✓ Importing agents.state...")
    from agents.state import AgentState

    print("✓ Importing agents.tools...")
    from agents.tools import AgentTools

    print("✓ Importing agents.orchestrator...")
    from agents.orchestrator import orchestrator_node

    print("✓ Importing agents.log_analyst...")
    from agents.log_analyst import log_analyst_node

    print("✓ Importing agents.anomaly_hunter...")
    from agents.anomaly_hunter import anomaly_hunter_node

    print("✓ Importing agents.threat_mapper...")
    from agents.threat_mapper import threat_mapper_node

    print("✓ Importing agents.graph...")
    from agents.graph import run_copilot

    print("✓ Importing routers.upload...")
    from routers.upload import router as upload_router

    print("✓ Importing routers.search...")
    from routers.search import router as search_router

    print("✓ Importing routers.anomalies...")
    from routers.anomalies import router as anomalies_router

    print("✓ Importing routers.logs...")
    from routers.logs import router as logs_router

    print("✓ Importing routers.copilot...")
    from routers.copilot import router as copilot_router

    print("\n✅ All imports successful!")
    print("The backend should start without errors.")

except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
