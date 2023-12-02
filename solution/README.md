# Intermediate Solution Forms

We annotate two expression formats: an expression tree and Python code.

## Definition of Operators
To annotate DMath, we introduce 50 operators. Their detailed explanation can be found in Appendix B in our [paper]().

## Python Code Conversion
We implement an automatic code generator to convert the expression tree into Python code.

How to use it is as follows.
```
# import `PostfixConverter` class
from converter import PostfixConverter

# Make an instance
converter = PostfixConverter()

# Target solution (expression tree solution form)
solution = "12 53 1 [OP_LIST_ARANGE] 2 [OP_LIST_DIVISIBLE] [OP_SET_DIFFERENCE] [OP_LIST_MEAN]"

# Get an answer and a code
ans, code = converter.convert(solution)

# Print
print(f"Solution: {solution}\n")
print(f"Answer: {ans}\n")
print(f"Code:")
print(code)
```

The output of the code above is as follows.
```
Solution: 12 53 1 [OP_LIST_ARANGE] 2 [OP_LIST_DIVISIBLE] [OP_SET_DIFFERENCE] [OP_LIST_MEAN]

Answer: 33

Code:
var_a = 12
var_b = 53
var_c = 1
list_a = [i for i in range(var_a, var_b + 1, var_c)]
var_d = 2
list_b = []
var_d = int(var_d)
for i in list_a:
    i = int(i)
    if i % var_d == 0:
        list_b.append(i)
list_c = list(set(list_a) - set(list_b))
list_c = [float(i) for i in list_c]
var_e = sum(list_c)/len(list_c)
print(int(var_e))
```