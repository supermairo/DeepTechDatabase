import requests
import psycopg2.extras
import psycopg2


def notion_input(token, database, property, msg, id):
    # 初期設定
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-02-22"
    }
    # idはnotionデータベースのID列に登録する値であり、各行一意の値
    # notionのデータベースに、idに一致するデータがあるか確認
    url = f"https://api.notion.com/v1/databases/{database}/query"
    data = {
        "filter": {
            "property": "ID",
            "number": {
                "equals": id
            }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    if (result["results"]):
        # この値がある場合は更新する
        page_id = result["results"][0]["id"]
        url = f"https://api.notion.com/v1/pages/{page_id}"
        data = {
            "properties": {
                property: {
                    "rich_text": [
                        {
                            "text": {
                                "content": msg
                            }
                        }
                    ]
                },
                "ID": {
                    "number": id
                }
            }
        }
        response = requests.patch(url, headers=headers, json=data)
        return response.json()
    else:
        # この値がない場合は新規作成する
        url = "https://api.notion.com/v1/pages"
        data = {
            "parent": {"database_id": database},
            "properties": {
                property: {
                    "rich_text": [
                        {
                            "text": {
                                "content": msg
                            }
                        }
                    ]
                },
                "ID": {
                    "number": id  # IDを数値型として設定
                }
            }
        }
        response = requests.post(url, headers=headers, json=data)
        return response.json()


def get_value_from_db(table, id, prop, keys):
    # PostgreSQL データベースへの接続情報
    conn = psycopg2.connect(
        dbname="deeptechlab",
        user=keys["db"]["user"],
        password=keys["db"]["password"],
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = f"SELECT {prop} FROM {table} WHERE id = %s;"
    cursor.execute(query, (id,))
    # 結果の取得
    result = cursor.fetchone()
    conn.close()
    # プロパティの値を返す（値がない場合はNone）
    return result[0] if result else None, table, id
