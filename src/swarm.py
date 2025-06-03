from typing import Any, Dict, List
from langchain_openai import ChatOpenAI
import json

def make_trade() -> str:
    """Decide whether or not to make a trade, and if you decide to make a trade return the players traded."""
    return f"Trade executed: Player A for Player B"

def sign_free_agent() -> str:
    """Sign a free agent to improve the team."""
    return f"Signed free agent: Player X"

def proceed_in_game() -> str:
    """Advance the game to the next milestone (e.g., trade deadline, playoffs)."""
    return f"Proceeded to next milestone in the game"

async def basketball_decision(state: Dict[str, Any]) -> str:
    """
    Given the current browser/game state, make a decision using a single LLM call.
    """
    llm = ChatOpenAI(model="gpt-4o")
    
    # Create a detailed prompt for the LLM
    prompt = f"""You are a basketball team manager at the trade deadline. Analyze the current state and make a strategic decision.

Current game state:
Season: {state.get('current_season', 'N/A')}
Record: {state.get('team_wins', 0)}-{state.get('team_losses', 0)}
Team Rating: {state.get('team_rating', 'N/A')}
Cap Space: ${state.get('available_cap_space', 0):,.2f}
Roster Size: {state.get('roster_size', 0)}
Playoff Position: {state.get('playoff_position', 'N/A')}

Based on this state, you must:
1. Analyze the team's current situation
2. Evaluate if trades are needed
3. Check if free agent signings would help
4. Make a clear recommendation for the next action
5. Provide reasoning for your decision

Return your decision in the following JSON format:
{{
    "decision": "Your specific action recommendation",
    "reasoning": "Your detailed explanation",
    "next_steps": ["Step 1", "Step 2", "Step 3"]
}}

Make sure to focus on immediate actions that can improve the team's performance."""

    # Get response from LLM
    response = await llm.ainvoke(prompt)
    
    try:
        # Try to parse as JSON
        decision_data = json.loads(response.content)
        return f"DECISION: {decision_data['decision']}\nREASONING: {decision_data['reasoning']}\nNEXT STEPS:\n" + "\n".join(f"- {step}" for step in decision_data['next_steps'])
    except:
        # Fallback if JSON parsing fails
        return f"DECISION: Continue with current strategy\nREASONING: {response.content}"

if __name__ == "__main__":
    import asyncio
    # Test the function
    test_state = {
        "current_season": 2025,
        "team_wins": 30,
        "team_losses": 20,
        "team_rating": 75,
        "available_cap_space": 5000000,
        "roster_size": 12,
        "playoff_position": "8th in conference"
    }
    result = asyncio.run(basketball_decision(test_state))
    print(result)

