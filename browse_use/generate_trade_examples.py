import random
from datetime import datetime, timedelta
import json

# Sample player pool with realistic salaries and ratings
PLAYERS = [
    {"name": "James Harden", "salary": 35.6, "rating": 85},
    {"name": "Joel Embiid", "salary": 42.1, "rating": 92},
    {"name": "Tyrese Maxey", "salary": 4.3, "rating": 82},
    {"name": "Tobias Harris", "salary": 39.2, "rating": 80},
    {"name": "De'Anthony Melton", "salary": 8.0, "rating": 78},
    {"name": "Jalen Brunson", "salary": 26.3, "rating": 84},
    {"name": "Julius Randle", "salary": 28.2, "rating": 83},
    {"name": "RJ Barrett", "salary": 23.8, "rating": 79},
    {"name": "Donovan Mitchell", "salary": 33.2, "rating": 88},
    {"name": "Darius Garland", "salary": 33.5, "rating": 85},
    {"name": "Evan Mobley", "salary": 8.9, "rating": 82},
    {"name": "Jarrett Allen", "salary": 20.0, "rating": 83},
    {"name": "Giannis Antetokounmpo", "salary": 45.6, "rating": 96},
    {"name": "Damian Lillard", "salary": 45.6, "rating": 89},
    {"name": "Khris Middleton", "salary": 29.3, "rating": 84},
    {"name": "Brook Lopez", "salary": 25.0, "rating": 81},
    {"name": "Stephen Curry", "salary": 51.9, "rating": 93},
    {"name": "Klay Thompson", "salary": 43.2, "rating": 82},
    {"name": "Draymond Green", "salary": 22.3, "rating": 80},
    {"name": "Andrew Wiggins", "salary": 24.3, "rating": 79},
]

TEAMS = [
    "Philadelphia 76ers",
    "New York Knicks",
    "Cleveland Cavaliers",
    "Milwaukee Bucks",
    "Golden State Warriors",
    "Boston Celtics",
    "Miami Heat",
    "Los Angeles Lakers",
    "Phoenix Suns",
    "Denver Nuggets"
]

def generate_trade_example():
    # Randomly select teams
    team1 = random.choice(TEAMS)
    team2 = random.choice([t for t in TEAMS if t != team1])
    
    # Generate random number of players for each team (1-3)
    num_players_team1 = random.randint(1, 3)
    num_players_team2 = random.randint(1, 3)
    
    # Select random players
    team1_players = random.sample(PLAYERS, num_players_team1)
    team2_players = random.sample([p for p in PLAYERS if p not in team1_players], num_players_team2)
    
    # Calculate total salaries
    team1_salary = sum(p["salary"] for p in team1_players)
    team2_salary = sum(p["salary"] for p in team2_players)
    
    # Generate random draft picks (0-2)
    team1_picks = random.randint(0, 2)
    team2_picks = random.randint(0, 2)
    
    # Generate team ratings
    team1_rating = random.randint(50, 70)
    team2_rating = random.randint(50, 70)
    
    # Generate trade evaluation
    trade_info = f"""**Trade Proposal Breakdown**

---

### 1. Players/Assets being traded from your team ({team1}):
{chr(10).join([f"- **{p['name']}** (${p['salary']}M)" for p in team1_players])}
{chr(10).join([f"- {random.randint(2024, 2028)} {random.choice(['1st', '2nd'])} round pick" for _ in range(team1_picks)]) if team1_picks > 0 else ""}

### 2. Players/Assets being received by your team ({team1}):
{chr(10).join([f"- **{p['name']}** (${p['salary']}M)" for p in team2_players])}
{chr(10).join([f"- {random.randint(2024, 2028)} {random.choice(['1st', '2nd'])} round pick" for _ in range(team2_picks)]) if team2_picks > 0 else ""}

### 3. Draft picks involved:
- {team1} sends: {team1_picks} pick(s)
- {team1} receives: {team2_picks} pick(s)

### 4. Salary implications:
- **{team1} payroll after trade:** ${random.randint(180, 220)}M
- **Salary cap:** $140.6M
- **Team overall rating:** {team1_rating} → {team1_rating + random.randint(-2, 2)}

- **{team2} payroll after trade:** ${random.randint(180, 220)}M
- **Salary cap:** $140.6M
- **Team overall rating:** {team2_rating} → {team2_rating + random.randint(-2, 2)}

---

**Summary:**  
{team1} is trading {', '.join([p['name'] for p in team1_players])} and {team1_picks} pick(s) to {team2} in exchange for {', '.join([p['name'] for p in team2_players])} and {team2_picks} pick(s). The trade {'increases' if team1_salary < team2_salary else 'decreases'} {team1}'s payroll by ${abs(team1_salary - team2_salary)}M."""

    # Generate AI decision (biased towards REJECT for salary cap issues)
    ai_decision = "REJECT" if random.random() < 0.7 else "ACCEPT"
    
    # Generate user feedback (biased towards agreement with AI)
    user_feedback = "yes" if random.random() < 0.8 else "no"
    
    return {
        "timestamp": (datetime.now() + timedelta(minutes=random.randint(1, 60))).strftime("%Y-%m-%d %H:%M:%S"),
        "trade_info": trade_info,
        "ai_decision": ai_decision,
        "user_feedback": user_feedback
    }

def main():
    # Generate 30 trade examples
    trades = [generate_trade_example() for _ in range(30)]
    
    # Write to file
    with open("trade_feedback.txt", "a") as f:
        for trade in trades:
            f.write(f"\n=== Trade Evaluation {trade['timestamp']} ===\n")
            f.write(f"Trade Information:\n{trade['trade_info']}\n")
            f.write(f"AI Decision: {trade['ai_decision']}\n")
            f.write(f"User Feedback: {trade['user_feedback']}\n")
            f.write("="*50 + "\n")

if __name__ == "__main__":
    main() 