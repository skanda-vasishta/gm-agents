import asyncio
from autogen_agentchat.ui import Console
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer


async def main() -> None:
    # Define an agent
    web_surfer_agent = MultimodalWebSurfer(
        name="MultimodalWebSurfer",
        model_client=OpenAIChatCompletionClient(model="gpt-4o-2024-08-06"),
        headless=False,
    )

    # Define a team
    agent_team = RoundRobinGroupChat([web_surfer_agent], max_turns=3)

    # Run the team and stream messages to the console
    stream = agent_team.run_stream(task= '''You are an advanced browser automation agent tasked with managing a basketball team in Basketball GM. Your goal is to navigate to the league creation page, execute a precise sequence of actions to create a new league, and then make strategic decisions to win the game.

        Step 1: Navigate to the League Creation Page
        - Go to: https://play.basketball-gm.com/l/1/trade

        Step 2: Execute the Following Actions Sequentially (using Playwright or equivalent browser automation):
        1. Click the link with role "link" and name "Create a new league".
        2. Click the button with role "button" and name "Random".
        3. Select the option "real" from the combobox at index 2.
        4. Click the second button with role "button" and name "Random" (nth=1).
        5. Click the button with role "button" and name "Create League Processing".

        Step 3: After the League is Created
        - Navigate to the main league page: https://play.basketball-gm.com/l/1
        - From this point forward, only interact with the game interface within this league. Do not leave this page or navigate to any external sites.

        Step 4: Strategic Gameplay
        - Your objective is to make decisions and take actions that will maximize your team's chances of winning the championship.
        - Analyze the current state of your team, roster, finances, and available actions.
        - Consider simulating games, making trades, signing free agents, adjusting lineups, and any other actions that could improve your team's performance.
        - Always explain your reasoning for each action you take.
        - Prioritize actions that have the highest expected impact on winning games and ultimately securing the championship.

        Guidelines:
        - Be methodical and strategic in your approach.
        - Only interact with elements visible and available in the game interface.
        - Never navigate away from the league page after initialization.
        - Provide clear explanations for your decisions and actions.

        Your mission: Build a championship-winning basketball team through smart, sequential actions and strategic management! 
        ''')
    await Console(stream)
    # Close the browser controlled by the agent
    await web_surfer_agent.close()


asyncio.run(main())

