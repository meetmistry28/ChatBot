import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.animation import FuncAnimation
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox

# Load data
df = pd.read_csv("student_report.csv")

root = tk.Tk()
root.title("3D Student Marks Viewer (Animated)")
root.geometry("1080x720")

input_frame = ttk.Frame(root)
input_frame.pack(pady=10)

year_label = ttk.Label(input_frame, text="Enter Year:")
year_label.pack(side=tk.LEFT, padx=5)
year_entry = ttk.Entry(input_frame)
year_entry.pack(side=tk.LEFT, padx=5)

plot_frame = ttk.Frame(root)
plot_frame.pack(fill=tk.BOTH, expand=True)

def plot_animated_chart():
    year = year_entry.get()
    if not year.isdigit():
        messagebox.showerror("Invalid Input", "Please enter a valid year.")
        return

    year = int(year)
    year_data = df[df["Year"] == year]

    if year_data.empty:
        messagebox.showinfo("No Data", f"No data found for the year {year}.")
        return

    students = year_data["Name"].unique()
    subjects = year_data["Subject"].unique()

    cmap = cm.get_cmap('tab10', len(students))
    student_color_map = {student: cmap(i) for i, student in enumerate(students)}

    x_pos, y_pos, z_pos, dz, colors = [], [], [], [], []

    for i, student in enumerate(students):
        for j, subject in enumerate(subjects):
            record = year_data[(year_data["Name"] == student) & (year_data["Subject"] == subject)]
            if not record.empty:
                x_pos.append(j)
                y_pos.append(i)
                z_pos.append(0)
                dz.append(record.iloc[0]["Final"])
                colors.append(student_color_map[student])

    dx = dy = 0.5
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')

    bars = []

    for i in range(len(x_pos)):
        bar = ax.bar3d([x_pos[i]], [y_pos[i]], [0], dx, dy, [0], color=[colors[i]], shade=True)
        bars.append(bar)

    ax.set_xticks(np.arange(len(subjects)))
    ax.set_xticklabels(subjects, rotation=45)
    ax.set_yticks(np.arange(len(students)))
    ax.set_yticklabels(students)
    ax.set_xlabel("Subjects")
    ax.set_ylabel("Students")
    ax.set_zlabel("Final Marks")
    ax.set_title(f"Final Marks 3D Chart - Year {year}")
    
    def update(frame):
        for i, bar in enumerate(bars):
            bar.remove()
            bars[i] = ax.bar3d([x_pos[i]], [y_pos[i]], [0], dx, dy, [dz[i] * frame / 100], color=[colors[i]], shade=True)
        return bars

    ani = FuncAnimation(fig, update, frames=np.linspace(0, 100, 30), interval=100, blit=False)

    for widget in plot_frame.winfo_children():
        widget.destroy()

    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

plot_button = ttk.Button(input_frame, text="Generate Animated Chart", command=plot_animated_chart)
plot_button.pack(side=tk.LEFT, padx=5)

root.mainloop()