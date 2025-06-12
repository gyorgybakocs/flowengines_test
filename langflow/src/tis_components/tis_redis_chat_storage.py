from urllib import parse

from langchain_community.chat_message_histories.redis import RedisChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langflow.base.memory.model import LCChatMemoryComponent
from langflow.field_typing.constants import Memory
from langflow.inputs import IntInput, MessageTextInput, SecretStrInput, StrInput
from langflow.inputs import MessageInput
from langflow.schema.message import Message
from langflow.template import Output
from langflow.utils.constants import MESSAGE_SENDER_AI, MESSAGE_SENDER_NAME_AI, MESSAGE_SENDER_USER, \
    MESSAGE_SENDER_NAME_USER
from loguru import logger

from langflow.memory import aget_messages
from langflow.schema import Data
from langflow.helpers.data import data_to_text, messages_to_text
from typing import cast

class TisRedisChatStorageComponent(LCChatMemoryComponent):
    """
    TIS Redis Chat Storage Component for managing chat message persistence.

    This component extends LCChatMemoryComponent to provide Redis-based storage
    for chat messages, allowing retrieval and storage of conversation history
    in a Redis database.
    """
    display_name = "Tis Redis Chat Storage"
    description = "Retrieves and store chat messages from Redis."
    name = "TisRedisChatStorageComponent"
    icon = "Redis"

    inputs = [
        # Redis connection configuration
        StrInput(
            name="host",
            display_name="hostname",
            required=True,
            value="localhost",
            info="IP address or hostname of the Redis server."
        ),
        IntInput(
            name="port",
            display_name="port",
            required=True,
            value=6379,  # Default Redis port
            info="Redis server port number."
        ),
        StrInput(
            name="database",
            display_name="database",
            required=True,
            value="0",  # Default Redis database
            info="Redis database number to use."
        ),

        # Authentication credentials
        MessageTextInput(
            name="username",
            display_name="Username",
            value="",
            info="Redis username for authentication (optional).",
            advanced=True
        ),
        SecretStrInput(
            name="password",
            display_name="Password",
            value="",
            info="Password for Redis authentication (optional).",
            advanced=True
        ),

        # Storage configuration
        StrInput(
            name="key_prefix",
            display_name="Key prefix",
            info="Prefix for Redis keys to namespace chat sessions.",
            advanced=True
        ),
        MessageTextInput(
            name="session_id",
            display_name="Session ID",
            info="Unique identifier for the chat session.",
            advanced=True
        ),

        # Message content inputs
        MessageTextInput(
            name="user_message",
            display_name="User Message",
            info="The user's message content to store in Redis.",
            value="",
        ),
        MessageInput(
            name="ai_message",
            display_name="AI Message",
            info="The AI's response message to store in Redis.",
            value={},
        ),

        # Message metadata
        MessageTextInput(
            name="sender",
            display_name="Sender",
            info="Message sender type (Machine or User). Uses default if empty.",
            advanced=True,
        ),
        MessageTextInput(
            name="sender_name",
            display_name="Sender Name",
            info="Display name of the message sender (AI or User). Uses default if empty.",
            advanced=True,
        ),
        MessageTextInput(
            name="session_id",
            display_name="Session ID",
            info="Chat session identifier. Uses current session ID if empty.",
            value="",
            advanced=True,
        ),
    ]


    def _get_memory(self) -> Memory:
        kwargs = {}
        password: str | None = self.password
        if password:
            password = parse.quote_plus(password)

        # Add key prefix to kwargs if specified
        if self.key_prefix:
            kwargs["key_prefix"] = self.key_prefix

        # Construct Redis connection URL with authentication
        url = f"redis://{self.username}:{password}@{self.host}:{self.port}/{self.database}"

        # Create Redis chat message history instance
        return RedisChatMessageHistory(session_id=self.session_id, url=url, **kwargs)

    def build_message_history(self) -> Memory:
        """
        Build and configure Redis chat message history with stored messages.

        This method:
        1. Constructs the Redis connection URL with authentication
        2. Creates a RedisChatMessageHistory instance
        3. Formats user and AI messages according to LangChain standards
        4. Stores both messages in Redis

        Returns:
            Memory: Configured RedisChatMessageHistory instance with stored messages

        Note:
            There appears to be a bug in the sender/sender_name assignments -
            both user and AI messages are incorrectly assigned AI sender constants.
        """
        # Create Redis chat message history instance
        memory = self._get_memory()

        # Create AI message object with proper metadata
        ai_message = AIMessage(
            content=self.ai_message.text,  # Extract text content from Message object
            session_id=self.session_id,
            sender=MESSAGE_SENDER_AI,
            sender_name=MESSAGE_SENDER_NAME_AI
        )

        # Create user message object with proper metadata
        user_message = HumanMessage(
            content=self.user_message,
            session_id=self.session_id,
            sender=MESSAGE_SENDER_USER,
            sender_name=MESSAGE_SENDER_NAME_USER
        )

        # Store messages in Redis in chronological order
        memory.add_message(user_message)
        memory.add_message(ai_message)

        return memory
