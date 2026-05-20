import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from  app.agent_langgraph.wc_nodes.api_ingestion_node import api_ingestion_node

# Simulate the state the worker will pass in
fake_state = {
    'data_source':   'api',
    'policy_number': 'MWC0183363-05',
}

result = api_ingestion_node(fake_state)

print(f'  Count: {len(result["excel_records"])}')
print(f'  First: {result["excel_records"][0]}')

print()
print('=== xml_records (class codes) ===')
print(f'  Count: {len(result["xml_records"])}')
print(f'  First: {result["xml_records"][0]}')

print()
print('=== audit_xl_records (audit meta) ===')
print(f'  {result["audit_xl_records"]}')

print()
print('=== policy_config ===')
print(f'  {result["policy_config"]}')

print()
print('=== errors ===')
print(f'  {result.get("errors", "none")}')