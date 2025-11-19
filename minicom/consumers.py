import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message

def sanitize_email(email: str) -> str:
    return email.replace('@', '-at-').replace('+', '-plus-')


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        role = 'user' or 'admin'
        email = participant email
        """
        self.role = self.scope["url_route"]["kwargs"]["role"]
        self.email = self.scope["url_route"]["kwargs"]["email"]

        print("CONNECTING", self.role, self.email)

        # Room name for this user
        self.user_room = f"user_{sanitize_email(self.email)}"

        # USER joins their room immediately
        if self.role == "user":
            await self.channel_layer.group_add(self.user_room, self.channel_name)

        # Admin does NOT join any room until switching
        self.active_room = None

        await self.accept()

        # USER: Send full message history on connect
        if self.role == "user":
            messages = await self.get_messages(self.email)
            await self.send_json({
                "type": "history",
                "messages": messages
            })

        # ADMIN: nothing yet – admin UI will request conversations


    async def disconnect(self, close_code):
        if self.role == "user":
            await self.channel_layer.group_discard(self.user_room, self.channel_name)

        if self.active_room:
            await self.channel_layer.group_discard(self.active_room, self.channel_name)


    async def receive(self, text_data=None):
        data = json.loads(text_data)

        # ---------------------------------------------------------
        # USER sends a message
        # ---------------------------------------------------------
        if data.get("type") == "message" and self.role == "user":
            text = data.get("message", "").strip()
            if not text:
                return

            saved = await self.save_message(self.email, text, "user")

            # Notify the user themself
            await self.channel_layer.group_send(
                self.user_room,
                {"type": "chat_message", "message": saved}
            )

            # Notify admin ONLY if admin is currently in this room
            if self.active_room == self.user_room:
                await self.channel_layer.group_send(
                    self.active_room,
                    {"type": "chat_message", "message": saved}
                )

        # ---------------------------------------------------------
        # ADMIN sends message to a user
        # ---------------------------------------------------------
        elif data.get("type") == "message" and self.role == "admin":
            target = data.get("to")
            text = data.get("message", "").strip()
            if not target or not text:
                return

            saved = await self.save_message(target, text, "admin")
            target_room = f"user_{sanitize_email(target)}"

            # Deliver to target user
            await self.channel_layer.group_send(
                target_room,
                {"type": "chat_message", "message": saved}
            )

        # ---------------------------------------------------------
        # ADMIN requests conversation with a user
        # ---------------------------------------------------------
        elif data.get("type") == "get_conversation" and self.role == "admin":
            target = data.get("email")
            new_room = f"user_{sanitize_email(target)}"

            # Leave previous room
            if self.active_room:
                await self.channel_layer.group_discard(self.active_room, self.channel_name)

            # Join new one
            await self.channel_layer.group_add(new_room, self.channel_name)
            self.active_room = new_room

            # Send conversation history
            messages = await self.get_messages(target)
            await self.send_json({
                "type": "conversation",
                "email": target,
                "messages": messages
            })

        # ---------------------------------------------------------
        # Read Receipts
        # ---------------------------------------------------------
        elif data.get("type") == "read_messages":
            # The client says "I have read these messages"
            # We can either take a list of IDs or just mark all messages *from* the other person as read.
            # For simplicity in this demo, let's mark all messages in the current conversation as read
            # if the sender is the *other* person.

            if self.role == "user":
                # User is reading messages from Admin
                await self.mark_messages_read(self.email, sender_type="admin")
                
                # Notify Admin that user read them
                # Admin might be in the user's room
                await self.channel_layer.group_send(
                    self.user_room,
                    {"type": "messages_read", "reader": "user", "email": self.email}
                )

            elif self.role == "admin":
                # Admin is reading messages from User
                target = data.get("email")
                if target:
                    await self.mark_messages_read(target, sender_type="user")
                    
                    # Notify User that admin read them
                    target_room = f"user_{sanitize_email(target)}"
                    await self.channel_layer.group_send(
                        target_room,
                        {"type": "messages_read", "reader": "admin", "email": target}
                    )


    # ---------------------------------------------------------
    # Broadcast handler
    # ---------------------------------------------------------
    async def chat_message(self, event):
        await self.send_json({
            "type": "message",
            "message": event["message"]
        })

    async def messages_read(self, event):
        await self.send_json({
            "type": "messages_read",
            "reader": event["reader"],
            "email": event["email"]
        })

    # ---------------------------------------------------------
    # Database helpers — matching EXACT model fields
    # ---------------------------------------------------------
    @database_sync_to_async
    def save_message(self, email, text, sender_type):
        msg = Message.objects.create(
            participant_email=email,
            sender_type=sender_type,
            content=text
        )
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
            participant_email=email
        ).order_by("timestamp")

        return [
            {
                "id": m.id,
                "email": m.participant_email,
                "sender_type": m.sender_type,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
                "is_read": m.is_read,
            }
            for m in msgs
        ]

    @database_sync_to_async
    def mark_messages_read(self, participant_email, sender_type):
        # Mark all messages *sent by* sender_type as read
        Message.objects.filter(
            participant_email=participant_email,
            sender_type=sender_type,
            is_read=False
        ).update(is_read=True)

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload))
