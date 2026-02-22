import httpx
import os

class FeishuBot:
    def __init__(self):
        self.app_id = os.getenv('FEISHU_APP_ID', '')
        self.app_secret = os.getenv('FEISHU_APP_SECRET', '')
        self.base_url = 'https://open.feishu.cn/open-apis'
        
    async def send_message(self, user_id, content):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{self.base_url}/im/v1/messages',
                json={'receive_id': user_id, 'msg_type': 'text', 'content': {'text': content}}
            )
            return response.json()

print("✅ 飞书集成")
