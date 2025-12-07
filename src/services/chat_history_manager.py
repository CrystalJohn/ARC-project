import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from decimal import Decimal
import uuid
import logging
import json

logger = logging.getLogger(__name__)


def convert_floats_to_decimal(obj: Any) -> Any:
    """Convert float values to Decimal for DynamoDB compatibility"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    return obj


@dataclass
class ChatMessage:
    """Chat message model"""
    message_id: str
    conversation_id: str
    user_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    metadata: Optional[Dict] = None


class ChatHistoryManager:
    """
    Manage chat history in DynamoDB
    
    Works with existing table: arc-chatbot-dev-chat-history
    Schema: PK=user_id, SK=sk, GSI=conversation-index
    """
    
    def __init__(
        self,
        table_name: str = "arc-chatbot-dev-chat-history",
        region_name: str = "ap-southeast-1",
        ttl_days: int = 30
    ):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(table_name)
        self.ttl_days = ttl_days
    
    def _generate_sort_key(self, conversation_id: str, timestamp: str) -> str:
        """Generate sort key: CONV#{conversation_id}#MSG#{timestamp}"""
        return f"CONV#{conversation_id}#MSG#{timestamp}"
    
    def _generate_ttl(self) -> int:
        """Generate TTL timestamp (30 days from now)"""
        expiry = datetime.utcnow() + timedelta(days=self.ttl_days)
        return int(expiry.timestamp())
    
    def save_user_message(
        self,
        conversation_id: str,
        user_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> ChatMessage:
        """Save user message to DynamoDB"""
        timestamp = datetime.utcnow().isoformat()
        message_id = f"msg-{uuid.uuid4().hex[:12]}"
        
        item = {
            "user_id": user_id,
            "sk": self._generate_sort_key(conversation_id, timestamp),
            "conversation_id": conversation_id,
            "message_id": message_id,
            "role": "user",
            "content": content,
            "timestamp": timestamp,
            "created_at": timestamp,  # For GSI
            "ttl": self._generate_ttl()
        }
        
        if metadata:
            item["metadata"] = convert_floats_to_decimal(metadata)
        
        try:
            self.table.put_item(Item=item)
            logger.info(f"✅ Saved user message: {message_id}")
            return ChatMessage(
                message_id=message_id,
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                content=content,
                timestamp=timestamp,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"❌ Failed to save user message: {e}")
            raise
    
    def save_assistant_message(
        self,
        conversation_id: str,
        user_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> ChatMessage:
        """Save assistant message with metadata (citations, scores)"""
        timestamp = datetime.utcnow().isoformat()
        message_id = f"msg-{uuid.uuid4().hex[:12]}"
        
        item = {
            "user_id": user_id,
            "sk": self._generate_sort_key(conversation_id, timestamp),
            "conversation_id": conversation_id,
            "message_id": message_id,
            "role": "assistant",
            "content": content,
            "timestamp": timestamp,
            "created_at": timestamp,  # For GSI
            "ttl": self._generate_ttl()
        }
        
        if metadata:
            item["metadata"] = convert_floats_to_decimal(metadata)
        
        try:
            self.table.put_item(Item=item)
            logger.info(f"✅ Saved assistant message: {message_id}")
            return ChatMessage(
                message_id=message_id,
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=content,
                timestamp=timestamp,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"❌ Failed to save assistant message: {e}")
            raise
    
    def get_conversation_history(
        self,
        conversation_id: str,
        user_id: str,
        max_messages: int = 20
    ) -> Dict:
        """Get conversation history using main table query"""
        try:
            response = self.table.query(
                KeyConditionExpression="user_id = :user_id AND begins_with(sk, :sk_prefix)",
                ExpressionAttributeValues={
                    ":user_id": user_id,
                    ":sk_prefix": f"CONV#{conversation_id}#MSG#"
                },
                Limit=max_messages,
                ScanIndexForward=False  # Most recent first
            )
            
            messages = []
            for item in response.get("Items", []):
                # Handle legacy data that may use created_at instead of timestamp
                timestamp = item.get("timestamp") or item.get("created_at", "")
                messages.append(ChatMessage(
                    message_id=item.get("message_id", "unknown"),
                    conversation_id=item.get("conversation_id", conversation_id),
                    user_id=item.get("user_id", user_id),
                    role=item.get("role", "user"),
                    content=item.get("content", ""),
                    timestamp=timestamp,
                    metadata=item.get("metadata")
                ))
            
            return {
                "messages": messages,
                "has_more": len(messages) == max_messages
            }
        except Exception as e:
            logger.error(f"❌ Failed to get conversation history: {e}")
            raise
    
    def get_history_for_context(
        self,
        conversation_id: str,
        user_id: str,
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for LLM context
        
        Returns: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        result = self.get_conversation_history(
            conversation_id=conversation_id,
            user_id=user_id,
            max_messages=max_messages
        )
        
        # Reverse to chronological order (oldest first)
        messages = result["messages"][::-1]
        
        # Format for LLM
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return formatted
    
    def list_user_conversations(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """List all conversations for a user"""
        try:
            response = self.table.query(
                KeyConditionExpression="user_id = :user_id",
                ExpressionAttributeValues={
                    ":user_id": user_id
                },
                Limit=limit * 10,  # Get more items to group
                ScanIndexForward=False
            )
            
            # Group by conversation_id
            conversations = {}
            for item in response.get("Items", []):
                conv_id = item.get("conversation_id")
                if not conv_id:
                    continue
                timestamp = item.get("timestamp") or item.get("created_at", "")
                if conv_id not in conversations:
                    conversations[conv_id] = {
                        "conversation_id": conv_id,
                        "last_message_time": timestamp,
                        "message_count": 0
                    }
                conversations[conv_id]["message_count"] += 1
            
            # Sort by last message time and limit
            sorted_convs = sorted(
                conversations.values(),
                key=lambda x: x["last_message_time"],
                reverse=True
            )
            
            return sorted_convs[:limit]
        except Exception as e:
            logger.error(f"❌ Failed to list conversations: {e}")
            raise
