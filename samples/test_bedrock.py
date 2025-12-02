"""
Test Bedrock APIs - Claude 3.5 Sonnet & Titan Embeddings v2
"""
import boto3
import json

# Initialize Bedrock client
bedrock = boto3.client('bedrock-runtime', region_name='ap-southeast-1')

def test_cohere_embeddings():
    """Test Cohere Embed Multilingual v3 - 1024 dimensions"""
    print("=" * 50)
    print("Testing Cohere Embed Multilingual v3...")
    
    response = bedrock.invoke_model(
        modelId='cohere.embed-multilingual-v3',
        body=json.dumps({
            "texts": ["Hello, this is a test for embeddings."],
            "input_type": "search_document"
        })
    )
    
    result = json.loads(response['body'].read())
    embedding = result['embeddings'][0]
    
    print(f"✅ Success! Embedding dimension: {len(embedding)}")
    print(f"   First 5 values: {embedding[:5]}")
    return embedding

def test_claude_sonnet():
    """Test Claude 3.5 Sonnet"""
    print("=" * 50)
    print("Testing Claude 3.5 Sonnet...")
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 256,
            "messages": [
                {"role": "user", "content": "Say hello in Vietnamese, keep it short."}
            ]
        })
    )
    
    result = json.loads(response['body'].read())
    text = result['content'][0]['text']
    
    print(f"✅ Success! Response: {text}")
    return text

if __name__ == "__main__":
    print("\n🚀 Bedrock API Test\n")
    
    try:
        test_cohere_embeddings()
    except Exception as e:
        print(f"❌ Cohere Embeddings Error: {e}")
    
    print()
    
    try:
        test_claude_sonnet()
    except Exception as e:
        print(f"❌ Claude Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")
