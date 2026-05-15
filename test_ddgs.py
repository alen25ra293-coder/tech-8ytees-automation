import sys
from duckduckgo_search import DDGS
import json

def test_search():
    try:
        results = DDGS().images("Portronics PAT wireless charger", max_results=3)
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(e)

if __name__ == "__main__":
    test_search()
