import asyncio, json
from typing import Sequence, TypedDict, Any
from playwright.async_api import async_playwright

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_agentchat.ui import Console
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.models.openai import OpenAIChatCompletionClient

# ───────────────────────────────────────────────────────
# 1.  Shared state 
# ───────────────────────────────────────────────────────
class BBGMState(TypedDict, total=False):
    phase: str
    moves_left: int
    roster_json: str
    last_advice: str

# ───────────────────────────────────────────────────────
# 2.  Build agents with MUCH shorter, focused prompts
# ───────────────────────────────────────────────────────
def make_team() -> SelectorGroupChat:
    """Return a SelectorGroupChat with one acting agent + advisors."""

    llm_big   = OpenAIChatCompletionClient(model="gpt-4o-mini")  # Use mini for speed
    llm_small = OpenAIChatCompletionClient(model="gpt-4o-mini")

    # ————— Ultra-concise advisor archetype —————
    def advisor(name: str, role_spec: str) -> AssistantAgent:
        return AssistantAgent(
            name,
            description=f"{name} advisor",
            model_client=llm_big,
            system_message=role_spec
        )

    trade_adv = advisor("TradeAdvisor", """
You give INSTANT trade advice. Answer in 1-2 sentences max.
Format: "Target [player name] for [our asset]. Improves [weakness]."
No explanations, just quick recommendations.
""")

    fa_adv = advisor("FAAdvisor", """
You give INSTANT free agent advice. Answer in 1-2 sentences max.
Format: "Sign [player name] for $X. Fills [position need]."
No explanations, just quick recommendations.
""")

    roster_adv = advisor("RosterAdvisor", """
You give INSTANT roster advice. Answer in 1-2 sentences max.
Format: "Start [player]. Bench [player]. Cut [player if needed]."
No explanations, just quick lineup decisions.
""")

    sim_adv = advisor("SimAdvisor", """
You give INSTANT simulation advice. Answer in 1 sentence max.
Format: "Sim to [date/event]" or "Make moves first."
No explanations, just timing decisions.
""")

    # ————— CoachBot: Streamlined and action-focused —————
    coach = MultimodalWebSurfer(
        name="CoachBot",
        description="Fast Basketball GM controller",
        model_client=llm_big,
        headless=False,  # Faster without visual browser
        start_page="https://play.basketball-gm.com/l/1",
        animate_actions=False,  # Skip animations for speed
        to_save_screenshots=False,  # Skip screenshots for speed
        use_ocr=False,  # Skip OCR for speed unless critical
        to_resize_viewport=False,
        # Remove debug options for speed
    )

    coach.system_message = """
You are CoachBot. Be FAST and decisive. 
upon initialization, do the Following Actions Sequentially (using Playwright or equivalent browser automation):
        1. Click the link with role "link" and name "Create a new league".
        2. Click the button with role "button" and name "Random".
        3. Select the option "real" from the combobox at index 2.
        4. Click the second button with role "button" and name "Random" (nth=1).
        5. Click the button with role "button" and name "Create League Processing".

SPEED RULES:
- Take action immediately after advisor responds
- No long descriptions or explanations
- Ask advisors ONE specific question, get answer, act
- Skip verification screenshots unless action fails

PHASES:
- PRESEASON: 2 quick moves, sim to trade deadline
- TRADE: 2 quick moves, sim to playoffs  
- PLAYOFFS: Sim through

WORKFLOW (FAST):
1. Quick look at page
2. Ask advisor: "[Advisor], what should I do?"
3. Execute their advice immediately
4. Move to next decision

Example:
"On roster page. TradeAdvisor, who should I trade?"
[Response: "Trade Smith for Jones"]
"Making that trade now." [Execute]

GO FAST. Make decisions quickly.
"""

    # ————— Fast termination —————
    term = TextMentionTermination("TERMINATE") | MaxMessageTermination(30)  # Much shorter

    # ————— Simple selector —————
    def choose_next(msgs: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
        if not msgs:
            return "CoachBot"
        
        last_src = msgs[-1].source
        
        # Always return to CoachBot after any advisor
        if last_src in ["TradeAdvisor", "FAAdvisor", "RosterAdvisor", "SimAdvisor"]:
            return "CoachBot"
        
        return None

    return SelectorGroupChat(
        [coach, trade_adv, fa_adv, roster_adv, sim_adv],
        model_client=llm_small,
        termination_condition=term,
        selector_func=choose_next,
        max_turns=100,  # Limit advisor back-and-forth
    )

# ───────────────────────────────────────────────────────
# 3.  Main with faster execution
# ───────────────────────────────────────────────────────
async def main():
    print("Starting FAST Basketball GM System...")
    
    team = make_team()

    task = """
SPEED RUN: Win championship fast.

1. Quick screenshot
2. Ask one advisor what to do  
3. Do it immediately
4. Repeat until championship

GO NOW.
"""

    await Console(team.run_stream(task=task))

if __name__ == "__main__":
    asyncio.run(main())