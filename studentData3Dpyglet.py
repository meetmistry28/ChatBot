import pyglet
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

generated_frames = []
current_frame = 0    


# Load data
df = pd.read_csv("student_report.csv")

window = pyglet.window.Window(width=1000, height=700, caption="3D Student Marks Viewer (Animated)")

user_input = ""
instruction_label = pyglet.text.Label("Enter Year and Press ENTER:",
                                      font_size=18,
                                      x=50, y=650, anchor_x='left')

year_label = pyglet.text.Label("",
                               font_size=18,
                               x=50, y=600, anchor_x='left')

def generate_chart(year):
    global generated_frames
    year_data = df[df["Year"] == year]

    if year_data.empty:
        print(f"No data for year {year}")
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
    generated_frames.clear()

    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot(111, projection='3d')

    for i in range(len(x_pos)):
        ax.bar3d([x_pos[i]], [y_pos[i]], [0], dx, dy, [dz[i]], color=[colors[i]], shade=True)

    ax.set_xticks(np.arange(len(subjects)))
    ax.set_xticklabels(subjects, rotation=45)
    ax.set_yticks(np.arange(len(students)))
    ax.set_yticklabels(students)
    ax.set_xlabel("Subjects")
    ax.set_ylabel("Students")
    ax.set_zlabel("Final Marks")
    ax.set_title(f"Final Marks 3D Chart - Year {year}")

    for angle in range(0, 360, 10):  # rotate from 0° to 360° by 10°
        ax.view_init(elev=20, azim=angle)
        filename = f"frame_{angle}.png"
        plt.savefig(filename)
        frame_image = pyglet.image.load(filename)
        generated_frames.append(frame_image)

    plt.close()

@window.event
def on_draw():
    global current_frame  # Moved to top ✅
    window.clear()
    instruction_label.draw()
    year_label.draw()
    if generated_frames:
        generated_frames[current_frame].blit(150, 50, width=700, height=500)

@window.event
def on_text(text):
    global user_input
    if text.isdigit():
        user_input += text
        year_label.text = f"Year: {user_input}"

@window.event
def on_key_press(symbol, modifiers):
    global user_input
    if symbol == pyglet.window.key.ENTER:
        if user_input:
            generate_chart(int(user_input))
            user_input = ""

def update(dt):
    global current_frame
    if generated_frames:
        current_frame = (current_frame + 1) % len(generated_frames)

pyglet.clock.schedule_interval(update, 0.1)  # 10 frames per second

pyglet.app.run()