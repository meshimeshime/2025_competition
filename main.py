from flask import Flask, request, render_template, url_for
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from tree_search import embed_message as embed_id, extract_message

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/embed', methods=['POST'])
def embed():
    file = request.files['image']

    # 입력된 정보 수집
    creator = request.form.get('creator', '')
    title = request.form.get('title', '')
    created_at = request.form.get('created_at', '')
    ref_title = request.form.get('ref_title', '')
    ref_creator = request.form.get('ref_creator', '')

    #  압축된 워터마크 메시지 구성
    watermark_message = f"{creator}|{title}|{created_at}|{ref_title}|{ref_creator}"

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        output_filename = 'watermarked_' + filename
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        try:
            embed_id(input_path, output_path, message=watermark_message, alpha=15.0)
        except ValueError as e:
            return f"워터마크 삽입 실패: {e}", 400

        return render_template('result.html',
                               original=filename,
                               watermarked=output_filename,
                               extracted=watermark_message)
    return '파일 업로드 오류', 400

@app.route('/detect', methods=['POST'])
def detect():
    file = request.files.get('image')

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        try:
            extracted = extract_message(input_path)
        except Exception as e:
            print(f"[오류] 워터마크 검출 실패: {e}")
            return f"워터마크 검출 중 오류 발생: {e}", 500

        return render_template('result.html',
                               original=filename,
                               watermarked=None,
                               extracted=extracted)
    return '파일 업로드 오류', 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

