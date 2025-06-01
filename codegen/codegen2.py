import asyncio
import re
from playwright.async_api import Playwright, async_playwright, expect


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

    await page.get_by_role("button", name="Play", exact=True).click()
    await page.get_by_role("button", name="Until playoffs").click()
    await page.get_by_role("button", name="Play", exact=True).click()
    await page.get_by_role("button", name="Through playoffs").click()
    await page.get_by_role("button", name="Play", exact=True).click()
    await page.get_by_role("link", name="Read new message").click()
    await page.get_by_role("button", name="Play", exact=True).click()
    await page.get_by_role("button", name="Until draft").click()
    await page.get_by_role("button", name="To your next pick").click()
    await page.get_by_role("row", name="1 Kasparas Jakucionis  PG 19").get_by_role("button").nth(1).click()
    await page.get_by_role("row", name="1 Kon Knueppel  GF 19 41 67").get_by_role("button").nth(1).click()
    await page.get_by_role("button", name="Play", exact=True).click()
    await page.get_by_role("button", name="Re-sign players with expiring").click()
    await page.get_by_role("button", name="Play", exact=True).click()
    await page.get_by_role("button", name="Until free agency").click()
    await page.get_by_role("button", name="Proceed").click()
    await page.get_by_role("button", name="Play", exact=True).click()
    await page.get_by_role("button", name="Until preseason").click()
    await page.get_by_role("button", name="Play", exact=True).click()
    await page.get_by_role("button", name="Until regular season").click()

    # ---------------------
    # await context.close()
    # await browser.close()


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


asyncio.run(main())
