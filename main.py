import requests
import psycopg2.extras
import psycopg2


def notion_input(token, database, property, msg):
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
                            "content": msg
                        }
                    }
                ]
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
