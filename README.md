# GM Agents: Heuristic-Based, Reward-Oriented Browser Game Playing Agents

## Usage Instructions

To get started with this project, ensure you have Python 3.x installed on your system. Clone the repository to your local machine and install the required dependencies using `pip install playwright langchain-openai openai python-dotenv pydantic joblib numpy scikit-learn`. You will need an OpenAI API key, which should be set in your environment variables (for example, by creating a `.env` file with the line `OPENAI_API_KEY=your_key_here`).

To run the main agent, execute `python browse_use/web2.py`. This will launch the browser automation and begin the agent's management of a Basketball GM team. If you wish to train or retrain the reward model on your own feedback data, you can run `python browse_use/train_reward.py` after collecting trade feedback. To test the reward model, use `python browse_use/test_reward.py`.

The agent may prompt you for feedback on trade decisions during operation, and your responses will be logged for future model improvement. For best results, ensure you have a stable internet connection and that all dependencies are properly installed.

This system is a modular automation framework built to manage a basketball team in the Basketball GM game. It uses Playwright for browser control, OCR and parsing routines to extract game state, and a logistic regression model trained on trade data to provide structured decision support. The design is phase-aware, with heuristics tailored to preseason, trade deadlines, and playoffs, ensuring that decisions are both technically sound and contextually aligned with how a real general manager would operate.
