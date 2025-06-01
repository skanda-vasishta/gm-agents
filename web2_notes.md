
## **Imports and Setup (Lines 1-18)**

```python
"""
Multi-Agent Basketball GM System
- Controller Agent: Handles navigation and game flow
- Specialist Agents: Provide strategic advice for specific decisions
"""
```
This is just documentation explaining what the system does.

```python
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
```
These import Python's built-in libraries:
- `asyncio` - for running asynchronous code (multiple things at once)
- `json` - for handling JSON data format
- `logging` - for recording what the program does
- `datetime` - for timestamps
- `typing` - for type hints (saying what kind of data variables should hold)
- `dataclasses` - for creating simple data structures
- `enum` - for creating named constants
- `abc` - for creating abstract base classes (templates for other classes)

```python
from langchain_openai import ChatOpenAI
from browser_use import Agent
from dotenv import load_dotenv
```
These import external libraries:
- `ChatOpenAI` - connects to OpenAI's GPT models
- `Agent` - the browser automation tool
- `load_dotenv` - loads environment variables from a .env file

```python
# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```
- `load_dotenv()` loads your API keys from a .env file
- The logging lines set up a system to record what happens when the code runs
- `logger` is the object we'll use to write log messages

## **Data Structures (Lines 20-52)**

```python
class GamePhase(Enum):
    REGULAR_SEASON = "regular_season"
    PLAYOFFS = "playoffs" 
    DRAFT = "draft"
    FREE_AGENCY = "free_agency"
    PRESEASON = "preseason"
```
This creates named constants for different phases of a basketball season. Instead of using strings like "regular_season", we use `GamePhase.REGULAR_SEASON`.

```python
@dataclass
class GameState:
    current_season: int = 1
    current_phase: GamePhase = GamePhase.REGULAR_SEASON
    team_wins: int = 0
    team_losses: int = 0
    salary_cap_used: float = 0.0
    roster_size: int = 0
    available_cap_space: float = 0.0
    team_rating: int = 0
    playoff_position: str = "Unknown"
    roster_data: Dict = None
    upcoming_schedule: List = None
    trade_offers: List = None
    free_agents: List = None
    draft_prospects: List = None
```
`@dataclass` automatically creates a class that holds data. This `GameState` class stores all the information about your basketball team:
- What season you're in
- Your team's record (wins/losses)  
- Financial info (salary cap)
- Player data (roster, prospects, etc.)
Each line defines a field with its type and default value.

```python
@dataclass
class Decision:
    decision_type: str
    recommendation: str
    reasoning: str
    confidence: float
    alternatives: List[str] = None
    data_used: Dict = None
```
This holds the recommendations that specialist agents make:
- What type of decision (trade, draft, etc.)
- What they recommend doing
- Why they recommend it
- How confident they are (0.0 to 1.0)
- Alternative options
- What data they based it on

## **Base Consulting Agent (Lines 54-66)**

```python
class ConsultingAgent(ABC):
    def __init__(self, llm_model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=llm_model)
        self.name = self.__class__.__name__
```
This creates a template that all specialist agents will follow:
- `ABC` means it's an abstract base class (a template)
- `__init__` runs when you create the agent
- `self.llm` connects to the AI model (GPT-4o by default)
- `self.name` gets the class name (like "TradeAgent")

```python
    @abstractmethod
    async def analyze(self, game_state: GameState, context: Dict[str, Any]) -> Decision:
        pass
```
`@abstractmethod` means every specialist agent MUST have an `analyze` method. This method takes the current game state and context, then returns a decision.

```python
    def _create_system_prompt(self) -> str:
        return f"You are a {self.name} for Basketball GM. Provide strategic advice based on the game data."
```
This creates a basic prompt telling the AI what its role is.

## **Trade Agent (Lines 68-129)**

```python
class TradeAgent(ConsultingAgent):
    """Specializes in trade analysis and recommendations"""
    
    async def analyze(self, game_state: GameState, context: Dict[str, Any]) -> Decision:
        """Analyze trade opportunities and make recommendations"""
```
This creates the trade specialist. It inherits from `ConsultingAgent`, so it gets the `__init__` method automatically.

```python
        # Extract relevant data
        roster = context.get('roster_data', {})
        trade_offers = context.get('trade_offers', [])
        team_needs = context.get('team_needs', [])
```
This pulls specific data from the context dictionary:
- Current roster
- Available trade offers  
- What positions the team needs

