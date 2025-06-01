import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI
from browser_use import Agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GamePhase(Enum):
    REGULAR_SEASON = "regular_season"
    PLAYOFFS = "playoffs" 
    DRAFT = "draft"
    FREE_AGENCY = "free_agency"
    PRESEASON = "preseason"

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

@dataclass
class Decision:
    decision_type: str
    recommendation: str
    reasoning: str
    confidence: float
    alternatives: List[str] = None
    data_used: Dict = None

# Base class for consulting agents
class ConsultingAgent(ABC):
    def __init__(self, llm_model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=llm_model)
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def analyze(self, game_state: GameState, context: Dict[str, Any]) -> Decision:
        pass
    
    def _create_system_prompt(self) -> str:
        return f"You are a {self.name} for Basketball GM. Provide strategic advice based on the game data."

class TradeAgent(ConsultingAgent):
    """Specializes in trade analysis and recommendations"""
    
    async def analyze(self, game_state: GameState, context: Dict[str, Any]) -> Decision:
        """Analyze trade opportunities and make recommendations"""
        
        # Extract relevant data
        roster = context.get('roster_data', {})
        trade_offers = context.get('trade_offers', [])
        team_needs = context.get('team_needs', [])
        
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
        
        response = await self.llm.ainvoke(prompt)
        
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

class DraftAgent(ConsultingAgent):
    """Specializes in draft strategy and prospect evaluation"""
    
    async def analyze(self, game_state: GameState, context: Dict[str, Any]) -> Decision:
        """Analyze draft prospects and make recommendations"""
        
        draft_prospects = context.get('draft_prospects', [])
        team_needs = context.get('team_needs', [])
        draft_position = context.get('draft_position', 'Unknown')
        
        prompt = f"""
        As a Basketball GM Draft Specialist, analyze the draft situation:
        
        TEAM STATUS:
        - Season: {game_state.current_season}
        - Record: {game_state.team_wins}-{game_state.team_losses}
        - Draft Position: {draft_position}
        - Team Rating: {game_state.team_rating}
        
        DRAFT PROSPECTS: {json.dumps(draft_prospects[:10], indent=2)}
        TEAM NEEDS: {team_needs}
        
        Provide draft recommendations:
        1. Who should we target with our pick?
        2. Should we trade up/down in the draft?
        3. What positions should we prioritize?
        4. Any sleeper picks to watch?
        
        Response format:
        {{
            "recommendation": "specific draft action",
            "reasoning": "detailed scouting analysis",
            "confidence": 0.0-1.0,
            "alternatives": ["backup options"],
            "target_positions": ["position priorities"]
        }}
        """
        
        response = await self.llm.ainvoke(prompt)
        
        try:
            result = json.loads(response.content)
            return Decision(
                decision_type="draft",
                recommendation=result.get("recommendation", "Take best available"),
                reasoning=result.get("reasoning", "Standard draft approach"),
                confidence=result.get("confidence", 0.5),
                alternatives=result.get("alternatives", []),
                data_used={"prospects_available": len(draft_prospects)}
            )
        except:
            return Decision(
                decision_type="draft",
                recommendation="Take best available player",
                reasoning="Default draft strategy",
                confidence=0.5
            )

