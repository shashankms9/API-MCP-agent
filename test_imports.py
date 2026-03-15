"""Test SDK imports and RunStatus values."""
from azure.ai.agents.models import RequiredFunctionToolCall, ToolOutput, RunStatus
print("Imports OK")
print(f"REQUIRES_ACTION = {RunStatus.REQUIRES_ACTION}")
print(f"QUEUED = {RunStatus.QUEUED}")
print(f"IN_PROGRESS = {RunStatus.IN_PROGRESS}")
print(f"COMPLETED = {RunStatus.COMPLETED}")
print(f"FAILED = {RunStatus.FAILED}")
