"""
Basalt SDK Example
==================
This example demonstrates how to use the Basalt Python SDK to notarize
digital assets with cryptographic provenance.

Requirements:
    pip install requests

Usage:
    1. Start the Basalt server: uvicorn main:app --reload
    2. Run this script: python example_usage.py
"""

import basalt  # or: from basalt_sdk import BasaltClient

# ============================================================
# EXAMPLE 1: Basic Notarization
# ============================================================

def basic_example():
    """Simple notarization of a single file."""
    
    # Initialize Client
    # For production: client = basalt.Client(api_key="b_live_...")
    client = basalt.Client(base_url="http://localhost:8000")
    
    # Notarize an asset
    evidence = client.notarize("photo_evidence.jpg")
    
    # Access the proof
    print(f"IPFS CID: {evidence.ipfs_cid}")
    print(f"SHA-256:  {evidence.sha256_hash}")
    print(f"Solana:   {evidence.solana_tx}")
    

# ============================================================
# EXAMPLE 2: Full Integration (with metadata)
# ============================================================

def full_example():
    """Complete example with metadata and error handling."""
    
    from basalt_sdk import BasaltClient, Evidence
    import os
    
    # Create a test file
    test_file = "surveillance_footage.jpg"
    
    # Create a dummy JPEG for testing
    try:
        from PIL import Image
        img = Image.new('RGB', (640, 480), color='blue')
        img.save(test_file, "JPEG")
    except ImportError:
        # Fallback if PIL not installed
        with open(test_file, 'wb') as f:
            # Minimal valid JPEG header
            f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
            f.write(b'\xFF\xD9')
    
    try:
        # Initialize the client
        client = BasaltClient(
            base_url="http://localhost:8000",
            # api_key="b_live_xxxx"  # For production
        )
        
        print("=" * 50)
        print("BASALT PROTOCOL - NOTARIZATION")
        print("=" * 50)
        
        # Notarize with optional metadata
        evidence = client.notarize(
            file_path=test_file,
            metadata={
                "location": "Sector 7, Camera 4",
                "captured_by": "SecCorp_Device_A",
                "classification": "CONFIDENTIAL"
            }
        )
        
        # Display results
        print(f"""
╔══════════════════════════════════════════════════════════╗
║                   EVIDENCE SECURED                        ║
╠══════════════════════════════════════════════════════════╣
║ SHA-256 Hash:                                             ║
║   {evidence.sha256_hash[:32]}...
║                                                           ║
║ IPFS CID:                                                 ║
║   {evidence.ipfs_cid}
║                                                           ║
║ Blockchain Proof:                                         ║
║   {evidence.solana_tx[:60]}...
║                                                           ║
║ C2PA Signature: {evidence.c2pa_status}
╚══════════════════════════════════════════════════════════╝
        """)
        
        # Verification link
        print(f"\n🔗 Verify at: http://localhost:8000/verify/{evidence.ipfs_cid}")
        print(f"🔗 View on IPFS: {evidence.ipfs_url}")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Hint: Make sure the Basalt server is running!")
        print("   Run: uvicorn main:app --reload")
    finally:
        # Cleanup test file
        if os.path.exists(test_file):
            os.remove(test_file)


# ============================================================
# EXAMPLE 3: Batch Processing
# ============================================================

def batch_example():
    """Notarize multiple files in sequence."""
    
    from basalt_sdk import BasaltClient
    
    client = BasaltClient(base_url="http://localhost:8000")
    
    files_to_notarize = [
        "document_1.pdf",
        "photo_evidence.jpg",
        "contract_signed.png"
    ]
    
    results = []
    for file_path in files_to_notarize:
        try:
            evidence = client.notarize(file_path)
            results.append({
                "file": file_path,
                "status": "SECURED",
                "cid": evidence.ipfs_cid
            })
        except Exception as e:
            results.append({
                "file": file_path,
                "status": "FAILED",
                "error": str(e)
            })
    
    # Print summary
    for r in results:
        status = "✅" if r["status"] == "SECURED" else "❌"
        print(f"{status} {r['file']}: {r.get('cid', r.get('error'))}")


# ============================================================
# RUN EXAMPLES
# ============================================================

if __name__ == "__main__":
    print("\n🪨 BASALT SDK EXAMPLE\n")
    
    # Run the full example
    full_example()
