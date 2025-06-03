from langchain_openai import ChatOpenAI
from browser_use import Agent, Controller, ActionResult
from dotenv import load_dotenv
from playwright.async_api import Page
import asyncio
from basketball_decision import make_basketball_decision  # Import the new function
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
# from .models import GameState  # wherever you save the GameState model

load_dotenv()

llm = ChatOpenAI(model="gpt-4o")

controller = Controller()

class GameState(BaseModel):
    current_season: int = Field(..., description="Current season number")
    current_phase: str = Field(..., description="Game phase (e.g., regular_season, playoffs, draft, free_agency, preseason)")
    team_wins: int = Field(..., description="Number of team wins")
    team_losses: int = Field(..., description="Number of team losses")
    salary_cap_used: float = Field(..., description="Salary cap used")
    roster_size: int = Field(..., description="Number of players on the roster")
    available_cap_space: float = Field(..., description="Available salary cap space")
    team_rating: int = Field(..., description="Overall team rating")
    playoff_position: Optional[str] = Field(None, description="Current playoff position")
    roster_data: Optional[Dict] = Field(None, description="Detailed roster data")
    upcoming_schedule: Optional[List] = Field(None, description="Upcoming games")
    trade_offers: Optional[List] = Field(None, description="Current trade offers")
    free_agents: Optional[List] = Field(None, description="Available free agents")
    draft_prospects: Optional[List] = Field(None, description="Draft prospects")

def log_game_state(state, filename="game_state_log.txt"):
    # Print to terminal
    print("Current Game State:")
    print(state)
    print("-" * 40)
    # Write to file (append mode)
    with open(filename, "a") as f:
        f.write(str(state) + "\n" + "-"*40 + "\n")

@controller.action('Get basketball management decision', param_model=GameState)
async def get_basketball_decision(params: GameState, page: Page) -> ActionResult:
    # Log the state
    log_game_state(params.model_dump())
    # Use params (which is a GameState instance)
    decision = await make_basketball_decision(params.model_dump())
    return ActionResult(extracted_content=decision, include_in_memory=True)

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

        Step 3: At Trade Deadline - IMPORTANT
         IF YOU HAVE NOT DONE THIS ALREADY, DO THE FOLLOWING FOUR STEPS!!!!!
         5) await page.get_by_role("button", name="Play", exact=True).click() --- CLICK ON THE GREEN PLAY BUTTON AT THE TP OF THE SCREEN
        6) await page.get_by_role("button", name="Until regular season").click()
        7) await page.get_by_role("button", name="Play", exact=True).click()
        8) await page.get_by_role("button", name="Until trade deadline").click() --- THIS IS CRUCIAL: MAKE SURE YOU SELECT THE RIGHT DROP DOWN MENU: "simulate until trade deadline"
        - Your objective is to make decisions and take actions that will maximize your team's chances of winning the championship, starting at the trade deadline.
        When you reach the trade deadline, you MUST:
        1) Extract the current game state including:
           - Current season
           - Team wins/losses
           - Salary cap used
           - Roster size
           - Available cap space
           - Team rating
           - Playoff position
           - Roster data
           - Upcoming schedule
           - Trade offers
           - Free agents
           - Draft prospects
        2) Call the get_basketball_decision action with this state
        3) Log the state to game_state_log.txt
        4) Make decisions based on the returned recommendation

        Step 4: Strategic Gameplay
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
        - IMPORTANT: Always call get_basketball_decision and log the state when reaching the trade deadline.

        Your mission: Build a championship-winning basketball team through smart, sequential actions and strategic management! 
        ''',
        llm=llm,
        controller=controller,
    )
    result = await agent.run()
    print(result)

asyncio.run(main())