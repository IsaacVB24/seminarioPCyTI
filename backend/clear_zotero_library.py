import asyncio
import os
import urllib.request
import urllib.parse
from app.services.zotero import get_zotero_items, get_headers, ZOTERO_API_URL
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def clear_library():
    """
    Fetches all items from the Zotero library and deletes them.
    Useful for resetting the environment during testing.
    """
    print("🔄 Fetching items from Zotero...")
    # Fetch up to 100 items (chunk if more needed in future)
    items = await get_zotero_items(limit=100)
    
    if not items:
        print("✅ Library is already empty.")
        return

    print(f"found {len(items)} items. Deleting...")
    
    api_key = os.getenv("ZOTERO_API_KEY", "").strip()
    user_id = os.getenv("ZOTERO_USER_ID", "").strip()
    
    if not api_key or not user_id:
        print("❌ Error: Zotero credentials missing in .env")
        return

    # Extract keys
    keys = [item["key"] for item in items]
    keys_str = ",".join(keys)
    
    # Zotero allows deleting multiple items via comma-separated keys
    endpoint = f"{ZOTERO_API_URL}/users/{user_id}/items"
    params = {"itemKey": keys_str}
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url, headers=get_headers(api_key), method="DELETE")
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 204:
                print(f"✅ Successfully deleted {len(items)} items.")
            else:
                print(f"❌ Failed to delete. Status: {response.getcode()}")
    except Exception as e:
        print(f"❌ Error during deletion: {e}")

if __name__ == "__main__":
    asyncio.run(clear_library())
