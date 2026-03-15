"""
Challenge 5 - Microsoft Agent Framework + MCP Tools Integration

This agent uses Azure AI Agent Service (Microsoft Foundry) to:
1. Create an AI agent with defined roles and intents
2. Connect to a remote MCP server for tool execution
3. Route inference through APIM gateway for secure communication
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import (
    Agent,
    AgentThread,
    MessageRole,
    RunStatus,
    ThreadMessage,
)
from azure.identity import DefaultAzureCredential

from config import load_config

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def create_project_client(config) -> AgentsClient:
    """Create an authenticated Agents client using Foundry endpoint."""
    credential = DefaultAzureCredential()
    client = AgentsClient(
        endpoint=config.foundry_endpoint,
        credential=credential,
    )
    return client


def create_agent(
    client: AgentsClient,
    model: str,
    name: str,
    instructions: str,
) -> Agent:
    """
    Create an agent with the Microsoft Agent Framework.
    Defines agent role via instructions and connects to the Foundry backend.
    """
    agent = client.create_agent(
        model=model,
        name=name,
        instructions=instructions,
    )
    print(f"[INFO] Agent created: {agent.name} (id={agent.id})")
    return agent


def run_conversation(client: AgentsClient, agent: Agent, user_message: str) -> str:
    """
    Run a single-turn conversation with the agent.
    Creates a thread, sends a message, runs the agent, and returns the response.
    """
    # Create a conversation thread
    thread: AgentThread = client.threads.create()
    print(f"[INFO] Thread created: {thread.id}")

    # Send user message
    client.messages.create(
        thread_id=thread.id,
        role=MessageRole.USER,
        content=user_message,
    )
    print(f"[USER] {user_message}")

    # Run the agent on this thread
    run = client.runs.create_and_process(
        thread_id=thread.id,
        agent_id=agent.id,
    )

    if run.status == RunStatus.FAILED:
        print(f"[ERROR] Run failed: {run.last_error}")
        return f"Error: {run.last_error}"

    # Retrieve messages
    messages = client.messages.list(thread_id=thread.id)

    # Get the last assistant message
    for msg in reversed(messages.data):
        if msg.role == MessageRole.AGENT:
            response_text = msg.content[0].text.value if msg.content else "(empty)"
            print(f"[AGENT] {response_text}")
            return response_text

    return "(no response)"


def cleanup(client: AgentsClient, agent: Agent):
    """Delete the agent to clean up resources."""
    client.delete_agent(agent.id)
    print(f"[INFO] Agent deleted: {agent.id}")


def main():
    """Main entry point for the Challenge 5 agent."""
    print("=" * 60)
    print("Challenge 5: Microsoft Agent Framework + MCP Integration")
    print("=" * 60)

    # Load configuration
    config = load_config()

    # Create project client
    client = create_project_client(config)
    print(f"[INFO] Connected to Foundry project: {config.project_name}")

    # Create agent
    agent = create_agent(
        client=client,
        model=config.model_deployment_name,
        name=config.agent_name,
        instructions=config.agent_instructions,
    )

    try:
        # Interactive conversation loop
        print("\n--- Agent Ready. Type 'quit' to exit. ---\n")
        while True:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                break

            response = run_conversation(client, agent, user_input)
            print(f"\nAssistant: {response}\n")

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")
    finally:
        cleanup(client, agent)
        print("[INFO] Done.")


if __name__ == "__main__":
    main()
