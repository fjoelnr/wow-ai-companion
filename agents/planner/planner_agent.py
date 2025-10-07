class PlannerAgent:
    """
    Entscheidet, welche Tools genutzt werden sollen (z. B. lookup, generate_tips etc.)
    Orchestriert Workflows.
    """
    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url

    def plan(self, session: dict) -> dict:
        """
        Input: Session-Daten
        Output: Plan mit Aktionen, z. B.
          { "do_tips": True, "lookup_zone_info": True, ... }
        """
        # Platzhalter
        return {}
