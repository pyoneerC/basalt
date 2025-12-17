"""
Basalt SDK
==========
Python SDK for the Basalt Protocol - Digital Provenance & Notarization

Usage:
    import basalt
    
    client = basalt.Client(api_key="b_live_...")
    evidence = client.notarize("my_file.jpg")
    print(evidence.solana_tx)
"""

# Re-export from basalt_sdk for cleaner imports
from basalt_sdk.client import BasaltClient as Client
from basalt_sdk.client import Evidence

__version__ = "1.0.0"
__all__ = ["Client", "Evidence"]
