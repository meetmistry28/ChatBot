import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

df = pd.read_csv("student_report.csv")

student_name = input("Enter student name: ")
year = int(input("Enter year: "))
chart_type = input("Which chart do you want to see? (bar / pie / line): ").strip().lower()
student_data = df[(df["Name"] == student_name) & (df["Year"] == year)]

if student_data.empty:
    print("❌ No data found for that student and year.")
else:
    subjects = student_data["Subject"].values
    ce_array = np.array(student_data[["CE1", "CE2"]])
    final_year_array = np.array(student_data[["Final", "Year"]])

    ce1 = ce_array[:, 0]
    ce2 = ce_array[:, 1]
    final = final_year_array[:, 0]

    x = np.arange(len(subjects))

    if chart_type == "bar":
        fig, ax = plt.subplots(figsize=(12, 6))

        bar_ce1 = ax.bar(x - 0.25, ce1, width=0.25, label='CE1', color='skyblue')
        bar_ce2 = ax.bar(x, ce2, width=0.25, label='CE2', color='lightgreen')
        bar_final = ax.bar(x + 0.25, final, width=0.25, label='Final', color='salmon')

        ax.set_xticks(x)
        ax.set_xticklabels(subjects, rotation=45)
        ax.set_ylim(0, max(np.max(ce1), np.max(ce2), np.max(final)) + 10)
        ax.set_xlabel("Subjects")
        ax.set_ylabel("Marks")
        ax.set_title(f"Marks of {student_name} in {year} (Bar Chart)")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)

        plt.tight_layout()
        plt.show()

    elif chart_type == "pie":
        fig, ax = plt.subplots()
        ax.pie(final, labels=subjects, autopct='%1.1f%%', startangle=140, colors=plt.cm.Set3.colors)
        ax.set_title(f"Final Marks Distribution of {student_name} ({year})")
        plt.show()

    elif chart_type == "line":
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(subjects, ce1, marker='o', label='CE1', color='skyblue')
        ax.plot(subjects, ce2, marker='s', label='CE2', color='lightgreen')
        ax.plot(subjects, final, marker='^', label='Final', color='salmon')

        ax.set_title(f"Marks Trend of {student_name} in {year} (Line Chart)")
        ax.set_xlabel("Subjects")
        ax.set_ylabel("Marks")
        ax.set_ylim(0, max(np.max(ce1), np.max(ce2), np.max(final)) + 10)
        ax.legend()
        ax.grid(True)
        plt.tight_layout()
        plt.show()

    else:
        print("⚠️ Invalid chart type selected.")