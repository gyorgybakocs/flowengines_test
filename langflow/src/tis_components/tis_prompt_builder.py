"""
TIS Prompt Builder - Simple Message Builder

Builds prompts programmatically from API data and domain knowledge.
No template variables - direct Message building.

Author: BGDS
Version: 1.0.0
"""

import json
from typing import Dict, Any, Optional

from langflow.custom import Component
from langflow.inputs import HandleInput, MessageTextInput
from langflow.schema import Data
from langflow.schema.message import Message
from langflow.template import Output
from loguru import logger


class TisPromptBuilderComponent(Component):
    """
    TIS Prompt Builder - Simple Message Builder

    🎯 NO TEMPLATE VARIABLES:
    • API Response Data input
    • Domain Knowledge Message input  
    • Custom prompt text input
    • Builds final Message programmatically

    No automatic input generation - full control!
    """

    display_name = "TIS Prompt Builder"
    description = "Build prompts from API data and domain knowledge"
    name = "TisPromptBuilderComponent"
    icon = "MessageSquare"

    inputs = [
        HandleInput(
            name="api_response",
            display_name="API Response",
            input_types=["Data"],
            info="Data object from API Request component",
            required=False
        ),
        HandleInput(
            name="domain_knowledge",
            display_name="Domain Knowledge",
            input_types=["Message"],
            info="Domain knowledge from Redis GET component",
            required=False
        ),
    ]

    outputs = [
        Output(display_name="Built Prompt", name="prompt", method="build_prompt_message"),
    ]

    def _extract_result_data(self, api_response: Data) -> Optional[Dict[str, Any]]:
        """Extract the actual API result from the API Request response structure"""
        if not api_response or not hasattr(api_response, 'data'):
            return None

        response_data = api_response.data

        # API Request component structure: {"source": "...", "result": {...}, "status_code": 200}
        if isinstance(response_data, dict):
            if "result" in response_data:
                return response_data["result"]
            return response_data

        return None

    def build_prompt_message(self) -> Message:
        """Build prompt message programmatically"""
        try:
            # Extract API data
            api_data_str = ""
            if self.api_response:
                result_data = self._extract_result_data(self.api_response)
                if result_data:
                    # Convert to JSON string
                    api_data_str = json.dumps(result_data, indent=2, ensure_ascii=False)

            # Get domain knowledge
            domain_knowledge_str = ""
            if self.domain_knowledge:
                domain_knowledge_str = self.domain_knowledge.text if hasattr(self.domain_knowledge, 'text') else str(self.domain_knowledge)

            # Build prompt automatically - fixed template
            final_prompt = f"""Convert this API response data into natural, human-readable sentences.

API Data:
{api_data_str}

Domain Knowledge:
{domain_knowledge_str}

Instructions:
- Extract the most important and meaningful information
- Ignore technical fields (IDs, timestamps, coordinates, status codes)  
- Focus on data that would be useful to a human
- Write 2-4 clear, natural sentences

Write only the natural language explanation:"""

            # Update status
            status_parts = []
            if api_data_str:
                status_parts.append(f"API: {len(api_data_str)} chars")
            if domain_knowledge_str:
                status_parts.append(f"Knowledge: {len(domain_knowledge_str)} chars")

            self.status = " | ".join(status_parts) if status_parts else f"Prompt: {len(final_prompt)} chars"

            return Message(text=final_prompt)

        except Exception as e:
            error_msg = f"❌ Prompt building failed: {str(e)}"
            logger.error(error_msg)
            self.status = error_msg
            return Message(text=error_msg)