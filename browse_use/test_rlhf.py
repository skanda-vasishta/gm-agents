import joblib
import numpy as np

def load_model():
    """Load the trained reward model."""
    return joblib.load("reward_model.pkl")

def evaluate_trade(trade_text: str, model) -> dict:
    """Evaluate a trade proposal using the reward model."""
    # Get probability of being a good trade
    prob = model.predict_proba([trade_text])[0][1]
    
    return {
        "probability": prob,
        "recommendation": "ACCEPT" if prob > 0.5 else "REJECT",
        "confidence": abs(prob - 0.5) * 2  # Scale to 0-1 range
    }

def main():
    # Load model
    print("Loading reward model...")
    model = load_model()
    
    # Test cases
    test_trades = [
        """Trade Proposal:
        Team A receives:
        - Player X ($20M)
        - 2025 1st round pick
        
        Team B receives:
        - Player Y ($18M)
        - Player Z ($5M)
        
        Salary implications:
        - Team A payroll: $180M
        - Team B payroll: $175M
        - Both teams over salary cap ($140.6M)""",
        
        """Trade Proposal:
        Team C receives:
        - Player W ($15M)
        
        Team D receives:
        - Player V ($14M)
        - 2026 2nd round pick
        
        Salary implications:
        - Team C payroll: $160M
        - Team D payroll: $165M
        - Both teams over salary cap ($140.6M)"""
    ]
    
    # Evaluate each test case
    print("\nEvaluating trade proposals...")
    for i, trade in enumerate(test_trades, 1):
        print(f"\nTrade Proposal {i}:")
        print(trade)
        
        result = evaluate_trade(trade, model)
        print("\nEvaluation Results:")
        print(f"Probability of being a good trade: {result['probability']:.2f}")
        print(f"Recommendation: {result['recommendation']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print("-" * 50)

if __name__ == "__main__":
    main() 