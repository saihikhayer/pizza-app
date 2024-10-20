import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChefOrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "orders",  # Group name
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "orders",
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            "orders",
            {
                'type': 'order_message',
                'message': data['message']
            }
        )

    async def order_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))
