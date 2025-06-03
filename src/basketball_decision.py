from typing import Any, Dict
from langchain_openai import ChatOpenAI
import json
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/basketball.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_decision(state: Dict[str, Any], decision_data: Dict[str, Any], filename: str = "basketball.log"):
    """Log both the game state and decision data to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "game_state": state,
        "decision": decision_data
    }
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", filename)
    
    # Log to console
    logger.info("="*80)
    logger.info("NEW DECISION LOGGED")
    logger.info(f"Logging to: {log_path}")
    logger.info(f"Game State: {json.dumps(state, indent=2)}")
    logger.info(f"Tool calls: {json.dumps(decision_data.get('tool_calls', []), indent=2)}")
    logger.info("="*80)
    
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry, indent=2) + "\n" + "-"*80 + "\n")

async def make_basketball_decision(state: Dict[str, Any]) -> str:
    """
    Given the current browser/game state, make a decision using a single LLM call.
    """
    logger.info("="*80)
    logger.info("STARTING NEW BASKETBALL DECISION")
    logger.info(f"Input state: {json.dumps(state, indent=2)}")
    
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
    "next_steps": ["Step 1", "Step 2", "Step 3"],
    "tool_calls": [
        {{
            "type": "click",
            "selector": "#submit"
        }},
        {{
            "type": "click",
            "selector": "#next"
        }}
    ],
    "current_state": "trade_deadline"  // or whatever the current state is
}}

Make sure to:
1. Focus on immediate actions that can improve the team's performance
2. Include tool_calls array with every action that needs to be taken
3. Specify the current state in the game
4. Use proper CSS selectors for the tool_calls
5. ALWAYS include at least one tool call in your response"""

    # Get response from LLM
    logger.info("Sending request to LLM...")
    response = await llm.ainvoke(prompt)
    logger.info(f"Received response from LLM: {response.content[:200]}...")
    
    try:
        # Try to parse as JSON
        decision_data = json.loads(response.content)
        
        # Ensure tool_calls exists
        if 'tool_calls' not in decision_data:
            decision_data['tool_calls'] = [{"type": "click", "selector": "#submit"}]
            logger.warning("No tool_calls found in response, adding default")
        
        # Log the decision and state
        log_decision(state, decision_data)
        
        # Format the tool calls
        tool_calls_str = "\nTOOL CALLS:\n" + "\n".join(
            f"- {tool['type']}: {tool['selector']}" 
            for tool in decision_data.get('tool_calls', [])
        )
        
        result = (
            f"DECISION: {decision_data['decision']}\n"
            f"REASONING: {decision_data['reasoning']}\n"
            f"CURRENT STATE: {decision_data.get('current_state', 'unknown')}\n"
            f"NEXT STEPS:\n" + "\n".join(f"- {step}" for step in decision_data['next_steps']) + "\n"
            f"{tool_calls_str}"
        )
        logger.info(f"Returning result: {result[:200]}...")
        logger.info("="*80)
        return result
        
    except Exception as e:
        # Log the error
        error_data = {
            "error": str(e),
            "raw_response": response.content
        }
        logger.error(f"Error processing response: {str(e)}")
        log_decision(state, error_data, "basketball_errors.log")
        logger.info("="*80)
        
        # Fallback if JSON parsing fails
        return f"DECISION: Continue with current strategy\nREASONING: {response.content}\nERROR: {str(e)}" 