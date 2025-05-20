import pandas as pd

subjects = ['Maths', 'English', 'Physics', 'Computer', 'History', 'Science','Chemistry','Biology']
years = [2021, 2022, 2023, 2024, 2025]

students = []
for i in range(7):
    name = input(f"Enter name of student {i+1}: ")
    students.append(name)

rows = []

for student in students:
    for year in years:
        for subject in subjects:
            print(f"\nEnter marks for {student} - {year} - {subject}:")
            ce1 = int(input("  CE1 (out of 25): "))
            ce2 = int(input("  CE2 (out of 25): "))
            final = int(input("  Final (out of 50): "))

            total = ce1 + ce2 + final

            if total >= 90:
                grade = 'A+'
            elif total >= 80:
                grade = 'A'
            elif total >= 70:
                grade = 'B'
            elif total >= 60:
                grade = 'C'
            elif total >= 50:
                grade = 'D'
            else:
                grade = 'F'

            rows.append([student, year, subject, ce1, ce2, final, total, grade])

df = pd.DataFrame(rows, columns=["Name", "Year", "Subject", "CE1", "CE2", "Final", "Total", "Grade"])

df.to_csv("student_report.csv", index=False)
print("✅ Data saved to 'student_report.csv'")