```python
        prompt = f"""
        As a Basketball GM Trade Specialist, analyze the current situation:
        
        TEAM STATUS:
        - Season: {game_state.current_season}
        - Record: {game_state.team_wins}-{game_state.team_losses}
        - Salary Cap Used: ${game_state.salary_cap_used:,.0f}
        - Available Cap Space: ${game_state.available_cap_space:,.0f}
        - Team Rating: {game_state.team_rating}
        
        ROSTER DATA: {json.dumps(roster, indent=2)}
        TRADE OFFERS: {json.dumps(trade_offers, indent=2)}
        TEAM NEEDS: {team_needs}
        
        Provide trade recommendations:
        1. Should we accept any current trade offers?
        2. What positions should we target in trades?
        3. Which players should we consider trading away?
        4. What's our trade deadline strategy?
        
        Response format:
        {{
            "recommendation": "clear action to take",
            "reasoning": "detailed explanation",
            "confidence": 0.0-1.0,
            "alternatives": ["option1", "option2"],
            "priority_targets": ["position1", "position2"]
        }}
        """
```
This creates a detailed prompt for the AI:
- It tells the AI it's a trade specialist
- Provides all the current team data
- Asks specific questions about trades
- Requests the response in JSON format

```python
        response = await self.llm.ainvoke(prompt)
```
This sends the prompt to the AI model and waits for a response.

```python
        try:
            result = json.loads(response.content)
            return Decision(
                decision_type="trade",
                recommendation=result.get("recommendation", "No trades recommended"),
                reasoning=result.get("reasoning", "Analysis unavailable"),
                confidence=result.get("confidence", 0.5),
                alternatives=result.get("alternatives", []),
                data_used={"trade_offers": len(trade_offers), "roster_size": len(roster)}
            )
        except:
            return Decision(
                decision_type="trade",
                recommendation="Unable to parse trade analysis",
                reasoning="Error in analysis",
                confidence=0.0
            )
```
This tries to parse the AI's JSON response:
- If successful, it creates a `Decision` object with the AI's recommendations
- If it fails (bad JSON), it returns a default decision with 0 confidence
- `result.get("key", default)` safely gets values from the JSON, using defaults if keys don't exist

## **Draft Agent (Lines 131-187)**

The Draft Agent follows the same pattern as Trade Agent:

```python
class DraftAgent(ConsultingAgent):
    """Specializes in draft strategy and prospect evaluation"""
```
This agent focuses on draft decisions.

The structure is identical:
1. Extract relevant data (draft prospects, team needs, draft position)
2. Create a specialized prompt asking about draft strategy
3. Send to AI model
4. Parse response into a Decision object
5. Handle errors with defaults

The prompt asks different questions:
- Who to draft
- Whether to trade draft picks
- What positions to prioritize
- Sleeper picks to watch

## **Free Agency Agent (Lines 189-245)**

Again, same pattern but focused on free agency:

```python
class FreeAgencyAgent(ConsultingAgent):
    """Specializes in free agency signings and roster construction"""
```

The prompt focuses on:
- Which free agents to target
- Budget allocation
- Salary cap management
- Contract decisions

## **Lineup Agent (Lines 247-303)**

Same pattern for lineup optimization:

```python
class LineupAgent(ConsultingAgent):
    """Specializes in lineup optimization and rotations"""
```

Focuses on:
- Starting lineups
- Player rotations  
- Matchup adjustments
- Minutes distribution

## **Controller Agent - Setup (Lines 305-330)**

```python
class ControllerAgent:
    """Main agent that handles navigation and coordinates with specialists"""
    
    def __init__(self, 
                 llm_model: str = "gpt-4o",
                 game_url: str = "https://play.basketball-gm.com/"):
        
        self.llm = ChatOpenAI(model=llm_model)
        self.game_url = game_url
        self.game_state = GameState()
        
        # Initialize specialist agents
        self.trade_agent = TradeAgent()
        self.draft_agent = DraftAgent()  
        self.free_agency_agent = FreeAgencyAgent()
        self.lineup_agent = LineupAgent()
        
        self.decisions_log = []
        
        logger.info("Multi-Agent Basketball GM System initialized")
```

This is the main controller:
- Creates connection to AI model
- Stores the game URL
- Creates a `GameState` to track everything
- **Creates all the specialist agents** - this is key!
- Creates an empty list to log all decisions
- Logs that the system started

## **Controller Agent - Browser Navigation (Lines 332-336)**

```python
    async def create_browser_agent(self, task: str) -> Agent:
        """Create browser-use agent for navigation tasks"""
        return Agent(task=task, llm=self.llm)
```

This method creates a browser automation agent for any navigation task. It's a helper method used throughout the controller.

## **Controller Agent - Data Extraction (Lines 338-365)**

