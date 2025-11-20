# Django Channels & WebSockets: Complete Guide

A comprehensive guide to understanding real-time web applications with Django Channels, WebSockets, and ASGI.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [ASGI vs WSGI](#asgi-vs-wsgi)
4. [Django Channels Architecture](#django-channels-architecture)
5. [WebSocket Fundamentals](#websocket-fundamentals)
6. [Consumers Deep Dive](#consumers-deep-dive)
7. [Channel Layers & Groups](#channel-layers--groups)
8. [Consumer Instance Management](#consumer-instance-management)
9. [Message Flow Architecture](#message-flow-architecture)
10. [Common Patterns & Best Practices](#common-patterns--best-practices)
11. [Interview Questions & Answers](#interview-questions--answers)

---

## Introduction

Django Channels extends Django to handle WebSockets, HTTP2, and other async protocols in addition to traditional HTTP. This guide explains how it all works together to create real-time applications.

### What You'll Learn

- How WebSockets enable real-time, bidirectional communication
- The difference between ASGI and WSGI
- How Django Channels manages WebSocket connections
- Consumer lifecycle and instance management
- Channel layers and group-based broadcasting
- Real-world message flow in a chat application

---

## Core Concepts

### 1. WebSockets

**What is a WebSocket?**
- A protocol that enables **full-duplex, bidirectional communication** between client and server
- Built on top of TCP, like HTTP
- **Persistent connection** - stays open for the duration of the session
- Server can **push** data to clients without being asked

**HTTP vs WebSocket:**

```
HTTP (Traditional):
Client: "Give me data"  →  Server
Client                ←  Response: "Here's data"
[Connection closes]
[Repeat for every request]

WebSocket:
Client: "Connect"      →  Server
Client                ←  "Connected"
[Connection stays open]
Client: "Message 1"    →  Server
Client                ←  "Response 1"
Server: "Push update"  →  Client
Client: "Message 2"    →  Server
... [Connection persists] ...
```

**WebSocket URL Format:**
```
ws://localhost:8000/ws/chat/user/john@example.com/
^^
WebSocket protocol (ws:// or wss:// for secure)
```

---

### 2. Django Channels

**What is Django Channels?**
- An extension to Django that adds support for WebSockets and other async protocols
- Allows Django to handle **both** HTTP and WebSocket connections
- Introduces the concept of "Consumers" (like Views for WebSockets)

**Why is it needed?**
- Traditional Django is built for **synchronous** request-response cycles
- Can't handle persistent connections or server-to-client push
- Channels adds **async** capabilities

---

### 3. Consumers

**What is a Consumer?**
- The WebSocket equivalent of a Django View
- Handles WebSocket connection lifecycle:
  - `connect()` - When client connects
  - `receive()` - When client sends message
  - `disconnect()` - When connection closes

**Example Consumer:**

```python
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Called when WebSocket handshake completes
        await self.accept()
    
    async def disconnect(self, close_code):
        # Called when WebSocket closes
        pass
    
    async def receive(self, text_data):
        # Called when client sends message
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({
            'message': 'Got your message!'
        }))
```

---

## ASGI vs WSGI

### WSGI (Web Server Gateway Interface)

**Traditional Django:**

```
┌─────────────────────────────────┐
│  WSGI Server (Gunicorn)         │
│  ↓                              │
│  wsgi.py                        │
│  ↓                              │
│  Django (synchronous only)      │
│  ↓                              │
│  Views → Response               │
└─────────────────────────────────┘

❌ No WebSocket Support
❌ No async support
✅ Simple HTTP only
```

**Characteristics:**
- Synchronous only
- One request → One response → Connection closes
- Cannot handle WebSockets
- Cannot push data to clients

---

### ASGI (Asynchronous Server Gateway Interface)

**Modern Django with Channels:**

```
┌─────────────────────────────────────┐
│  ASGI Server (Daphne)               │
│  ↓                                  │
│  asgi.py                            │
│  ↓                                  │
│  ProtocolTypeRouter                 │
│  ├─→ HTTP → Django Views            │
│  └─→ WebSocket → Consumers          │
└─────────────────────────────────────┘

✅ WebSocket Support
✅ Async support
✅ HTTP + more
```

**Characteristics:**
- Asynchronous capable
- Persistent connections supported
- Handles HTTP AND WebSocket
- Can push data to clients

---

### How ASGI Handles HTTP (Without wsgi.py)

**The Magic: Automatic Fallback**

When you only define WebSocket routing:

```python
# asgi.py
from channels.routing import ProtocolTypeRouter, URLRouter
from minicom.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "websocket": URLRouter(websocket_urlpatterns),
    # No "http" defined!
})
```

**Channels automatically adds HTTP handling:**

```python
# What actually happens (behind the scenes)
from channels.http import AsgiHandler

application = ProtocolTypeRouter({
    "http": AsgiHandler(),  # ← AUTO-ADDED by Channels!
    "websocket": URLRouter(websocket_urlpatterns),
})
```

**The AsgiHandler:**
- Bridges ASGI to Django's WSGI-style views
- Allows Django 2.2 (WSGI-only) to work in ASGI environment
- Routes to `urls.py` just like traditional Django

**Source Code Proof (Channels 2.x):**

```python
# From channels.routing.ProtocolTypeRouter
def __init__(self, application_mapping):
    self.application_mapping = application_mapping
    
    # If no "http" key provided, use AsgiHandler as default!
    if "http" not in self.application_mapping:
        from channels.http import AsgiHandler
        self.application_mapping["http"] = AsgiHandler()
```

---

## Django Channels Architecture

### The Complete Stack

```
┌─────────────────────────────────────────────────┐
│ 1. Browser (JavaScript)                         │
│    new WebSocket("ws://localhost:8000/...")     │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ 2. Daphne (ASGI Server)                         │
│    - Receives WebSocket connection              │
│    - Loads asgi.py                              │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ 3. ProtocolTypeRouter                           │
│    - Checks protocol type                       │
│    - Routes to appropriate handler              │
│      • HTTP → AsgiHandler → Django              │
│      • WebSocket → Next layer                   │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ 4. URLRouter                                    │
│    - Matches WebSocket URL pattern              │
│    - Extracts URL parameters                    │
│    - Routes to specific Consumer                │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ 5. ChatConsumer                                 │
│    - Handles connection lifecycle               │
│    - Processes messages                         │
│    - Sends responses                            │
└─────────────────────────────────────────────────┘
```

---

### Middleware Stack (The Onion Model)

Requests flow **inward** through layers, responses flow **outward**:

```python
ProtocolTypeRouter({
    "websocket": 
        AuthMiddlewareStack(        # ← Layer 2
            URLRouter(              # ← Layer 3
                websocket_urlpatterns  # ← Layer 4
            )
        )
})
```

**Request Flow (Outside → Inside):**

```
Request → ProtocolTypeRouter → AuthMiddlewareStack → URLRouter → Consumer
```

Each layer:
1. Receives the `scope` (connection metadata)
2. Modifies/enriches the `scope`
3. Passes to next layer

**What each layer adds to scope:**

```python
# After ProtocolTypeRouter:
scope = {
    'type': 'websocket',
    'path': '/ws/chat/user/john@example.com/',
}

# After AuthMiddlewareStack:
scope = {
    'type': 'websocket',
    'path': '/ws/chat/user/john@example.com/',
    'user': <User: john@example.com>,      # ← Added
    'session': <Session>,                   # ← Added
}

# After URLRouter:
scope = {
    'type': 'websocket',
    'path': '/ws/chat/user/john@example.com/',
    'user': <User: john@example.com>,
    'session': <Session>,
    'url_route': {                          # ← Added
        'kwargs': {
            'role': 'user',
            'email': 'john@example.com'
        }
    }
}
```

---

### Optional: AuthMiddlewareStack

**What it does:**
- Reads session cookie from WebSocket connection
- Loads authenticated user from database
- Adds `scope['user']` to the connection

**When you need it:**
- Verifying users are logged in
- Restricting access based on permissions
- Accessing `request.user` equivalent

**When you DON'T need it:**
- Using URL parameters for identity (like minicom does)
- Building public/demo applications
- Handling auth yourself

**Security Note:**
```python
# Without AuthMiddlewareStack (INSECURE):
self.email = self.scope["url_route"]["kwargs"]["email"]
# ⚠️ Anyone can claim to be anyone!

# With AuthMiddlewareStack (SECURE):
user = self.scope['user']
if not user.is_authenticated:
    await self.close()
    return
self.email = user.email  # ✅ Verified from database
```

---

## WebSocket Fundamentals

### Connection Lifecycle

```
┌─────────────────────────────────────────────┐
│ 1. HANDSHAKE                                │
│    Client: "Upgrade to WebSocket?"          │
│    Server: "101 Switching Protocols"        │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│ 2. OPEN                                     │
│    - Consumer.connect() called              │
│    - Connection established                 │
│    - Can send/receive messages              │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│ 3. ACTIVE (Message Exchange)                │
│    Client → Server: Messages                │
│    Server → Client: Responses/Push          │
│    [Connection stays open]                  │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│ 4. CLOSE                                    │
│    - User closes tab / network failure      │
│    - Consumer.disconnect() called           │
│    - Connection terminated                  │
└─────────────────────────────────────────────┘
```

---

### Client-Side WebSocket API (JavaScript)

```javascript
// 1. Create connection
const socket = new WebSocket('ws://localhost:8000/ws/chat/user/john@example.com/');

// 2. Connection opened
socket.onopen = () => {
    console.log('Connected!');
    socket.send(JSON.stringify({ type: 'hello' }));
};

// 3. Receive message
socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// 4. Connection closed
socket.onclose = () => {
    console.log('Disconnected');
};

// 5. Error occurred
socket.onerror = (error) => {
    console.error('WebSocket error:', error);
};

// 6. Send message
socket.send(JSON.stringify({
    type: 'message',
    content: 'Hello, server!'
}));
```

---

## Consumers Deep Dive

### Consumer Class Structure

```python
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json

class ChatConsumer(AsyncWebsocketConsumer):
    
    # ═══════════════════════════════════════════
    # LIFECYCLE METHODS
    # ═══════════════════════════════════════════
    
    async def connect(self):
        """
        Called when WebSocket connection is established.
        This is where you:
        - Extract URL parameters
        - Join groups
        - Accept or reject the connection
        - Send initial data
        """
        # Get URL parameters
        self.role = self.scope["url_route"]["kwargs"]["role"]
        self.email = self.scope["url_route"]["kwargs"]["email"]
        
        # Create room name
        self.user_room = f"user_{self.email}"
        
        # Join a group
        await self.channel_layer.group_add(
            self.user_room,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Send initial data
        await self.send_json({
            'type': 'connected',
            'message': 'Welcome!'
        })
    
    async def disconnect(self, close_code):
        """
        Called when WebSocket connection closes.
        This is where you:
        - Leave groups
        - Clean up resources
        - Update online status
        """
        await self.channel_layer.group_discard(
            self.user_room,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Called when client sends a message.
        This is where you:
        - Parse incoming data
        - Validate input
        - Process business logic
        - Send responses
        """
        data = json.loads(text_data)
        
        # Route by message type
        if data['type'] == 'message':
            await self.handle_message(data)
        elif data['type'] == 'typing':
            await self.handle_typing(data)
    
    # ═══════════════════════════════════════════
    # CUSTOM HANDLERS
    # ═══════════════════════════════════════════
    
    async def handle_message(self, data):
        """Handle chat message"""
        # Save to database
        message = await self.save_message(data['text'])
        
        # Broadcast to group
        await self.channel_layer.group_send(
            self.user_room,
            {
                'type': 'chat_message',
                'message': message
            }
        )
    
    # ═══════════════════════════════════════════
    # BROADCAST RECEIVERS
    # ═══════════════════════════════════════════
    
    async def chat_message(self, event):
        """
        Called when group_send() is triggered with type='chat_message'.
        This is the handler that receives group broadcasts.
        
        Method name MUST match the 'type' in group_send(),
        with dots replaced by underscores.
        """
        await self.send_json({
            'type': 'message',
            'message': event['message']
        })
    
    # ═══════════════════════════════════════════
    # DATABASE HELPERS
    # ═══════════════════════════════════════════
    
    @database_sync_to_async
    def save_message(self, text):
        """
        Decorator bridges sync Django ORM to async consumer.
        Required because Django's ORM is synchronous!
        """
        from .models import Message
        msg = Message.objects.create(
            content=text,
            sender=self.email
        )
        return {
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat()
        }
    
    # ═══════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════
    
    async def send_json(self, data):
        """Helper to send JSON data"""
        await self.send(text_data=json.dumps(data))
```

---

### async/await Pattern

**Why async/await?**

```python
# Synchronous (blocking):
def get_data():
    result = slow_operation()  # ← Blocks entire thread!
    return result

# Asynchronous (non-blocking):
async def get_data():
    result = await slow_operation()  # ← Pauses this function,
                                      #   but other code can run!
    return result
```

**In Consumers:**

```python
async def receive(self, text_data):
    # Database operation (sync → async bridge)
    message = await self.save_message(text)
    
    # Channel layer operation (already async)
    await self.channel_layer.group_send(
        self.room,
        {'type': 'chat_message', 'message': message}
    )
    
    # Send to client (async)
    await self.send_json({'status': 'sent'})
```

---

### @database_sync_to_async Decorator

**The Problem:**
- Django ORM is **synchronous**
- Consumers are **async**
- Can't mix them directly!

**The Solution:**

```python
from channels.db import database_sync_to_async

@database_sync_to_async
def get_messages(email):
    # This is sync code!
    return list(Message.objects.filter(user=email))

# Can now use in async function:
async def connect(self):
    messages = await get_messages(self.email)  # ✅ Works!
```

**What it does:**
- Runs the sync function in a thread pool
- Returns a Future/coroutine that can be awaited
- Makes it safe to use Django ORM in async code

---

## Channel Layers & Groups

### What is a Channel Layer?

A **message broker** that handles communication between different parts of your application.

**Think of it as:**
- A pub/sub system
- A message queue
- An event bus

```
┌─────────────────────────────────────────────┐
│          CHANNEL LAYER                      │
│          (Message Broker)                   │
│                                             │
│  Groups:                                    │
│  ┌──────────────────────────────────┐      │
│  │ "room_general": [                │      │
│  │    "channel_abc123",             │      │
│  │    "channel_def456",             │      │
│  │    "channel_xyz789"              │      │
│  │ ]                                │      │
│  └──────────────────────────────────┘      │
│                                             │
│  ┌──────────────────────────────────┐      │
│  │ "room_vip": [                    │      │
│  │    "channel_abc123"              │      │
│  │ ]                                │      │
│  └──────────────────────────────────┘      │
└─────────────────────────────────────────────┘
```

---

### Channel Layer Backends

**InMemoryChannelLayer (Development):**

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}
```

**Pros:**
- ✅ Easy to set up
- ✅ No dependencies
- ✅ Fast for dev

**Cons:**
- ❌ Lost on server restart
- ❌ Single server only
- ❌ Not for production!

---

**RedisChannelLayer (Production):**

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
        },
    },
}
```

**Pros:**
- ✅ Persistent
- ✅ Multiple servers
- ✅ Scales horizontally
- ✅ Production-ready

**Cons:**
- ⚠️ Requires Redis server

---

### Groups Explained

**What is a Group?**
- A named collection of channel names
- Like a "chat room" or "topic"
- Allows broadcasting to multiple consumers at once

**Group Operations:**

```python
# Join a group
await self.channel_layer.group_add(
    "room_general",      # group name
    self.channel_name    # this consumer's unique channel
)

# Leave a group
await self.channel_layer.group_discard(
    "room_general",
    self.channel_name
)

# Send to everyone in a group
await self.channel_layer.group_send(
    "room_general",
    {
        'type': 'chat_message',  # Handler method name
        'message': 'Hello everyone!'
    }
)
```

---

### How group_send() Works

**Step-by-step:**

```python
# 1. You call group_send
await self.channel_layer.group_send(
    "room_general",
    {
        'type': 'chat_message',
        'text': 'Hello!'
    }
)

# 2. Channel layer looks up group members
# "room_general": ["channel_abc123", "channel_def456", "channel_xyz789"]

# 3. Channel layer sends event to EACH channel
# Each consumer instance receives the event

# 4. For each consumer that receives it:
async def chat_message(self, event):
    # ↑ Method name matches 'type' from group_send
    # This is called automatically!
    await self.send_json({
        'message': event['text']
    })
```

**Important:** The method name MUST match the `type` field (with dots → underscores):
- `type: 'chat_message'` → `async def chat_message(self, event)`
- `type: 'user.online'` → `async def user_online(self, event)`

---

### Pub/Sub Pattern

```
Publisher (Consumer #1):
    ↓
    await channel_layer.group_send("topic", {...})
    ↓
Channel Layer:
    ↓
    Finds all subscribers in group "topic"
    ↓
    Delivers to each channel
    ↓
Subscribers (All consumers in group):
    ↓
    Handler method called
    ↓
    Each sends to their WebSocket client
```

---

## Consumer Instance Management

### The Golden Rule

```
1 WebSocket Connection = 1 Consumer Instance
```

**NOT:**
- ❌ 1 webpage = 1 consumer
- ❌ 1 user = 1 consumer
- ❌ 1 browser = 1 consumer

**BUT:**
- ✅ 1 WebSocket connection = 1 consumer instance

---

### Multiple Instances Scenario

**User opens 3 tabs:**

```
┌─────────────────────────────────────────┐
│        User's Browser                   │
│                                         │
│  Tab 1      Tab 2      Tab 3           │
│  (Chat)     (Chat)     (Chat)          │
│    │          │          │             │
│    │WS        │WS        │WS           │
└────┼──────────┼──────────┼─────────────┘
     │          │          │
     └──────────┼──────────┘
                ↓
    ┌───────────────────────────────┐
    │      SERVER                   │
    │                               │
    │  ChatConsumer #1 (Tab 1)      │
    │  - channel: abc123            │
    │                               │
    │  ChatConsumer #2 (Tab 2)      │
    │  - channel: def456            │
    │                               │
    │  ChatConsumer #3 (Tab 3)      │
    │  - channel: xyz789            │
    │                               │
    │  All in same group!           │
    └───────────────────────────────┘
```

**What happens when Tab 1 sends a message?**

1. Tab 1's WebSocket sends message
2. Instance #1 receives it in `receive()`
3. Instance #1 broadcasts to group
4. Channel layer delivers to ALL 3 instances
5. All 3 tabs receive and display the message

---

### Instance Isolation

Each consumer instance is **completely separate**:

```python
# Instance #1:
self.role = "user"
self.email = "john@example.com"
self.channel_name = "specific.abc123"

# Instance #2 (different connection):
self.role = "admin"
self.email = "admin@example.com"
self.channel_name = "specific.def456"

# These are DIFFERENT objects in memory!
# Changing one doesn't affect the other
```

---

### Channel Names

Every consumer instance gets a **unique** channel name:

```python
async def connect(self):
    print(self.channel_name)
    # → "specific.abc123xyz..."
```

**Characteristics:**
- Auto-generated by Channels
- Unique per connection
- Used for routing messages
- Format: `"specific.{random_id}"`

---

## Message Flow Architecture

### Complete Flow Example

**Scenario:** User sends "Hello" → Admin receives it

---

### Step 1: User Sends Message

```javascript
// User's browser (JavaScript)
socket.send(JSON.stringify({
    type: 'message',
    message: 'Hello!'
}));
```

---

### Step 2: User's Consumer Receives

```python
# User's ChatConsumer instance
async def receive(self, text_data):
    data = json.loads(text_data)
    # data = {'type': 'message', 'message': 'Hello!'}
    
    if data.get("type") == "message" and self.role == "user":
        text = data.get("message")  # "Hello!"
        
        # Save to database
        saved = await self.save_message(self.email, text, "user")
        # saved = {
        #     'id': 42,
        #     'content': 'Hello!',
        #     'sender': 'john@example.com',
        #     'timestamp': '2025-11-20T10:30:00Z'
        # }
```

---

### Step 3: Broadcast to Group

```python
        # Broadcast to user's room
        await self.channel_layer.group_send(
            self.user_room,  # "user_john-at-example.com"
            {
                "type": "chat_message",
                "message": saved
            }
        )
```

---

### Step 4: Channel Layer Distributes

```
Channel Layer:
  Groups = {
      "user_john-at-example.com": [
          "specific.abc123",  ← User's channel
          "specific.def456"   ← Admin's channel (joined this room)
      ]
  }

Action: Send event to BOTH channels
```

---

### Step 5: Both Consumers Receive

**User's Consumer:**
```python
async def chat_message(self, event):
    # event = {'type': 'chat_message', 'message': {...}}
    await self.send_json({
        "type": "message",
        "message": event["message"]
    })
    # → Sends to user's browser (echo)
```

**Admin's Consumer:**
```python
async def chat_message(self, event):
    # Same handler!
    await self.send_json({
        "type": "message",
        "message": event["message"]
    })
    # → Sends to admin's browser
```

---

### Step 6: Browsers Update UI

```javascript
// Both browsers receive:
socket.onmessage = (evt) => {
    const data = JSON.parse(evt.data);
    // data = {
    //     type: 'message',
    //     message: {
    //         id: 42,
    //         content: 'Hello!',
    //         sender: 'john@example.com',
    //         timestamp: '2025-11-20T10:30:00Z'
    //     }
    // }
    
    // Update DOM to show message
    addMessageToChat(data.message);
};
```

---

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ 1. User's Browser                                       │
│    socket.send({type: 'message', message: 'Hello!'})    │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ 2. User's ChatConsumer Instance                         │
│    - receive() called                                   │
│    - Parse JSON                                         │
│    - Save to database                                   │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Channel Layer (group_send)                           │
│    - Send to group: "user_john-at-example.com"          │
│    - Lookup members: [abc123, def456]                   │
└─────────┬──────────────────────────────┬────────────────┘
          ↓                              ↓
┌───────────────────────┐    ┌──────────────────────────┐
│ 4a. User's Consumer   │    │ 4b. Admin's Consumer     │
│    chat_message()     │    │     chat_message()       │
│    - Send to browser  │    │     - Send to browser    │
└──────────┬────────────┘    └──────────┬───────────────┘
           ↓                            ↓
┌───────────────────────┐    ┌──────────────────────────┐
│ 5a. User's Browser    │    │ 5b. Admin's Browser      │
│    Message displayed  │    │     Message displayed    │
└───────────────────────┘    └──────────────────────────┘
```

---

## Common Patterns & Best Practices

### 1. Type-Based Message Routing

```python
async def receive(self, text_data):
    data = json.loads(text_data)
    
    # Route based on message type
    message_type = data.get('type')
    
    if message_type == 'message':
        await self.handle_message(data)
    elif message_type == 'typing':
        await self.handle_typing(data)
    elif message_type == 'read_receipt':
        await self.handle_read_receipt(data)
    else:
        await self.send_error('Unknown message type')
```

---

### 2. Room Switching (Admin Pattern)

```python
async def switch_room(self, new_room):
    """Switch from one room to another"""
    
    # Leave old room
    if self.active_room:
        await self.channel_layer.group_discard(
            self.active_room,
            self.channel_name
        )
    
    # Join new room
    await self.channel_layer.group_add(
        new_room,
        self.channel_name
    )
    
    # Update state
    self.active_room = new_room
```

---

### 3. Sending History on Connect

```python
async def connect(self):
    await self.accept()
    
    # Load and send message history
    messages = await self.get_messages()
    await self.send_json({
        'type': 'history',
        'messages': messages
    })
```

---

### 4. Presence Tracking

```python
async def connect(self):
    await self.accept()
    
    # Notify others that user came online
    await self.channel_layer.group_send(
        "global",
        {
            'type': 'user_online',
            'user': self.email
        }
    )

async def disconnect(self, close_code):
    # Notify others that user went offline
    await self.channel_layer.group_send(
        "global",
        {
            'type': 'user_offline',
            'user': self.email
        }
    )
```

---

### 5. Read Receipts

```python
async def mark_as_read(self, message_ids):
    # Update database
    await self.update_read_status(message_ids)
    
    # Notify sender
    await self.channel_layer.group_send(
        f"user_{sender_email}",
        {
            'type': 'messages_read',
            'message_ids': message_ids,
            'reader': self.email
        }
    )
```

---

### 6. Error Handling

```python
async def receive(self, text_data):
    try:
        data = json.loads(text_data)
    except json.JSONDecodeError:
        await self.send_error('Invalid JSON')
        return
    
    try:
        await self.process_message(data)
    except ValueError as e:
        await self.send_error(str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await self.send_error('Internal server error')

async def send_error(self, message):
    await self.send_json({
        'type': 'error',
        'message': message
    })
```

---

### 7. Rate Limiting

```python
from time import time

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.message_times = []
        await self.accept()
    
    async def receive(self, text_data):
        # Check rate limit
        now = time()
        self.message_times = [t for t in self.message_times if now - t < 60]
        
        if len(self.message_times) >= 10:  # 10 messages per minute
            await self.send_error('Rate limit exceeded')
            return
        
        self.message_times.append(now)
        
        # Process message...
```

---

### 8. Database Query Optimization

```python
@database_sync_to_async
def get_messages(self, email):
    # Use select_related/prefetch_related for efficiency
    return list(
        Message.objects
        .filter(participant_email=email)
        .select_related('sender')  # Avoid N+1 queries
        .order_by('-timestamp')[:50]  # Limit results
    )
```

---

## Interview Questions & Answers

### Q1: What happens when a user sends a message?

**Good Answer:**

"When a user clicks 'Send', JavaScript sends a WebSocket message to the server. Daphne (ASGI server) receives it and routes through the ProtocolTypeRouter to the URLRouter, which matches the URL pattern and calls the appropriate Consumer's `receive()` method.

The consumer saves the message to the database using `@database_sync_to_async`, then broadcasts it to the user's room using `channel_layer.group_send()`. The channel layer delivers this event to all consumer instances in that group - including the user themselves (for echo) and the admin if they're currently viewing that conversation.

Each consumer's `chat_message()` handler then sends the message to their respective browser via WebSocket, where JavaScript updates the UI."

---

### Q2: Explain ASGI vs WSGI

**Good Answer:**

"WSGI is Django's traditional synchronous interface for handling HTTP-only requests. It follows a strict request-response cycle where the connection closes after each response.

ASGI is the asynchronous version that supports persistent connections like WebSockets, HTTP/2, and other protocols. With Django 2.2 and Channels, even though Django itself doesn't natively support ASGI, Channels provides an `AsgiHandler` that bridges ASGI to Django's WSGI views.

The key difference: WSGI can only handle traditional HTTP, while ASGI can handle both HTTP AND WebSocket connections, enabling real-time bidirectional communication."

---

### Q3: How many consumer instances exist?

**Good Answer:**

"The golden rule is: one WebSocket connection equals one consumer instance. If a user opens three browser tabs, that creates three separate WebSocket connections and therefore three separate ChatConsumer instances on the server - even though they're all for the same user.

Each instance is completely isolated with its own state (`self.channel_name`, `self.user_room`, etc.). They communicate via the channel layer, not directly with each other. This is why the channel layer and groups are essential - they provide the pub/sub mechanism for instances to broadcast messages to each other."

---

### Q4: What is a channel layer and why is it needed?

**Good Answer:**

"The channel layer is a message broker that enables communication between different consumer instances. It's needed because each WebSocket connection runs in its own consumer instance, and they need a way to send messages to each other.

For example, when User A sends a message, their consumer instance needs to notify User B's consumer instance. The channel layer provides this through a pub/sub pattern using 'groups'. Consumer A broadcasts to a group, and the channel layer delivers to all consumers in that group.

For development, we use `InMemoryChannelLayer`, but in production you'd use `RedisChannelLayer` because it's persistent, scalable across multiple servers, and survives restarts."

---

### Q5: Explain the group_send() mechanism

**Good Answer:**

"When you call `channel_layer.group_send()`, you specify a group name and an event dictionary with a 'type' field. The channel layer looks up all channel names registered in that group and delivers the event to each one.

The 'type' field is special - it determines which method gets called on the receiving consumer. For example, `type: 'chat_message'` will call the `chat_message()` method. Channels converts dots to underscores, so `type: 'user.online'` calls `user_online()`.

This is a pub/sub pattern: the sender publishes to a topic (group), and all subscribers (consumers in that group) receive it via their handler methods."

---

### Q6: Why is @database_sync_to_async needed?

**Good Answer:**

"Django's ORM is synchronous - it was built before async Python existed. Our consumers are async functions. If you try to call a synchronous function directly from an async function, it will block the entire event loop, preventing other async operations from running.

The `@database_sync_to_async` decorator solves this by running the sync function in a separate thread pool. It returns a coroutine that can be awaited, making it safe to use in async code. The async function pauses while waiting for the database operation, but other async operations can continue running."

---

### Q7: Security implications of URL-based authentication

**Good Answer:**

"In the current implementation, we extract role and email directly from the URL:

```python
self.role = self.scope['url_route']['kwargs']['role']
self.email = self.scope['url_route']['kwargs']['email']
```

This is insecure because anyone can connect to any URL and claim to be anyone. A malicious user could open a WebSocket to `/ws/chat/admin/victim@example.com/` and impersonate that user.

For production, you'd use `AuthMiddlewareStack` to verify the user is actually logged in:

```python
user = self.scope['user']
if not user.is_authenticated:
    await self.close()
    return
self.email = user.email  # Verified from session
```

This way, identity comes from a verified session cookie, not a forgeable URL parameter."

---

### Q8: How does HTTP work without wsgi.py?

**Good Answer:**

"When you only define WebSocket routing in your `ProtocolTypeRouter`, Channels automatically adds HTTP handling. Looking at Channels' source code, the `ProtocolTypeRouter.__init__` method checks if 'http' is in the application mapping, and if not, it automatically adds `AsgiHandler()`.

`AsgiHandler` is a bridge that converts ASGI protocol to WSGI-style Django views. It receives ASGI requests, converts them to WSGI format, passes them through Django's normal URL routing and views, then converts the response back to ASGI format.

This is why you never need `wsgi.py` when using Daphne - the ASGI server handles both HTTP and WebSocket through the same entry point (`asgi.py`)."

---

### Q9: Scalability challenges and solutions

**Good Answer:**

"The main bottlenecks would be:

1. **InMemoryChannelLayer** - Only works on a single server, lost on restart. Solution: Use RedisChannelLayer for persistence and multi-server support.

2. **Database queries** - Loading full message history on every connect. Solution: Implement pagination, only load recent messages, lazy-load older ones.

3. **Single Daphne instance** - Limited concurrent connections. Solution: Run multiple Daphne workers behind a load balancer with sticky sessions or Redis channel layer.

4. **No message queuing** - If Redis goes down, messages are lost. Solution: Add a message queue (Celery + RabbitMQ) for critical operations.

5. **Database writes** - High concurrency could overwhelm the database. Solution: Use connection pooling, read replicas, and consider denormalization for frequently accessed data.

For 10,000 concurrent users, I'd architect it with: multiple Daphne instances, Redis for channel layer, PostgreSQL with connection pooling, and a CDN for static assets."

---

## Summary

### Key Takeaways

1. **WebSockets** enable real-time, bidirectional communication via persistent connections
2. **ASGI** is the async successor to WSGI, supporting both HTTP and WebSocket
3. **Consumers** are like Views for WebSockets, handling connection lifecycle
4. **Channel Layers** provide pub/sub messaging between consumer instances
5. **Groups** enable broadcasting to multiple consumers at once
6. **One WebSocket = One Consumer Instance** - this is the fundamental rule
7. **@database_sync_to_async** bridges Django's sync ORM to async consumers
8. **Daphne** automatically handles HTTP even without explicit configuration

---

### Further Learning

- [Django Channels Documentation](https://channels.readthedocs.io/)
- [WebSocket Protocol Specification](https://datatracker.ietf.org/doc/html/rfc6455)
- [ASGI Specification](https://asgi.readthedocs.io/)
- [Redis Channel Layer](https://github.com/django/channels_redis)

---

**Created:** 2025-11-20  
**Based on:** minicom real-time chat application  
**Topics:** Django Channels, WebSockets, ASGI, Real-time Communication