class FreeAgencyAgent(ConsultingAgent):
    """Specializes in free agency signings and roster construction"""
    
    async def analyze(self, game_state: GameState, context: Dict[str, Any]) -> Decision:
        """Analyze free agency options and make recommendations"""
        
        free_agents = context.get('free_agents', [])
        current_roster = context.get('roster_data', {})
        team_needs = context.get('team_needs', [])
        
        prompt = f"""
        As a Basketball GM Free Agency Specialist, analyze the situation:
        
        TEAM STATUS:
        - Season: {game_state.current_season}
        - Salary Cap Used: ${game_state.salary_cap_used:,.0f}
        - Available Cap Space: ${game_state.available_cap_space:,.0f}
        - Roster Size: {game_state.roster_size}
        
        FREE AGENTS: {json.dumps(free_agents[:15], indent=2)}
        CURRENT_ROSTER: {json.dumps(current_roster, indent=2)}
        TEAM NEEDS: {team_needs}
        
        Provide free agency recommendations:
        1. Which free agents should we target?
        2. What's our budget allocation strategy?  
        3. Should we make any qualifying offers?
        4. Who should we let walk?
        
        Response format:
        {{
            "recommendation": "specific signings to make",
            "reasoning": "cap management strategy",
            "confidence": 0.0-1.0,
            "alternatives": ["backup options"],
            "budget_allocation": {{"position": "max_offer"}}
        }}
        """
        
        response = await self.llm.ainvoke(prompt)
        
        try:
            result = json.loads(response.content)
            return Decision(
                decision_type="free_agency",
                recommendation=result.get("recommendation", "Sign value players"),
                reasoning=result.get("reasoning", "Budget-conscious approach"),
                confidence=result.get("confidence", 0.5),
                alternatives=result.get("alternatives", []),
                data_used={"free_agents_available": len(free_agents)}
            )
        except:
            return Decision(
                decision_type="free_agency", 
                recommendation="Sign affordable role players",
                reasoning="Conservative cap management",
                confidence=0.5
            )

