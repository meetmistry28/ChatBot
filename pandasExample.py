import pandas as pd

data = {"Name" : ["John","Eons","Kala"],
        "Age" : [25,22,31],
        "Salary" : [30000,45000,40000]
    }
df = pd.DataFrame(data)
# print(df)



data = pd.read_csv("C:/Users/Admin/Desktop/Sample.csv", encoding="latin1")
# print(data)

data = pd.read_excel("Godown.xlsx")
# print(data)
# print(data.info())

data = pd.read_csv("C:/Users/Admin/Desktop/Sample.csv", encoding="latin1")
# print(data.describe())
# print(data.isnull().sum())

# print(pd.__version__)


data = pd.read_excel("Godown.xlsx")
print(data)
# print(data["Id"].duplicated().sum())
print(data["Id"].duplicated())
print(data.drop_duplicates("Id"))