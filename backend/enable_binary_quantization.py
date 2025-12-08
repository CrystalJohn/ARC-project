#!/usr/bin/env python3
"""
Enable Binary Quantization for existing Qdrant collection.

Cohere Embed Multilingual v3 is specifically designed to work well with BQ.
Benefits:
- 32x memory reduction (4KB -> 128 bytes per vector)
- 40x faster search
- ~96-98% recall (minimal loss due to Matryoshka training)

Usage:
    python enable_binary_quantization.py

This will:
1. Check current quantization status
2. Enable Binary Quantization if not already enabled
3. Verify the change
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.qdrant_client import QdrantVectorStore


def main():
    # Get Qdrant connection from environment
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    
    print(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}...")
    
    store = QdrantVectorStore(host=qdrant_host, port=qdrant_port)
    
    # Check health
    if not store.health_check():
        print("❌ Cannot connect to Qdrant")
        sys.exit(1)
    
    print("✅ Connected to Qdrant")
    
    # Get collection info
    info = store.get_collection_info()
    print(f"\nCollection: {info.get('name', 'N/A')}")
    print(f"Vectors: {info.get('vectors_count', 0):,}")
    print(f"Status: {info.get('status', 'N/A')}")
    
    # Check current quantization
    quant_info = store.get_quantization_info()
    print(f"\nCurrent Quantization:")
    print(f"  Enabled: {quant_info.get('enabled', False)}")
    print(f"  Type: {quant_info.get('type', 'None')}")
    
    if quant_info.get('type') == 'binary':
        print("\n✅ Binary Quantization is already enabled!")
        print("   No action needed.")
        return
    
    # Confirm before enabling
    print("\n" + "=" * 60)
    print("BINARY QUANTIZATION FOR COHERE EMBED v3")
    print("=" * 60)
    print("""
Benefits:
  • 32x memory reduction (4KB → 128 bytes per vector)
  • 40x faster search speed
  • ~96-98% recall (Cohere v3 is optimized for BQ)

This operation will:
  1. Enable Binary Quantization on the collection
  2. Quantize all existing vectors in-place
  3. Future vectors will be automatically quantized

Note: Original vectors are preserved for rescoring.
""")
    
    response = input("Enable Binary Quantization? [y/N]: ").strip().lower()
    
    if response != 'y':
        print("Cancelled.")
        return
    
    print("\nEnabling Binary Quantization...")
    
    if store.enable_binary_quantization():
        print("✅ Binary Quantization enabled successfully!")
        
        # Verify
        new_quant_info = store.get_quantization_info()
        print(f"\nNew Quantization Status:")
        print(f"  Enabled: {new_quant_info.get('enabled', False)}")
        print(f"  Type: {new_quant_info.get('type', 'None')}")
        print(f"  Always RAM: {new_quant_info.get('always_ram', False)}")
        
        print("\n✅ Migration complete!")
        print("   Search will now use BQ with automatic rescoring.")
    else:
        print("❌ Failed to enable Binary Quantization")
        sys.exit(1)


if __name__ == "__main__":
    main()
