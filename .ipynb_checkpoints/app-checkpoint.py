from flask import Flask, request, jsonify

# Flask 애플리케이션 객체 만들기
app = Flask(__name__)

@app.route('/')
def index():
    return "서버 잘 작동 중이에요!"

@app.route('/detect', methods=['POST'])
def detect():
    file = request.files['image']
    # 워터마크 분석 로직 대신 예시
    return jsonify({"creator": "김재준", "ai": False})

# 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0')
