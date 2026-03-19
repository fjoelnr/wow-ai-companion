class CoachAgent:
    """
    Nimmt Session + Plan und erzeugt ggf. Prompt zum MCP-Tool `generate_tips`.
    """
    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url

    def create_tips(self, session: dict, n: int) -> list[str]:
        # z. B. HTTP POST zu /tools/generate_tips
        return []
