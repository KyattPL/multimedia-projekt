import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk

if __name__ == "__main__":
    # Connect to the SQLite database
    conn = sqlite3.connect('face_recognition_db.db')
    cursor = conn.cursor()


    def update_treeview():
        data = fetch_data()

        # Clear the existing data in the Treeview
        for item in tree.get_children():
            tree.delete(item)

        # Populate the Treeview with the new data
        for row in data:
            tree.insert("", "end", values=row)

        # Schedule the update_treeview function to be called after a delay (e.g., every 1000 milliseconds)
        root.after(1000, update_treeview)


    # Function to fetch data from the database
    def fetch_data():
        try:
            cursor.execute("SELECT * FROM face_recognition_log")
            data = cursor.fetchall()
            return data
        except Exception as e:
            messagebox.showerror("Error", f"Error fetching data from the database: {e}")
            return []

    # Function to display the selected record
    def display_record(selected_item):
        if selected_item:
            record_id = selected_item[0]
            timestamp = selected_item[1]
            recognized = "Yes" if selected_item[2] else "No"
            name = selected_item[3]
            image_filename = selected_item[4]

            # Create a new window for displaying the record
            window = tk.Toplevel(root)
            window.title(f"Record ID: {record_id}")

            # Display timestamp
            timestamp_label = tk.Label(window, text=f"Timestamp: {timestamp}")
            timestamp_label.pack()

            # Display recognition status
            recognized_label = tk.Label(window, text=f"Recognized: {recognized}")
            recognized_label.pack()

            name_label = tk.Label(window, text=f"Name: {name}")
            name_label.pack()

            # Load and display the image
            try:
                img = Image.open(image_filename)
                img.thumbnail((300, 300))  # Resize the image
                img = ImageTk.PhotoImage(img)
                image_label = tk.Label(window, image=img)
                image_label.image = img  # Keep a reference to prevent garbage collection
                image_label.pack()
            except Exception as e:
                messagebox.showerror("Error", f"Error loading image: {e}")

    # Function to handle item selection in the treeview
    def on_select(event):
        item = tree.selection()
        if item:
            selected_item = tree.item(item, 'values')
            display_record(selected_item)

    # Create the main window
    root = tk.Tk()
    root.title("Face Recognition Database Viewer")

    # Create a Treeview widget to display the data
    tree = ttk.Treeview(root, columns=("ID", "Timestamp", "Recognized", "Name"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Timestamp", text="Timestamp")
    tree.heading("Recognized", text="Recognized")
    tree.heading("Name", text="Name")
    tree.pack(pady=10)

    # Populate the Treeview with data from the database
    data = fetch_data()
    for row in data:
        tree.insert("", "end", values=row)

    # Bind the on_select function to the treeview selection event
    tree.bind('<ButtonRelease-1>', on_select)

    update_treeview()

    # Run the Tkinter main loop
    root.mainloop()

    # Close the database connection when the application exits
    conn.close()
