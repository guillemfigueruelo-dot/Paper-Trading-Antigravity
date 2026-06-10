import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_finnhub():
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"c": 150.0} # Current price mock
        yield mock_get

@pytest.fixture
def mock_ai():
    with patch('google.generativeai.generate_text') as mock_ai_call:
        mock_ai_call.return_value.result = '{"decision": "BUY", "justification": "Market is trending up", "confidence": 0.8}'
        yield mock_ai_call

@pytest.fixture
def mock_db():
    # Mock supabase client
    with patch('supabase.create_client') as mock_supa:
        client = MagicMock()
        client.table().select().execute.return_value = MagicMock(data=[{"balance": 100000}])
        mock_supa.return_value = client
        yield client
