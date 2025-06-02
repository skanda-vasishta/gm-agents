import asyncio
from playwright.async_api import Playwright, async_playwright, expect
import time
from pydantic import BaseModel
from openai import OpenAI
import base64
import json
from datetime import datetime

# npx playwright codegen https://play.basketball-gm.com
class GameState(BaseModel):
    record: str
    team_rating: str
    average_mov: str
    average_age: str
    open_roster_spots: str
    payroll: str
    salary_cap: str
    profit: str


async def parse_game_state_with_openai(page) -> GameState:
    # Take a screenshot of the relevant area
    element = page.locator("#actual-actual-content > div.d-sm-flex.mb-3 > div.d-flex > div:nth-child(2)")
    screenshot = await element.screenshot()
    
    # Convert screenshot to base64
    base64_image = base64.b64encode(screenshot).decode("utf-8")
    
    # Initialize OpenAI client
    client = OpenAI()
    
    # Compose prompt for OpenAI
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
    
    # Parse the response and create GameState object
    state_dict = json.loads(response.output_text)
    return GameState(**state_dict)

async def extract_trade_info(page):
    # Take a screenshot of the trade proposal area
    element = page.locator("#actual-actual-content > div > div.col-md-3 > div")
    await element.wait_for(state="visible", timeout=5000)
    screenshot = await element.screenshot()
    base64_image = base64.b64encode(screenshot).decode("utf-8")

    client = OpenAI()
    prompt = """
    You are an expert basketball GM. Extract the following information from the trade proposal image:
    1. Players/Assets being traded from your team
    2. Players/Assets being received by your team
    3. Any draft picks involved
    4. Salary implications
    Format the response as a clear, structured text description.
    """
    
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
    return response.output_text

async def evaluate_trade_logic(page):
    # Take a screenshot of the trade proposal area
    element = page.locator("#actual-actual-content > div > div.col-md-3 > div")
    await element.wait_for(state="visible", timeout=5000)
    screenshot = await element.screenshot()
    base64_image = base64.b64encode(screenshot).decode("utf-8")

    client = OpenAI()
    prompt = (
        "You are an expert basketball GM. "
        "Given the trade proposal shown in the image, respond with 'ACCEPT' if you recommend accepting/proposing the trade, "
        "or 'REJECT' if not. Only respond with 'ACCEPT' or 'REJECT'."
    )
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
    result = response.output_text.strip().upper()
    return result == "ACCEPT"

async def get_user_feedback():
    while True:
        feedback = input("\nDo you agree with this trade decision? (yes/no/skip): ").lower()
        if feedback in ['yes', 'no', 'skip']:
            return feedback
        print("Please enter 'yes', 'no', or 'skip'")

async def save_trade_data(trade_info, ai_decision, user_feedback, filename="trade_feedback.txt"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filename, "a") as f:
        f.write(f"\n=== Trade Evaluation {timestamp} ===\n")
        f.write(f"Trade Information:\n{trade_info}\n")
        f.write(f"AI Decision: {ai_decision}\n")
        f.write(f"User Feedback: {user_feedback}\n")
        f.write("="*50 + "\n")

async def evaluate_trade_proposals(page):
    try:
        # Navigate to trade proposals
        await page.get_by_role("link", name="Trade Proposals").click()
        await asyncio.sleep(2)  # Wait for page to load
        
        while True:  # Keep checking for new trade proposals
            try:
                # Wait for negotiate buttons to be visible
                await page.wait_for_selector('button:has-text("Negotiate")', state="visible", timeout=5000)
                
                # Get all negotiate buttons
                negotiate_buttons = await page.query_selector_all('button:has-text("Negotiate")')
                if not negotiate_buttons:
                    print("No trade proposals found")
                    break
                    
                print(f"Found {len(negotiate_buttons)} trade proposals")
                
                # Process each proposal
                for i in range(len(negotiate_buttons)):
                    try:
                        # Get fresh reference to the button
                        buttons = await page.query_selector_all('button:has-text("Negotiate")')
                        if i >= len(buttons):
                            break
                            
                        # Click negotiate
                        await buttons[i].click()
                        await asyncio.sleep(1)  # Wait for trade modal
                        
                        # Extract trade information
                        trade_info = await extract_trade_info(page)
                        print("\nTrade Information:")
                        print(trade_info)
                        
                        # Evaluate the trade
                        is_good_trade = await evaluate_trade_logic(page)
                        ai_decision = "ACCEPT" if is_good_trade else "REJECT"
                        print(f"\nAI Decision: {ai_decision}")
                        
                        # Get user feedback
                        user_feedback = await get_user_feedback()
                        
                        # Save the data
                        await save_trade_data(trade_info, ai_decision, user_feedback)
                        
                        # Execute the trade based on AI decision
                        if is_good_trade:
                            print(f"Accepting trade proposal {i+1}")
                            await page.get_by_role("button", name="Propose trade").click()
                            await asyncio.sleep(2)  # Wait for trade to process
                        else:
                            print(f"Rejecting trade proposal {i+1}")
                            await page.go_back()
                            await asyncio.sleep(1)  # Wait for page to settle
                            
                        # Go back to trade proposals page
                        await page.get_by_role("link", name="Trade Proposals").click()
                        await asyncio.sleep(2)  # Wait for page to load
                        
                    except Exception as e:
                        print(f"Error processing trade proposal {i+1}: {str(e)}")
                        # Try to recover by going back to trade proposals
                        try:
                            await page.get_by_role("link", name="Trade Proposals").click()
                            await asyncio.sleep(2)
                        except:
                            pass
                        continue
                        
            except Exception as e:
                print(f"No more trade proposals available: {str(e)}")
                break
                
    except Exception as e:
        print(f"Error in evaluate_trade_proposals: {str(e)}")

async def run(playwright: Playwright) -> None:
    try:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Basic setup
        await page.goto("https://play.basketball-gm.com/l/1/trade")
        await page.get_by_role("link", name="Create a new league").click()
        await page.get_by_role("combobox").nth(2).select_option("real")
        await page.get_by_role("button", name="Create League Processing").click()
        
        # Get to trade deadline
        await page.get_by_role("button", name="Play", exact=True).click()
        await page.get_by_role("button", name="Until regular season").click()
        await page.get_by_role("button", name="Play", exact=True).click()
        
        # Wait for trade deadline button and click it
        await page.get_by_role("button", name="Until trade deadline").click()

        
        # Wait for trade deadline phase to be fully established
        await asyncio.sleep(3)
        
        # Verify we're in trade deadline phase
        try:
            phase_element = await page.wait_for_selector("#content > nav > div > div.dropdown-links.navbar-nav.flex-shrink-1.overflow-hidden.text-nowrap > div > a", timeout=5000)
            phase_text = await phase_element.inner_text()
            print(f"Current phase: {phase_text}")
        except Exception as e:
            print(f"Error getting phase text: {str(e)}")
        
        # Evaluate all trade proposals
        await evaluate_trade_proposals(page)
        
        # Keep the browser open for inspection
        await asyncio.sleep(30)  # Keep open for 30 seconds
        
    except Exception as e:
        print(f"Error in run: {str(e)}")
        try:
            await page.screenshot(path="error_screenshot.png")
        except:
            pass
    finally:
        try:
            await context.close()
            await browser.close()
        except:
            pass


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


asyncio.run(main())
