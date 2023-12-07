import requests


def notion_input(token, database, property):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-02-22"
    }
    data = {
        "parent": {"database_id": database},
        "properties": {
            property: {
                "rich_text": [
                    {
                        "text": {
                            "content": "Hello world"
                        }
                    }
                ]
            }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()
