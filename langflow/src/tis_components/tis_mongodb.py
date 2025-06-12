"""
Tis MongoDB Smart Component - Intelligent Store & Search

An intelligent MongoDB component that automatically detects whether you want to:
• Store data (JSON input) → Stores document
• Search data (text query) → Searches documents

Author: BGDS
Version: 3.0.0 - Smart detection
"""

from typing import List, Any, Optional
import json
from datetime import datetime

from langflow.custom import Component
from langflow.inputs import MessageTextInput, SecretStrInput, StrInput
from langflow.schema.message import Message
from langflow.template import Output
from loguru import logger

# MongoDB imports with better error handling
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, OperationFailure
    logger.info("✅ pymongo imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import pymongo: {e}")
    MongoClient = None
    ConnectionFailure = Exception
    OperationFailure = Exception


class TisMongoDBComponent(Component):
    """
    Tis MongoDB Smart - Intelligent Store & Search

    🧠 SMART DETECTION:
    • JSON input → Automatically stores as document
    • Text input → Automatically searches documents
    • No manual operation selection needed!

    Examples:
    📝 Store: {"title": "My Code", "code": "print('hello')", "language": "python"}
    🔍 Search: "python code examples"
    🔍 Search: "redis connection"
    """

    display_name = "Tis MongoDB Smart"
    description = "Intelligent MongoDB component - auto-detects store vs search operations"
    name = "TisMongoDBSmartComponent"
    icon = "MongoDB"

    inputs = [
        # MongoDB Connection
        SecretStrInput(
            name="connection_string",
            display_name="MongoDB Connection String",
            required=True,
            value="mongodb://langflow_user:langflow_password@localhost:27017/fetest-mongodb",
            info="MongoDB connection string"
        ),
        StrInput(
            name="database_name",
            display_name="Database Name",
            required=True,
            value="fetest-mongodb",
            info="Name of the MongoDB database"
        ),
        StrInput(
            name="collection_name",
            display_name="Collection Name",
            required=True,
            value="documents",
            info="Name of the collection"
        ),

        # Smart Input - Auto-detects intent!
        MessageTextInput(
            name="user_input",
            display_name="Input (JSON to store / Text to search)",
            info="🧠 SMART: JSON = Store document | Text = Search documents",
            value="",
            required=True,
        ),

        # Advanced options
        StrInput(
            name="search_limit",
            display_name="Search Result Limit",
            value="5",
            info="Max search results",
            advanced=True,
        ),
    ]

    outputs = [
        Output(display_name="Result", name="result", method="smart_operation"),
        Output(display_name="Status", name="status", method="get_status"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = None
        self._status_message = "Ready"
        self._operation_type = "unknown"

    def _get_client(self):
        """Get MongoDB client"""
        try:
            from pymongo import MongoClient
            from pymongo.errors import ConnectionFailure, OperationFailure
        except ImportError:
            raise Exception("❌ pymongo not available - MongoDB operations not supported")

        if self._client is None:
            try:
                self._client = MongoClient(self.connection_string)
                self._client.admin.command('ping')
                logger.info("✅ MongoDB connection established")
            except Exception as e:
                error_msg = f"❌ MongoDB connection failed: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg)
        return self._client

    def _get_collection(self):
        """Get MongoDB collection"""
        client = self._get_client()
        db = client[self.database_name]
        return db[self.collection_name]

    def _detect_intent(self, user_input: str) -> tuple[str, any]:
        """
        🧠 Smart intent detection:
        - Tries to parse as JSON → STORE operation
        - If not JSON → SEARCH operation
        """
        if not user_input or not user_input.strip():
            return "empty", None

        user_input = user_input.strip()

        # Try to detect JSON
        if user_input.startswith('{') and user_input.endswith('}'):
            try:
                json_data = json.loads(user_input)
                return "store", json_data
            except json.JSONDecodeError:
                pass

        # Also try if it looks like JSON but without obvious brackets
        try:
            json_data = json.loads(user_input)
            return "store", json_data
        except json.JSONDecodeError:
            pass

        # If not JSON, treat as search query
        return "search", user_input

    def _store_document(self, json_data: dict) -> dict:
        """Store a document"""
        try:
            collection = self._get_collection()

            # MongoDB validation requires: source, content, created_at
            # Transform user data to match schema
            doc_to_store = {
                'source': 'langflow_tis_smart',  # Required field
                'content': self._extract_content(json_data),  # Required field
                'created_at': datetime.utcnow(),  # Required field
                'metadata': json_data,  # Store original data as metadata
                '_updated_at': datetime.utcnow(),
            }

            result = collection.insert_one(doc_to_store)

            stored_doc = {
                '_id': str(result.inserted_id),
                **doc_to_store
            }

            self._status_message = f"✅ Document stored with ID: {result.inserted_id}"
            logger.info(self._status_message)

            return stored_doc

        except Exception as e:
            error_msg = f"❌ Error storing document: {str(e)}"
            self._status_message = error_msg
            logger.error(error_msg)
            raise Exception(error_msg)

    def _extract_content(self, json_data: dict) -> str:
        """Extract meaningful content from JSON data for the required 'content' field"""
        # Try to build a readable content string from the JSON
        content_parts = []

        if 'title' in json_data:
            content_parts.append(f"Title: {json_data['title']}")

        if 'description' in json_data:
            content_parts.append(f"Description: {json_data['description']}")

        if 'code' in json_data:
            content_parts.append(f"Code: {json_data['code']}")

        if 'content' in json_data:
            content_parts.append(f"Content: {json_data['content']}")

        if 'language' in json_data:
            content_parts.append(f"Language: {json_data['language']}")

        if 'tags' in json_data:
            content_parts.append(f"Tags: {', '.join(json_data['tags']) if isinstance(json_data['tags'], list) else json_data['tags']}")

        # If no recognizable content, use JSON string
        if not content_parts:
            content_parts.append(json.dumps(json_data, default=str))

        return " | ".join(content_parts)

    def _search_documents(self, search_query: str) -> List[dict]:
        """Search documents"""
        try:
            collection = self._get_collection()

            # Search in content field and metadata fields
            search_conditions = [
                # Search in main content field
                {'content': {'$regex': search_query, '$options': 'i'}},
                # Search in metadata fields
                {'metadata.title': {'$regex': search_query, '$options': 'i'}},
                {'metadata.description': {'$regex': search_query, '$options': 'i'}},
                {'metadata.code': {'$regex': search_query, '$options': 'i'}},
                {'metadata.tags': {'$regex': search_query, '$options': 'i'}},
                {'metadata.language': {'$regex': search_query, '$options': 'i'}},
                {'metadata.category': {'$regex': search_query, '$options': 'i'}},
                {'metadata.type': {'$regex': search_query, '$options': 'i'}},
            ]

            query = {'$or': search_conditions}
            cursor = collection.find(query).sort('created_at', -1).limit(int(self.search_limit))
            results = list(cursor)

            # Convert ObjectId to string
            for doc in results:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])

            self._status_message = f"✅ Found {len(results)} documents for '{search_query}'"
            logger.info(self._status_message)

            return results

        except Exception as e:
            error_msg = f"❌ Error searching: {str(e)}"
            self._status_message = error_msg
            logger.error(error_msg)
            raise Exception(error_msg)

    def _format_search_results(self, results: List[dict], query: str) -> str:
        """Format search results in a readable way"""
        if not results:
            return f"🔍 No documents found for: '{query}'"

        formatted_parts = [f"🔍 Found {len(results)} results for: '{query}'\n"]

        for i, doc in enumerate(results, 1):
            # Get title from metadata or use default
            metadata = doc.get('metadata', {})
            title = metadata.get('title', 'Untitled Document')

            # Get content preview
            content_preview = doc.get('content', '')[:100]
            if len(content_preview) > 97:
                content_preview += "..."

            # Get tags from metadata
            tags = metadata.get('tags', [])
            tag_str = f" #{' #'.join(tags)}" if tags else ""

            # Get language from metadata
            language = metadata.get('language', '')
            lang_str = f" [{language}]" if language else ""

            formatted_parts.append(f"📄 {i}. {title}{lang_str}")
            if content_preview:
                formatted_parts.append(f"   {content_preview}")
            if tag_str:
                formatted_parts.append(f"   {tag_str}")
            formatted_parts.append("")  # Empty line

        return "\n".join(formatted_parts)

    def smart_operation(self) -> Message:
        """🧠 Smart operation - auto-detects store vs search"""
        try:
            # Detect user intent
            intent, data = self._detect_intent(self.user_input)
            self._operation_type = intent

            if intent == "empty":
                return Message(text="⚠️ Please provide input: JSON to store or text to search")

            elif intent == "store":
                # Store the JSON document
                logger.info(f"🧠 Detected STORE operation")
                result = self._store_document(data)
                formatted_result = f"✅ STORED DOCUMENT:\n\n{json.dumps(result, indent=2, default=str)}"
                return Message(text=formatted_result)

            elif intent == "search":
                # Search for documents
                logger.info(f"🧠 Detected SEARCH operation: '{data}'")
                results = self._search_documents(data)
                formatted_result = self._format_search_results(results, data)
                return Message(text=formatted_result)

            else:
                return Message(text="❌ Could not determine operation from input")

        except Exception as e:
            error_msg = f"❌ Smart operation failed: {str(e)}"
            logger.error(error_msg)
            return Message(text=error_msg)

    def get_status(self) -> Message:
        """Get operation status"""
        status_with_type = f"{self._status_message} (Operation: {self._operation_type})"
        return Message(text=status_with_type)

    def __del__(self):
        """Clean up connection"""
        if hasattr(self, '_client') and self._client:
            self._client.close()
