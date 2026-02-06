
import httpx
import asyncio
import json

async def test_search():
    url = "http://localhost:8000/api/search"
    params = {
        "q": "covid",
        "sources": "pubmed,arxiv",
        "max_results": 2
    }
    print(f"Querying {url} with params {params}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            if response.status_code == 200:
                print("Success!")
                data = response.json()
                print("Total results:", data.get("total"))
                print("Articles found:", len(data.get("articles", [])))
                for art in data.get("articles", []):
                    print(f"- [{art.get('source')}] {art.get('title')}")
                for err in data.get("errors", []):
                    print(f"ERROR in {err.get('error')}: {err.get('message')}")
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_search())
