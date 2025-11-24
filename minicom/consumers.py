import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message
from .ai import reply
import asyncio


def sanitize_email(email: str) -> str:
    return email.replace('@', '-at-').replace('+', '-plus-')


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.role = self.scope["url_route"]["kwargs"]["role"]
        self.email = self.scope["url_route"]["kwargs"]["email"]

        print("CONNECTING", self.role, self.email)

        self.user_room = f"user_{sanitize_email(self.email)}"

        if self.role == "user":
            await self.channel_layer.group_add(self.user_room,
                                               self.channel_name)

        self.active_room = None

        await self.accept()

        if self.role == "user":
            messages = await self.get_messages(self.email)
            await self.send_json({"type": "history", "messages": messages})

    async def disconnect(self, close_code):
        if self.role == "user":
            await self.channel_layer.group_discard(self.user_room,
                                                   self.channel_name)

        if self.active_room:
            await self.channel_layer.group_discard(self.active_room,
                                                   self.channel_name)

    async def generate_ai_reply(self, user_text: str) -> str:
        ai_text = f"AI Agent: {await reply(user_text)}"
        ai_msg = await self.save_message(self.email, ai_text, "ai")

        await self.channel_layer.group_send(self.user_room, {
            "type": "chat_message",
            "message": ai_msg
        })

    async def receive(
        self,
        text_data=None
    ):  #browser can never know until receive is complete and therfore async await will have a problem becuase
        data = json.loads(text_data)

        if data.get("type") == "message" and self.role == "user":
            text = data.get("message", "").strip()
            if not text:
                return

            saved = await self.save_message(self.email, text, "user")

            await self.channel_layer.group_send(self.user_room, {
                "type": "chat_message",
                "message": saved
            })

            if not await self.check_admin_replied(self.email):
                asyncio.create_task(self.generate_ai_reply(text))

        elif data.get("type") == "message" and self.role == "admin":
            target = data.get("to")
            text = data.get("message", "").strip()
            if not target or not text:
                return

            saved = await self.save_message(target, text, "admin")
            target_room = f"user_{sanitize_email(target)}"

            await self.channel_layer.group_send(target_room, {
                "type": "chat_message",
                "message": saved
            })

        elif data.get("type") == "get_conversation" and self.role == "admin":
            target = data.get("email")
            new_room = f"user_{sanitize_email(target)}"

            if self.active_room:
                await self.channel_layer.group_discard(self.active_room,
                                                       self.channel_name)

            await self.channel_layer.group_add(new_room, self.channel_name)
            self.active_room = new_room

            messages = await self.get_messages(target)
            await self.send_json({
                "type": "conversation",
                "email": target,
                "messages": messages
            })

        elif data.get("type") == "read_messages":

            if self.role == "user":
                await self.mark_messages_read(self.email, sender_type="admin")

                await self.channel_layer.group_send(self.user_room, {
                    "type": "messages_read",
                    "reader": "user",
                    "email": self.email
                })

            elif self.role == "admin":
                target = data.get("email")
                if target:
                    await self.mark_messages_read(target, sender_type="user")

                    target_room = f"user_{sanitize_email(target)}"
                    await self.channel_layer.group_send(
                        target_room, {
                            "type": "messages_read",
                            "reader": "admin",
                            "email": target
                        })

    async def chat_message(self, event):
        await self.send_json({"type": "message", "message": event["message"]})

    async def messages_read(self, event):
        await self.send_json({
            "type": "messages_read",
            "reader": event["reader"],
            "email": event["email"]
        })

    @database_sync_to_async
    def check_admin_replied(self, email):
        return Message.objects.filter(participant_email=email,
                                      sender_type="admin").exists()

    @database_sync_to_async
    def save_message(self, email, text, sender_type):
        msg = Message.objects.create(participant_email=email,
                                     sender_type=sender_type,
                                     content=text)
        return {
            "id": msg.id,
            "email": msg.participant_email,
            "sender_type": msg.sender_type,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "is_read": msg.is_read,
        }

    @database_sync_to_async
    def get_messages(self, email):
        msgs = Message.objects.filter(
            participant_email=email).order_by("timestamp")

        return [{
            "id": m.id,
            "email": m.participant_email,
            "sender_type": m.sender_type,
            "content": m.content,
            "timestamp": m.timestamp.isoformat(),
            "is_read": m.is_read,
        } for m in msgs]

    @database_sync_to_async
    def mark_messages_read(self, participant_email, sender_type):
        Message.objects.filter(participant_email=participant_email,
                               sender_type=sender_type,
                               is_read=False).update(is_read=True)

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload))
