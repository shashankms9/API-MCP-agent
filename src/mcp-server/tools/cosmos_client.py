"""
Shared Cosmos DB client for all MCP tool modules.
Uses DefaultAzureCredential for authentication (RBAC-based, no keys).
"""

import os
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

COSMOS_ENDPOINT = os.environ.get(
    "COSMOS_ENDPOINT",
    "https://cosmos-challenge5-mhdnafeklrure.documents.azure.com:443/"
)
DATABASE_NAME = os.environ.get("COSMOS_DATABASE", "helpdesk-db")

_client = None
_db = None


def get_db():
    """Get the Cosmos DB database client (singleton)."""
    global _client, _db
    if _db is None:
        credential = DefaultAzureCredential()
        _client = CosmosClient(COSMOS_ENDPOINT, credential=credential)
        _db = _client.get_database_client(DATABASE_NAME)
    return _db


def get_container(name: str):
    """Get a Cosmos DB container client by name."""
    return get_db().get_container_client(name)
