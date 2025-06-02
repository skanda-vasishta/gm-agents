from langchain_openai import ChatOpenAI
from browser_use import Agent, Controller, ActionResult
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import os
from pathlib import Path
from playwright.async_api import Page
from openai import OpenAI
import base64
import json
import logging
import joblib
import numpy as np
#  more high level planning: first, extract team name, and then at end see who won to see how team does - index 35 i believe

load_dotenv()

import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameState(BaseModel):
    record: str
    team_rating: str
    average_mov: str
    average_age: str
    open_roster_spots: str
    payroll: str
    salary_cap: str
    profit: str

class SeasonState(BaseModel):
    phase: str  # e.g., "2024 preseason", "2024 regular season", etc.
    comments: str  # Any additional comments or context about the phase

class PhaseManager:
    def __init__(self):
        self.current_phase = "trade_deadline"
        self.actions_remaining = 4  
        self.logger = logging.getLogger(__name__)

    async def handle_phase_change(self, page: Page) -> None:
        """Handle phase transitions when actions are depleted"""
        global first_move_of_phase
        if self.current_phase == "trade_deadline" and self.actions_remaining <= 0:
            # await evaluate_trade_proposals(page)
            self.logger.info("Trade deadline actions depleted, transitioning to playoffs")
            self.current_phase = "playoffs"
            self.actions_remaining = 0
            
            try:
                await page.get_by_role("button", name="Play", exact=True).click()
                await page.get_by_role("button", name="Until playoffs").click()
                await page.get_by_role("button", name="Play", exact=True).click()
                await page.get_by_role("button", name="Through playoffs").click()
                await page.get_by_role("button", name="Play", exact=True).click()
                first_move_of_phase = True  # Reset for the new phase

            except Exception as e:
                self.logger.error(f"Error during phase transition: {str(e)}")
                await page.screenshot(path="error_playoffs_transition.png")
                raise
        elif self.current_phase == "trade_deadline" and self.actions_remaining == 3:
            await evaluate_trade_proposals(page)


    def decrement_counter(self) -> bool:
        """Decrement the action counter and return True if actions are still available"""
        if self.actions_remaining > 0:
            self.actions_remaining -= 1
            self.logger.info(f"Actions remaining in {self.current_phase}: {self.actions_remaining}")
            return True
        self.logger.info(f"No actions remaining in {self.current_phase}")
        return False

# Global state variables
initialized = False
game_state = None
phase_manager = PhaseManager()
first_move_of_phase = True

controller = Controller()

#helper function for state extraction
async def parse_game_state_with_openai(page) -> GameState:
    element = page.locator("#actual-actual-content > div.d-sm-flex.mb-3 > div.d-flex > div:nth-child(2)")
    screenshot = await element.screenshot()
    
    base64_image = base64.b64encode(screenshot).decode("utf-8")
    
    client = OpenAI()
    
    prompt = """
    You are an OCR and information extraction agent. Extract the following fields from the image and output as JSON:
    {
      "record": "...",
      "team_rating": "...",
      "average_mov": "...",
      "average_age": "...",
      "open_roster_spots": "...",
      "payroll": "...",
      "salary_cap": "...",
      "profit": "..."
    }
    If a field is missing, use an empty string.
    """
    
    # Call OpenAI API with the new format
    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{base64_image}"
                    }
                ]
            }
        ]
    )
    
    state_dict = json.loads(response.output_text)
    return GameState(**state_dict)

async def parse_season_state_with_openai(page) -> SeasonState:
    # Use the selector you suggested, or fallback to a screenshot of the area if needed
    element = page.locator("#content > nav > div > div.dropdown-links.navbar-nav.flex-shrink-1.overflow-hidden.text-nowrap > div > a")
    screenshot = await element.screenshot()
    base64_image = base64.b64encode(screenshot).decode("utf-8")
    client = OpenAI()
    prompt = (
        "You are an OCR and information extraction agent. "
        "Extract the current phase of the basketball season from the image and output as JSON:\n"
        "{ \"phase\": \"...\", \"comments\": \"...\" }\n"
        "The 'phase' field should be the main text (e.g., 'regular_season'). "
        "The 'comments' field should include any additional context, such as if the phase is preseason, playoffs, draft, etc., or if the text is unclear. "
        "If you cannot determine the phase, use an empty string."
    )
    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{base64_image}"
                    }
                ]
            }
        ]
    )
    state_dict = json.loads(response.output_text)
    return SeasonState(**state_dict)


