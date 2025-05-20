import numpy

arr = numpy.array([1, 2, 3, 4, 5])

print(arr)

import numpy as np

arr = np.array([1, 2, 3, 4, 5])

print(arr)

import numpy as np

print(np.__version__)


import numpy as np 

arr = np.array([1,2,3,4,5,6,7])

print(arr)

print(type(arr))


import numpy as np 

arr = np.array((1,2,3,4,5,6,7))

print(arr)

print(type(arr))


import numpy as np

arr = np.array(42)

print(arr)


import numpy as np

arr = np.array([1, 2, 3, 4, 5])

print(arr)

import numpy as np

arr = np.array([[1, 2, 3], [4, 5, 6]])

print(arr)

import numpy as np

arr = np.array([[[1, 2, 3], [4, 5, 6]], [[1, 2, 3], [4, 5, 6]]])

print(arr)


import numpy as np 

arr = np.array([1,2,3,4], ndmin=15)

print(arr)

print(type(arr))

print('number of dimensions :', arr.ndim)


#index
import numpy as np

arr = np.array([1, 2, 3, 4])

print(arr[2])

import numpy as np

arr = np.array([[1,2,3,4,5], [6,7,8,9,10]])

print('2nd element on 1st row: ', arr[0, 3])

import numpy as np

arr = np.array([[1,2,3,4,5], [6,7,8,9,10]])

print('5th element on 2nd row: ', arr[1, 4])





import numpy as np

arr = np.array([1, 2, 3, 4, 5, 6, 7])

print(arr[1:5])