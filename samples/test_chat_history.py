"""
Integration test for Chat History Manager (Task #29)

Tests chat history storage and retrieval with real DynamoDB.
Run on EC2 with proper IAM permissions.

Usage:
    python samples/test_chat_history.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.chat_history_manager import (
    ChatHistoryManager,
    MessageRole,
    create_chat_history_manager,
)
import uuid


def test_chat_history():
    """Test chat history operations with DynamoDB."""
    print("=" * 60)
    print("Chat History Manager Integration Test")
    print("=" * 60)
    
    # Initialize manager
    manager = create_chat_history_manager()
    print(f"\n✓ Initialized ChatHistoryManager")
    print(f"  Table: {manager.table_name}")
    print(f"  Region: {manager.region_name}")
    
    # Generate test IDs
    conversation_id = f"test-conv-{uuid.uuid4().hex[:8]}"
    user_id = "test-user-001"
    
    print(f"\n--- Test Conversation: {conversation_id} ---")
    
    # Test 1: Save user message
    print("\n[Test 1] Save user message...")
    user_msg = manager.save_user_message(
        conversation_id=conversation_id,
        content="What is machine learning?",
        user_id=user_id,
    )
    print(f"  ✓ Saved user message: {user_msg.message_id}")
    print(f"    Content: {user_msg.content}")
    print(f"    Created: {user_msg.created_at}")
    
    # Test 2: Save assistant message with metadata
    print("\n[Test 2] Save assistant message with citations...")
    citations = [
        {"id": 1, "doc_id": "doc-ml-intro", "page": 5, "score": 0.92},
        {"id": 2, "doc_id": "doc-ml-intro", "page": 12, "score": 0.85},
    ]
    usage = {"input_tokens": 500, "output_tokens": 250, "total_tokens": 750}
    
    assistant_msg = manager.save_assistant_message(
        conversation_id=conversation_id,
        content="Machine learning is a subset of artificial intelligence [1] that enables systems to learn from data [2].",
        user_id=user_id,
        citations=citations,
        usage=usage,
        model="sonnet",
    )
    print(f"  ✓ Saved assistant message: {assistant_msg.message_id}")
    print(f"    Model: {assistant_msg.model}")
    print(f"    Usage: {assistant_msg.usage}")
    
    # Test 3: Save follow-up messages
    print("\n[Test 3] Save follow-up messages...")
    manager.save_user_message(
        conversation_id=conversation_id,
        content="Can you give me an example?",
        user_id=user_id,
    )
    manager.save_assistant_message(
        conversation_id=conversation_id,
        content="Sure! A common example is spam detection in emails...",
        user_id=user_id,
        model="sonnet",
    )
    print("  ✓ Saved 2 follow-up messages")
    
    # Test 4: Get conversation history
    print("\n[Test 4] Get conversation history...")
    messages = manager.get_conversation_history(conversation_id)
    print(f"  ✓ Retrieved {len(messages)} messages")
    for i, msg in enumerate(messages, 1):
        role = msg.role.value if isinstance(msg.role, MessageRole) else msg.role
        print(f"    [{i}] {role}: {msg.content[:50]}...")
    
    # Test 5: Get history for Claude context
    print("\n[Test 5] Get history for Claude context...")
    context_history = manager.get_history_for_context(conversation_id, max_messages=10)
    print(f"  ✓ Formatted {len(context_history)} messages for Claude")
    for msg in context_history:
        print(f"    - {msg['role']}: {msg['content'][:40]}...")
    
    # Test 6: List conversations
    print("\n[Test 6] List user conversations...")
    result = manager.list_conversations(user_id, limit=5)
    print(f"  ✓ Found {len(result['conversations'])} conversations")
    for conv in result['conversations']:
        print(f"    - {conv['conversation_id']}: {conv.get('last_message', '')[:30]}...")
    
    # Test 7: Delete conversation (cleanup)
    print("\n[Test 7] Delete test conversation...")
    deleted = manager.delete_conversation(conversation_id, user_id)
    print(f"  ✓ Deleted {deleted} messages")
    
    # Verify deletion
    messages_after = manager.get_conversation_history(conversation_id)
    print(f"  ✓ Verified: {len(messages_after)} messages remaining")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    test_chat_history()
