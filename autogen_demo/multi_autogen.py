import asyncio, json
from typing import Sequence, TypedDict, Any
from playwright.async_api import async_playwright

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_agentchat.ui import Console
from autogen_ext.agents.web_surfer import MultimodalWebSurfer, PlaywrightController
from autogen_ext.models.openai import OpenAIChatCompletionClient

# ───────────────────────────────────────────────────────
# 1.  Shared state (NO Playwright types, avoid Pydantic error)
# ───────────────────────────────────────────────────────
class BBGMState(TypedDict, total=False):
    phase: str
    moves_left: int
    roster_json: str  # Coach can dump roster here for advisors
    last_advice: str

# ───────────────────────────────────────────────────────
# 2.  Helper Playwright actions (Coach only)
# ───────────────────────────────────────────────────────
def click(sel: str, shared: dict):
    return asyncio.run(shared["page"].click(sel))

def sim_one_week(shared: dict):
    sel = 'button:has-text("One week")'
    return asyncio.run(shared["page"].click(sel))

# ───────────────────────────────────────────────────────
# 3.  Build agents with detailed prompts
# ───────────────────────────────────────────────────────
def make_team(shared_browser: dict) -> SelectorGroupChat:
    """Return a SelectorGroupChat with one acting agent + four advisors."""

    llm_big   = OpenAIChatCompletionClient(model="gpt-4o")
    llm_small = OpenAIChatCompletionClient(model="gpt-4o-mini")  # router LLM

    # ————— Advisor archetype (text-only) —————
    def advisor(name: str, role_spec: str) -> AssistantAgent:
        return AssistantAgent(
            name,
            description=f"{name} advisor",
            model_client=llm_big,
            system_message=role_spec
        )

    trade_adv = advisor("TradeAdvisor", """
You are TradeAdvisor, an expert in NBA trades and the Basketball GM trade system. Your job is to analyze the team's current roster, assets, and trade block, and provide actionable trade recommendations.

When asked:
- Evaluate the team's current strengths and weaknesses (positions, contracts, star players, cap space)
- Suggest specific trade targets (players or picks) that would improve the team
- Recommend which players or assets to offer in trades, and which to keep
- If a trade is proposed, assess its value and suggest improvements
- Always reference the actual players, contracts, and trade rules visible in the interface

Constraints:
- Only suggest trades that are possible within the game's salary cap and trade rules
- Prioritize trades that improve the team's championship odds
- Be concise and specific in your advice

Example questions you might receive:
- "Who should we target in a trade to improve our defense?"
- "Is this trade proposal beneficial for our team?"
- "Which players should we put on the trade block?"

Your mission: Help CoachBot make the best possible trades to build a championship contender.
""")

    fa_adv = advisor("FAAdvisor", """
You are FAAdvisor, an expert in free agent signings and contract management in Basketball GM. Your job is to identify the best available free agents and advise on contract offers.

When asked:
- Analyze the team's roster needs and available cap space
- Recommend specific free agents to target, based on their ratings, fit, and contract demands
- Advise on contract offer amounts and lengths, considering the team's financial situation
- Warn about potential luxury tax or cap issues

Constraints:
- Only suggest signings that are possible under the current cap and roster limits
- Prioritize signings that fill key roster gaps or provide high value
- Be specific about which player to sign and why

Example questions you might receive:
- "Which free agent should we sign to improve our bench scoring?"
- "Can we afford to sign this player under the cap?"

Your mission: Help CoachBot make the best possible free agent signings to strengthen the team.
""")

    roster_adv = advisor("RosterAdvisor", """
You are RosterAdvisor, an expert in roster construction, salary cap, and lineup optimization in Basketball GM.

When asked:
- Review the current roster for balance, depth, and salary cap compliance
- Suggest lineup changes, player rotations, or contract adjustments
- Advise on waiving, releasing, or re-signing players as needed
- Ensure the team never exceeds the 15-player roster limit or violates cap rules

Constraints:
- Only suggest legal roster moves
- Prioritize a balanced, competitive lineup

Example questions you might receive:
- "Should we waive a player to make room for a new signing?"
- "How can we optimize our starting lineup for better defense?"

Your mission: Help CoachBot maintain a legal, competitive, and well-balanced roster.
""")

    sim_adv = advisor("SimAdvisor", """
You are SimAdvisor, an expert in simulation strategy and phase management in Basketball GM.

When asked:
- Advise when to simulate games versus making more roster moves
- Recommend simulation intervals (one day, one week, until trade deadline, etc.)
- Warn if the team is about to miss a key phase (e.g., trade deadline, playoffs)
- Suggest when to pause simulation for further roster adjustments

Constraints:
- Only recommend simulation actions that comply with the current phase rules
- Prioritize simulation strategies that maximize the team's chances of success

Example questions you might receive:
- "Should we simulate to the trade deadline now?"
- "Is it time to simulate through the playoffs?"

Your mission: Help CoachBot time simulations optimally for the best possible season outcome.
""")

    # ————— CoachBot: the ONLY agent with browser power —————
    coach = MultimodalWebSurfer(
        name="CoachBot",
        description="Controls the UI based on advisors' input.",
        model_client=llm_big,
        headless=False,
        start_page="https://play.basketball-gm.com/l/1",
        animate_actions=True,
        to_save_screenshots=True,  # Save screenshots for debugging
        use_ocr=True,  # Enable OCR for better text recognition
        to_resize_viewport=True,  # Ensure proper viewport size
        debug_dir="./debug",  # Save debug info
        downloads_folder="./downloads",  # Save any downloads
        browser_data_dir="./browser_data",  # Persist browser data
        # Remove browser_channel to use default Chromium
    )
    coach.shared = shared_browser            # attach Playwright page + state

    # Configure the PlaywrightController
    coach._playwright_controller = PlaywrightController(
        animate_actions=True,
        # use_ocr=True,
        # to_save_screenshots=True,
        # debug_dir="./debug",
    )
    # Set the page after initialization
    coach._playwright_controller.page = shared_browser["page"]

    coach.system_message = """
You are CoachBot, the only agent allowed to interact with the Basketball GM web interface. Your mission is to lead your team to a championship by making strategic decisions, but you must always consult your advisors before taking action.

IMPORTANT: You MUST take actual browser actions after consulting advisors. Do not just discuss - execute the actions you describe.

Workflow for each turn:
1. Take a screenshot and analyze the current game state
2. Decide which advisor (TradeAdvisor, FAAdvisor, RosterAdvisor, SimAdvisor) to consult for the next best move
3. Ask that advisor a specific, targeted question about your current situation
4. Wait for their response and reasoning
5. EXECUTE exactly one browser action based on the advisor's input
6. Update the shared state (phase, moves_left, last_advice, etc.)
7. Repeat until the season is complete or you win the championship

Available Actions (you MUST execute these, not just describe them):
- To simulate: "Click the 'Play' dropdown and select 'One week'"
- To make trades: "Click the 'Trade' button and select the players to trade"
- To sign free agents: "Click the 'Free Agents' button and select the player to sign"
- To adjust lineups: "Click the 'Roster' button and drag players to adjust positions"

For each action:
1. First take a screenshot and analyze the current page
2. Identify the exact element to interact with
3. Execute the action using natural language
4. Wait for the page to update
5. Take another screenshot to confirm the action succeeded

Constraints:
- You may only interact with elements visible in the Basketball GM interface
- Never navigate away from the current league page after initialization
- You may make up to 3 roster moves (trades or free agent signings) in the preseason, then must simulate to the trade deadline
- At the trade deadline, you may make up to 3 more moves, then simulate to the end of the season
- During the draft, select the best available player for your team's needs
- Always explain your reasoning for each action you take
- Prioritize actions that maximize your team's chances of winning

Your mission: Build a championship-winning team through smart, sequential actions and strategic management, always leveraging your advisors' expertise.

REMEMBER: You MUST take actual browser actions after consulting advisors. Do not just discuss - execute the actions you describe.
"""

    # ————— Termination guards —————
    term = TextMentionTermination("TERMINATE") | MaxMessageTermination(60)

    # ————— Selector: always return to Coach after an advisor speaks —————
    def choose_next(msgs: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
        last_src = msgs[-1].source
        return "CoachBot" if last_src != "CoachBot" else None

    return SelectorGroupChat(
        [coach, trade_adv, fa_adv, roster_adv, sim_adv],
        model_client=llm_small,
        termination_condition=term,
        selector_func=choose_next,
    )


async def create_new_league(page):
    await page.goto("https://play.basketball-gm.com/l/1/trade")

    await page.get_by_role("link", name="Create a new league").click()
    await page.get_by_role("button", name="Random").click()
    await page.get_by_role("combobox").nth(2).select_option("real")
    await page.get_by_role("button", name="Random").nth(1).click()
    await page.get_by_role("button", name="Create League Processing").click()

    # land on the main league page
    await page.wait_for_url("**/l/1")



# ───────────────────────────────────────────────────────
# 4.  Main
# ───────────────────────────────────────────────────────
async def main():
    # Only create one Playwright tab and pass it in shared
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=False,
    )
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080}  # Set a large viewport
    )
    page = await context.new_page()
    await page.goto("https://play.basketball-gm.com/l/1/trade")

    await create_new_league(page)

    shared = {
        "page": page,
        "state": BBGMState(phase="preseason", moves_left=100, last_advice="")
    }

    team = make_team(shared)  # Only CoachBot gets browser power

    task = "Start a new league and win the championship following phase rules."
    await Console(team.run_stream(task=task))

    await browser.close()
    await pw.stop()



if __name__ == "__main__":
    asyncio.run(main())
