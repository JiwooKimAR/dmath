from converter import PostfixConverter

converter = PostfixConverter()

# solution = "12 53 1 [OP_LIST_ARANGE] 2 [OP_LIST_DIVISIBLE] [OP_SET_DIFFERENCE] [OP_LIST_MEAN]"
solution = "0.72 0.46 [OP_SUB] 2 [OP_DIV]"
ans, code = converter.convert(solution)

print(f"Solution: {solution}\n")
print(f"Answer: {ans}\n")
print(f"Code:")
print(code)