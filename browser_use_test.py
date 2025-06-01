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
        ESSENTIALLY, RUN THE EQUIVALENT OF THE FOLLOWING ACTIONS:
        1) await page.goto("https://play.basketball-gm.com/l/1/trade")
        2) await page.get_by_role("link", name="Create a new league").click()
        3) await page.get_by_role("combobox").nth(2).select_option("real")
        4) await page.get_by_role("button", name="Create League Processing").click()
        5) await page.get_by_role("button", name="Play", exact=True).click()
        6) await page.get_by_role("button", name="Until regular season").click()
        7) await page.get_by_role("button", name="Play", exact=True).click()
        8) await page.get_by_role("button", name="Until trade deadline").click()

        Step 4: Strategic Gameplay
        IF YOU HAVE NOT DONE THIS ALREADY, DO THE FOLLOWING FOUR STEPS!!!!!
         5) await page.get_by_role("button", name="Play", exact=True).click() --- CLICK ON THE GREEN PLAY BUTTON AT THE TP OF THE SCREEN
        6) await page.get_by_role("button", name="Until regular season").click()
        7) await page.get_by_role("button", name="Play", exact=True).click()
        8) await page.get_by_role("button", name="Until trade deadline").click() --- THIS IS CRUCIAL: MAKE SURE YOU SELECT THE RIGHT DROP DOWN MENU: "simulate until trade deadline"
        - Your objective is to make decisions and take actions that will maximize your team's chances of winning the championship, starting at the trade deadline.
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

        AFTER THIS CRITICAL STEP, RUN THE EQUIVALENT OF THE FOLLOWING ACTIONS WHEN READY
        1) await page.get_by_role("button", name="Play", exact=True).click()
        2) await page.get_by_role("button", name="Until playoffs").click()
        3) await page.get_by_role("button", name="Play", exact=True).click()
        4) await page.get_by_role("button", name="Through playoffs").click()
        5) await page.get_by_role("button", name="Play", exact=True).click()
        6) await page.get_by_role("link", name="Read new message").click()

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