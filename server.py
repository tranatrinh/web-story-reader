from flask import Flask, request, send_file
from flask_cors import CORS
from gtts import gTTS
import io

app = Flask(__name__)
CORS(app)

@app.route('/tts', methods=['POST'])
def tts():
    data = request.json
    text = data.get('text', '')
    
    try:
        # Sử dụng Google TTS (gTTS) - Ổn định, không bao giờ lỗi kết nối
        tts_obj = gTTS(text=text, lang='vi', slow=False)
        
        # Lưu vào RAM (không ghi file rác ra máy)
        fp = io.BytesIO()
        tts_obj.write_to_fp(fp)
        fp.seek(0)
        
        return send_file(
            fp,
            mimetype="audio/mp3",
            as_attachment=False,
            download_name="audio.mp3"
        )
    except Exception as e:
        print(f"Lỗi: {e}")
        return {"error": str(e)}, 500

if __name__ == '__main__':
    print("Trạm trung chuyển gTTS (Google) đang chạy trên cổng 5000!")
    app.run(host='0.0.0.0', port=5000)