```python
    async def extract_game_data(self) -> Dict[str, Any]:
        """Extract comprehensive game data for consultant agents"""
        task = """
        Extract comprehensive game data from the Basketball GM interface:
        1. Current season, record, team rating
        2. Full roster with player stats and salaries
        3. Salary cap information
        4. Available trade offers
        5. Upcoming schedule/opponents
        6. Free agents list (if in free agency)
        7. Draft prospects (if in draft)
        8. Team needs and weaknesses
        
        Return as much structured data as possible.
        """
        
        agent = await self.create_browser_agent(task)
        result = await agent.run()
        
        # In real implementation, parse the extracted data
        # For now, return mock structure
        return {
            'roster_data': {},
            'trade_offers': [],
            'free_agents': [],
            'draft_prospects': [],
            'upcoming_schedule': [],
            'team_needs': ['PG', 'Center'],
            'injuries': []
        }
```

This method:
1. Creates a task asking the browser agent to extract all game data
2. Creates a browser agent with that task
3. Runs the browser agent to actually extract the data
4. **Currently returns mock data** - in real use, you'd parse the actual extracted data
5. Returns a dictionary with all the data the specialists need

## **Controller Agent - Specialist Consultation (Lines 367-383)**

```python
    async def consult_specialists(self, decision_type: str, context: Dict[str, Any]) -> Decision:
        """Get recommendation from appropriate specialist agent"""
        
        if decision_type == "trade":
            return await self.trade_agent.analyze(self.game_state, context)
        elif decision_type == "draft":
            return await self.draft_agent.analyze(self.game_state, context)
        elif decision_type == "free_agency":
            return await self.free_agency_agent.analyze(self.game_state, context)
        elif decision_type == "lineup":
            return await self.lineup_agent.analyze(self.game_state, context)
        else:
            return Decision(
                decision_type=decision_type,
                recommendation="No specialist available",
                reasoning="Default action",
                confidence=0.3
            )
```

This is the **key coordination method**:
- Takes a decision type and context data
- Routes to the appropriate specialist agent
- Each specialist analyzes the situation and returns a `Decision`
- If no specialist exists for that decision type, returns a low-confidence default

## **Controller Agent - Decision Execution (Lines 385-410)**

```python
    async def execute_decision(self, decision: Decision) -> None:
        """Execute the recommended decision via browser automation"""
        
        task = f"""
        Execute the following Basketball GM decision:
        
        Decision Type: {decision.decision_type}
        Recommendation: {decision.recommendation}
        Reasoning: {decision.reasoning}
        
        Navigate to the appropriate section and implement this decision.
        Confirm the action was completed successfully.
        """
        
        agent = await self.create_browser_agent(task)
        await agent.run()
        
        # Log the decision
        self.decisions_log.append({
            "timestamp": datetime.now().isoformat(),
            "decision": decision.__dict__,
            "executed": True
        })
        
        logger.info(f"Executed {decision.decision_type}: {decision.recommendation}")
```

This method:
1. Takes a `Decision` from a specialist
2. Creates a browser task to execute that decision
3. Creates and runs a browser agent to do the actual clicking/navigation
4. Logs the decision with timestamp and details
5. Records that the decision was successfully executed

## **Controller Agent - Game Phase Handlers (Lines 412-467)**

```python
    async def handle_regular_season(self) -> None:
        """Handle regular season with specialist consultation"""
        logger.info("=== Regular Season Management ===")
        
        # Extract current game data
        context = await self.extract_game_data()
        
        # Consult lineup specialist
        lineup_decision = await self.consult_specialists("lineup", context)
        if lineup_decision.confidence > 0.6:
            await self.execute_decision(lineup_decision)
        
        # Check for trade opportunities
        trade_decision = await self.consult_specialists("trade", context)
        if trade_decision.confidence > 0.7:
            await self.execute_decision(trade_decision)
        
        # Simulate games
        await self.simulate_games()
```

This shows the **confidence-based decision making**:
1. Extract all current game data
2. Ask lineup specialist for advice
3. **Only execute if confidence > 0.6** (60% confident)
4. Ask trade specialist for advice  
5. **Only execute if confidence > 0.7** (70% confident - higher bar for trades)
6. Simulate the actual games

```python
    async def handle_draft(self) -> None:
        """Handle draft with draft specialist consultation"""
        logger.info("=== Draft Phase ===")
        
        context = await self.extract_game_data()
        draft_decision = await self.consult_specialists("draft", context)
        
        # Execute draft picks based on specialist recommendation
        await self.execute_decision(draft_decision)
```

Draft handling is simpler - just get advice and execute it (presumably draft decisions are always executed).

```python
    async def handle_free_agency(self) -> None:
        """Handle free agency with specialist consultation"""
        logger.info("=== Free Agency Phase ===")
        
        context = await self.extract_game_data()
        fa_decision = await self.consult_specialists("free_agency", context)
        
        # Execute free agency signings
        await self.execute_decision(fa_decision)
```