@controller.action('Ask human for help with a question AT THE BEGINNING OF EACH PHASE for guidance.', domains=['https://play.basketball-gm.com'])   # pass allowed_domains= or page_filter= to limit actions to certain pages
def ask_human(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)

@controller.action('Ask LLM for guidance at the beginning of each phase.', domains=['https://play.basketball-gm.com'])
def ask_llm(question: str) -> ActionResult:
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert basketball team manager. Provide strategic guidance based on the current situation."},
            {"role": "user", "content": question}
        ]
    )
    answer = response.choices[0].message.content
    return ActionResult(extracted_content=f'The LLM responded with: {answer}', include_in_memory=True)

async def state_hook(agent: Agent):
    global initialized, game_state, first_move_of_phase
    page = await agent.browser_session.get_current_page()
    if not initialized:
        await page.goto("https://play.basketball-gm.com/")
        await page.get_by_role("link", name="New league » Real players").click()
        await page.get_by_role("button", name="Random").nth(1).click()
        await page.get_by_role("button", name="Create League Processing").click()
        await page.get_by_role("button", name="Play", exact=True).click()
        await page.get_by_role("button", name="Until regular season").click()
        await page.get_by_role("button", name="Play", exact=True).click()
        await page.get_by_role("button", name="Until trade deadline").click()
        initialized = True

    if first_move_of_phase:
        await page.get_by_role("link", name="Roster", exact=True).click()
        game_state = await parse_game_state_with_openai(page)
        first_move_of_phase = False  # Set to False after first move
        return await get_state(agent)
    else:
        return None

async def router_hook(agent: Agent):
    global game_state, initialized, phase_manager, first_move_of_phase
    page = await agent.browser_session.get_current_page()

    try:
        season_state = await parse_season_state_with_openai(page)
        logger.info(f"Current season phase: {season_state.phase} | Comments: {season_state.comments}")

        # Handle phase changes
        await phase_manager.handle_phase_change(page)
        # if season_state.phase == "trade_deadline" and phase_manager.actions_remaining == 1:
        #     await evaluate_trade_proposals(page)

        # Check if we have actions remaining
        if not phase_manager.decrement_counter():
            logger.info(f"No actions left in phase {season_state.phase}. Please transition to the next phase.")

        if not initialized:
            await page.goto("https://play.basketball-gm.com/")
            await page.get_by_role("link", name="New league » Real players").click()
            await page.get_by_role("button", name="Random").nth(1).click()
            await page.get_by_role("button", name="Create League Processing").click()
            await page.get_by_role("button", name="Play", exact=True).click()
            await page.get_by_role("button", name="Until regular season").click()
            await page.get_by_role("button", name="Play", exact=True).click()
            await page.get_by_role("button", name="Until trade deadline").click()
            initialized = True

        # Only get state if first_move_of_phase is True
        if first_move_of_phase:
            state_result = await get_state(agent)
            combined_content = json.dumps({
                "season_phase": season_state.phase,
                "season_comments": season_state.comments,
                "actions_remaining": phase_manager.actions_remaining,
                "game_state": json.loads(state_result.extracted_content)
            })
            return ActionResult(extracted_content=combined_content)
        else:
            return None
    except Exception as e:
        logger.error(f"Error in router_hook: {str(e)}")
        raise

async def get_state(agent: Agent):
    global game_state
    page = await agent.browser_session.get_current_page() 
    try:
        await page.get_by_role("link", name="Roster", exact=True).click()
        game_state = await parse_game_state_with_openai(page)
        state_json = game_state.model_dump_json()
        print(state_json)
        return ActionResult(extracted_content=state_json)

    except Exception as e:
        game_state = GameState(
            record="0-0",
            team_rating="0",
            average_mov="0.0",
            average_age="0.0",
            open_roster_spots="0",
            payroll="0.0",
            salary_cap="0.0",
            profit="0.0"
        )
        state_json = game_state.model_dump_json()
        return ActionResult(extracted_content=state_json)

