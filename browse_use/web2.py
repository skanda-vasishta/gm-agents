from langchain_openai import ChatOpenAI
from browser_use import Agent, Controller, ActionResult
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from pathlib import Path
from playwright.async_api import Page

load_dotenv()

import asyncio

class GameState(BaseModel):
    record: str
    team_rating: int
    average_mov: float
    average_age: float
    open_roster_spots: int
    payroll: float
    salary_cap: float
    profit: float


controller = Controller()

# @controller.action('Get game state', param_model=GameState)
# async def get_state(params: GameState, page: Page) -> ActionResult:
#     await page.get_by_role("link", name="Dashboard", exact=True).click()

#     record = await page.locator("text=Record").nth(0).evaluate("el => el.nextSibling.textContent")  # or use regex if needed
#     team_rating = int((await page.locator("text=Team rating:").text_content()).split(":")[1].split("/")[0].strip())
#     average_mov = float((await page.locator("text=Average MOV:").text_content()).split(":")[1].strip())
#     average_age = float((await page.locator("text=Average age:").text_content()).split(":")[1].strip())
#     open_roster_spots = int((await page.locator("text=open roster spots").text_content()).split(" ")[0])
#     payroll = float((await page.locator("text=Payroll:").text_content()).split("$")[1].replace("M", ""))
#     salary_cap = float((await page.locator("text=Salary cap:").text_content()).split("$")[1].replace("M", ""))
#     profit = float((await page.locator("text=Profit:").text_content()).split("$")[1].replace("M", ""))

#     state = GameState(
#         record=record,
#         team_rating=team_rating,
#         average_mov=average_mov,
#         average_age=average_age,
#         open_roster_spots=open_roster_spots,
#         payroll=payroll,
#         salary_cap=salary_cap,
#         profit=profit
#     )
#     print(state.model_dump_json())
#     return ActionResult(extracted_content=state.model_dump_json())


@controller.action('Ask human for help with a question', domains=['https://play.basketball-gm.com'])   # pass allowed_domains= or page_filter= to limit actions to certain pages
def ask_human(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)


async def get_state_hook(agent: Agent):
    page = await agent.browser_session.get_current_page() 
    try:
        await page.get_by_role("link", name="Dashboard", exact=True).click()

        record = await page.locator("text=Record").nth(0).evaluate("el => el.nextSibling.textContent")
        team_rating = int((await page.locator("text=Team rating:").text_content()).split(":")[1].split("/")[0].strip())
        average_mov = float((await page.locator("text=Average MOV:").text_content()).split(":")[1].strip())
        average_age = float((await page.locator("text=Average age:").text_content()).split(":")[1].strip())
        open_roster_spots = int((await page.locator("text=open roster spots").text_content()).split(" ")[0])
        payroll = float((await page.locator("text=Payroll:").text_content()).split("$")[1].replace("M", ""))
        salary_cap = float((await page.locator("text=Salary cap:").text_content()).split("$")[1].replace("M", ""))
        profit = float((await page.locator("text=Profit:").text_content()).split("$")[1].replace("M", ""))
    except Exception:
        record = "0-0"
        team_rating = 0
        average_mov = 0.0
        average_age = 0.0
        open_roster_spots = 0
        payroll = 0.0
        salary_cap = 0.0
        profit = 0.0

    state = GameState(
        record=record,
        team_rating=team_rating,
        average_mov=average_mov,
        average_age=average_age,
        open_roster_spots=open_roster_spots,
        payroll=payroll,
        salary_cap=salary_cap,
        profit=profit
    )
    state_json = state.model_dump_json()
    print(state_json)
    with open("state_log.txt", "a") as logf:
        logf.write(state_json + "\\n")

    return ActionResult(extracted_content=state.model_dump_json())


async def main():
    with open("instructions.txt", "r") as f:
        task = f.read()

    model = ChatOpenAI(model='gpt-4o')
    agent = Agent(task=task, llm=model, controller=controller)

    await agent.run(
        on_step_start=get_state_hook
    )
    
   

if __name__ == '__main__':
    asyncio.run(main())