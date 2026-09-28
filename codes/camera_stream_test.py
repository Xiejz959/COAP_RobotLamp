import cv2


stream_url = "tcp://192.168.137.27:8888"
capture = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)

if not capture.isOpened():
    raise RuntimeError(f"无法连接树莓派视频流：{stream_url}")

try:
    while True:
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError("视频流已中断")

        cv2.imshow("Pi Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    capture.release()
    cv2.destroyAllWindows()
