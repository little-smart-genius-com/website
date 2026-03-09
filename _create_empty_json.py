import json

with open("articles.json", "w", encoding="utf-8") as f:
    json.dump([], f)

with open("search_index.json", "w", encoding="utf-8") as f:
    json.dump([], f)
