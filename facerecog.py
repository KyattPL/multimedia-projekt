import face_recognition
import cv2
import numpy as np
import requests
from time import perf_counter
import sqlite3
from datetime import datetime
import os

DEBOUNCE_TIME = 3

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS face_recognition_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            recognized BOOLEAN,
            name TEXT,
            image_link TEXT
        )
    ''')
    conn.commit()


# Funkcja do dodawania rekordu do bazy danych
def add_record(conn, recognized, name, image_link):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO face_recognition_log (timestamp, recognized, name, image_link) VALUES (?, ?, ?, ?)",
                   (timestamp, recognized, name, image_link))
    conn.commit()


def log(conn):
    cursor = conn.cursor()
    # Wyświetl zawartość tabeli face_recognition_log
    cursor.execute("SELECT * FROM face_recognition_log")
    rows = cursor.fetchall()
    print("\nZawartość tabeli face_recognition_log:")
    for row in rows:
        print(row)

if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.realpath(__file__))
    db_file_path = os.path.join(current_directory, 'face_recognition_db.db')

    # Połączenie z bazą danych SQLite w pliku (utworzy nowy plik, jeśli nie istnieje)
    conn = sqlite3.connect(db_file_path)
    # Połączenie z bazą danych SQLite w pliku

    # Utwórz tabelę w bazie danych, jeśli nie istnieje
    create_table(conn)
    # Get a reference to webcam #0 (the default one)
    video_capture = cv2.VideoCapture(0)

    # Load a sample picture and learn how to recognize it.
    dorian_image = face_recognition.load_image_file("michal.jpg")
    dorian_face_encoding = face_recognition.face_encodings(dorian_image)[0]

    kajet_image = face_recognition.load_image_file("kajet.jpg")
    kajet_face_encoding = face_recognition.face_encodings(kajet_image)[0]

    # michal_image = face_recognition.load_image_file("michal.jpg")
    # michal_face_encoding = face_recognition.face_encodings(michal_image)[0]

    # Create arrays of known face encodings and their names
    known_face_encodings = [
        dorian_face_encoding,
        kajet_face_encoding
        # michal_face_encoding
    ]
    known_face_names = [
        "Dorian B.",
        "Kajet P."
    ]

    # Initialize some variables
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    timestep = None

    while True:
        # Grab a single frame of video
        ret, frame = video_capture.read()

        # Only process every other frame of video to save time
        if process_this_frame:
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]
            code = cv2.COLOR_BGR2RGB
            rgb_frame = cv2.cvtColor(rgb_small_frame, code)

            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"

                # If a match was found in known_face_encodings, just use the first one.
                # if True in matches:
                #     first_match_index = matches.index(True)
                #     name = known_face_names[first_match_index]

                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                face_names.append(name)

        process_this_frame = not process_this_frame

        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            if timestep is None:
                timestep = perf_counter()
            else:
                break

            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"log/{timestamp_str}.jpg"
            # Utwórz nazwę pliku z timestampem
            cv2.imwrite(filename, frame)

            if name == "Unknown":
                cv2.imwrite("newFrame.jpg", frame)

                # Dodaj rekord do bazy danych
                add_record(conn, False, name, filename)

                requests.put("https://ntfy.sh/multimedia-projekt",
                            data=open("./newFrame.jpg", "rb"),
                            headers={
                                "Filename": "newFrame.jpg"
                            })
            else:
                add_record(conn, True, name, filename)

            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        if face_locations == []:
            if timestep is not None and perf_counter() - timestep > DEBOUNCE_TIME:
                timestep = None
        else:
            timestep = perf_counter()

        # Display the resulting image
        cv2.imshow('Video', frame)
        log(conn)

        cv2.waitKey(1000)
        # # Hit 'q' on the keyboard to quit!
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

    # Release handle to the webcam
    # video_capture.release()
    # cv2.destroyAllWindows()
