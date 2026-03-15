"""
MCP Tool 2: Knowledge Base (backed by Cosmos DB)
Search troubleshooting articles for known solutions across all IT categories.
Container: knowledgebase (partition key: /category)
"""

import json
from .cosmos_client import get_container

CONTAINER_NAME = "knowledgebase"


def search_knowledge_base(query: str) -> str:
    """Search the IT knowledge base for troubleshooting steps and known solutions.

    :param query: Describe the issue or symptoms, e.g. 'VPN keeps disconnecting' or 'password locked out'
    :return: JSON with matching KB articles and solutions
    """
    container = get_container(CONTAINER_NAME)
    articles = list(container.query_items(
        query="SELECT * FROM c",
        enable_cross_partition_query=True,
    ))

    query_lower = query.lower()
    scored = []
    for article in articles:
        score = 0
        for symptom in article.get("symptoms", []):
            if symptom in query_lower:
                score += 3
            else:
                for word in symptom.split():
                    if len(word) > 2 and word in query_lower:
                        score += 1
        for word in article.get("title", "").lower().split():
            if len(word) > 2 and word in query_lower:
                score += 1
        if article.get("category", "").lower() in query_lower:
            score += 2
        if score > 0:
            scored.append((score, article))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:3]
    if not top:
        return json.dumps({
            "message": f"No KB articles found for: '{query}'. Consider creating a support ticket.",
            "articles": [],
        })

    results = [{"id": a["id"], "title": a["title"], "category": a["category"], "solution": a["solution"]} for _, a in top]
    return json.dumps({"count": len(results), "articles": results}, indent=2)


def list_kb_categories() -> str:
    """List all available knowledge base categories and article counts.

    :return: JSON with categories and counts
    """
    container = get_container(CONTAINER_NAME)
    articles = list(container.query_items(
        query="SELECT c.category FROM c",
        enable_cross_partition_query=True,
    ))
    cats = {}
    for a in articles:
        cat = a["category"]
        cats[cat] = cats.get(cat, 0) + 1
    return json.dumps({
        "total_articles": len(articles),
        "categories": cats,
    }, indent=2)


ALL_FUNCTIONS = {search_knowledge_base, list_kb_categories}
