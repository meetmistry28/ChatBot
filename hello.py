print("Hello Universe")



if 5 > 2:
 print("Five is greater than two!") 
if 5 > 2:
        print("Five is greater than two!") 


x = 5
y = "Hello, World!"

print(x)
print(y)

x = 4
x = "Sally"
print(x)


x = str(8)    
y = int(8)    
z = float(8)  

print(x)
print(y)
print(z)

#Python Variables

x = 5
y = "John"
print(type(x))
print(type(y))

x = "John Bhai"
print(x)
print(type(x))

x = 'John Bhai'
print(x)
print(type(x))

a = 4
A = "Sally"

print(a)
print(A)

x, y, z = "Orange", "Banana", "Cherry"

print(x) 
print(y)
print(z)


x = y = z = "Orange"
print(x)
print(y)
print(z)


fruits = ["apple", "banana", "cherry"]
x, y, z = fruits

print(x)
print(y)
print(z)

x = "Python is awesome"
print(x)

x = "awesome"

def myFunc():
    print("Python Is Well " + x)

myFunc()

x = "awesome"

def myfunc():
  x = "fantastic"
  print("Python is " + x)

myfunc()

print("Python is " + x)

def myfunc():
  global x
  x = "fantastic"

myfunc()

print("Python is " + x)


# Python Data Types
# 1. Text Type:	str
# 2. Numeric Types:	int, float, complex
# 3. Sequence Types:	list, tuple, range
# 4. Mapping Type:	dict
# 5. Set Types:	set, frozenset
# 6. Boolean Type:	bool
# 7. Binary Types:	bytes, bytearray, memoryview
# 8. None Type:	NoneType

x = 5
print(type(x))

# Setting the Data Type
# In Python, the data type is set when you assign a value to a variable:

# Example	Data Type	Try it

# 1. x = "Hello World"	str	
# 2. x = 20	int	
# 3. x = 20.5	float	
# 4. x = 1j	complex	
# 5. x = ["apple", "banana", "cherry"]	list	
# 6. x = ("apple", "banana", "cherry")	tuple	
# 7. x = range(6)	range	
# 8. x = {"name" : "John", "age" : 36}	dict	
# 9. x = {"apple", "banana", "cherry"}	set	
# 10. x = frozenset({"apple", "banana", "cherry"})	frozenset	
# 11. x = True	bool	
# 12. x = b"Hello"	bytes	
# 13. x = bytearray(5)	bytearray	
# 14. x = memoryview(bytes(5))	memoryview	
# 15. x = None	NoneType



# Setting the Specific Data Type
# If you want to specify the data type, you can use the following constructor functions:

x = str("Hello World")	#str	
x = int(20)	#int	
x = float(20.5)	#float	
x = complex(1j)	#complex	
x = list(("apple", "banana", "cherry"))	#list	
x = tuple(("apple", "banana", "cherry"))	#tuple	
x = range(6)	#range	
x = dict(name="John", age=36)	#dict	
x = set(("apple", "banana", "cherry"))	#set	
x = frozenset(("apple", "banana", "cherry"))	#frozenset	
x = bool(5)	#bool	
x = bytes(5)	#bytes	
x = bytearray(5)	#bytearray	
x = memoryview(bytes(5))	#memoryview

print(x)
print(type(x))