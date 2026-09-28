import csv
from datetime import datetime
from pathlib import Path
import time

import cv2
from picamera2 import Picamera2

from person_detection_test import MODEL_PATH, detect_person


DURATION_SECONDS = 60
OUTPUT_PATH = Path.home() / f"person_detection_{datetime.now():%Y%m%d_%H%M%S}.csv"


def main():
    network = cv2.dnn.readNetFromONNX(str(MODEL_PATH))
    camera = Picamera2()
    camera.configure(
        camera.create_video_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            controls={"FrameRate": 20},
        )
    )

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(
            [
                "timestamp",
                "frame",
                "detected",
                "confidence",
                "center_x",
                "center_y",
                "dx",
                "dy",
                "capture_ms",
                "inference_ms",
                "frame_ms",
            ]
        )
        camera.start()
        start = time.monotonic()
        frame_number = 0
        try:
            while time.monotonic() - start < DURATION_SECONDS:
                frame_start = time.perf_counter()
                frame = camera.capture_array("main")
                capture_end = time.perf_counter()
                result = detect_person(frame, network)
                inference_end = time.perf_counter()

                frame_number += 1
                frame_height, frame_width = frame.shape[:2]
                if result is None:
                    values = (0, "", "", "", "", "")
                else:
                    x1, y1, x2, y2, confidence = result
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    values = (
                        1,
                        round(confidence, 4),
                        center_x,
                        center_y,
                        center_x - frame_width // 2,
                        center_y - frame_height // 2,
                    )

                writer.writerow(
                    [
                        datetime.now().isoformat(timespec="milliseconds"),
                        frame_number,
                        *values,
                        round((capture_end - frame_start) * 1000, 2),
                        round((inference_end - capture_end) * 1000, 2),
                        round((inference_end - frame_start) * 1000, 2),
                    ]
                )
        finally:
            camera.stop()

    print(f"完成：{frame_number} 帧，CSV 已保存到 {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
