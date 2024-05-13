import cv2
import numpy as np
import json
import os
import pandas as pd
from ultralytics import YOLO
import sys
mode = None  

drawing = False
points = []
area_map = {}
current_name = 0
delete_mode = False
delete_area = None
insert_mode = False
shape_mode = None
saved=False
if len(sys.argv) != 2:
    print("Usage: python edit_and_test.py <video_path>")
    sys.exit(1)

video_path = sys.argv[1]


if os.path.exists('area_map.json'):
    with open('area_map.json', 'r') as f:
        area_map = json.load(f)

cap = cv2.VideoCapture(video_path)
def edit(event, x, y, flags, params):
    global points, drawing, delete_mode, delete_area, insert_mode, shape_mode
    if delete_mode:
        if event == cv2.EVENT_LBUTTONDOWN:
            for name, points_array in area_map.items():
                points_array = np.array(points_array, np.int32).reshape((-1, 2))
                if cv2.pointPolygonTest(points_array, (x, y), False) >= 0:
                    del area_map[name]
                    delete_area = None
                    break
    elif insert_mode:
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            points = [(x, y)]
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                points.append((x, y))
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            if shape_mode == 'r':
                x1, y1 = points[0]
                x2, y2 = points[-1]
                points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            # current_name = input("Enter the area name or press Enter to auto-assign: ")
            # if current_name == "":
            current_name = len(area_map) + 1
            area_map[str(current_name)] = [int(pt) for p in points for pt in p]  
            points = []  

def edit_mode():
    global mode, points, drawing, delete_mode, delete_area, insert_mode, shape_mode,saved
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (1280, 720))
        for name, points_array in area_map.items():
            if len(points_array) > 0: 
                points_array = np.array(points_array, np.int32).reshape((-1, 2))
                cv2.polylines(frame, [points_array], True, (255, 255, 255), 2)
                cv2.putText(frame, str(name), tuple(points_array[0]), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        if insert_mode:
            if shape_mode !="r":
                cv2.putText(frame, "Press r to Chose Rectrangle Bouding Box or simple draw a plygon", (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            elif shape_mode =="r":
                cv2.putText(frame, "You are in the Rectrangle to Chose the Area to draw", (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                cv2.putText(frame, "Press P disabled the Rectrangle Mode", (10, frame.shape[0] - 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, "Press d to Chose the Delete mode", (10, frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, "Press s to save the Bounding Box ", (40, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
             

        if delete_mode:
            cv2.putText(frame, "Click on the polygon which you want to delete", (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, "Press i to Chose the Insert mode", (10, frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, "Press s to save the remaining Bbox ", (40, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        if delete_area is not None:
            cv2.polylines(frame, [delete_area], True, (0, 0, 255), 2)
        if not delete_mode and not insert_mode:
            cv2.putText(frame, "Press t  to Switch to Test  mode", (10, frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, "Press i or d  to Switch to Insert mode or Delete mode", (10, frame.shape[0] - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        if (saved and delete_mode) or (saved and insert_mode):
            cv2.putText(frame, "The Bouding Box has been saved", (10, frame.shape[0] - 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            saved=False

        cv2.imshow('FRAME', frame)
        cv2.setMouseCallback("FRAME", edit)
        key = cv2.waitKey(30) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):  
            with open('area_map.json', 'w') as f:
                saved=True
                json.dump(area_map, f)
            print("Area map saved.")
        elif key == ord('d'):
            delete_mode = not delete_mode
            insert_mode = False
            if delete_mode:
                print("Delete mode enabled. Click on an area to delete.")
            else:
                print("Delete mode disabled.")
                delete_area = None
        elif key == ord('i'):
            insert_mode = not insert_mode
            delete_mode = False
            shape_mode = None
            if insert_mode:
                print("Insert mode enabled. Press 'r' to draw a rectangle, or click to draw a polygon.")
            else:
                pass
        elif key == ord("t"):
            print("Insert mode disabled. Switching to test mode.")
           
            test_mode() 
        elif key == ord('r'):
            shape_mode = 'r'
            print("Rectangle mode enabled. Click and drag to draw a rectangle.")
        elif key==ord('p'):
            shape_mode=None
            print("Rectangle mode disabled. Click and drag to draw a Polygons.") 

    cap.release()
    cv2.destroyAllWindows()


def test_mode():
    global mode
    # mode = "test"
    my_file = open("coco.txt", "r")
    data = my_file.read()
    class_list = data.split("\n")
    model = YOLO('yolov9c.pt')
    filter_class = ["car", "truck"]

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        frame = cv2.resize(frame, (1280, 720))
        # frame_copy = frame.copy()
        results = model.predict(frame)
        a = results[0].boxes.data.cpu().numpy()
        px = pd.DataFrame(a).astype("float")
        list_1 = []
        for index, row in px.iterrows():
            x1 = int(row[0])
            y1 = int(row[1])
            x2 = int(row[2])
            y2 = int(row[3])
            d = int(row[5])
            cx = int(x1 + x2) // 2
            cy = int(y1 + y2) // 2
            c = class_list[d]

            if c in filter_class:
                list_1.append((cx, cy))
                if c== "car":
                 cv2.putText(frame, "Car",(cx,cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
                #  cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,255),2)
                if c== "truck":
                 cv2.putText(frame, "Truck",(cx,cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                #  cv2.rectangle(frame,(x1,y1),(x2,y2),(255,255,0),2)
            else:
                pass
        in_counter = []
        for name, points_array in area_map.items():
            points_array = np.array(points_array, np.int32).reshape((-1, 2))
            cv2.polylines(frame, [points_array], True, (0, 255, 0), 2)
            cv2.putText(frame, str(name), tuple(points_array[0]), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            for center in list_1:
                results = cv2.pointPolygonTest(points_array, (center[0], center[1]), False)
                if results >= 0:
                    cv2.polylines(frame, [points_array], True, (0, 0, 255), 2)
                    in_counter.append(center[0])

        car_count = len(in_counter)
        out_counter = len(area_map) - car_count
        cv2.putText(frame, "Occupied=" + str(car_count), (40, 60), cv2.FONT_HERSHEY_TRIPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "Free=" + str(out_counter), (40, 100), cv2.FONT_HERSHEY_TRIPLEX, 1, (255, 255, 255), 2)
        if mode=="init_test":
            cv2.putText(frame, "Press q to Exit", (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        if mode=="test":
            cv2.putText(frame, "Press q to return to edit mode", (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow('FRAME', frame)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break


if __name__ == "__main__":
    while True:
        print("Select mode:")
        print("1. Edit mode")
        print("2. Test mode")
        print("q. Quit")
        mode_choice = input("Enter your choice (1 or 2): ")
        if mode_choice == "1":
            mode="test"
            edit_mode()
            break
        elif mode_choice == "2":
            mode='init_test'
            test_mode()
            break
        elif mode_choice == "q":
            break
cap.release()
cv2.destroyAllWindows()