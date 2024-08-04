from typing import Any, List, Optional
from pydantic import Field
from crewai import Crew, Agent
from crewai.tools.agent_tools import AgentTools
from crewai.utilities import I18N

class CustomCrew(Crew):
    tools: Optional[List[Any]] = Field(
        default_factory=list, description="Tools at agents disposal"
    )
    goal: Optional[str] = Field(None, description="Objective of the agent")
    def _run_hierarchical_process(self) -> str:
        """Creates and assigns a manager agent to make sure the crew completes the tasks."""

        i18n = I18N(language=self.language, language_file=self.language_file)

        tools = AgentTools(agents=self.agents).tools()
        if self.tools:
            tools += self.tools

        goal + i18n.retrieve("hierarchical_manager_agent", "goal")
        if self.goal:
            goal += "Your final goal is: " + self.goal

        manager = Agent(
            role=i18n.retrieve("hierarchical_manager_agent", "role"),
            goal=i18n.retrieve("hierarchical_manager_agent", "goal"),
            backstory=i18n.retrieve("hierarchical_manager_agent", "backstory"),
            tools=tools,
            llm=self.manager_llm,
            verbose=True,
        )

        task_output = ""
        for task in self.tasks:
            self._logger.log("debug", f"Working Agent: {manager.role}")
            self._logger.log("info", f"Starting Task: {task.description}")

            if self.output_log_file:
                self._file_handler.log(
                    agent=manager.role, task=task.description, status="started"
                )

            task_output = task.execute(
                agent=manager, context=task_output, tools=manager.tools
            )

            self._logger.log("debug", f"[{manager.role}] Task output: {task_output}")

            if self.output_log_file:
                self._file_handler.log(
                    agent=manager.role, task=task_output, status="completed"
                )

        self._finish_execution(task_output)
        return self._format_output(task_output), manager._token_process.get_summary()
