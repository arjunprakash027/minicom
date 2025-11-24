# Minicom Chat Application - Interview Questions

This document contains comprehensive interview questions covering all aspects of your chat application implementation. Questions range from easy to SWE-2 level difficulty.

---

## Table of Contents
1. [WebSockets & Real-Time Communication](#websockets--real-time-communication)
2. [Django Channels Architecture](#django-channels-architecture)
3. [Database & Data Modeling](#database--data-modeling)
4. [Authentication & Security](#authentication--security)
5. [AI Integration](#ai-integration)
6. [Scalability & Performance](#scalability--performance)
7. [Frontend Architecture](#frontend-architecture)
8. [System Design](#system-design)
9. [Debugging & Troubleshooting](#debugging--troubleshooting)
10. [Production Readiness](#production-readiness)

---

## WebSockets & Real-Time Communication

### Easy

**Q1: What is a WebSocket and how does it differ from HTTP?**
- Expected: Explain persistent bidirectional connection vs request-response
- Your context: You use WebSocket for chat at `ws://localhost:8000/ws/chat/...`
- Follow-up: Why did you choose WebSocket over HTTP polling?

**Q2: Walk me through what happens when a user sends a message in your application.**
- Expected: Trace flow from frontend socket.send() to backend consumer to broadcast
- Your context: `foo-website/chat.html` → `ChatConsumer.receive()` → `group_send()` → `chat_message()` handler
- Key file: `minicom/consumers.py:receive()`

**Q3: What are the different message types your WebSocket protocol supports?**
- Expected: List `message`, `get_conversation`, `read_messages`
- Your context: Explain purpose of each type
- Follow-up: Why use a type field instead of separate WebSocket endpoints?

**Q4: How do you establish a WebSocket connection in your frontend?**
- Expected: `new WebSocket('ws://...')`, explain URL parameters
- Your context: `ws/chat/{role}/{email}/` pattern
- Follow-up: What happens if the connection fails?

### Medium

**Q5: Explain how your read receipts feature works end-to-end.**
- Expected: Describe `is_read` field, `mark_messages_read()` function, broadcast mechanism
- Your context: User sends `read_messages` → Update DB → `group_send('messages_read')` → Update UI ticks
- Key files: `consumers.py:mark_messages_read()`, both frontend files

**Q6: What happens if a user opens your chat in multiple browser tabs?**
- Expected: Multiple WebSocket connections, both join same group, both receive messages
- Your context: `channel_layer.group_add()` adds multiple channel_names to same room
- Follow-up: How does this affect read receipts? (Both tabs can mark read independently)

**Q7: How does your admin switch between different user conversations?**
- Expected: Explain `get_conversation` message type, group_discard/group_add pattern
- Your context: Admin sends `{type: 'get_conversation', email: 'user@example.com'}` → Consumer leaves old room, joins new room
- Key code: `consumers.py:receive()` get_conversation handler

**Q8: What is the Channel Layer and why is it necessary?**
- Expected: Abstraction for message passing between consumer instances
- Your context: `InMemoryChannelLayer` in settings, enables `group_send()` to broadcast
- Follow-up: What are the limitations of InMemoryChannelLayer?

### Hard

**Q9: Your application uses group_send() for broadcasting. Explain how this works internally and what happens if one of the consumers in the group is slow to process messages.**
- Expected: Discuss async nature, channel layer queues, potential backpressure
- Your context: Multiple consumers listening to `user_{email}` group
- Deep dive: What if admin's consumer is processing slowly? Does it block user's message?

**Q10: You sanitize emails when creating room names (@ to -at-). Why is this necessary and what would break if you didn't do it?**
- Expected: Channel layer backends have restrictions on group names, Redis doesn't allow special chars
- Your context: `sanitize_email()` function in `consumers.py`
- Follow-up: What other characters might cause issues? How would you handle Unicode emails?

**Q11: Explain the lifecycle of a WebSocket consumer in your application from connection to disconnection.**
- Expected: `connect()` → `accept()` → `receive()` loop → `disconnect()`, group membership management
- Your context: Walk through `ChatConsumer` class methods
- Follow-up: What happens to messages sent to a group after a consumer disconnects but before group_discard completes?

**Q12: If two users send messages at exactly the same time, how does your system ensure message ordering?**
- Expected: Discuss timestamp ordering, database auto_now_add, potential race conditions
- Your context: `Message.timestamp` with `ordering = ['timestamp']`
- Deep dive: What if two messages have identical timestamps down to the microsecond?

---

## Django Channels Architecture

### Easy

**Q13: What is ASGI and how does it differ from WSGI?**
- Expected: Async Server Gateway Interface vs Web Server Gateway Interface
- Your context: You use Daphne ASGI server, `asgi.py` defines application
- Follow-up: Can you run Django views under ASGI?

**Q14: What is the purpose of the ProtocolTypeRouter in your asgi.py?**
- Expected: Routes connections based on protocol (websocket, http, etc.)
- Your context: `ProtocolTypeRouter({"websocket": URLRouter(...)})`
- Follow-up: Where does HTTP routing happen? (Channels adds it automatically)

**Q15: What does @database_sync_to_async do and why do you need it?**
- Expected: Bridges sync Django ORM to async consumer
- Your context: Used in `save_message()`, `get_messages()`, etc.
- Follow-up: What happens if you call ORM directly without this decorator?

### Medium

**Q16: Your ChatConsumer inherits from AsyncWebsocketConsumer. What would be different if you used WebsocketConsumer instead?**
- Expected: Sync vs async, performance implications, blocking operations
- Your context: You use async because of await channel_layer operations
- Follow-up: When would you choose sync over async?

**Q17: Explain how Django Channels routes WebSocket connections to your consumer.**
- Expected: URL routing in `routing.py`, regex pattern matching, kwargs extraction
- Your context: `r"ws/chat/(?P<role>\w+)/(?P<email>[^/]+)/$"`
- Follow-up: Why use regex path instead of path()?

**Q18: How does your application serve both HTTP requests (REST API) and WebSocket connections?**
- Expected: ASGI handles both, ProtocolTypeRouter separates, AsgiHandler for HTTP
- Your context: `/api/users/` via Django views, `/ws/chat/` via consumers
- Follow-up: Do they share the same process? What about concurrency?

**Q19: You use channel_layer.group_send() with type='chat_message'. How does this get routed to the chat_message() method?**
- Expected: Channels converts dots to underscores, calls method with that name
- Your context: `type: 'chat_message'` → `await self.chat_message(event)`
- Follow-up: What if you had a method called `chat.message()` with a dot?

### Hard

**Q20: Your AI reply function is marked async but actually calls a synchronous LLM. What are the implications of this?**
- Expected: Blocks event loop, prevents other consumers from processing
- Your context: `await reply(text)` but `llm.create_chat_completion()` is sync
- Solution: Wrap in `@database_sync_to_async` or use `asyncio.to_thread()`
- Deep dive: How many concurrent users can this support?

**Q21: Explain the difference between self.send() and self.channel_layer.group_send() in your consumer.**
- Expected: Direct send to one WebSocket vs broadcast to group
- Your context: Use send() for loading history, group_send() for new messages
- Follow-up: When would you use channel_layer.send() to a specific channel_name?

**Q22: Your InMemoryChannelLayer stores messages in memory. What happens during a deployment when you restart the server?**
- Expected: All messages in channel layer queues are lost
- Your context: InMemoryChannelLayer doesn't persist
- Deep dive: How would Redis channel layer behave differently? What about message durability guarantees?

**Q23: You store role and email in self.scope from URL parameters. How would you implement proper authentication using Django's session system?**
- Expected: Use AuthMiddlewareStack, access self.scope['user'], verify permissions
- Your context: Current implementation trusts client-provided role
- Implementation: Show how to wrap routing in AuthMiddlewareStack and check user.is_authenticated

---

## Database & Data Modeling

### Easy

**Q24: Walk through your Message model schema.**
- Expected: Explain all fields, their types, and purposes
- Your context: `participant_email`, `sender_type`, `content`, `timestamp`, `is_read`
- Follow-up: Why did you index `participant_email`?

**Q25: What are the possible values for sender_type and what does each represent?**
- Expected: 'user', 'admin', 'ai' and their purposes
- Your context: User messages, admin replies, AI-generated responses
- Follow-up: How did you add 'ai' after initially having only user/admin? (Migration 0003)

**Q26: How do you ensure messages are returned in chronological order?**
- Expected: Meta class with `ordering = ['timestamp']`
- Your context: `models.py:Message.Meta`
- Follow-up: What's the query performance impact of this?

### Medium

**Q27: Your participant_email field is just a CharField, not a ForeignKey. What are the pros and cons of this approach?**
- Expected: Flexibility vs referential integrity, no User model dependency
- Your context: No User model exists, using email as identifier
- Trade-offs: Can't cascade delete, can't join for user info, allows flexibility

**Q28: How do you retrieve all messages for a specific user? Walk through the query.**
- Expected: `Message.objects.filter(participant_email=email).order_by('timestamp')`
- Your context: `get_messages()` function in consumers.py
- Follow-up: How would this query perform with 1 million messages? What indexes help?

**Q29: Explain your database migrations history. What changes did you make and why?**
- Expected: 0001 creates initial table, 0002 adds is_read, 0003 adds 'ai' sender_type
- Your context: `migrations/` folder
- Follow-up: What would happen if you deployed 0003 before adding the AI code?

**Q30: How does your check_admin_replied() function work and what's its performance impact?**
- Expected: Queries all messages for user, checks if any are from admin
- Your context: `Message.objects.filter(participant_email=email, sender_type='admin').exists()`
- Problem: Runs on every user message, full table scan without proper index

### Hard

**Q31: Your application loads ALL message history on WebSocket connect. How would you implement pagination for users with thousands of messages?**
- Expected: Limit query, load recent N messages, implement "load more" button
- Your context: `get_messages()` returns all messages
- Implementation: Add offset/limit parameters, frontend infinite scroll
- Deep dive: How do you ensure new messages appear correctly with pagination?

**Q32: You use SQLite in development. What problems would you encounter in production with concurrent WebSocket connections?**
- Expected: Write locks, database is locked errors, poor concurrent performance
- Your context: Multiple consumers writing messages simultaneously
- Solution: PostgreSQL with connection pooling
- Deep dive: How does SQLite's locking work differently from PostgreSQL's MVCC?

**Q33: Design a database schema to support group chats (multiple participants per conversation) instead of just 1-on-1.**
- Expected: Create Conversation model, make Message.participant a ManyToMany or ForeignKey to Conversation
- Your context: Current model assumes 1 user + admin per conversation
- Design considerations: How do read receipts work? How does admin dashboard change?

**Q34: How would you optimize the query that lists all users in the admin dashboard when you have 100,000 users?**
- Expected: Current query `Message.objects.values_list('participant_email', flat=True).distinct()`
- Your context: `api.py:list_users()`
- Optimizations: Pagination, caching, separate User table with last_message_at, search functionality
- Deep dive: How would you implement real-time updates when new users message?

---

## Authentication & Security

### Easy

**Q35: How does a user authenticate in your current implementation?**
- Expected: Enters email in login page, stored in sessionStorage
- Your context: `foo-website/login.html`
- Follow-up: What are the security issues with this approach?

**Q36: How does admin authentication work?**
- Expected: Hardcoded check for 'admin@minicom.com'
- Your context: `bar-website/login.html`
- Follow-up: How would you implement this properly?

**Q37: Where is the user's email stored on the client side and how is it used?**
- Expected: sessionStorage, passed in WebSocket URL
- Your context: `sessionStorage.getItem('email')` used in WebSocket connection
- Follow-up: Can a user modify this? What happens if they do?

### Medium

**Q38: List all the security vulnerabilities in your current implementation.**
- Expected: No authentication, CSRF disabled, DEBUG=True, exposed SECRET_KEY, CORS allows all
- Your context: Multiple issues in `settings.py` and consumer design
- Follow-up: Prioritize these by severity

**Q39: Your CSRF protection is disabled with a comment "FIXME: Disabled for widget API calls". Why is this dangerous and how would you fix it?**
- Expected: CSRF attacks allow malicious sites to make requests on behalf of users
- Your context: `settings.py:CSRF_COOKIE_SECURE = False` commented
- Solution: Use CSRF tokens or SameSite cookies, implement proper CORS

**Q40: How could an attacker impersonate another user in your current system?**
- Expected: Change email in sessionStorage, change email in WebSocket URL
- Your context: No server-side verification of identity
- Demonstration: Show exact steps to access someone else's messages

**Q41: You allow any origin to connect via CORS. What attacks does this enable?**
- Expected: Any website can call your API, steal data, make requests
- Your context: `CORS_ORIGIN_ALLOW_ALL = True`
- Follow-up: What origins should you allow for an embedded chat widget?

### Hard

**Q42: Design a proper authentication system for this chat application using Django's built-in authentication.**
- Expected: Create User model, use Django sessions, implement AuthMiddlewareStack
- Implementation: Show login view, session cookies, consumer authentication
- Your context: Replace URL-based email with session-based user
- Deep dive: How do you handle WebSocket authentication when cookies are involved?

**Q43: How would you implement rate limiting to prevent spam in your chat application?**
- Expected: Track messages per user per time window, reject excess
- Implementation: Redis counter, decorator on receive(), return error to client
- Your context: Currently no rate limiting
- Deep dive: Where do you implement this - consumer, middleware, or separate service?

**Q44: Your application stores messages in plaintext. How would you implement end-to-end encryption?**
- Expected: Client-side encryption, server stores encrypted blobs, key management
- Challenges: AI can't read messages, admin can't read messages, key exchange
- Your context: Currently `content` field is plaintext
- Deep dive: How does this affect search? Read receipts? AI responses?

**Q45: An attacker could inject malicious JavaScript in a message. How would you prevent XSS attacks?**
- Expected: Sanitize input on server, escape output on client, CSP headers
- Your context: Currently no input sanitization
- Frontend: Using `textContent` vs `innerHTML` in your code
- Follow-up: What about markdown or HTML formatting in messages?

---

## AI Integration

### Easy

**Q46: What AI model are you using and how is it loaded?**
- Expected: Gemma-3-270M quantized model via llama-cpp-python
- Your context: `ai.py` loads from `./model_cache/gemma-3-270m-it-UD-Q2_K_XL.gguf`
- Follow-up: What does Q2_K_XL quantization mean?

**Q47: When does the AI automatically respond to a user message?**
- Expected: When user sends message AND no admin has replied yet
- Your context: `check_admin_replied()` in `consumers.py`
- Follow-up: What happens if admin joins after AI has been responding?

**Q48: What is the system prompt you're using for the AI?**
- Expected: "You are a customer service assistant..."
- Your context: `ai.py:reply()` function
- Follow-up: How would you customize this per organization?

### Medium

**Q49: Walk through the complete flow when a user message triggers an AI response.**
- Expected: User sends → save to DB → check admin replied → call AI → save AI message → broadcast
- Your context: Trace through `consumers.py:receive()` for user messages
- Follow-up: What happens if the AI takes 30 seconds to respond?

**Q50: Your AI reply function is called with 'await' but the actual LLM call is synchronous. What problems does this cause?**
- Expected: Blocks event loop, all other consumers wait, poor concurrency
- Your context: `await reply(text)` but `llm.create_chat_completion()` is blocking
- Solution: Use `asyncio.to_thread()` or `@database_sync_to_async`

**Q51: The AI only sees the current message, not conversation history. How would you provide conversation context?**
- Expected: Load recent messages, build message array with roles
- Implementation: Modify `reply()` to accept message list instead of single message
- Your context: Currently just `[{"role": "user", "content": message}]`
- Challenge: How many previous messages? How to handle token limits?

**Q52: What happens if the AI model crashes or runs out of memory?**
- Expected: Currently no error handling, consumer crashes, user never gets response
- Your context: No try-except in `ai.py`
- Solution: Wrap in try-except, provide fallback response, log error

### Hard

**Q53: With your current AI implementation, how many concurrent users can your system handle before performance degrades?**
- Expected: Very few (maybe 5-10) because LLM blocks event loop
- Your context: Single-threaded CPU inference, no queuing
- Deep dive: Calculate based on 10-second inference time
- Solution: Separate AI service, queue-based system, multiple workers

**Q54: Design an architecture to scale AI responses to 1000 concurrent conversations.**
- Expected: Separate AI service, message queue (RabbitMQ/Redis), worker pool
- Architecture: Consumer → Queue → Workers → Response Queue → Consumer
- Your context: Current in-process LLM doesn't scale
- Deep dive: How do you handle worker failures? How do you prioritize requests?

**Q55: How would you implement a feature where users can choose between different AI personalities (friendly, professional, technical)?**
- Expected: Store personality preference per user, load different system prompts
- Implementation: Add field to user settings, lookup table for prompts
- Your context: Currently hardcoded system prompt
- Challenge: How do you A/B test personalities? How do you measure quality?

**Q56: Your AI is always on. How would you implement a hybrid system where AI handles initial messages but escalates to human agents for complex issues?**
- Expected: Intent classification, confidence scoring, automatic escalation
- Implementation: AI predicts if it can handle query, notifies admin if not
- Your context: Currently AI responds until admin replies
- Design: How does UI change? How do you notify admin of escalation?

---

## Scalability & Performance

### Easy

**Q57: What would be the first bottleneck if you had 10,000 concurrent users?**
- Expected: InMemoryChannelLayer or single Daphne instance
- Your context: Current setup is single-machine development
- Follow-up: How would you identify this bottleneck in production?

**Q58: Why is SQLite not suitable for production use in your application?**
- Expected: Write locks, poor concurrent access, single file
- Your context: Multiple consumers writing simultaneously
- Follow-up: What database would you use instead?

**Q59: Your start script runs everything on one machine. How would you deploy this to handle more load?**
- Expected: Separate services, load balancer, multiple Daphne instances, Redis
- Your context: `start` script runs foo-website, bar-website, and daphne together
- Follow-up: What components can be scaled horizontally?

### Medium

**Q60: Your application loads all message history on WebSocket connect. What's the performance impact at scale?**
- Expected: Large payload, slow connection, memory usage, database load
- Your context: `get_messages()` loads everything
- Optimization: Pagination, load recent N messages, lazy loading

**Q61: Explain how you would horizontally scale your WebSocket servers.**
- Expected: Multiple Daphne instances, Redis channel layer, load balancer with sticky sessions
- Your context: Currently single Daphne instance
- Challenge: How does group_send() work across multiple servers?

**Q62: What caching strategies would you implement to improve performance?**
- Expected: Cache message history, user lists, read receipts status
- Implementation: Redis cache, cache invalidation on new messages
- Your context: Currently no caching, all DB queries
- Trade-offs: Consistency vs speed

**Q63: Your check_admin_replied() function runs a database query on every user message. How would you optimize this?**
- Expected: Cache result, add database flag, denormalize data
- Your context: `Message.objects.filter(..., sender_type='admin').exists()`
- Implementation: Add `admin_replied` boolean to conversation/user model

### Hard

**Q64: Design a complete scalable architecture for this chat application to handle 100,000 concurrent connections.**
- Expected: 
  - Load balancer (ALB/nginx) with sticky sessions
  - Multiple Daphne instances (20-50)
  - Redis channel layer (clustered)
  - PostgreSQL (with read replicas)
  - Separate AI service cluster
  - Message queue for AI (RabbitMQ/Kafka)
  - CDN for static assets
  - Monitoring (Prometheus/Grafana)
- Your context: Current single-machine setup
- Deep dive: How do you handle failover? Database backups? Monitoring?

**Q65: Calculate the infrastructure costs and requirements for 100,000 concurrent WebSocket connections.**
- Expected: 
  - Estimate: ~2,000-5,000 connections per Daphne instance = 20-50 instances
  - Memory: Each connection ~10KB = 1GB for 100K connections
  - Database: Messages per day, storage growth
  - AI: GPU costs if using AI
  - Network: WebSocket bandwidth
- Deep dive: Where do costs grow most? What's most expensive?

**Q66: Your read receipts require updating messages in the database and broadcasting to all connected clients. How would you optimize this for millions of messages?**
- Expected:
  - Batch updates instead of individual
  - Update only unread messages (indexed)
  - Use database triggers or pub/sub
  - Cache read status in Redis
  - Denormalize into separate table
- Your context: `mark_messages_read()` does bulk update then broadcasts
- Trade-off: Eventually consistent vs strongly consistent read receipts

**Q67: Explain how you would implement read-after-write consistency in a distributed deployment with multiple database replicas.**
- Expected:
  - Write to primary, read from primary for user's own messages
  - Use session routing to same replica
  - Implement read-your-writes guarantee
  - Accept eventual consistency for other users' messages
- Your context: Currently single database, no replicas
- Challenge: WebSocket might be on different server than HTTP request

---

## Frontend Architecture

### Easy

**Q68: Why did you choose vanilla JavaScript instead of a framework like React?**
- Expected: Simplicity, no build step, lightweight, widget requirements
- Your context: Pure HTML/CSS/JS in foo-website and bar-website
- Follow-up: At what scale would you introduce a framework?

**Q69: How does the admin dashboard load the list of users?**
- Expected: fetch() call to /api/users/ REST endpoint
- Your context: `bar-website/index.html` buildUserList()
- Follow-up: How often does this refresh? What if new user messages?

**Q70: Explain how the floating chat widget works on the user side.**
- Expected: Fixed position bubble, click expands window, toggle visibility
- Your context: `foo-website/chat.html` CSS and JavaScript
- Follow-up: How would you embed this on any website?

### Medium

**Q71: Your frontend stores the user's email in sessionStorage. What are the limitations of this approach?**
- Expected: Lost on browser close, not shared across tabs, can be tampered with
- Your context: Login stores, chat.html reads
- Alternative: Cookies, localStorage, secure httpOnly cookies

**Q72: How would you handle WebSocket reconnection if the connection drops?**
- Expected: Detect onclose, exponential backoff retry, queue pending messages
- Your context: Currently just logs "WS closed", no reconnection
- Implementation: Show retry logic, message queue, connection status UI

**Q73: What happens if a user sends a message while disconnected?**
- Expected: Currently fails silently or throws error
- Your context: No offline handling
- Solution: Detect readyState, queue messages, show connection status, retry on reconnect

**Q74: Your admin dashboard loads conversations on demand. How would you implement real-time notifications when a new user messages?**
- Expected: Listen for messages on global admin channel, show badge count, highlight user
- Your context: Currently admin must click user to see new messages
- Implementation: Separate notification group, count unread, desktop notifications

### Hard

**Q75: Design a component architecture to make your frontend more maintainable at scale.**
- Expected: Break into components (ChatWindow, MessageList, MessageInput, UserList)
- Architecture: Component pattern in vanilla JS or introduce framework
- Your context: Currently all code in single HTML file
- Deep dive: State management? Event bus? Component communication?

**Q76: Implement offline support: users can read message history and compose messages while offline, which send when reconnected.**
- Expected:
  - Cache messages in IndexedDB
  - Queue outgoing messages
  - Service worker for offline capability
  - Sync API or custom sync on reconnect
- Your context: Currently requires connection for everything
- Challenge: How do you handle conflicts? Message ordering?

**Q77: How would you implement optimistic UI updates for sending messages?**
- Expected: 
  - Immediately show message with "sending" state
  - Update to "sent" on server confirmation
  - Handle failures (show error, allow retry)
- Your context: Currently waits for server response
- Implementation: Temporary message ID, replace on server response

**Q78: Your admin dashboard lists all users in a sidebar. How would you implement this for 10,000+ users?**
- Expected:
  - Virtual scrolling for performance
  - Search/filter functionality
  - Pagination or infinite scroll
  - Load only active/recent users
  - Separate "all users" view
- Your context: Currently loads all in simple list
- UX: How do you help admin find users quickly? Priority inbox?

---

## System Design

### Easy

**Q79: Draw the architecture diagram of your current system.**
- Expected: Browser → WebSocket → Daphne → ChatConsumer → Database
- Components: foo-website, bar-website, Django, SQLite, LLM
- Your context: All on localhost, simple architecture

**Q80: Explain the data flow when an admin sends a message to a user.**
- Expected: Admin frontend → WebSocket → Consumer → Save DB → group_send → User receives
- Your context: Trace through code in `consumers.py`

**Q81: What are the different types of clients in your system and how do they differ?**
- Expected: User client (foo-website) and admin client (bar-website)
- Differences: Role, permissions, UI, features
- Your context: Same backend, different frontends

### Medium

**Q82: Your system has both REST API (/api/users/) and WebSocket. When would you use each?**
- Expected: REST for one-time queries, WebSocket for real-time bidirectional
- Your context: REST for loading user list, WebSocket for messaging
- Follow-up: Could you implement everything over WebSocket? Should you?

**Q83: Design a notification system to alert admins when a user sends their first message.**
- Expected: 
  - Check if user exists in conversations
  - Send notification to admin channel
  - Show badge/alert in admin UI
  - Optional: Email/SMS notification
- Your context: Currently admin must check user list
- Implementation: Where does this logic go? How do you avoid duplicate notifications?

**Q84: How would you implement message search functionality?**
- Expected:
  - Full-text search in database (PostgreSQL tsvector)
  - Elasticsearch for advanced search
  - Search endpoint, search UI
  - Highlight matches
- Your context: Currently no search
- Challenge: How do you search across all conversations as admin? Privacy concerns?

**Q85: Design a system to track and display when a user is typing.**
- Expected:
  - Send typing events via WebSocket
  - Debounce on client side
  - Temporary state (don't save to DB)
  - Show/hide typing indicator
  - Timeout after 5 seconds
- Implementation: New message type, ephemeral state, UI component

### Hard

**Q86: Design a complete customer support platform built on your chat application with ticketing, assignment, and SLA tracking.**
- Expected:
  - Ticket model (status, priority, assigned_to)
  - Conversation to ticket linking
  - Assignment logic (round-robin, skill-based)
  - SLA calculations (response time, resolution time)
  - Escalation rules
  - Metrics dashboard
- Your context: Current system is basic chat
- Architecture: How does this integrate? New services? Same database?

**Q87: How would you implement a chat widget that can be embedded on any third-party website?**
- Expected:
  - JavaScript snippet to include
  - iframe for isolation
  - PostMessage API for cross-origin
  - CORS configuration
  - Authentication/identity management
  - Customization options (colors, position)
- Your context: Currently standalone HTML pages
- Security: How do you prevent abuse? Rate limiting per domain?

**Q88: Design a system to support multiple organizations with isolated data.**
- Expected:
  - Organization/tenant model
  - Tenant isolation (schema, database, or row-level)
  - Subdomain routing
  - Separate channel layer groups per org
  - Admin can only see their org's users
- Your context: Currently single-tenant
- Deep dive: How do you handle shared vs dedicated infrastructure?

**Q89: Implement a queue system where customers wait for an available agent instead of all conversations going to one admin.**
- Expected:
  - Queue model (position, wait time)
  - Agent availability status
  - Assignment algorithm
  - Queue position updates
  - Estimated wait time
  - Transfer between agents
- Architecture: Where does queue logic live? How do you route conversations?
- Real-time: How do you update queue position?

---

## Debugging & Troubleshooting

### Easy

**Q90: A user reports they sent a message but the admin never received it. How do you debug this?**
- Expected: Check database, check WebSocket connection, check group membership
- Your context: Look at Message table, check if admin joined room
- Tools: Database query, browser DevTools, server logs

**Q91: How would you check if a WebSocket connection is active?**
- Expected: Browser DevTools Network tab, check readyState, ping/pong
- Your context: socket.readyState === WebSocket.OPEN
- Follow-up: How do you detect half-open connections?

**Q92: What logging would you add to help debug issues in production?**
- Expected: Connection events, message sends, errors, performance metrics
- Your context: Currently only print() statements
- Tools: Python logging module, structured logging, log aggregation

### Medium

**Q93: Users report messages are appearing out of order. How do you investigate and fix this?**
- Expected:
  - Check timestamp accuracy
  - Check database ordering
  - Check frontend sorting
  - Investigate race conditions
- Your context: Should be ordered by timestamp
- Root cause: Possible network delays, clock skew, concurrent inserts

**Q94: The AI stops responding after a few hours. How do you debug this?**
- Expected:
  - Check process status
  - Check memory usage (model might OOM)
  - Check error logs
  - Check if model file is corrupted
  - Check for hung threads
- Your context: LLM loaded in-process
- Tools: htop, memory profiling, exception logs

**Q95: An admin reports they can see messages from users they didn't select. How is this possible?**
- Expected:
  - Group membership not cleaned up
  - Multiple rooms joined simultaneously
  - Broadcast to wrong group
- Your context: Check group_discard in get_conversation
- Bug: Forgot to leave old room before joining new one

**Q96: Messages are being saved to the database but not appearing in the UI. What could be wrong?**
- Expected:
  - group_send() failing silently
  - Frontend not listening to correct message type
  - Channel layer issue
  - Consumer not in group
- Your context: Trace broadcast flow
- Debug: Check channel layer, check frontend onmessage handler

### Hard

**Q97: In production, some WebSocket connections close after exactly 60 seconds. What's happening and how do you fix it?**
- Expected:
  - Load balancer timeout (AWS ALB default 60s)
  - Proxy timeout
  - Solution: Implement ping/pong keepalive
- Implementation: Send ping every 30s, pong response, detect dead connections
- Your context: No keepalive mechanism currently

**Q98: You're seeing "Database is locked" errors in production. Explain the root cause and your solution.**
- Expected:
  - SQLite write locking with concurrent access
  - Multiple consumers trying to write simultaneously
  - Solution: Migrate to PostgreSQL
  - Temporary: Use connection pooling, retry logic, reduce write frequency
- Your context: SQLite in development

**Q99: Memory usage grows continuously and never decreases. How do you identify and fix the memory leak?**
- Expected:
  - Profile with memory_profiler or objgraph
  - Check for circular references
  - Check consumer cleanup in disconnect
  - Check channel layer subscriptions
  - Check LLM model keeping contexts
- Your context: Possible leaks in consumer instances, AI model caching
- Tools: Python memory profiling, heap snapshots

**Q100: You have 1000 connected users but messages are taking 30+ seconds to arrive. How do you diagnose and fix this?**
- Expected:
  - Check event loop blocking
  - Profile async tasks
  - Identify slow database queries
  - Check AI blocking event loop
  - Monitor channel layer latency
- Your context: Likely AI inference blocking
- Solution: Move AI to separate service, add monitoring, profile with asyncio debug mode
- Tools: APM tools, custom metrics, profiling

---

## Production Readiness

### Easy

**Q101: List 5 things you would need to change before deploying this to production.**
- Expected:
  - Replace InMemoryChannelLayer with Redis
  - Implement proper authentication
  - Use PostgreSQL instead of SQLite
  - Enable HTTPS
  - Fix security settings (DEBUG, SECRET_KEY, CSRF)
- Your context: Multiple issues in settings.py

**Q102: How would you monitor the health of your chat application?**
- Expected: WebSocket connection count, message latency, database performance, error rates
- Tools: Prometheus, Grafana, CloudWatch, Datadog
- Your context: No monitoring currently

**Q103: What environment variables would you use instead of hardcoded settings?**
- Expected: SECRET_KEY, DATABASE_URL, REDIS_URL, DEBUG, ALLOWED_HOSTS
- Your context: Currently all in settings.py
- Tool: python-decouple, django-environ

### Medium

**Q104: How would you implement proper logging for debugging production issues?**
- Expected:
  - Python logging module
  - Log levels (DEBUG, INFO, WARNING, ERROR)
  - Structured logging (JSON)
  - Centralized logging (ELK, CloudWatch)
  - Request IDs for tracing
- Your context: Currently print() statements
- Implementation: Show logging configuration

**Q105: Design a deployment pipeline for this application.**
- Expected:
  - Git workflow (develop, staging, main branches)
  - CI: Run tests, linters
  - Build Docker images
  - CD: Deploy to staging, run integration tests, deploy to prod
  - Blue-green or rolling deployment
- Tools: GitHub Actions, Jenkins, CircleCI
- Your context: Manual start script currently

**Q106: How would you implement database migrations in a zero-downtime deployment?**
- Expected:
  - Backward-compatible migrations
  - Deploy code first, migrate later (or vice versa)
  - Online migrations for large tables
  - Rollback strategy
- Your context: Django migrations exist
- Challenge: Adding non-nullable column, renaming fields

**Q107: What metrics would you track to understand application health and user behavior?**
- Expected:
  - Technical: Response time, error rate, connection count, database queries
  - Business: Messages per day, active users, AI usage rate, admin response time
- Tools: Custom metrics, analytics platform
- Your context: No metrics currently

### Hard

**Q108: Design a complete disaster recovery plan for your chat application.**
- Expected:
  - Database backups (point-in-time recovery)
  - Redis persistence for channel layer
  - Multi-region deployment
  - Failover procedures
  - RPO/RTO targets
  - Testing DR plan regularly
- Your context: Single machine, no backups
- Scenario: Database corruption, entire region failure, accidental deletion

**Q109: How would you implement feature flags to gradually roll out new features?**
- Expected:
  - Feature flag service (LaunchDarkly, custom)
  - Percentage rollouts
  - User targeting
  - Kill switch for emergencies
  - A/B testing capabilities
- Implementation: Where do flags go? Consumer, middleware, frontend?
- Example: Rolling out AI to 10% of users

**Q110: Design an auto-scaling strategy for your WebSocket servers.**
- Expected:
  - Metrics: CPU, memory, connection count per instance
  - Scale up trigger: >80% capacity
  - Scale down: <40% capacity with min instances
  - Graceful shutdown (drain connections)
  - Connection migration or accept brief disconnects
- Challenge: WebSocket connections are stateful
- Your context: Currently fixed capacity

**Q111: Implement a blue-green deployment strategy for your application with zero downtime.**
- Expected:
  - Run old and new versions simultaneously
  - Shift load balancer gradually
  - Keep old version running until all WebSockets drain
  - Rollback strategy
  - Database migration compatibility
- Challenge: WebSocket connections to old version during deploy
- Implementation: How long do you keep old version? How do you drain?

---

## Bonus: Advanced Topics

### Q112: How would you implement message encryption at rest?
- Expected: Encrypt content field before saving, decrypt on read, key management (KMS)
- Challenge: Search, AI processing, admin viewing

### Q113: Design a system to handle file attachments (images, documents) in chat.
- Expected: S3 storage, upload presigned URLs, thumbnail generation, virus scanning
- Your context: Currently text-only

### Q114: How would you implement message delivery guarantees (at-least-once, exactly-once)?
- Expected: Message IDs, deduplication, acknowledgments, persistence
- Your context: Currently at-most-once with no guarantees

### Q115: Implement a ban/block system for abusive users.
- Expected: Blocked users table, check on message send, admin UI, ban duration
- Challenge: Existing connections, ban evasion

### Q116: How would you support multiple languages/internationalization?
- Expected: Django i18n, frontend translations, user language preference, AI multilingual
- Your context: Currently English only

### Q117: Design a system to export conversation transcripts.
- Expected: Export formats (PDF, CSV, JSON), privacy concerns, bulk export, scheduled exports
- Implementation: Background job, file generation, download UI

### Q118: Implement message reactions (emoji reactions like 👍).
- Expected: Reaction model, WebSocket events, UI updates, notification behavior
- Database: Reaction table with message_id, user, emoji

### Q119: How would you handle timezone differences for message timestamps?
- Expected: Store UTC, display in user's timezone, relative times ("2 hours ago")
- Your context: Currently using server timezone

### Q120: Design a system to automatically detect and flag inappropriate content.
- Expected: ML moderation API (OpenAI Moderation), keyword filtering, admin review queue
- Implementation: On message receive, check content, flag/block, notify admin

---

## Question Difficulty Summary

- **Easy (35 questions):** Basic understanding of implementation, direct code questions
- **Medium (50 questions):** Design decisions, trade-offs, optimization opportunities
- **Hard (35 questions):** System design, scalability, complex problem-solving

## How to Prepare

1. **Understand every file:** Read through all code, understand purpose of each function
2. **Trace data flows:** Follow message from user click to database to other user's screen
3. **Know your trade-offs:** Why did you choose this approach? What are alternatives?
4. **Identify problems:** List all issues in current implementation
5. **Design improvements:** How would you fix issues and scale up?
6. **Practice explaining:** Talk through your code out loud
7. **Draw diagrams:** Architecture, data flow, deployment diagrams
8. **Know your stack:** Deep dive into Django Channels, WebSockets, ASGI
9. **Prepare stories:** "I implemented X by doing Y because Z"
10. **Be honest:** If you don't know, say so and explain how you'd find out

## Key Files to Review Before Interview

1. `minicom/consumers.py` - Core WebSocket logic
2. `minicom/models.py` - Database schema
3. `minicom/ai.py` - AI integration
4. `minicom/settings.py` - Configuration
5. `bar-website/index.html` - Admin UI and logic
6. `foo-website/chat.html` - User chat widget

## Recommended Topics to Study

- Django Channels documentation
- WebSocket protocol (RFC 6455)
- ASGI specification
- Redis pub/sub
- Database indexing and query optimization
- System design patterns for chat applications
- Async/await in Python
- Authentication & security best practices
- Scalability patterns
- Production deployment strategies

---

Good luck with your Intercom interview! 🚀
