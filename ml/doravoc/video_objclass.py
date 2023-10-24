import cv2
import os
import ffmpeg
import numpy as np

def load_net(wpath: str, cpath: str):
    """Loads YOLOv3 configuration to OpenCV"""
    return cv2.dnn.readNet(wpath, cpath)

def recognize_video_objects(request_id: str):
    net = load_net(wpath=f'/ml/doravoc/yolo/yolov3.weights', cpath=f'/ml/doravoc/yolo/yolov3.cfg')
    classes = [l.rstrip() for l in open(f'/ml/doravoc/coco.names').readlines()]
    video = cv2.VideoCapture(f'media/{request_id}_rgb.mp4')
    font = cv2.FONT_HERSHEY_PLAIN
    colors = np.random.uniform(0, 255, size=(100, 3))

    new_video = (
    ffmpeg
    .input('pipe:', framerate=15, format='rawvideo', pix_fmt='bgr24', s='640x480', loglevel='error')
    .output(f'media/{request_id}_final.mp4', vcodec='h264', pix_fmt='yuv420p')
    .overwrite_output()
    .run_async(pipe_stdin=True) 
    )
    
    count_of_calls = dict.fromkeys(classes, [0, 0])

    _, img = video.read()
    while img is not None:
        height, width, _ = img.shape

        blob = cv2.dnn.blobFromImage(img, 1 / 255, (416, 416), (0, 0, 0), swapRB=True, crop=False)
        net.setInput(blob)
        output_layers_names = net.getUnconnectedOutLayersNames()
        layerOutputs = net.forward(output_layers_names)

        boxes = []
        confidences = []
        class_ids = []

        for output in layerOutputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    boxes.append([x, y, w, h])
                    confidences.append((float(confidence)))
                    class_ids.append(class_id)

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

        if len(indexes) > 0:
            for i in indexes.flatten():
                x, y, w, h = boxes[i]
                label = str(classes[class_ids[i]])
                
                if label == 'person':               # remove person tracking
                    continue

                
                # counting quantity & confidence
                confidence = str(round(confidences[i], 2))
                count_of_calls[label] = [count_of_calls[label][0] + 1 ,\
                                            count_of_calls[label][1] + round(confidences[i], 2) ]  
                
                color = colors[i]
                cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
                cv2.putText(img, label + " " + confidence, (x, y + 20), font, 2, (255, 255, 255), 2)

        new_video.stdin.write(img)
        _, img = video.read()

    # calculation avg confidence
    for names_label in classes:
        if count_of_calls[names_label][0] != 0:
            count_of_calls[names_label] = [count_of_calls[names_label][0],\
                                            count_of_calls[label][1] / count_of_calls[names_label][0]]
    new_video.terminate()
    video.release()
