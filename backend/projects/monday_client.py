import os
import requests
from typing import Optional


class MondayClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('MONDAY_API_KEY')
        self.url = 'https://api.monday.com/v2'

    def create_task(self, title: str, deadline: str, assignee: str) -> dict:
        if not self.api_key:
            return {'ok': False, 'error': 'missing_api_key'}

        # In production implement GraphQL mutation with board and column IDs
        # This is a simple placeholder return value
        return {'ok': True, 'task': {'title': title, 'deadline': deadline, 'assignee': assignee}}