class LineupAgent(ConsultingAgent):
    """Specializes in lineup optimization and rotations"""
    
    async def analyze(self, game_state: GameState, context: Dict[str, Any]) -> Decision:
        """Analyze lineup and rotation decisions"""
        
        roster = context.get('roster_data', {})
        upcoming_games = context.get('upcoming_schedule', [])
        injury_report = context.get('injuries', [])
        
        prompt = f"""
        As a Basketball GM Lineup Specialist, analyze the rotation:
        
        TEAM STATUS:
        - Season: {game_state.current_season} 
        - Record: {game_state.team_wins}-{game_state.team_losses}
        - Team Rating: {game_state.team_rating}
        
        ROSTER: {json.dumps(roster, indent=2)}
        UPCOMING_GAMES: {json.dumps(upcoming_games[:5], indent=2)}
        INJURIES: {injury_report}
        
        Provide lineup recommendations:
        1. Who should start at each position?
        2. What should our rotation look like?
        3. Any matchup-specific adjustments needed?
        4. Minutes distribution strategy?
        
        Response format:
        {{
            "recommendation": "starting lineup changes",
            "reasoning": "player performance analysis", 
            "confidence": 0.0-1.0,
            "alternatives": ["rotation options"],
            "starting_five": ["PG", "SG", "SF", "PF", "C"]
        }}
        """
        
        response = await self.llm.ainvoke(prompt)
        
        try:
            result = json.loads(response.content)
            return Decision(
                decision_type="lineup",
                recommendation=result.get("recommendation", "Keep current lineup"),
                reasoning=result.get("reasoning", "Maintain continuity"),
                confidence=result.get("confidence", 0.5),
                alternatives=result.get("alternatives", []),
                data_used={"roster_size": len(roster)}
            )
        except:
            return Decision(
                decision_type="lineup",
                recommendation="Optimize based on player ratings",
                reasoning="Start highest rated players",
                confidence=0.5
            )

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
        
        # Action limits and thresholds
        self.max_trades_per_phase = 2
        self.max_fa_signings_per_phase = 2
        self.max_lineup_changes_per_phase = 3
        self.trade_confidence_threshold = 0.85  # Higher threshold for trades
        self.fa_confidence_threshold = 0.80    # Higher threshold for free agency
        self.lineup_confidence_threshold = 0.70
        
        # Track actions per phase
        self.actions_this_phase = {
            "trades": 0,
            "fa_signings": 0,
            "lineup_changes": 0
        }
        
        logger.info("Multi-Agent Basketball GM System initialized")
    
    async def create_browser_agent(self, task: str) -> Agent:
        """Create browser-use agent for navigation tasks"""
        return Agent(task=task, llm=self.llm)
    
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
    
    def _reset_phase_actions(self):
        """Reset action counters for new phase"""
        self.actions_this_phase = {
            "trades": 0,
            "fa_signings": 0,
            "lineup_changes": 0
        }

    async def handle_regular_season(self) -> None:
        """Handle regular season with specialist consultation"""
        logger.info("=== Regular Season Management ===")
        
        # Reset action counters for new phase
        self._reset_phase_actions()
        
        # Extract current game data
        context = await self.extract_game_data()
        
        # Consult lineup specialist if under limit
        if self.actions_this_phase["lineup_changes"] < self.max_lineup_changes_per_phase:
            lineup_decision = await self.consult_specialists("lineup", context)
            if lineup_decision.confidence > self.lineup_confidence_threshold:
                await self.execute_decision(lineup_decision)
                self.actions_this_phase["lineup_changes"] += 1
        
        # Check for trade opportunities if under limit
        if self.actions_this_phase["trades"] < self.max_trades_per_phase:
            trade_decision = await self.consult_specialists("trade", context)
            if trade_decision.confidence > self.trade_confidence_threshold:
                await self.execute_decision(trade_decision)
                self.actions_this_phase["trades"] += 1
        
        # Simulate games
        await self.simulate_games()
    
    async def handle_draft(self) -> None:
        """Handle draft with draft specialist consultation"""
        logger.info("=== Draft Phase ===")
        
        context = await self.extract_game_data()
        draft_decision = await self.consult_specialists("draft", context)
        
        # Execute draft picks based on specialist recommendation
        # Draft decisions are always executed as they're time-sensitive
        await self.execute_decision(draft_decision)
    
    async def handle_free_agency(self) -> None:
        """Handle free agency with specialist consultation"""
        logger.info("=== Free Agency Phase ===")
        
        # Reset action counters for new phase
        self._reset_phase_actions()
        
        context = await self.extract_game_data()
        
        # Only proceed if under signing limit
        if self.actions_this_phase["fa_signings"] < self.max_fa_signings_per_phase:
            fa_decision = await self.consult_specialists("free_agency", context)
            
            # Execute free agency signings only if confidence is high enough
            if fa_decision.confidence > self.fa_confidence_threshold:
                await self.execute_decision(fa_decision)
                self.actions_this_phase["fa_signings"] += 1
            else:
                logger.info(f"Free agency signing rejected - confidence {fa_decision.confidence} below threshold {self.fa_confidence_threshold}")
    
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
    
    async def initialize_league(self) -> None:
        """Initialize a new league with real players and simulate to trade deadline"""
        logger.info("=== Initializing New League ===")
        
        task = """
        Execute the following steps in exact order:
        1. Navigate to https://play.basketball-gm.com/l/1/trade
        2. Click the "Create a new league" link
        3. Click the "Random" button for team selection
        4. Select "real" from the third dropdown (real players)
        5. Click the second "Random" button for team selection
        6. Click "Create League Processing" button
        7. Wait for the league to be created
        8. Once on the main page, click the "Play" dropdown
        9. Select "Until Trade Deadline" to simulate to that point
        10. Wait for simulation to complete
        
        Do not proceed with any other actions until these steps are completed.
        """
        
        agent = await self.create_browser_agent(task)
        await agent.run()
        
        # Update game state
        self.game_state.current_phase = GamePhase.REGULAR_SEASON
        logger.info("League initialized and simulated to trade deadline")

    async def run_complete_season(self) -> None:
        """Run complete season with multi-agent coordination"""
        try:
            # Initialize league if first season
            if self.game_state.current_season == 1:
                await self.initialize_league()
            
            # Regular season (starting from trade deadline)
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
            
            # Log phase completion
            logger.info(f"Completed season {self.game_state.current_season}")
            logger.info(f"Actions taken this phase: {self.actions_this_phase}")
            
        except Exception as e:
            logger.error(f"Error in season management: {e}")
    
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

# Main execution
async def main():
    """Main execution with multi-agent system"""
    controller = ControllerAgent()
    
    try:
        # Run multiple seasons with specialist consultation
        for season in range(3):
            logger.info(f"=== SEASON {season + 1} ===")
            await controller.run_complete_season()
            
            # Brief pause between seasons
            await asyncio.sleep(2)
        
        # Generate final report
        report = await controller.generate_decisions_report()
        print(f"\n=== MULTI-AGENT SESSION SUMMARY ===")
        print(f"Total Decisions Made: {report['total_decisions']}")
        print(f"Decisions by Type: {report['decisions_by_type']}")
        print(f"High Confidence Decisions: {len(report['high_confidence_decisions'])}")
        
    except Exception as e:
        logger.error(f"Multi-agent system error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())