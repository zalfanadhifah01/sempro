from flask import Flask, render_template, Response, request
import cv2
import dlib

app = Flask(__name__)

@app.route('/')
def index():
    client_ip = request.remote_addr
    return render_template('index.html', client_ip=client_ip)

def gen_frames(ip):
    # Ubah URL berikut dengan URL dari IP Webcam
    video_stream_url = 'http://' + ip + '/video'

    # Memuat model deteksi wajah dari dlib
    detector = dlib.get_frontal_face_detector()

    cap = cv2.VideoCapture(video_stream_url)
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            # Konversi frame ke grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Deteksi wajah
            faces = detector(gray)
            
            # Gambar bounding box di sekitar wajah
            for face in faces:
                x, y, w, h = (face.left(), face.top(), face.width(), face.height())
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Encode frame ke format JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    client_ip = request.remote_addr
    return Response(gen_frames(client_ip), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
