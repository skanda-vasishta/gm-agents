from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import re
from playwright.sync_api import Page, expect, sync_playwright
import asyncio, json
from typing import Sequence, TypedDict, Any
from playwright.async_api import Playwright, async_playwright, expect

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.agents.web_surfer import MultimodalWebSurfer, PlaywrightController
from autogen_ext.models.openai import OpenAIChatCompletionClient

load_dotenv()

llm = ChatOpenAI(model="gpt-4o")
model_client = OpenAIChatCompletionClient(model="gpt-4o")

async def run(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://play.basketball-gm.com/l/1/trade")
    await page.get_by_role("link", name="Create a new league").click()
    await page.get_by_role("combobox").nth(2).select_option("real")
    await page.get_by_role("button", name="Create League Processing").click()
    await page.get_by_role("button", name="Play", exact=True).click()
    await page.get_by_role("button", name="Until regular season").click()
    await page.get_by_role("button", name="Play", exact=True).click()
    await page.get_by_role("button", name="Until trade deadline").click()
    return page

async def main():
    # Create Playwright instance and get page
    pw = await async_playwright().start()
    page = await run(pw)

    # Create the web surfer agent with the existing page
    web_surfer = MultimodalWebSurfer(
        name="BasketballGM",
        model_client=model_client,
        headless=False,
    )

    # Configure the PlaywrightController with our existing page
    web_surfer._playwright_controller = PlaywrightController(
        animate_actions=True,
    )
    web_surfer._playwright_controller.page = page

    # Create the team with model_client
    team = SelectorGroupChat(
        agents=[web_surfer],
        model_client=model_client,
        max_turns=10
    )

    # Run the team
    task = """
    You are an advanced browser automation agent tasked with managing a basketball team in Basketball GM. Your goal is to navigate to the league creation page, execute a precise sequence of actions to create a new league, and then make strategic decisions to win the game.

    Step 1: Navigate to the League Creation Page
    - Go to: https://play.basketball-gm.com/l/1/trade

    Step 2: Execute the Following Actions Sequentially:
    1. Click the link with role "link" and name "Create a new league"
    2. Click the button with role "button" and name "Random"
    3. Select the option "real" from the combobox at index 2
    4. Click the second button with role "button" and name "Random" (nth=1)
    5. Click the button with role "button" and name "Create League Processing"

    Step 3: After the League is Created
    - Navigate to the main league page: https://play.basketball-gm.com/l/1
    - From this point forward, only interact with the game interface within this league

    Step 4: Strategic Gameplay
    - Make decisions to maximize your team's chances of winning
    - Consider simulating games, making trades, signing free agents, adjusting lineups
    - Always explain your reasoning for each action
    """
    
    await Console(team.run_stream(task=task))

    # Cleanup
    await page.close()
    await pw.stop()

if __name__ == "__main__":
    asyncio.run(main())