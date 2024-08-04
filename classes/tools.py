"""Tool for asking human input."""

from typing import Callable, Optional
from crewai_tools import BaseTool


class HumanInput(BaseTool):
    """Tool that asks user for input."""

    name: str = "human-input"
    description: str = (
        "You can ask a human when required or when something is not clear or you think you "
        "got stuck and you need guidance or you are not sure what to do next. "
        "The input should be a question for the human. "
    )
    prompt_func: Callable[[str], None]

    def _run(self, query: str) -> str:
        """Use the Human input tool."""
        return_value = self.prompt_func(query)
        print(f"Human input: {return_value}")
        return return_value
