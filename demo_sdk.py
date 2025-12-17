from basalt_sdk import BasaltClient
import os

# 1. Initialize the Client
# In the future, you would pass your API key here: client = BasaltClient(api_key="b_live_...")
client = BasaltClient(base_url="http://localhost:8000")

# 2. Select an asset to secure
# We'll create a dummy file just for this test
test_file = "evidence_sample.txt"
with open(test_file, "w") as f:
    f.write("This is a sensitive document maintained by Basalt.")

try:
    print(f"--- STARTING NOTARIZATION PROTOCOL ---")
    
    # 3. Notarize the Asset
    evidence = client.notarize(test_file)
    
    # 4. Print the Proof
    print(evidence)
    
    print("--- PROTOCOL COMPLETE ---")
    print(f"Verify manually at: {evidence.solana_tx}")

except Exception as e:
    print(f"\n[!] ERROR: {e}")
    if "ConnectionError" in str(e):
        print("HINT: Make sure 'uvicorn main:app --reload' is running in another terminal!")
finally:
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
