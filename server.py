from flask import Flask, request, send_file
from flask_cors import CORS
import edge_tts
import asyncio
import os
import time
import traceback

app = Flask(__name__)
CORS(app)

def run_sync(coro):
    """Hàm chạy bất đồng bộ an toàn qua new_event_loop độc lập"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

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

        # Sử dụng time.time() thay vì asyncio để tránh hoàn toàn lỗi Thread Event Loop
        output_file = f"temp_{os.getpid()}_{int(time.time() * 1000)}.mp3"
        
        # Gọi sinh âm thanh an toàn
        run_sync(generate_audio(text, output_file))

        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            return {"error": "Không tạo được file âm thanh"}, 500

        response = send_file(output_file, mimetype="audio/mp3", as_attachment=False)
        return response

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
