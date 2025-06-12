"""
Tis Redis Chat Storage - Simple & Clean

A minimalist Redis chat storage inspired by Langflow's Message Store.
Less code, more functionality.

Author: Tis Custom Components
Version: 3.0.0 - Simplified
"""

from urllib import parse
from langchain_community.chat_message_histories.redis import RedisChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langflow.custom import Component
from langflow.inputs import HandleInput, MessageTextInput, SecretStrInput, StrInput, IntInput
from langflow.schema.message import Message
from langflow.template import Output
from langflow.utils.constants import MESSAGE_SENDER_AI, MESSAGE_SENDER_NAME_AI, MESSAGE_SENDER_USER, MESSAGE_SENDER_NAME_USER
from loguru import logger

class TisRedisChatStorageComponent(Component):
    """
    Simple Redis Chat Storage - Like Message Store but for Redis

    Usage:
    1. Store user message: Connect Chat Input → user_message
    2. Store AI message: Connect Chat Output → ai_message
    3. Get history: Use messages output → Prompt
    """
    display_name = "Tis Redis Chat Storage"
    description = "Simple Redis chat storage - stores messages and returns formatted history"
    name = "TisRedisChatStorageComponent"
    icon = "Redis"

    inputs = [
        # Redis connection
        StrInput(
            name="host",
            display_name="Redis Host",
            value="localhost",
            required=True
        ),
        IntInput(
            name="port",
            display_name="Redis Port",
            value=6379,
            required=True
        ),
        StrInput(
            name="database",
            display_name="Database",
            value="0",
            required=True
        ),
        SecretStrInput(
            name="password",
            display_name="Password",
            value="",
            advanced=True
        ),

        # Session config
        MessageTextInput(
            name="session_id",
            display_name="Session ID",
            value="",
            advanced=True
        ),

        # Messages to store (optional - if empty, just returns history)
        MessageTextInput(
            name="user_message",
            display_name="User Message",
            value="",
            required=False
        ),
        HandleInput(
            name="ai_message",
            display_name="AI Message",
            input_types=["Message"],
            required=False
        ),
    ]

    outputs = [
        Output(
            display_name="Formatted History",
            name="messages",
            method="store_and_get_messages"
        ),
    ]

    def _get_redis_memory(self) -> RedisChatMessageHistory:
        """Create Redis connection"""
        password = parse.quote_plus(self.password) if self.password else ""
        url = f"redis://:{password}@{self.host}:{self.port}/{self.database}"
        return RedisChatMessageHistory(session_id=self.session_id, url=url)

    def store_and_get_messages(self) -> Message:
        """Store any new messages and return formatted conversation history"""
        memory = self._get_redis_memory()

        # Store user message if provided
        if self.user_message and self.user_message.strip():
            user_msg = HumanMessage(
                content=self.user_message,
                session_id=self.session_id,
                sender=MESSAGE_SENDER_USER,
                sender_name=MESSAGE_SENDER_NAME_USER
            )
            memory.add_message(user_msg)
            logger.info(f"✅ Stored user message: {self.user_message[:30]}...")

        # Store AI message if provided
        if self.ai_message and hasattr(self.ai_message, 'text'):
            ai_msg = AIMessage(
                content=self.ai_message.text,
                session_id=self.session_id,
                sender=MESSAGE_SENDER_AI,
                sender_name=MESSAGE_SENDER_NAME_AI
            )
            memory.add_message(ai_msg)
            logger.info(f"✅ Stored AI message: {self.ai_message.text[:30]}...")

        # Get and format all messages
        try:
            all_messages = memory.messages
            if not all_messages:
                return Message(text="No conversation history.")

            # Format as conversation
            formatted_lines = []
            for msg in all_messages:
                if hasattr(msg, 'type') and hasattr(msg, 'content'):
                    sender = "User" if msg.type == "human" else "AI"
                    formatted_lines.append(f"{sender}: {msg.content}")

            conversation = "\n".join(formatted_lines)
            logger.info(f"📋 Returned {len(all_messages)} messages")
            return Message(text=conversation)

        except Exception as e:
            logger.error(f"❌ Error getting messages: {e}")
            return Message(text="Error retrieving conversation history.")
