import asyncio
from playwright.async_api import Playwright, async_playwright, expect
import time
from pydantic import BaseModel
from openai import OpenAI
import base64
import json

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
    await page.get_by_role("link", name="Roster", exact=True).click()
   
    
    await asyncio.sleep(30)
    state = await parse_game_state_with_openai(page)
    state_json = state.model_dump_json()
    print(state_json)
    print("\n--------------------------------\n")

    await page.get_by_role("button", name="Play", exact=True).click()
    await page.get_by_role("button", name="Until playoffs").click()
    await page.get_by_role("button", name="Play", exact=True).click()
    await page.get_by_role("button", name="Through playoffs").click()
    await page.get_by_role("button", name="Play", exact=True).click()
    # ---------------------
    # await context.close()
    # await browser.close()


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


asyncio.run(main())
