"""Quick test: verify Cosmos DB is accessible from tool modules."""
import sys
sys.path.insert(0, "src/mcp-server")
from dotenv import load_dotenv
load_dotenv()

from tools.cosmos_client import get_container

# Test each container
containers = ["tickets", "knowledgebase", "systems", "incidents", "employees", "security_alerts", "access_requests", "compliance"]
for name in containers:
    c = get_container(name)
    count = len(list(c.query_items("SELECT c.id FROM c", enable_cross_partition_query=True)))
    print(f"  {name}: {count} items")

print("\nAll containers accessible!")
