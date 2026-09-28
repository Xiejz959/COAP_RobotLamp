from pathlib import Path

import cv2
import numpy as np


STREAM_URL = "tcp://192.168.137.27:8888"
MODEL_PATH = Path(__file__).resolve().parent / "models" / "object_detection_nanodet_2022nov.onnx"
INPUT_SIZE = 416
CONFIDENCE_THRESHOLD = 0.35
NMS_THRESHOLD = 0.6
STRIDES = (8, 16, 32)
MEAN = np.array((103.53, 116.28, 123.675), dtype=np.float32)
STD = np.array((57.375, 57.12, 58.395), dtype=np.float32)


def detect_person(frame, network):
    frame_height, frame_width = frame.shape[:2]
    scale = min(INPUT_SIZE / frame_width, INPUT_SIZE / frame_height)
    resized_width = round(frame_width * scale)
    resized_height = round(frame_height * scale)
    left = (INPUT_SIZE - resized_width) // 2
    top = (INPUT_SIZE - resized_height) // 2

    resized = cv2.resize(frame, (resized_width, resized_height))
    image = cv2.copyMakeBorder(
        resized,
        top,
        INPUT_SIZE - resized_height - top,
        left,
        INPUT_SIZE - resized_width - left,
        cv2.BORDER_CONSTANT,
        value=(0, 0, 0),
    )
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32)
    image = (image - MEAN) / STD
    network.setInput(cv2.dnn.blobFromImage(image))
    outputs = network.forward(network.getUnconnectedOutLayersNames())
    class_outputs = {output.shape[1]: output for output in outputs if output.shape[2] == 80}
    box_outputs = {output.shape[1]: output for output in outputs if output.shape[2] == 32}

    boxes = []
    scores = []
    for stride in STRIDES:
        grid_size = INPUT_SIZE // stride
        cells = grid_size * grid_size
        class_output = class_outputs[cells]
        box_output = box_outputs[cells]
        person_scores = class_output.reshape(-1, 80)[:, 0]
        selected = person_scores >= CONFIDENCE_THRESHOLD
        if not np.any(selected):
            continue

        grid_x, grid_y = np.meshgrid(np.arange(grid_size), np.arange(grid_size))
        anchors = np.column_stack((grid_x.ravel(), grid_y.ravel())) * stride
        anchors = anchors + (stride - 1) / 2
        anchors = anchors[selected]

        distributions = box_output.reshape(-1, 4, 8)[selected]
        probabilities = np.exp(distributions - distributions.max(axis=2, keepdims=True))
        probabilities /= probabilities.sum(axis=2, keepdims=True)
        distances = (probabilities * np.arange(8)).sum(axis=2) * stride

        x1 = np.clip(anchors[:, 0] - distances[:, 0], 0, INPUT_SIZE)
        y1 = np.clip(anchors[:, 1] - distances[:, 1], 0, INPUT_SIZE)
        x2 = np.clip(anchors[:, 0] + distances[:, 2], 0, INPUT_SIZE)
        y2 = np.clip(anchors[:, 1] + distances[:, 3], 0, INPUT_SIZE)
        boxes.extend(np.column_stack((x1, y1, x2, y2)).tolist())
        scores.extend(person_scores[selected].tolist())

    if not boxes:
        return None

    boxes_xywh = [[x1, y1, x2 - x1, y2 - y1] for x1, y1, x2, y2 in boxes]
    kept = cv2.dnn.NMSBoxes(boxes_xywh, scores, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
    best = max(np.asarray(kept).reshape(-1), key=lambda index: scores[index])
    x1, y1, x2, y2 = boxes[best]

    return (
        round(np.clip((x1 - left) * frame_width / resized_width, 0, frame_width - 1)),
        round(np.clip((y1 - top) * frame_height / resized_height, 0, frame_height - 1)),
        round(np.clip((x2 - left) * frame_width / resized_width, 0, frame_width - 1)),
        round(np.clip((y2 - top) * frame_height / resized_height, 0, frame_height - 1)),
        scores[best],
    )


def main():
    network = cv2.dnn.readNetFromONNX(str(MODEL_PATH))
    capture = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)
    if not capture.isOpened():
        raise RuntimeError(f"无法连接树莓派视频流：{STREAM_URL}")

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError("视频流已中断")

            frame_height, frame_width = frame.shape[:2]
            frame_center = (frame_width // 2, frame_height // 2)
            cv2.circle(frame, frame_center, 5, (0, 0, 255), -1)

            result = detect_person(frame, network)
            if result is not None:
                x1, y1, x2, y2, confidence = result
                person_center = ((x1 + x2) // 2, (y1 + y2) // 2)
                dx = person_center[0] - frame_center[0]
                dy = person_center[1] - frame_center[1]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.circle(frame, person_center, 5, (0, 255, 0), -1)
                cv2.putText(
                    frame,
                    f"person {confidence:.2f}  dx={dx:+d}  dy={dy:+d}",
                    (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )
            else:
                cv2.putText(
                    frame, "No person", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2
                )

            cv2.imshow("Person Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
