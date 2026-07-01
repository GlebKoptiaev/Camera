import cv2
import numpy as np
import math

# Параметры по умолчанию
H_DEFAULT = 0.75
TILT_DEG_DEFAULT = 0
VFOV_DEG = 43.0
FRAME_HEIGHT = 480
D1_DEFAULT = 2.0
D2_DEFAULT = 3.0

mouse_x, mouse_y = -1, -1

def mouse_callback(event, x, y, flags, param):
    global mouse_x, mouse_y
    if event == cv2.EVENT_MOUSEMOVE:
        mouse_x, mouse_y = x, y

def get_fy(frame_height, vfov_deg):
    return (frame_height / 2.0) / math.tan(math.radians(vfov_deg / 2.0))

def get_y_for_distance(distance, H, tilt_deg, fy, cy):
    alpha = math.atan2(H, distance)
    beta = alpha - math.radians(tilt_deg)
    y_rel = fy * math.tan(beta)
    return cy + y_rel

def get_distance_from_y(y, H, tilt_deg, fy, cy):
    y_rel = y - cy
    beta = math.atan2(y_rel, fy)
    alpha = beta + math.radians(tilt_deg)
    if alpha <= 0.0:
        return float('inf')
    return H / math.tan(alpha)

def main():
    global mouse_x, mouse_y

    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)   #индекс камеры
    if not cap.isOpened():
        print("Ошибка: не удалось открыть камеру")
        return

    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    real_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    real_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    print(f"Разрешение камеры: {real_width}x{real_height}")

    cy = real_height / 2.0
    fy = get_fy(real_height, VFOV_DEG)

    cv2.namedWindow("Camera")
    cv2.setMouseCallback("Camera", mouse_callback)

    cv2.namedWindow("Settings")
    cv2.createTrackbar("Height (cm)", "Settings", int(H_DEFAULT*100), 100, lambda x: None)
    cv2.createTrackbar("Tilt (deg)", "Settings", int(TILT_DEG_DEFAULT), 45, lambda x: None)
    cv2.createTrackbar("Dist1 (cm)", "Settings", int(D1_DEFAULT*100), 500, lambda x: None)
    cv2.createTrackbar("Dist2 (cm)", "Settings", int(D2_DEFAULT*100), 500, lambda x: None)

    print("Клавиши: h - высота (мм), t - наклон (град), 1 - дист1 (см), 2 - дист2 (см), q/ESC - выход")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Значения со слайдера
        H_m = cv2.getTrackbarPos("Height (cm)", "Settings") / 100.0
        tilt_deg = cv2.getTrackbarPos("Tilt (deg)", "Settings")
        dist1_m = cv2.getTrackbarPos("Dist1 (cm)", "Settings") / 100.0
        dist2_m = cv2.getTrackbarPos("Dist2 (cm)", "Settings") / 100.0

        y1 = get_y_for_distance(dist1_m, H_m, tilt_deg, fy, cy)
        y2 = get_y_for_distance(dist2_m, H_m, tilt_deg, fy, cy)

        h, w = frame.shape[:2]

        # Рисуем линии
        if 0 <= y1 < h:
            y1_int = int(round(y1))
            cv2.line(frame, (0, y1_int), (w, y1_int), (0, 255, 0), 2)
            cv2.putText(frame, f"{dist1_m:.2f} m", (10, y1_int - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, f"Dist1 ({dist1_m:.2f}m) out of frame", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        if 0 <= y2 < h:
            y2_int = int(round(y2))
            cv2.line(frame, (0, y2_int), (w, y2_int), (0, 0, 255), 2)
            cv2.putText(frame, f"{dist2_m:.2f} m", (10, y2_int - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            cv2.putText(frame, f"Dist2 ({dist2_m:.2f}m) out of frame", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Расстояние курсора
        if 0 <= mouse_x < w and 0 <= mouse_y < h:
            dist_mouse = get_distance_from_y(mouse_y, H_m, tilt_deg, fy, cy)
            cv2.circle(frame, (mouse_x, mouse_y), 5, (255, 255, 0), -1)
            if math.isfinite(dist_mouse):
                text = f"Dist: {dist_mouse:.2f} m"
            else:
                text = "Dist: inf (horizon)"
            cv2.putText(frame, text, (mouse_x + 10, mouse_y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.putText(frame, "h/t/1/2: set values via console | q/ESC: quit",
                    (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Camera", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('q'):
            break

        # Значения с клавиатуры
        try:
            if key == ord('h'):
                val = int(input("Введите высоту камеры (cм, 0-100): "))
                val = max(0, min(100, val))
                cv2.setTrackbarPos("Height (cm)", "Settings", val)
            elif key == ord('t'):
                val = int(input("Введите угол наклона (градусы, 0-45): "))
                val = max(0, min(45, val))
                cv2.setTrackbarPos("Tilt (deg)", "Settings", val)
            elif key == ord('1'):
                val = int(input("Введите дистанцию 1 (см, 0-500): "))
                val = max(0, min(500, val))
                cv2.setTrackbarPos("Dist1 (cm)", "Settings", val)
            elif key == ord('2'):
                val = int(input("Введите дистанцию 2 (см, 0-500): "))
                val = max(0, min(500, val))
                cv2.setTrackbarPos("Dist2 (cm)", "Settings", val)
        except ValueError:
            print("Ошибка: введите целое число.")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
