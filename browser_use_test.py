from langchain_openai import ChatOpenAI
from browser_use import Agent
from dotenv import load_dotenv
load_dotenv()

import asyncio

llm = ChatOpenAI(model="gpt-4o")

async def main():
    agent = Agent(
        # task="Compare the price of gpt-4o and DeepSeek-V3",
        task=''' 
        You are an advanced browser automation agent tasked with managing a basketball team in Basketball GM. Your goal is to navigate to the league creation page, execute a precise sequence of actions to create a new league, and then make strategic decisions to win the game.
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
        - To simulate, select the dropdown at the top left of the screen that says "Play" , and then you can select "one day", "one month", "one week", "until trade deadline", "until all-star events", or "until playoffs"/
        - There are some key considerations to make here: 
            1) In the pre-season, you may attempt to do up to either THREE roster moves (free agent signings of trades), then must simulate until the trade deadline.
            2) Once simulated to the trade deadline, you may make up to three roster moves (same as above), then must simulate to the end of the season 
            3) Once at the end of the season, either simulate through the playoffs, or simulate to the end of the season if not qualified.
            4) Once you get to the draft, greedily make the best draft decision, then resign players based on contracts, performance, and rating.
        - Always explain your reasoning for each action you take.
        - Prioritize actions that have the highest expected impact on winning games and ultimately securing the championship.

        Guidelines:
        - Be methodical and strategic in your approach.
        - Only interact with elements visible and available in the game interface.
        - Never navigate away from the league page after initialization.
        - Provide clear explanations for your decisions and actions.

        Your mission: Build a championship-winning basketball team through smart, sequential actions and strategic management! 
        ''',

        llm=llm,
    )
    result = await agent.run()
    print(result)

asyncio.run(main())