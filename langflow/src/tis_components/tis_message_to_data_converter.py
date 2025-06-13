"""
TIS Message to Data - Simple Message→Data converter

Takes Message from Chat Input and converts to Data object
that API Request can use for query_params.

Author: BGDS
Version: 1.0.0
"""

import json
from typing import Dict, Any

from langflow.custom import Component
from langflow.inputs import HandleInput
from langflow.schema import Data
from langflow.schema.message import Message
from langflow.template import Output


class TisMessageToDataComponent(Component):
    """
    TIS Message to Data - Simple Converter

    Takes Message.text and converts to Data object.
    API Request uses Data.data for query_params.
    """

    display_name = "TIS Message to Data"
    description = "Convert Message to Data object for API Request"
    name = "TisMessageToDataComponent"
    icon = "ArrowRightLeft"

    inputs = [
        HandleInput(
            name="message",
            display_name="Message",
            input_types=["Message"],
            required=True
        ),
    ]

    outputs = [
        Output(display_name="Data", name="data", method="convert"),
    ]

    def convert(self) -> Data:
        """Convert Message to Data"""
        if not self.message:
            return Data(data={})

        message_text = self.message.text if hasattr(self.message, 'text') else str(self.message)

        if not message_text:
            return Data(data={})

        # Try JSON parse
        try:
            parsed = json.loads(message_text)
            if isinstance(parsed, dict):
                return Data(data=parsed)
        except json.JSONDecodeError:
            pass

        # Default: return the text as-is in data
        # User decides what to do with it
        return Data(data={"text": message_text})
