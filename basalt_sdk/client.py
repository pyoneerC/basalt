import requests
import json
import os
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class Evidence:
    """Represents the cryptographic proof returned by the Basalt Protocol."""
    ipfs_cid: str
    ipfs_url: str
    sha256_hash: str
    solana_tx: str
    c2pa_status: str
    
    def __str__(self):
        return f"""
        === BASALT EVIDENCE ===
        [HASH]   : {self.sha256_hash}
        [IPFS]   : {self.ipfs_cid}
        [SOLANA] : {self.solana_tx}
        [STATUS] : {self.c2pa_status}
        ========================
        """

class BasaltClient:
    """
    The official Python client for the Basalt Protocol.
    """
    
    def __init__(self, api_key: str = None, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        # In a real version, we would add headers={"Authorization": f"Bearer {api_key}"}

    def notarize(self, file_path: str, metadata: Optional[Dict] = None) -> Evidence:
        """
        Uploads a file to the Basalt engine, signs it with C2PA, 
        stores it on IPFS, and anchors the proof to Solana.
        
        :param file_path: Path to the local file (image/document)
        :param metadata: Optional dictionary of extra claims (e.g. location, author)
        :return: Evidence object containing proofs
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Asset not found at: {file_path}")

        url = f"{self.base_url}/notarize"
        
        # Prepare the file
        with open(file_path, 'rb') as f:
            files = {'file': f}
            
            # Send Request
            try:
                print(f"[*] Transmitting asset to Basalt Node: {self.base_url}...")
                response = requests.post(url, files=files)
                response.raise_for_status()
                
                data = response.json()
                
                if "error" in data:
                    raise Exception(f"Basalt Node Error: {data['error']}")
                
                ev_data = data["evidence"]
                
                return Evidence(
                    ipfs_cid=ev_data["ipfs_cid"],
                    ipfs_url=ev_data["ipfs_url"],
                    sha256_hash=ev_data["sha256_hash"],
                    solana_tx=ev_data["solana_tx"],
                    c2pa_status=ev_data["c2pa_verification"]
                )
                
            except requests.exceptions.ConnectionError:
                raise Exception("Could not connect to Basalt Node. Is the server running?")
            except Exception as e:
                raise Exception(f"Notarization Failed: {str(e)}")

    def verify(self, evidence: Evidence) -> bool:
        """
        Verifies the validity of an Evidence object locally.
        (Mock implementation for MVP)
        """
        # In a real app, this would query the blockchain to check the tx hash
        return True
