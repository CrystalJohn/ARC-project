"""Test citations in chat history"""
import sys
sys.path.insert(0, '.')

from app.services.chat_history_manager import ChatHistoryManager

manager = ChatHistoryManager(region_name="ap-southeast-1")

# Get a conversation with correct user_id
user_id = "395a95ec-4071-701d-103c-6b9daa39a380"
result = manager.list_conversations(user_id=user_id, limit=5)
print("Conversations:")
for conv in result.get("conversations", []):
    print(f"  - {conv.get('conversation_id')}: {conv.get('title', 'N/A')[:40]}")

if result.get("conversations"):
    conv_id = result["conversations"][0]["conversation_id"]
    print(f"\nMessages in {conv_id}:")
    messages = manager.get_conversation_history(conv_id, limit=10)
    for msg in messages:
        role = msg.role.value if hasattr(msg.role, 'value') else msg.role
        print(f"  [{role}] {msg.content[:60]}...")
        if msg.citations:
            print(f"    Citations: {len(msg.citations)} items")
            print(f"    First citation keys: {msg.citations[0].keys() if msg.citations else 'N/A'}")
        else:
            print(f"    Citations: None")