async def evaluate_trade_logic(page):
    """Evaluate trade using GPT for extraction and reward model for decision."""
    # Take screenshot of the trade proposal
    element = page.locator("#actual-actual-content > div > div.col-md-3 > div")
    await element.wait_for(state="visible", timeout=5000)
    screenshot = await element.screenshot()
    base64_image = base64.b64encode(screenshot).decode("utf-8")

    # Use GPT to extract and format trade information
    client = OpenAI()
    prompt = """Extract the trade information from the image and format it exactly like this:
    Trade Proposal:
    Team A receives:
    - Player X ($20M)
    - 2025 1st round pick
    
    Team B receives:
    - Player Y ($18M)
    - Player Z ($5M)
    
    Salary implications:
    - Team A payroll: $180M
    - Team B payroll: $175M
    - Both teams over salary cap ($140.6M)
    
    Make sure to include all players, picks, and salary information in this exact format."""
    
    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": f"data:image/png;base64,{base64_image}"}
                ]
            }
        ]
    )
    
    formatted_trade = response.output_text.strip()
    
    # Use reward model to make decision
    try:
        model = joblib.load("reward_model.pkl")
        prob = model.predict_proba([formatted_trade])[0][1]
        
        # Make decision based on probability threshold
        decision = "ACCEPT" if prob > 0.5 else "REJECT"
        confidence = abs(prob - 0.5) * 2  # Scale to 0-1 range
        
        # Save trade data with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("trade_feedback.txt", "a") as f:
            f.write(f"\n=== Trade Evaluation {timestamp} ===\n")
            f.write(f"Trade Information:\n{formatted_trade}\n")
            f.write(f"AI Decision: {decision}\n")
            f.write(f"Confidence: {confidence:.2f}\n")
            f.write("=" * 50 + "\n")
        
        return decision, confidence
        
    except Exception as e:
        print(f"Error using reward model: {e}")
        return "REJECT", 0.0  # Default to reject if model fails

async def get_user_feedback():
    """Get user feedback on the trade decision."""
    while True:
        feedback = input("\nDo you agree with this decision? (yes/no/skip): ").lower()
        if feedback in ['yes', 'no', 'skip']:
            return feedback
        print("Please enter 'yes', 'no', or 'skip'")

async def save_trade_data(trade_info, ai_decision, user_feedback, filename="trade_feedback.txt"):
    """Save trade information, AI decision, and user feedback to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(filename, "a") as f:
        f.write(f"\n=== Trade Evaluation {timestamp} ===\n")
        f.write(f"Trade Information:\n{trade_info}\n")
        f.write(f"AI Decision: {ai_decision}\n")
        f.write(f"User Feedback: {user_feedback}\n")
        f.write("=" * 50 + "\n")

async def evaluate_trade_proposals(page):
    # index 33: Trade 
    await page.get_by_role("link", name="Trade Proposals").click()
    negotiate_buttons = await page.query_selector_all('button:has-text("Negotiate")')
    if not negotiate_buttons:
        return False
    print("made it here")
    print(negotiate_buttons)

    for i, btn in enumerate(negotiate_buttons):
        await btn.click()
        # Evaluate trade using reward model
        decision, confidence = await evaluate_trade_logic(page)
        print(f"\nTrade Evaluation:")
        print(f"AI Decision: {decision}")
        print(f"Confidence: {confidence:.2f}")
        
        if decision == "ACCEPT":
            await page.get_by_role("button", name="Propose trade").click()
            return True
        # else, close/dismiss and continue
        await page.go_back()  # or close modal/dialog

    return False

async def main():
    with open("instructions.txt", "r") as f:
        task = f.read()

    model = ChatOpenAI(model='gpt-4o')
    agent = Agent(task=task, llm=model, controller=controller)

    await agent.run(
        on_step_start=state_hook,
        on_step_end=router_hook
    )
    
   

if __name__ == '__main__':
    asyncio.run(main())