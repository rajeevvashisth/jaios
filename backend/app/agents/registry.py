from app.agents.definitions import ALL_AGENT_SPECS
from app.agents.types import AgentSpec


class AgentRegistry:
    """In-process registry of agent specs, keyed by ``agent_key``.

    Deliberately a plain dict over the static specs rather than a DB-driven
    plugin system — 8 agents don't warrant one, and a typed Python
    collection is trivially testable and diffable in code review. DB state
    (enabled/config) is looked up separately by callers that need it.
    """

    def __init__(self, specs: list[AgentSpec]):
        self._by_key = {spec.key: spec for spec in specs}

    def get(self, key: str) -> AgentSpec:
        if key not in self._by_key:
            raise KeyError(f"Unknown agent key: {key}")
        return self._by_key[key]

    def list_specs(self) -> list[AgentSpec]:
        return list(self._by_key.values())

    def tools_for(self, key: str) -> list[str]:
        return self.get(key).allowed_tools

    def can_delegate(self, from_key: str, to_key: str) -> bool:
        return to_key in self.get(from_key).can_delegate_to


agent_registry = AgentRegistry(ALL_AGENT_SPECS)
