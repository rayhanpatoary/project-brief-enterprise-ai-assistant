from unittest.mock import patch
from pathlib import Path

import httpx
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / 'ui' / 'streamlit_app.py'


def test_chat_history_modes_and_clear():
    response = httpx.Response(200, json={'answer': 'Two days.', 'sources': [], 'queries': []})
    with patch('httpx.request', return_value=response) as request:
        at = AppTest.from_file(APP_PATH, default_timeout=20).run()
        assert not at.exception
        at.chat_input[0].set_value('How many remote days?').run()
        assert not at.exception
        assert len(at.chat_message) == 2
        assert at.session_state['messages'][1]['content'] == 'Two days.'
        at.chat_input[0].set_value('Who approves it?').run()
        assert len(request.call_args.kwargs['json']['history']) == 2
        at.button[-1].click().run()
        assert not at.session_state['messages'] and not at.exception


def test_api_failure_is_visible():
    with patch('httpx.request', side_effect=httpx.ConnectError('offline')):
        at = AppTest.from_file(APP_PATH, default_timeout=20).run()
        at.chat_input[0].set_value('What is the policy?').run()
        assert at.error and not at.exception