Same pattern for free agency.

## **Controller Agent - Game Simulation (Lines 469-480)**

```python
    async def simulate_games(self) -> None:
        """Simulate games through the season"""
        task = """
        Simulate Basketball GM games:
        1. Navigate to schedule or simulation options
        2. Simulate next batch of games (week/month)
        3. Check results and team performance
        4. Update any lineup changes if needed
        """
        
        agent = await self.create_browser_agent(task)
        await agent.run()
```

This creates a browser agent to actually play through games in Basketball GM.

## **Controller Agent - Season Management (Lines 482-505)**

```python
    async def run_complete_season(self) -> None:
        """Run complete season with multi-agent coordination"""
        try:
            # Regular season
            await self.handle_regular_season()
            
            # Playoffs (if qualified)
            if self.game_state.team_wins > 35:  # Rough playoff threshold
                await self.handle_playoffs()
            
            # Draft
            await self.handle_draft()
            
            # Free Agency  
            await self.handle_free_agency()
            
            # Advance season
            self.game_state.current_season += 1
            
        except Exception as e:
            logger.error(f"Error in season management: {e}")
```

This orchestrates a complete season:
1. Handle regular season (with specialist consultation)
2. Handle playoffs if team qualified (35+ wins)
3. Handle draft (with draft specialist)
4. Handle free agency (with FA specialist)
5. Increment season counter
6. Handle any errors that occur

## **Controller Agent - Playoffs (Lines 507-517)**

```python
    async def handle_playoffs(self) -> None:
        """Handle playoff phase"""
        task = """
        Navigate playoff phase:
        1. Check playoff bracket and matchups
        2. Optimize lineup for playoff intensity
        3. Simulate playoff games
        4. Track progress through rounds
        """
        
        agent = await self.create_browser_agent(task)
        await agent.run()
```

Creates browser agent to handle playoffs - could be enhanced to consult specialists.

## **Controller Agent - Reporting (Lines 519-543)**

```python
    async def generate_decisions_report(self) -> Dict[str, Any]:
        """Generate report of all specialist decisions"""
        return {
            "total_decisions": len(self.decisions_log),
            "decisions_by_type": self._count_decisions_by_type(),
            "high_confidence_decisions": [d for d in self.decisions_log 
                                        if d['decision']['confidence'] > 0.7],
            "recent_decisions": self.decisions_log[-10:],
            "season": self.game_state.current_season
        }
    
    def _count_decisions_by_type(self) -> Dict[str, int]:
        """Count decisions by type"""
        counts = {}
        for decision in self.decisions_log:
            decision_type = decision['decision']['decision_type']
            counts[decision_type] = counts.get(decision_type, 0) + 1
        return counts
```

These methods create reports:
- Count total decisions made
- Group decisions by type (trade, draft, etc.)
- Find high-confidence decisions (>70%)
- Get recent decisions
- Count how many of each decision type was made

## **Main Execution (Lines 545-580)**

```python
async def main():
    """Main execution with multi-agent system"""
    controller = ControllerAgent()
```
Creates the main controller (which creates all the specialists).

```python
    try:
        # Navigate to game
        task = "Navigate to Basketball GM and access the game interface"
        browser_agent = await controller.create_browser_agent(task)
        await browser_agent.run()
```
Creates browser agent to navigate to Basketball GM website.

```python
        # Run multiple seasons with specialist consultation
        for season in range(3):
            logger.info(f"=== SEASON {season + 1} ===")
            await controller.run_complete_season()
            
            # Brief pause between seasons
            await asyncio.sleep(2)
```
Runs 3 complete seasons, with specialist consultation in each one.

```python
        # Generate final report
        report = await controller.generate_decisions_report()
        print(f"\n=== MULTI-AGENT SESSION SUMMARY ===")
        print(f"Total Decisions Made: {report['total_decisions']}")
        print(f"Decisions by Type: {report['decisions_by_type']}")
        print(f"High Confidence Decisions: {len(report['high_confidence_decisions'])}")
```
Creates and displays final report.

```python
    except Exception as e:
        logger.error(f"Multi-agent system error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```
Error handling and program entry point.

## **Key Flow Summary:**

1. **Controller** creates all specialist agents
2. **Controller** navigates to Basketball GM  
3. For each season:
   - **Controller** extracts game data via browser
   - **Controller** asks specialists for advice
   - **Specialists** analyze data and return decisions
   - **Controller** executes high-confidence decisions via browser
   - **Controller** simulates games and advances to next phase
4. **Controller** generates report of all decisions made

The specialists never touch the browser - they only analyze data and make recommendations. The controller handles all navigation and execution.