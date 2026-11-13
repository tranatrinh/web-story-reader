from flask import Flask, request, send_file
from flask_cors import CORS
import edge_tts
import asyncio
import os
import traceback

app = Flask(__name__)
CORS(app)

def run_sync(coro):
    """Hàm hỗ trợ chạy bất đồng bộ an toàn trong môi trường Flask"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Nếu đã có loop đang chạy, tạo loop mới cho tiến trình hiện tại
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        return new_loop.run_until_complete(coro)

async def generate_audio(text, output_file):
    voice = "vi-VN-HoaiMyNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

@app.route('/tts', methods=['POST'])
def tts():
    output_file = None
    try:
        data = request.get_json()
        if not data:
            return {"error": "Invalid JSON"}, 400
            
        text = data.get('text', '').strip()
        if not text:
            return {"error": "Không có nội dung"}, 400

        output_file = f"temp_{os.getpid()}_{int(asyncio.get_event_loop().time())}.mp3"
        
        # Chạy sinh âm thanh bằng hàm bọc an toàn
        run_sync(generate_audio(text, output_file))

        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            return {"error": "Không tạo được file âm thanh"}, 500

        return send_file(output_file, mimetype="audio/mp3", as_attachment=False)

    except Exception as e:
        print("--- LỖI XẢY RA TRONG TTS ---")
        traceback.print_exc()
        return {"error": str(e)}, 500

@app.route('/')
def home():
    return "Server Edge-TTS đang hoạt động hoàn hảo!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
