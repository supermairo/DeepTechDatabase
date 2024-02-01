import requests
import psycopg2.extras
import psycopg2
import json
# from openai import OpenAI

# initialize
keys = json.load(open("secrets.json", "r"))
api_key = keys["API_KEYS"]["OPENAI"]
token = keys["notion"]["token"]

# F0


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

    # 編集しようとしているプロパティのデータ型を確認
    url = f"https://api.notion.com/v1/databases/{database}"
    db_info = requests.get(url, headers=headers).json()
    property_type = db_info["properties"][property]["type"]

    # データ型に応じたJSONの作成
    if property_type == "rich_text":
        property_json = {
            "rich_text": [{"text": {"content": msg}}]
        }
    elif property_type == "title":
        property_json = {
            "title": [{"text": {"content": msg}}]
        }

    if (result["results"]):
        # この値がある場合は更新する
        page_id = result["results"][0]["id"]
        url = f"https://api.notion.com/v1/pages/{page_id}"
        data = {
            "properties": {
                property: property_json,
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
                property: property_json,
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

# F1


def generate_pitch(pj_id):
    # データベースから対応する項目を抽出
    desc = get_value_from_db('"SocialIssue"', pj_id, "DESCRIPTION", keys)[0]
    bottle = get_value_from_db('"SocialIssue"', pj_id, "BOTTLENECK", keys)[0]
    approach = get_value_from_db('"Project"', pj_id, "APPROACH", keys)[0]
    novelty = get_value_from_db('"Project"', pj_id, "NOVELTY", keys)[0]
    title = get_value_from_db('"Project"', pj_id, "TITLE", keys)[0]

    # promptの作成
    prompt = (
        f"下記の要件を満たしながら、{title}というプロジェクトの概要説明文を生成してください。\n\n"
        "1. 下記の4項目の情報に基づく\n"
        f"取り組む社会課題の概要\n{desc}\n\n"
        f"解決に至らないボトルネック\n{bottle}\n\n"
        f"本プロジェクトの取る解決のアプローチ\n{approach}\n\n"
        f"このアプローチの新規性\n{novelty}\n\n"
        "2. 形式はmarkdownとする\n"
        "3. 下記の構成で文章を記述する\n"
        "見出し1: [適切な見出し]\n"
        "本文1: 注目する社会課題（200文字程度）\n"
        "見出し2: [適切な見出し]\n"
        "本文2: 本プロジェクトが提案する解決方法（200文字程度）\n\n"
        "以上"
    )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt},
        ]
    )
    draft = response.choices[0].message.content
    return draft

# F4


def getProject():
    # GraphQLのクエリを定義
    query = """
    {
    Project(limit: 1, where: { post: { _contains: { slack: "" } }, visibility: { _eq: "public" } }
    ) {
        title
        group_name
        country
        intro
        url
    }
    }
    """
    # GraphQLのエンドポイント
    url = keys["api_urls"]["hasura"]
    # ヘッダーの設定
    headers = {
        "Content-Type": "application/json",
        "x-hasura-admin-secret": keys["API_KEYS"]["HASURA"]
    }
    # リクエストの送信
    response = requests.post(url, headers=headers, json={"query": query})
    # 結果の取得
    data = response.json()
    # 結果を返す
    return data["data"]["Project"][0]
