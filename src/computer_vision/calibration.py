"""Camera calibration helper for live card scanning."""
from __future__ import annotations

from collections import Counter, deque
from pathlib import Path


def scan_card(target_label: str | None = None) -> str | None:
    """Scan a physical card using the live inference pipeline.

    Args:
        target_label: Optional card label (e.g., "4H", "QS") to wait for.

    Returns:
        Detected card label when stable, otherwise None.

    Raises:
        RuntimeError: If the camera or model cannot be initialised.
    """
    try:
        import cv2
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("Computer vision dependencies are unavailable.") from exc

    conf_threshold = 0.5
    history_length = 15
    stability_ratio = 0.6
    quit_key = ord("q")
    target = target_label.upper() if target_label else None

    base_dir = Path(__file__).resolve().parent
    model_path = base_dir / "yolov8s_playing_cards.pt"
    model = YOLO(model_path)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Camera failed to open.")

    history = deque(maxlen=history_length)
    last_stable_card = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame, conf=conf_threshold, verbose=False)
            r = results[0]

            detected_cards: list[str] = []
            if r.boxes is not None:
                for cls_id in r.boxes.cls:
                    class_id = int(cls_id.item())
                    card_name = r.names[class_id]
                    detected_cards.append(card_name)

            if detected_cards:
                history.extend(detected_cards)

            stable_card = None
            if len(history) == history_length:
                most_common, count = Counter(history).most_common(1)[0]
                if count >= history_length * stability_ratio:
                    stable_card = most_common

            if stable_card:
                stable_card = stable_card.upper()
                if stable_card != last_stable_card:
                    last_stable_card = stable_card
                if target is None or stable_card == target:
                    return stable_card

            annotated = r.plot()
            cv2.imshow("Playing Card Scanner", annotated)
            key = cv2.waitKey(1) & 0xFF
            if key in {quit_key, ord("Q"), 27}:
                return None
    finally:
        cap.release()
        cv2.destroyAllWindows()

    return None
