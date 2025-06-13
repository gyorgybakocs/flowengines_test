"""
TIS Redis GET - Simple Redis key-value lookup

Simple Redis GET operation by key.
No vector store, no complex operations.

Author: BGDS
Version: 1.0.0
"""

from langflow.custom import Component
from langflow.inputs import StrInput, SecretStrInput, IntInput
from langflow.schema.message import Message
from langflow.template import Output
from loguru import logger

# Redis imports
try:
    import redis
    logger.info("✅ redis imported successfully")
except ImportError:
    logger.error("❌ redis not available")
    redis = None


class TisRedisComponent(Component):
    """
    TIS Redis GET - Simple Key Lookup

    🎯 ONE JOB:
    • Connect to Redis
    • GET value by key
    • Return value as Message

    Example: key="openweathermap.org" → value="Weather API knowledge"
    """

    display_name = "TIS Redis"
    description = "Simple Redis key-value lookup"
    name = "TisRedisComponent"
    icon = "Redis"

    inputs = [
        StrInput(
            name="key",
            display_name="Redis Key",
            info="Key to lookup in Redis",
            required=True,
            value=""
        ),
        StrInput(
            name="redis_host",
            display_name="Redis Host",
            value="localhost",
            required=True
        ),
        IntInput(
            name="redis_port",
            display_name="Redis Port",
            value=6379,
            required=True
        ),
        StrInput(
            name="redis_db",
            display_name="Redis Database",
            value="0",
            required=True
        ),
        SecretStrInput(
            name="redis_password",
            display_name="Redis Password",
            value="",
            advanced=True
        ),
    ]

    outputs = [
        Output(display_name="Value", name="value", method="get_value"),
    ]

    def get_value(self) -> Message:
        """Get value from Redis by key"""
        try:
            if not redis:
                return Message(text="❌ Redis not available")

            if not self.key or not self.key.strip():
                return Message(text="❌ No key provided")

            # Connect to Redis
            redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=int(self.redis_db),
                password=self.redis_password if self.redis_password else None,
                decode_responses=True
            )

            # Simple GET
            value = redis_client.get(self.key.strip())

            if value:
                logger.info(f"✅ Found value for key: {self.key}")
                return Message(text=value)
            else:
                logger.info(f"⚠️ No value found for key: {self.key}")
                return Message(text="")

        except Exception as e:
            error_msg = f"❌ Redis GET failed: {str(e)}"
            logger.error(error_msg)
            return Message(text="")