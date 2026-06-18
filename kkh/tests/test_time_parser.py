import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from datetime import datetime
import pytz

# Add src root to sys.path so we can import core and database
SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_ROOT not in sys.path:
    sys.path.append(SRC_ROOT)

# We mock db_manager module to avoid SQLite/cryptography issues during testing
sys.modules['database.db_manager'] = MagicMock()
sys.modules['..database.db_manager'] = MagicMock()

# Now we can safely import core.agent
from core.agent import Agent

class TestTimeParserAndContext(unittest.TestCase):

    @patch('core.agent.add_or_get_user')
    @patch('core.agent.OpenAI')
    def setUp(self, mock_openai, mock_add_user):
        # Setup mock user info and OpenAI client
        mock_add_user.return_value = {"id": 1, "user_id": "test_user", "timezone": "Asia/Seoul"}
        self.agent = Agent(user_id="test_user")

    def test_kst_time_prompt_generation(self):
        """Test that _get_current_kst_time_prompt produces a string containing the current KST date/time."""
        prompt = self.agent._get_current_kst_time_prompt()
        self.assertIn("현재 한국 시간은", prompt)
        self.assertIn("요일", prompt)
        
        # Verify it uses KST timezone
        kst_timezone = pytz.timezone('Asia/Seoul')
        now_kst = datetime.now(kst_timezone)
        expected_year_month = now_kst.strftime("%Y년 %m월")
        self.assertIn(expected_year_month, prompt)

    @patch('core.agent.get_last_event_id')
    def test_query_contextualization_with_keyword(self, mock_get_last_event):
        """Test that contextual keywords trigger query enhancement when last event exists."""
        mock_get_last_event.return_value = "event_12345"
        
        # Mock OpenAI chat completion call
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].message.content = "처리했습니다."
        self.agent.client.chat.completions.create.return_value = mock_response

        # Call invoke with contextual keyword "방금"
        self.agent.invoke("방금 등록한 회의 취소해줘")

        # Verify that create was called with a query containing the event ID context
        create_args = self.agent.client.chat.completions.create.call_args[1]
        user_message = next(msg for msg in create_args['messages'] if msg['role'] == 'user')
        
        self.assertIn("방금 등록한 회의 취소해줘", user_message['content'])
        self.assertIn("컨텍스트: 방금 처리한 이벤트 ID는 'event_12345' 입니다.", user_message['content'])

    @patch('core.agent.get_last_event_id')
    def test_query_contextualization_without_keyword(self, mock_get_last_event):
        """Test that standard queries do NOT append event ID context even if last event exists."""
        mock_get_last_event.return_value = "event_12345"
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].message.content = "처리했습니다."
        self.agent.client.chat.completions.create.return_value = mock_response

        self.agent.invoke("내일 일정 알려줘")

        create_args = self.agent.client.chat.completions.create.call_args[1]
        user_message = next(msg for msg in create_args['messages'] if msg['role'] == 'user')
        
        self.assertEqual(user_message['content'], "내일 일정 알려줘")

if __name__ == '__main__':
    unittest.main()
