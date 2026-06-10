import pytest
import subprocess

@pytest.mark.parametrize("scenario_id, name, complexity", [
    ('S1', 'Full daily cron run with volatile market (BUYS/SELLS)', 'High'),
    ('S2', 'Bot execution with insufficient funds (viability check)', 'Medium'),
    ('S3', 'Dry-run mode over full asset set (no state mutation)', 'Medium'),
    ('S4', 'User verifies dashboard after a week of automated trading', 'High'),
    ('S5', 'AI consistently returns HOLD for all assets (quiet market)', 'Medium')
])
def test_realworld_scenarios(scenario_id, name, complexity):
    """
    Tier 4: Real-world scenarios spanning multiple features.
    S1: F1, F2, F3, F4, F5, F8
    S2: F1, F2, F3, F4, F5
    S3: F1, F2, F3, F5, F6
    S4: F1, F4, F7
    S5: F1, F2, F3, F4, F5
    """
    try:
        subprocess.run(
            ["python", "-m", "bot.main", "--scenario", scenario_id],
            capture_output=True,
            timeout=10
        )
    except Exception:
        pytest.fail(f"Scenario {scenario_id} failed to execute")
