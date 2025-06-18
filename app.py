from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "data.db"

# DB 초기화 함수
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS compliments (
            name TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

@app.route("/webhook", methods=["POST"])
def webhook():
    print("[DEBUG] /webhook 호출됨", flush=True)
    data = request.get_json()
    utterance = data.get('userRequest', {}).get('utterance', '').strip()
    params = data.get('action', {}).get('params', {})
    name = params.get('이름') or utterance.replace("/칭찬", "").strip()

    if utterance.startswith("/칭찬 "):
        name = utterance.replace("/칭찬", "").strip()
        print(f"[DEBUG] /칭찬 요청 감지됨 - name: {name}")
        if name:
            add_compliment(name)
        return empty_response()  # 사용자에게 응답하지 않음

    elif utterance == "/칭찬종합":
        print("[DEBUG] /칭찬종합 요청 감지됨")
        result = get_summary()
        print(f"[DEBUG] 응답 길이: {len(result)}")
        return kakao_response(result)

    else:
        return kakao_response("이 챗봇은 `/칭찬` 또는 `/칭찬종합` 명령에만 응답합니다.")

# 사용자에게 응답하는 함수 (카카오 메시지 형식)
def kakao_response(text):
    if not text or not isinstance(text, str):
        text = "응답 오류가 발생했습니다. 다시 시도해주세요."

    if len(text) > 1000:
        text = text[:990] + "\n(이하 생략...)"

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

# 사용자에게 아무 메시지도 보내지 않음
def empty_response():
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": " "  # 공백 문자열이라도 넣어줘야 schema 만족
                    }
                }
            ]
        }
    })

# 칭찬 수 증가 처리
def add_compliment(name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO compliments (name, count) VALUES (?, 0)", (name,))
    cur.execute("UPDATE compliments SET count = count + 1 WHERE name = ?", (name,))
    conn.commit()
    conn.close()

# 칭찬 전체 순위 출력
def get_summary():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name, count FROM compliments ORDER BY count DESC")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "아직 아무도 칭찬받지 않았어요 😅"

    lines = [f"{i+1}. {name} - {count}회" for i, (name, count) in enumerate(rows)]
    result = "📊 칭찬 종합 결과!\n" + "\n".join(lines)

    if len(result) > 990:
        result = result[:990] + "\n(이하 생략...)"

    return result

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
