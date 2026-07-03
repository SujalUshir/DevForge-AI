"""
Agent Registry — manages active agent singletons.
"""

from typing import Dict, Type
import structlog
from agents.base import BaseAgent

logger = structlog.get_logger(__name__)


class AgentRegistry:
    """
    Central registry keeping track of available agent classes.
    Enables dynamic loading of agent instances based on department requirements.
    """

    def __init__(self):
        self._registry: Dict[str, Type[BaseAgent]] = {}

    def register(self, agent_class: Type[BaseAgent]) -> Type[BaseAgent]:
        """
        Decorator pattern to register a concrete agent class.
        
        Example::
        
            @agent_registry.register
            class ProductLead(BaseAgent):
                ...
        """
        # Create temporary instance to check metadata properties
        temp_instance = agent_class()
        name = temp_instance.name
        
        if name in self._registry:
            logger.warning("agent_registry_duplicate_ignored", name=name)
            return agent_class
            
        self._registry[name] = agent_class
        logger.info("agent_registered", name=name, dept=temp_instance.department)
        return agent_class

    def get_agent_class(self, name: str) -> Type[BaseAgent]:
        """
        Retrieve agent class by name.
        """
        if name not in self._registry:
            raise KeyError(f"Agent '{name}' is not registered in the system.")
        return self._registry[name]

    def get_all_registered_names(self) -> list[str]:
        return list(self._registry.keys())


# Singleton instance shared across backend routes
agent_registry = AgentRegistry()
