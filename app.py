from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "data.db"

# DB 초기화 함수
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS compliments (name TEXT PRIMARY KEY, count INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    utterance = data.get('userRequest', {}).get('utterance', '').strip()

    if utterance.startswith("/칭찬 "):
        name = utterance.replace("/칭찬", "").strip()
        if not name:
            return kakao_response("칭찬할 이름을 입력해주세요.")
        result = add_compliment(name)
        return kakao_response(result)

    elif utterance == "/칭찬종합":
        result = get_summary()
        return kakao_response(result)

    else:
        return kakao_response("올바른 명령어를 입력해주세요.\n예: /칭찬 민준 또는 /칭찬종합")

def kakao_response(text):
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": text
                    }
                }
            ]
        }
    })

def add_compliment(name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO compliments (name, count) VALUES (?, 0)", (name,))
    cur.execute("UPDATE compliments SET count = count + 1 WHERE name = ?", (name,))
    conn.commit()
    cur.execute("SELECT count FROM compliments WHERE name = ?", (name,))
    count = cur.fetchone()[0]
    conn.close()
    return f"🎉 {count}번째 칭찬\n😀 {name} 칭찬해요!"

def get_summary():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name, count FROM compliments ORDER BY count DESC")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return "아직 아무도 칭찬받지 않았어요 😅"
    return "📊 칭찬 종합 결과!\n" + "\n".join([f"{i+1}. {name} - {count}회" for i, (name, count) in enumerate(rows)])

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
