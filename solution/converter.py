import itertools
import math
from string import ascii_lowercase, ascii_uppercase

from functools import wraps
import errno
import os
import signal

class TimeoutError(Exception):
    pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator

class StacknNames: # class comprises 2 stacks
    def __init__(self):
        self.content_stack = [] # stack for saving values
        self.name_stack = [] # stack for saving the vairable names
    def pop(self):
        if len(self.content_stack) < 1:
            return None
        return self.content_stack.pop(), self.name_stack.pop()

    def push(self, item, new_name):
        self.content_stack.append(item)
        self.name_stack.append(new_name) # New item is always saved with new variable names

    def size(self):
        return len(self.content_stack)


class PostfixConverter():
    def __init__(self):
        # operator_dic = {operator:['what it does', '# of input', 'type of operator', '# of operand created', '# of lists created']}
        self.operator_dic = {
            '[OP_ADD]':['+', 2, 'infix', 1, 0],                         
            '[OP_SUB]':['-', 2, 'infix', 1, 0], 
            '[OP_DIV]':['/', 2, 'infix', 1, 0],        
            '[OP_MUL]':['*', 2, 'infix', 1, 0],              
            '[OP_FDIV]':['//', 2, 'infix', 1, 0],     
            '[OP_MOD]':['%', 2, 'infix', 1, 0],  
            '[OP_POW]':['**', 2, 'infix', 1, 0],
            '[OP_CEIL]':['int', 2, 'function', 1, 0],
            '[OP_FLOOR]':['int', 2, 'function', 1, 0],
            '[OP_ROUND]':['round', 2, 'function', 1, 0],
            '[OP_ABS]':['abs', 1, 'function', 1, 0],
            '[OP_COMB]':['math.comb', 2, 'function', 1, 0],
            '[OP_PERM]':['math.perm', 2, 'function', 1, 0],
            '[OP_GCD]': ['math.gcd', 2, 'function'],
            '[OP_LCM]': ['', 2, 'function'],
            '[OP_LIST_SOL]':['',0,'list', 1, 0],
            '[OP_LIST_EOL]':['',0,'list', 99, 1],
            '[OP_LIST_ARANGE]':['', 3, 'list_function'],
            '[OP_LIST_ODD]':['', 2, 'list_function'],
            '[OP_LIST_EVEN]':['', 2, 'list_function'],
            '[OP_LIST_POP]':['',0,'list', 0 , -1],
            '[OP_LIST_GET_PERM]':['', 2, 'list_function'],
            '[OP_LIST_GET_PRODUCT]':['', 2, 'list_function'],
            '[OP_GEN_POSSIBLE_LIST]':['',1,'function_special'],
            '[OP_LIST_MAX]':['max',2,'list_function'],
            '[OP_LIST_MIN]':['min',2,'list_function'],
            '[OP_LIST_SUM]':['sum',1,'list_function'],
            '[OP_LIST_LEN]':['len',1,'list_function'],
            '[OP_LIST_GET]':['', 2, 'list_function'],
            '[OP_LIST_INDEX]':['', 2, 'list_function'],
            '[OP_LIST_FIND_NUM]':['',2,'list_function'],
            '[OP_LIST_MORE]':['', 2, 'list_function'],
            '[OP_LIST_LESS]':['', 2, 'list_function'],
            '[OP_LIST_MORE_EQUAL]':['', 2, 'list_function'],
            '[OP_LIST_LESS_EQUAL]':['', 2, 'list_function'],
            '[OP_SET_UNION]':['', 2, 'list_function'],
            '[OP_SET_DIFFERENCE]':['', 2, 'list_function'],
            '[OP_SET_INTERSECT]':['', 2, 'list_function'],
            '[OP_LIST_DIVISIBLE]':['',2,'list_function'],
            '[OP_LIST_DIVIDE_AND_REMAIN]':['',3,'list_function',0,1],
            '[OP_LIST_GET_DIVISOR]': ['', 1, 'list_function'],
            '[OP_LIST_COND_MAX_MIN]':['comp',2,'list_function'],
            '[OP_LIST2NUM]':['',1,'list_function'],
            '[OP_NUM2LIST]':['', 1, 'list_function'],
            '[OP_LIST_NUM2SUM]':['',1,'list_function',0,1],
            '[OP_LIST_SEARCH_FIXED_DIGIT]':['',3,'list_function',0,1],
            '[OP_DIGIT_UNK_SOLVER]':['',2,'function_special',1, 0],
            '[OP_LIST_FIND_UNK]':['',3,'list_function'],
            '[OP_NUM_UNK_SOLVER]':['',2,'function_special',1, 0],
            '[OP_LIST_MEAN]':['average',1,'list_function'],
        }

        self.operand_names = ['var_'+c for c in ascii_lowercase] + ['var_'+c for c in ascii_uppercase] + ['var_'+c for c in '0123456789']
        for c in ascii_lowercase:
            for d in ascii_lowercase:
                self.operand_names.append(f'var_{c}{d}')
        self.list_names = ['list_'+c for c in ascii_lowercase]

        self.operand_stack = StacknNames()
        self.list_stack = StacknNames()
        self.code_string = ''

        # convert number to int type if possible, or make it as float type
        self.intifint = lambda x: int(x) if int(x) == self.to_float(x) else self.to_float(x)
    
    def to_float(self, frac_str): # Process the fractional input string
        try:
            return float(frac_str)
        except ValueError:
            num, denom = frac_str.split('/')
            try:
                leading, num = num.split(' ')
                whole = float(leading)
            except ValueError:
                whole = 0
            frac = float(num) / float(denom)
            return whole - frac if whole < 0 else whole + frac


    def is_number(self, value):
        try:
            self.to_float(value)
            return True
        except ValueError:
            return False

    def is_fraction(self, value):
        try:
            float(value)
            return False
        except:
            return True

    # convert function
    @timeout(10)
    def convert(self, postfix_eq):
        # Core function: Generate code given postfix equation
        self.__init__()
        operand_operator_list = postfix_eq.split()
        for n, i in enumerate(operand_operator_list):
            if i in self.operator_dic: # if operator
                operator_name = i
                operator_info = self.operator_dic[i]
                
                # list exceptional functions - init
                if operator_info[2] == 'list':
                    if i == '[OP_LIST_SOL]':
                        self.operand_stack.push('SOL', 'SOL')
                    elif i == '[OP_LIST_EOL]':
                        new_list = []
                        list_name = self.list_names.pop(0)
                        self.code_string += '{}= []\n'.format(list_name)
                        while True:
                            element, var_name = self.operand_stack.pop()
                            if element == 'SOL':
                                new_list.reverse()
                                self.code_string += '{}.reverse()\n'.format(list_name)
                                self.list_stack.push(new_list, list_name) # Keep the stack of lists seperate
                                break
                            if '/' in str(element):
                                element = eval(str(element))
                            new_list.append(element)
                            self.code_string += 'if "/" in str({var_name}):\n    {var_name} = eval(str({var_name}))\n{list_name}.append({var_name})\n'.format(list_name=list_name, var_name=var_name)
                    
                    elif i == '[OP_LIST_POP]':
                        self.list_stack.pop()
                    else:
                        print("not defined")
                    
                # Operators in infix form: + - * / // % **
                elif operator_info[2] == 'infix':
                    b, b_name = self.operand_stack.pop()
                    a, a_name = self.operand_stack.pop()

                    var_name = self.operand_names.pop(0)
                    self.code_string += '{var} = {a} {operator} {b}\n'.format(var = var_name, a=a_name, operator=operator_info[0], b=b_name)
                    intermediate_eq = "{}".format(str(a) + operator_info[0] +str(b))
                    intermediate = eval(intermediate_eq)
                    self.operand_stack.push(intermediate, var_name)

                # function: math.perm(num1, num2) etc.
                elif operator_info[2] == 'function':
                    var_name = self.operand_names.pop(0)
                    if operator_info[1]==1:
                        a, a_name = self.operand_stack.pop()
                        intermediate_eq = str(operator_info[0]+'('+str(a)+')')
                        intermediate = eval(intermediate_eq)
                        self.code_string += '{} = {}({})\n'.format(var_name, operator_info[0], a_name)

                    elif operator_info[1]==2:
                        if operator_name == '[OP_GCD]':
                            num1, num1_name = self.operand_stack.pop()
                            num2, num2_name = self.operand_stack.pop()
                            num1, num2 = int(num1), int(num2)

                            intermediate = math.gcd(num1, num2) 
                            self.code_string += '{new_var} = math.gcd(int({var1}), int({var2}))\n'.format(new_var=var_name, var1=num1_name, var2=num2_name)

                        elif operator_name == '[OP_LCM]':
                            num1, num1_name = self.operand_stack.pop()
                            num2, num2_name = self.operand_stack.pop()
                            num1, num2 = int(num1), int(num2)

                            intermediate = num1 * num2 / math.gcd(num1, num2)
                            self.code_string += '{new_var} = {var1} * {var2} / math.gcd(int({var1}), int({var2}))\n'.format(new_var=var_name, var1=num1_name, var2=num2_name)

                        elif operator_name in ['[OP_CEIL]', '[OP_FLOOR]']:
                            b, b_name = self.operand_stack.pop()
                            b = int(b)
                            a, a_name = self.operand_stack.pop()
                            if operator_name == '[OP_CEIL]':
                                try:
                                    # rounding intergers
                                    int(a)
                                    intermediate_eq = 'int((({a}+9*10**({b}-2))//(10**({b}-1)))*10**({b}-1))\n'.format(a=a_name, b=b_name)
                                    intermediate = eval('int((({a}+9*10**({b}-2))//(10**({b}-1)))*10**({b}-1))\n'.format(a=a, b=b))
                                    self.code_string += '{var}={eq}\n'.format(var=var_name, eq=intermediate_eq)
                                except:
                                    # int(float) -> floor / int(float+1) -> ceil
                                    intermediate_eq = 'int({a}*10**{b}+1)/10**{b}\n'.format(a=a_name, b=b_name)
                                    intermediate = eval('int({a}*10**{b}+1)/10**{b}\n'.format(a=a, b=b))
                                    self.code_string += '{var}={eq}\n'.format(var=var_name, eq=intermediate_eq)
                            else: # [OP_FLOOR]
                                try:
                                    int(a)
                                    intermediate_eq = 'int(({a}//(10**({b}-1)))*10**({b}-1))\n'.format(a=a_name, b=b_name)
                                    intermediate = eval('int(({a}//(10**({b}-1)))*10**({b}-1))\n'.format(a=a, b=b))
                                    self.code_string += '{var}={eq}\n'.format(var=var_name, eq=intermediate_eq)
                                except:
                                    intermediate_eq = 'int({a}*10**{b})/10**{b}\n'.format(a=a_name, b=b_name)
                                    intermediate = eval('int({a}*10**{b})/10**{b}\n'.format(a=a, b=b))
                                    self.code_string += '{var}={eq}\n'.format(var=var_name, eq=intermediate_eq)
                        elif operator_name == '[OP_ROUND]':
                            b, b_name = self.operand_stack.pop()
                            b = int(b)
                            a, a_name = self.operand_stack.pop()
                            try:
                                int(str(a))
                                round_tgt = int(a//10**(b-2))%10
                                if round_tgt >= 5:
                                    intermediate = int(((a+9*10**(b-2))//(10**(b-1)))*10**(b-1))
                                else:
                                    intermediate = int((a//(10**(b-1)))*10**(b-1))
                                self.code_string += "round_tgt = int({a}//10**({b}-2)%10)\n\
if round_tgt >= 5:\n\
    {intermediate} = int((({a}+9*10**({b}-2))//(10**({b}-1)))*10**({b}-1))\n\
else:\n\
    {intermediate} = int(({a}//(10**({b}-1)))*10**({b}-1))".format(a=a, b=b, intermediate=var_name)
                            except:
                                a = self.to_float(a)
                                intermediate = round(a+1e-10, b) # Add epsilon to get the correct value. 1.7325 -> round(1.7325, 3) -> 1.732 / round(1.7325000001, 3) -> 1.733
                                self.code_string += '{var} = round(float({a})+1e-10, {b})\n'.format(var=var_name, a=a_name, b=b_name)

                        elif operator_name == '[OP_COMB]':
                            b, b_name = self.operand_stack.pop()
                            a, a_name = self.operand_stack.pop()
                            intermediate = 1
                            a = int(a)
                            b = int(b)
                            for i, elem in enumerate(range(b)):
                                intermediate = intermediate * (a-i)
                            for i, elem in enumerate(range(b)):
                                intermediate = intermediate / (i+1)
                            self.code_string += '{new_var} = 1\n\
{a} = int({a})\n\
{b} = int({b})\n\
for i, elem in enumerate(range({b})):\n\
    {new_var} = {new_var} * ({a}-i)\n\
for i, elem in enumerate(range({b})):\n\
    {new_var} = {new_var} / (i+1)\n'.format(new_var=var_name, a=a_name, b=b_name)
                        elif operator_name == '[OP_PERM]':
                            b, b_name = self.operand_stack.pop()
                            a, a_name = self.operand_stack.pop()
                            intermediate = 1
                            a = int(a)
                            b = int(b)
                            for i, elem in enumerate(range(b)):
                                intermediate = intermediate * (a-i)
                            self.code_string += '{new_var} = 1\n\
{a} = int({a})\n\
{b} = int({b})\n\
for i, elem in enumerate(range({b})):\n\
    {new_var} = {new_var} * ({a}-i)\n'.format(new_var=var_name, a=a_name, b=b_name)
                        else: # currently unused parts. Available above Python 3.8 version.
                            b, b_name = self.operand_stack.pop()
                            a, a_name = self.operand_stack.pop()
                            intermediate_eq = str(operator_info[0])+'('+a_name+','+b_name+')'
                            intermediate = eval(intermediate_eq)
                            self.code_string += '{var} = {intermediate}\n'.format(var=var_name, intermediate=intermediate_eq)
                    else:
                        print("not defined")
                    self.operand_stack.push(intermediate, var_name)
                elif operator_info[2] == 'function_special':
                    if operator_name == '[OP_DIGIT_UNK_SOLVER]':
                        x, x_name = self.operand_stack.pop()
                        eq, eq_name = self.operand_stack.pop()
                        eq = str(eq)
                        eq = eq.replace('×','*')
                        eq = eq.replace('x','*')
                        eq = eq.replace('÷','/')
                        ans_dict = dict()
                        variable_candi = set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'])
                        ans_dict = {v:[] for v in set(eq) & variable_candi}
                        candi = list(itertools.product('0123456789', repeat=len(ans_dict)))
                        for c in candi:
                            temp = eq
                            for i, (k, _) in enumerate(ans_dict.items()):
                                temp = temp.replace(k, str(c[i]))
                            term_list = []
                            op_list = []
                            temp_c = ''
                            for tc in temp:
                                if tc not in '+-*/=><().':
                                    temp_c += tc
                                else:
                                    op_list.append(tc)
                                    term_list.append(temp_c)
                                    temp_c = ''
                            term_list.append(temp_c)
                            new_eq = ''
                            for i in range(len(op_list)):
                                new_eq += str(int(term_list[i]))+op_list[i]
                            new_eq += str(int(term_list[-1]))
                            if len(new_eq) == len(eq):
                                new_eq=new_eq.replace('=', '==')
                                new_eq=new_eq.replace('>==', '>=')
                                new_eq=new_eq.replace('<==', '<=')
                                eval_result = False
                                try:
                                    eval_result = eval(new_eq)
                                except:
                                    pass
                                if eval_result:
                                    for i, (k, _) in enumerate(ans_dict.items()):
                                        ans_dict[k].append(int(c[i]))

                        intermediate = list(set(ans_dict[x]))
                        if len(intermediate) == 1:
                            intermediate = intermediate[0]

                        if isinstance(intermediate, list):
                            new_list_name = self.list_names.pop(0)
                            self.list_stack.push(intermediate, new_list_name)
                            self.code_string += "ans_dict = dict()\n\
{eq} = {eq}.replace('×','*')\n\
{eq} = {eq}.replace('x','*')\n\
{eq} = {eq}.replace('÷','/')\n\
variable_candi = set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'])\n\
for v in set({eq}):\n\
    if v in variable_candi:\n\
        ans_dict[v] = []\n\
candi = list(itertools.product('0123456789', repeat=len(ans_dict)))\n\
for c in candi:\n\
    temp = {eq}\n\
    for i, (k, _) in enumerate(ans_dict.items()):\n\
        temp = temp.replace(k, str(c[i]))\n\
    term_list = []\n\
    op_list = []\n\
    temp_c = ''\n\
    for tc in temp:\n\
        if tc not in '+-*/=><().':\n\
            temp_c += tc\n\
        else:\n\
            op_list.append(tc)\n\
            term_list.append(temp_c)\n\
            temp_c = ''\n\
    term_list.append(temp_c)\n\
    new_eq = ''\n\
    for i in range(len(op_list)):\n\
        new_eq += str(int(term_list[i]))+op_list[i]\n\
    new_eq += str(int(term_list[-1]))\n\
    if len(new_eq) == len({eq}):\n\
        new_eq=new_eq.replace('=', '==')\n\
        new_eq=new_eq.replace('>==', '>=')\n\
        new_eq=new_eq.replace('<==', '<=')\n\
        eval_result = False\n\
        try:\n\
            eval_result = eval(new_eq)\n\
        except:\n\
            pass\n\
        if eval_result:\n\
            for i, (k, _) in enumerate(ans_dict.items()):\n\
                ans_dict[k].append(int(c[i]))\n\
{intermediate} = list(set(ans_dict[{x}]))\n".format(intermediate=new_list_name, eq=eq_name, x=x_name)
                        else:
                            new_var_name = self.operand_names.pop(0)
                            self.operand_stack.push(intermediate, new_var_name)
                            self.code_string += "ans_dict = dict()\n\
{eq} = {eq}.replace('×','*')\n\
{eq} = {eq}.replace('x','*')\n\
{eq} = {eq}.replace('÷','/')\n\
variable_candi = set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'])\n\
for v in set({eq}):\n\
    if v in variable_candi:\n\
        ans_dict[v] = 1\n\
candi = list(itertools.product('0123456789', repeat=len(ans_dict)))\n\
for c in candi:\n\
    temp = {eq}\n\
    for i, (k, _) in enumerate(ans_dict.items()):\n\
        temp = temp.replace(k, str(c[i]))\n\
    term_list = []\n\
    op_list = []\n\
    temp_c = ''\n\
    for tc in temp:\n\
        if tc not in '+-*/=><().':\n\
            temp_c += tc\n\
        else:\n\
            op_list.append(tc)\n\
            term_list.append(temp_c)\n\
            temp_c = ''\n\
    term_list.append(temp_c)\n\
    new_eq = ''\n\
    for i in range(len(op_list)):\n\
        new_eq += str(int(term_list[i]))+op_list[i]\n\
    new_eq += str(int(term_list[-1]))\n\
    if len(new_eq) == len({eq}):\n\
        new_eq=new_eq.replace('=', '==')\n\
        new_eq=new_eq.replace('>==', '>=')\n\
        new_eq=new_eq.replace('<==', '<=')\n\
        eval_result = False\n\
        try:\n\
            eval_result = eval(new_eq)\n\
        except:\n\
            pass\n\
        if eval_result:\n\
            for i, (k, _) in enumerate(ans_dict.items()):\n\
                ans_dict[k] = int(c[i])\n\
{intermediate} = ans_dict[{x}]\n".format(intermediate=new_var_name, eq=eq_name, x=x_name)
                    elif operator_name == '[OP_NUM_UNK_SOLVER]':
                        x, x_name = self.operand_stack.pop()
                        eq, eq_name = self.operand_stack.pop()
                        eq = str(eq)
                        eq = eq.replace('×','*')
                        eq = eq.replace('x','*')
                        eq = eq.replace('÷','/')
                        ans_dict = dict()
                        variable_candi = set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'])
                        ans_dict = {v:[] for v in set(eq) & variable_candi}
                        candidate_num = [i for i in range(51)]
                        candi = list(itertools.product(candidate_num, repeat=len(ans_dict)))
                        for c in candi:
                            temp = eq
                            for i, (k, _) in enumerate(ans_dict.items()):
                                temp = temp.replace(k, str(c[i]))
                            term_list = []
                            op_list = []
                            temp_c = ''
                            for tc in temp:
                                if tc not in '+-*/=><().':
                                    temp_c += tc
                                else:
                                    op_list.append(tc)
                                    term_list.append(temp_c)
                                    temp_c = ''
                            term_list.append(temp_c)
                            new_eq = ''
                            for i in range(len(op_list)):
                                if term_list[i] == '':
                                    new_eq += str(term_list[i])+op_list[i]
                                else:
                                    new_eq += str(int(term_list[i]))+op_list[i]
                            new_eq += str(int(term_list[-1]))
                            new_eq=new_eq.replace('=', '==')
                            new_eq=new_eq.replace('>==', '>=')
                            new_eq=new_eq.replace('<==', '<=')
                            eval_result = False
                            try:
                                if '=' in new_eq and '>' not in new_eq and '<' not in new_eq:
                                    new_eq=new_eq.replace('==','=')
                                    new_eq=new_eq.replace('>','')
                                    new_eq=new_eq.replace('<','')
                                    new_eq=new_eq.split('=')
                                    for i in range(len(new_eq)-1):
                                        eval_result = math.isclose(eval(new_eq[i]), eval(new_eq[i+1]))
                                        if not eval_result:
                                            break
                                else:
                                    eval_result = eval(new_eq)
                            except:
                                eval_result = False
                                pass
                            if eval_result:
                                for i, (k, _) in enumerate(ans_dict.items()):
                                    ans_dict[k].append(int(c[i]))

                        intermediate = list(set(ans_dict[x]))
                        if len(intermediate) == 1:
                            intermediate = intermediate[0]

                        if isinstance(intermediate, list):
                            new_list_name = self.list_names.pop(0)
                            self.list_stack.push(intermediate, new_list_name)
                            self.code_string += "ans_dict = dict()\n\
{eq} = {eq}.replace('×','*')\n\
{eq} = {eq}.replace('x','*')\n\
{eq} = {eq}.replace('÷','/')\n\
variable_candi = set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'])\n\
for v in set({eq}):\n\
    if v in variable_candi:\n\
        ans_dict[v] = []\n\
candidate_num = [i for i in range(51)]\n\
candi = list(itertools.product(candidate_num, repeat=len(ans_dict)))\n\
for c in candi:\n\
    temp = {eq}\n\
    for i, (k, _) in enumerate(ans_dict.items()):\n\
        temp = temp.replace(k, str(c[i]))\n\
    term_list = []\n\
    op_list = []\n\
    temp_c = ''\n\
    for tc in temp:\n\
        if tc not in '+-*/=><().':\n\
            temp_c += tc\n\
        else:\n\
            op_list.append(tc)\n\
            term_list.append(temp_c)\n\
            temp_c = ''\n\
    term_list.append(temp_c)\n\
    new_eq = ''\n\
    for i in range(len(op_list)):\n\
        if term_list[i] == '':\n\
            new_eq += str(term_list[i])+op_list[i]\n\
        else:\n\
            new_eq += str(int(term_list[i]))+op_list[i]\n\
    new_eq += str(int(term_list[-1]))\n\
    new_eq=new_eq.replace('=', '==')\n\
    new_eq=new_eq.replace('>==', '>=')\n\
    new_eq=new_eq.replace('<==', '<=')\n\
    eval_result = False\n\
    try:\n\
        if '=' in new_eq and '>' not in new_eq and '<' not in new_eq:\n\
            new_eq=new_eq.replace('==','=')\n\
            new_eq=new_eq.replace('>','')\n\
            new_eq=new_eq.replace('<','')\n\
            new_eq=new_eq.split('=')\n\
            for i in range(len(new_eq)-1):\n\
                eval_result = math.isclose(eval(new_eq[i]), eval(new_eq[i+1]))\n\
                if not eval_result:\n\
                    break\n\
        else:\n\
            eval_result = eval(new_eq)\n\
    except:\n\
        eval_result = False\n\
        pass\n\
    if eval_result:\n\
        for i, (k, _) in enumerate(ans_dict.items()):\n\
            ans_dict[k].append(int(c[i]))\n\
{intermediate} = list(set(ans_dict[{x}]))\n".format(intermediate=new_list_name, eq=eq_name, x=x_name)
                        else:
                            new_var_name = self.operand_names.pop(0)
                            self.operand_stack.push(intermediate, new_var_name)
                            self.code_string += "ans_dict = dict()\n\
{eq} = {eq}.replace('×','*')\n\
{eq} = {eq}.replace('x','*')\n\
{eq} = {eq}.replace('÷','/')\n\
variable_candi = set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'])\n\
for v in set({eq}):\n\
    if v in variable_candi:\n\
        ans_dict[v] = 0\n\
candidate_num = [i for i in range(51)]\n\
candi = list(itertools.product(candidate_num, repeat=len(ans_dict)))\n\
for c in candi:\n\
    temp = {eq}\n\
    for i, (k, _) in enumerate(ans_dict.items()):\n\
        temp = temp.replace(k, str(c[i]))\n\
    term_list = []\n\
    op_list = []\n\
    temp_c = ''\n\
    for tc in temp:\n\
        if tc not in '+-*/=><().':\n\
            temp_c += tc\n\
        else:\n\
            op_list.append(tc)\n\
            term_list.append(temp_c)\n\
            temp_c = ''\n\
    term_list.append(temp_c)\n\
    new_eq = ''\n\
    for i in range(len(op_list)):\n\
        if term_list[i] == '':\n\
            new_eq += str(term_list[i])+op_list[i]\n\
        else:\n\
            new_eq += str(int(term_list[i]))+op_list[i]\n\
    new_eq += str(int(term_list[-1]))\n\
    new_eq=new_eq.replace('=', '==')\n\
    new_eq=new_eq.replace('>==', '>=')\n\
    new_eq=new_eq.replace('<==', '<=')\n\
    eval_result = False\n\
    try:\n\
        if '=' in new_eq and '>' not in new_eq and '<' not in new_eq:\n\
            new_eq=new_eq.replace('==','=')\n\
            new_eq=new_eq.replace('>','')\n\
            new_eq=new_eq.replace('<','')\n\
            new_eq=new_eq.split('=')\n\
            for i in range(len(new_eq)-1):\n\
                eval_result = math.isclose(eval(new_eq[i]), eval(new_eq[i+1]))\n\
                if not eval_result:\n\
                    break\n\
        else:\n\
            eval_result = eval(new_eq)\n\
    except:\n\
        eval_result = False\n\
        pass\n\
    if eval_result:\n\
        for i, (k, _) in enumerate(ans_dict.items()):\n\
            ans_dict[k] = int(c[i])\n\
{intermediate} = ans_dict[{x}]\n".format(intermediate=new_var_name, eq=eq_name, x=x_name)
                    elif operator_name == '[OP_GEN_POSSIBLE_LIST]':
                        unk, unk_name = self.operand_stack.pop()
                        unk = str(unk)
                        ans_dict = dict()
                        variable_candi = set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'])
                        ans_dict = {v:0 for v in set(unk) & variable_candi}
                        candi = list(itertools.product('0123456789', repeat=len(ans_dict)))
                        intermediate_list = []
                        for c in candi:
                            temp = unk
                            for i, (k, _) in enumerate(ans_dict.items()):
                                temp = temp.replace(k, str(c[i]))
                            if len(unk) == len(str(int(temp))):
                                new_elem = int(temp)
                                intermediate_list.append(new_elem)
                        
                        new_list_name = self.list_names.pop(0)
                        self.operand_stack.push(unk, unk_name)
                        self.list_stack.push(intermediate_list, new_list_name)
                        self.code_string += "ans_dict = dict()\n\
{unk} = str({unk})\n\
{intermediate_list} = []\n\
variable_candi = set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'])\n\
for v in set({unk}):\n\
    if v in variable_candi:\n\
        ans_dict[v] = 0\n\
candi = list(itertools.product('0123456789', repeat=len(ans_dict)))\n\
for c in candi:\n\
    temp = {unk}\n\
    for i, (k, _) in enumerate(ans_dict.items()):\n\
        temp = temp.replace(k, str(c[i]))\n\
    if len({unk}) == len(str(int(temp))):\n\
        new_elem = int(temp)\n\
        {intermediate_list}.append(new_elem)\n".format(unk=unk_name, intermediate_list=new_list_name)

                elif operator_info[2] == 'list_function':
                    if operator_info[1]==1: # input: list / output: scalar
                        if operator_name == '[OP_LIST_MEAN]':
                            temp_list, temp_lname = self.list_stack.pop()
                            temp_list = [self.to_float(i) for i in temp_list]
                            intermediate = sum(temp_list) / len(temp_list)
                            new_var_name = self.operand_names.pop(0)
                            self.code_string += '{temp_list} = [float(i) for i in {temp_list}]\n\
{new_var_name} = sum({temp_list})/len({temp_list})\n'.format(new_var_name=new_var_name, temp_list=temp_lname)
                            self.operand_stack.push(intermediate, new_var_name)
                            self.list_stack.push(temp_list, temp_lname)
                        elif operator_name == '[OP_LIST_SUM]':
                            temp_list, temp_lname = self.list_stack.pop()
                            temp_list = [self.to_float(i) for i in temp_list]
                            intermediate = sum(temp_list)
                            new_var_name = self.operand_names.pop(0)
                            self.code_string += '{temp_list} = [float(i) for i in {temp_list}]\n\
{new_var_name} = sum({temp_list})\n'.format(new_var_name=new_var_name, temp_list=temp_lname)
                            self.operand_stack.push(intermediate, new_var_name)
                            self.list_stack.push(temp_list, temp_lname)
                        elif operator_name == '[OP_LIST2NUM]':
                            temp_list, temp_lname = self.list_stack.pop()
                            new_var_name = self.operand_names.pop(0)
                            intermediate = ''
                            for i in temp_list:
                                i = str(i)
                                intermediate = intermediate + i
                            self.code_string += '{new_var_name}=""\n\
for i in {temp_list}:\n\
    i = str(i)\n\
    {new_var_name} = {new_var_name} + i\n'.format(new_var_name = new_var_name, temp_list = temp_lname)
                            self.operand_stack.push(intermediate, new_var_name)
                            self.list_stack.push(temp_list,temp_lname)
                        elif operator_name == '[OP_NUM2LIST]':
                            a, a_name = self.operand_stack.pop()
                            new_list_name = self.list_names.pop(0)
                            intermediate_list = []
                            a = int(a)
                            while a//10 > 0:
                                intermediate_list.append(a%10)
                                a = a//10
                            intermediate_list.append(a%10)
                            intermediate_list = intermediate_list[::-1]
                            self.code_string += '{new_list_name} = []\n\
{a} = int({a})\n\
while {a}//10 > 0:\n\
    {new_list_name}.append({a}%10)\n\
    {a} = {a}//10\n\
{new_list_name}.append({a}%10)\n\
{new_list_name} = {new_list_name}[::-1]\n'.format(a=a_name, new_list_name=new_list_name)
                            self.list_stack.push(intermediate_list, new_list_name)
                        elif operator_name == '[OP_LIST_NUM2SUM]':
                            temp_list, temp_lname = self.list_stack.pop()
                            a_name = self.operand_names.pop(0)
                            new_list_name = self.list_names.pop(0)
                            intermediate_list = []
                            for i in temp_list:
                                element = 0
                                i = int(i)
                                while i//10 > 0:
                                    element = element + i%10
                                    i = i//10
                                element = element + i%10
                                intermediate_list.append(element)
                            self.code_string += "{intermediate_list}=[]\n\
for i in {temp_list}:\n\
    {a_name} = 0\n\
    i = int(i)\n\
    while i//10 > 0:\n\
        {a_name} = {a_name} + i%10\n\
        i = i//10\n\
    {a_name} = {a_name} + i%10\n\
    {intermediate_list}.append({a_name})\n".format(intermediate_list=new_list_name, temp_list=temp_lname, a_name=a_name)
                            self.list_stack.push(intermediate_list, new_list_name)
                        elif operator_name == '[OP_LIST_GET_DIVISOR]':
                            num, num_name = self.operand_stack.pop()
                            new_list_name = self.list_names.pop(0)
                            num = int(num)
                            intermediate_list = []
                            num_sqrt = int(math.sqrt(num))
                            for i in range(1, num_sqrt+1):
                                if num % i == 0:
                                    intermediate_list.append(i)
                                    intermediate_list.append(int(num/i))
                            new_list = sorted(set(intermediate_list))
                            self.list_stack.push(new_list, new_list_name)
                            self.code_string += "{intermediate_list} = []\n\
num_sqrt = int(math.sqrt({num_name}))\n\
for i in range(1, num_sqrt+1):\n\
    if {num_name} % i == 0:\n\
        {intermediate_list}.append(i)\n\
        {intermediate_list}.append(int({num_name}/i))\n\
{intermediate_list} = sorted(set({intermediate_list}))\n".format(num_name=num_name, intermediate_list=new_list_name)
                        else: # [OP_LIST_LEN]
                            temp_list, temp_lname = self.list_stack.pop()
                            intermediate_eq = operator_info[0]+'('+str(temp_list)+')'
                            intermediate = eval(intermediate_eq)
                            new_var_name = self.operand_names.pop(0)
                            self.code_string += '{} = {}({})\n'.format(new_var_name, operator_info[0], temp_lname)
                            self.operand_stack.push(intermediate, new_var_name)
                            self.list_stack.push(temp_list, temp_lname)
                    elif operator_info[1]==2:
                        if operator_name in ['[OP_LIST_MAX]', '[OP_LIST_MIN]', '[OP_LIST_GET]', '[OP_LIST_INDEX]', '[OP_LIST_MORE]', '[OP_LIST_LESS]', '[OP_LIST_MORE_EQUAL]', '[OP_LIST_LESS_EQUAL]', \
                                             '[OP_LIST_GET_PERM]', '[OP_LIST_GET_PRODUCT]']:# input: list, scalar / output: scalar, list
                            temp_list, temp_lname = self.list_stack.pop()
                            a, a_name = self.operand_stack.pop()
                            try:
                                a = self.to_float(a)
                                a = self.intifint(a)
                            except:
                                pass
                            if operator_name == '[OP_LIST_GET]': # input: list, scalar / output: scalar
                                # print('[OP_LIST_GET]', temp_list)
                                intermediate = temp_list[a-1]
                                new_var_name = self.operand_names.pop(0)
                                self.code_string += '{} = {}[{}-1]\n'.format(new_var_name, temp_lname, a_name)
                                self.list_stack.push(temp_list, temp_lname)
                                self.operand_stack.push(intermediate, new_var_name)
                            elif operator_name == '[OP_LIST_INDEX]': # input: list, scalar / output: scalar
                                if isinstance(a, int):
                                    try:
                                        try:
                                            intermediate = temp_list.index(str(a))+1
                                        except:
                                            intermediate = temp_list.index(str(float(a)))+1
                                    except:
                                        try:
                                            intermediate = temp_list.index(int(a))+1
                                        except:
                                            intermediate = temp_list.index(float(a))+1
                                
                                elif isinstance(a, float):
                                    try:
                                        intermediate = temp_list.index(str(a))+1
                                    except:
                                        intermediate = temp_list.index(float(a))+1
                                
                                else:
                                    intermediate = temp_list.index(str(a))+1

                                new_var_name = self.operand_names.pop(0)
                                self.code_string += '{} = {}.index({})+1\n'.format(new_var_name, temp_lname, a_name)
                                self.list_stack.push(temp_list, temp_lname)
                                self.operand_stack.push(intermediate, new_var_name)
                            elif operator_name in ['[OP_LIST_MORE]', '[OP_LIST_LESS]', '[OP_LIST_MORE_EQUAL]', '[OP_LIST_LESS_EQUAL]']:
                                new_list_name = self.list_names.pop(0)
                                if operator_name == '[OP_LIST_MORE]':
                                    intermediate_list = [i for i in temp_list if self.intifint(self.to_float(i)) > a]
                                    self.code_string += '{new_list} = []\n\
for i in {temp}:\n\
    if i > {a}:\n\
        {new_list}.append(i)\n'.format(new_list=new_list_name, temp=temp_lname, a=a_name)
                                elif operator_name == '[OP_LIST_LESS]':
                                    intermediate_list = [i for i in temp_list if self.intifint(self.to_float(i)) < a]
                                    # self.code_string += '{} = [i for i in {} if i < {}]\n'.format(new_list_name, temp_lname, a_name)
                                    self.code_string += '{new_list} = []\n\
for i in {temp}:\n\
    if i < {a}:\n\
        {new_list}.append(i)\n'.format(new_list=new_list_name, temp=temp_lname, a=a_name)
                                elif operator_name == '[OP_LIST_MORE_EQUAL]':
                                    intermediate_list = [i for i in temp_list if self.intifint(self.to_float(i)) >= a]
                                    # self.code_string += '{} = [i for i in {} if i >= {}]\n'.format(new_list_name, temp_lname, a_name)
                                    self.code_string += '{new_list} = []\n\
for i in {temp}:\n\
    if i >= {a}:\n\
        {new_list}.append(i)\n'.format(new_list=new_list_name, temp=temp_lname, a=a_name)
                                elif operator_name == '[OP_LIST_LESS_EQUAL]':
                                    intermediate_list = [i for i in temp_list if self.intifint(self.to_float(i)) <= a]
                                    # self.code_string += '{} = [i for i in {} if i <= {}]\n'.format(new_list_name, temp_lname, a_name)
                                    self.code_string += '{new_list} = []\n\
for i in {temp}:\n\
    if i <= {a}:\n\
        {new_list}.append(i)\n'.format(new_list=new_list_name, temp=temp_lname, a=a_name)
                                self.list_stack.push(temp_list, temp_lname)
                                self.list_stack.push(intermediate_list, new_list_name)
                            elif operator_name == '[OP_LIST_MAX]':
                                zizigo = temp_list.copy()
                                # for i in range(len(zizigo)):
                                #     zizigo[i] = float(zizigo[i])
                                zizigo.sort()
                                intermediate = zizigo[-a]
                                new_var_name = self.operand_names.pop(0)
                                new_list_name = self.list_names.pop(0)
                                self.code_string += '{new_list}={temp_list}.copy()\n{new_list}.sort()\n{intermediate} = {new_list}[-{a}]\n'.format(new_list=new_list_name,temp_list=temp_lname,intermediate=new_var_name,a=a_name)
                                self.list_stack.push(temp_list, temp_lname)
                                self.operand_stack.push(intermediate, new_var_name)
                            elif operator_name == '[OP_LIST_MIN]':
                                zizigo = temp_list.copy()
                                # for i in range(len(zizigo)):
                                #     zizigo[i] = float(zizigo[i])
                                zizigo.sort()
                                intermediate = temp_list[a-1]
                                new_var_name = self.operand_names.pop(0)
                                new_list_name = self.list_names.pop(0)
                                self.code_string += '{new_list}={temp_list}.copy()\n{new_list}.sort()\n{intermediate} = {new_list}[{a}-1]\n'.format(new_list=new_list_name,temp_list=temp_lname,intermediate=new_var_name,a=a_name)
                                self.list_stack.push(temp_list, temp_lname)
                                self.operand_stack.push(intermediate, new_var_name)
                            elif operator_name == '[OP_LIST_GET_PERM]':
                                intermediate_list = [str(i) for i in temp_list]
                                if len(intermediate_list) > 10 or int(a) > 10:
                                    print("Memory issue")
                                    return -1, self.code_string
                                new_list_name = self.list_names.pop(0)
                                intermediate_list = list(itertools.permutations(intermediate_list, a))
                                intermediate_list = [''.join(num_list) for num_list in intermediate_list]
                                intermediate_list = [str_num for str_num in intermediate_list if str_num[0] != '0']
                                self.code_string += "{intermediate_list} = [str(i) for i in {temp_list}]\n\
{intermediate_list} = list(itertools.permutations({intermediate_list}, {a}))\n\
{intermediate_list} = [''.join(num_list) for num_list in {intermediate_list}]\n\
{intermediate_list} = [str_num for str_num in {intermediate_list} if str_num[0] != '0']\n".format(intermediate_list=new_list_name, temp_list=temp_lname, a=a_name)
                                if self.is_number(intermediate_list[0]):
                                    intermediate_list = [self.to_float(i) for i in intermediate_list]
                                    self.code_string += "{intermediate_list} = [float(i) for i in {intermediate_list}]\n".format(intermediate_list = new_list_name)
                                
                                self.list_stack.push(temp_list, temp_lname)
                                self.list_stack.push(intermediate_list, new_list_name)
                            elif operator_name == '[OP_LIST_GET_PRODUCT]':
                                intermediate_list = [str(i) for i in temp_list]
                                if len(intermediate_list) > 10 or int(a) > 6:
                                    print("Memory issue")
                                    return -1, self.code_string
                                intermediate_list = list(itertools.product(intermediate_list, repeat=a))
                                intermediate_list = [''.join(num_list) for num_list in intermediate_list]
                                intermediate_list = [str_num for str_num in intermediate_list if str_num[0] != '0']
                                new_list_name = self.list_names.pop(0)
                                self.code_string += "{intermediate_list} = [str(i) for i in {temp_list}]\n\
{intermediate_list} = list(itertools.product({intermediate_list}, repeat={a}))\n\
{intermediate_list} = [''.join(num_list) for num_list in {intermediate_list}]\n\
{intermediate_list} = [str_num for str_num in {intermediate_list} if str_num[0] != '0']\n".format(intermediate_list=new_list_name, temp_list=temp_lname, a=a_name)
                                if self.is_number(intermediate_list[0]):
                                  intermediate_list = [self.to_float(i) for i in intermediate_list]
                                  self.code_string += "{intermediate_list} = [float(i) for i in {intermediate_list}]\n".format(intermediate_list = new_list_name)
                                self.list_stack.push(temp_list, temp_lname)
                                self.list_stack.push(intermediate_list, new_list_name)
                                
                            else:
                                pass
                            
                        elif operator_name in ['[OP_SET_UNION]', '[OP_SET_INTERSECT]', '[OP_SET_DIFFERENCE]', '[OP_LIST_COND_MAX_MIN]']:# input: list, list / output: list
                            b_list, b_lname = self.list_stack.pop()
                            a_list, a_lname = self.list_stack.pop()
                            new_list_name = self.list_names.pop(0)
                            if operator_name == '[OP_SET_UNION]':
                                intermediate_list = list(set(a_list) | set(b_list))
                                self.code_string += '{} = list(set({}) | set({}))\n'.format(new_list_name, a_lname, b_lname)
                            elif operator_name == '[OP_SET_INTERSECT]':
                                intermediate_list = list(set(a_list) & set(b_list))
                                self.code_string += '{} = list(set({}) & set({}))\n'.format(new_list_name, a_lname, b_lname)
                            elif operator_name == '[OP_SET_DIFFERENCE]':
                                intermediate_list = list(set(a_list) - set(b_list))
                                self.code_string += '{} = list(set({}) - set({}))\n'.format(new_list_name, a_lname, b_lname)
                            elif operator_name == '[OP_LIST_COND_MAX_MIN]':
                                # a_list: List of items
                                # b_list: List of conditions -> multiple of 3
                                items_name_list = a_list.copy()

                                # Process conditions
                                # conditions: list[str], List of string conditions which is evaluated using `eval()` later
                                # If an operand is a string, it must be wrapped with { }
                                # ex) ["{A} < {B}", "{B} == 3", "{C} > {A}"]
                                conditions = []
                                condition_list = b_list.copy()
                                temp_stack = []  # Temporary stack for processing postfix conditions
                                for index_, cond_ in enumerate(map(str, condition_list)):
                                    try:
                                        if cond_ in ("<", ">", "="):
                                            # Operator
                                            operand_right = temp_stack.pop()
                                            operand_left = temp_stack.pop()

                                            if cond_ == "=":
                                                # Convert a single equal sign to double equal sign
                                                cond_ = "=="

                                            conditions.append(f"{operand_left} {cond_} {operand_right}")

                                        else:
                                            # Operand
                                            if not cond_.isdigit():
                                                # Wrap string operands with braces
                                                cond_ = "{" + cond_ + "}"

                                            temp_stack.append(cond_)

                                    except IndexError as e:
                                        # Expected an item from temp_stack, but temp_stack is empty
                                        raise AssertionError(f"error while processing {cond_} at {index_}:"
                                                             f"expected an operand from stack") from e

                                # temp_stack should be empty
                                assert len(temp_stack) == 0, f"temp_stack({temp_stack}) is not empty" \
                                                             f"after processing all condition inputs"

                                # Calculate combinations
                                condition_found = False
                                item_name_index_dict = {}
                                for perm in itertools.permutations(range(1, len(items_name_list) + 1)):
                                    item_name_index_dict = dict(
                                            zip(items_name_list, perm))  # ex) {"A": 2, "B": 1, "C": 3}

                                    # Format strings from `conditions`
                                    # ex) "{A} < {B}" -> "3 < 2"
                                    formatted_conditions = [condition.format_map(item_name_index_dict) for condition in
                                                            conditions]
                                    if all(map(eval, formatted_conditions)):
                                        # All conditions met
                                        condition_found = True
                                        break

                                assert condition_found, f"no combination found"

                                # Sort result
                                intermediate_list = list(item_name_index_dict.keys())
                                intermediate_list.sort(key=item_name_index_dict.get, reverse=True)

                                del item_name_index_dict

                                self.code_string += \
                                    f"global item_name_index_dict\n" \
                                    f"items_name_list = {a_lname}.copy()\n" \
                                    "conditions = []\n" \
                                    f"condition_list = {b_lname}.copy()\n" \
                                    "temp_stack = []\n" \
                                    "for index_, cond_ in enumerate(map(str, condition_list)):\n" \
                                    "    if cond_ in (\"<\", \">\", \"=\"):\n" \
                                    "        operand_right = temp_stack.pop()\n" \
                                    "        operand_left = temp_stack.pop()\n" \
                                    "        if cond_ == \"=\":\n" \
                                    "            cond_ = \"==\"\n" \
                                    "        conditions.append(f\"{operand_left} {cond_} {operand_right}\")\n" \
                                    "    else:\n" \
                                    "        if not cond_.isdigit():\n" \
                                    "            cond_ = \"{\" + cond_ + \"}\"\n" \
                                    "        temp_stack.append(cond_)\n" \
                                    "item_name_index_dict = {}\n" \
                                    "for perm in itertools.permutations(range(1, len(items_name_list) + 1)):\n" \
                                    "    item_name_index_dict = dict(zip(items_name_list, perm))\n" \
                                    "    formatted_conditions = \\\n" \
                                    "        [condition.format_map(item_name_index_dict) for condition in conditions]\n" \
                                    "    if all(map(eval, formatted_conditions)):\n" \
                                    "        break\n" \
                                    f"{new_list_name} = list(item_name_index_dict.keys())\n" \
                                    f"{new_list_name}.sort(key=item_name_index_dict.get, reverse=True)\n"

                            self.list_stack.push(a_list, a_lname)
                            self.list_stack.push(b_list, b_lname)
                            self.list_stack.push(intermediate_list, new_list_name)

                        elif operator_name == '[OP_LIST_DIVISIBLE]': # Return a new list which contains the numbers that are divisible by a in temp_list
                            a, a_name = self.operand_stack.pop()
                            temp_list, temp_lname = self.list_stack.pop()
                            new_list_name = self.list_names.pop(0)
                            intermediate_list = []
                            a = int(a)
                            for i in temp_list:
                                i =int(i)
                                if i % a == 0:
                                    intermediate_list.append(i)
                            self.code_string += "{intermediate_list} = []\n\
{a} = int({a})\n\
for i in {temp_list}:\n\
    i = int(i)\n\
    if i % {a} == 0:\n\
        {intermediate_list}.append(i)\n".format(intermediate_list=new_list_name, a=a_name, temp_list=temp_lname)
                            self.list_stack.push(temp_list, temp_lname)
                            self.list_stack.push(intermediate_list, new_list_name)

                        elif operator_name == '[OP_LIST_FIND_NUM]':
                            a, a_name = self.operand_stack.pop()
                            temp_list, temp_lname = self.list_stack.pop()
                            new_var_name = self.operand_names.pop(0)
                            intermediate = 0
                            a = int(a)
                            for i in temp_list:
                                i = int(i)
                                if i == a:
                                    intermediate = intermediate + 1
                            self.code_string += '{intermediate} = 0\n\
{a} = int({a})\n\
for i in {temp_list}:\n\
    i = int(i)\n\
    if i == {a}:\n\
        {intermediate} = {intermediate} + 1\n'.format(intermediate=new_var_name, temp_list=temp_lname, a=a_name)
                            self.list_stack.push(temp_list, temp_lname)
                            self.operand_stack.push(intermediate, new_var_name)
                        elif operator_name in ['[OP_LIST_ODD]', '[OP_LIST_EVEN]']:
                            b, b_name = self.operand_stack.pop()
                            a, a_name = self.operand_stack.pop()
                            new_list_name = self.list_names.pop(0)
                            b = self.intifint(b)
                            a = self.intifint(a)
                            intermediate_list = []
                            self.code_string += "{intermediate_list} = []\n".format(intermediate_list=new_list_name)
                            if operator_name == '[OP_LIST_ODD]':
                                if a%2==0:
                                    for i in range(a+1, b+1, 2):
                                        intermediate_list.append(i)
                                else:
                                    for i in range(a, b+1, 2):
                                        intermediate_list.append(i)
                                self.code_string += "if {a}%2==0:\n".format(a=a_name)
                            elif operator_name == '[OP_LIST_EVEN]':
                                if a%2!=0:
                                    for i in range(a+1, b+1, 2):
                                        intermediate_list.append(i)
                                else:
                                    for i in range(a, b+1, 2):
                                        intermediate_list.append(i)
                                self.code_string += "if {a}%2!=0:\n".format(a=a_name)

                            self.code_string += "    for i in range({a}+1, {b}+1, 2):\n\
        {intermediate_list}.append(i)\n\
else:\n\
    for i in range({a}, {b}+1, 2):\n\
        {intermediate_list}.append(i)\n".format(intermediate_list=new_list_name, a=a_name, b=b_name)

                            self.list_stack.push(intermediate_list, new_list_name)

                    elif operator_info[1]==3:
                        if operator_name == '[OP_LIST_ARANGE]':
                            c, c_name = self.operand_stack.pop()
                            b, b_name = self.operand_stack.pop()
                            a, a_name = self.operand_stack.pop()
                            c = self.intifint(c)
                            b = self.intifint(b)
                            a = self.intifint(a)
                            list_name = self.list_names.pop(0)
                            intermediate_list = [i for i in range(a, b + 1, c)]
                            self.code_string += '{} = [i for i in range({}, {} + 1, {})]\n'.format(list_name, a_name, b_name, c_name)
                            self.list_stack.push(intermediate_list, list_name)
                        elif operator_name == '[OP_LIST_FIND_UNK]':
                            b, b_name = self.operand_stack.pop()
                            a, a_name = self.operand_stack.pop()
                            temp_list, temp_lname = self.list_stack.pop()
                            a = str(a)
                            b = str(b)
                            unk_idx = a.index(b)
                            intermediate = []
                            for elem in temp_list:
                                elem = str(elem)
                                intermediate.append(int(elem[unk_idx]))
                            intermediate = list(set(intermediate))
                            if len(intermediate) == 1:
                                intermediate = intermediate[0]

                            if isinstance(intermediate, list):
                                new_list_name = self.list_names.pop(0)
                                self.list_stack.push(temp_list, temp_lname)
                                self.list_stack.push(intermediate, new_list_name)
                                self.code_string += '{a} = str({a})\n\
{b} = str({b})\n\
unk_idx = {a}.index({b})\n\
{intermediate_list} = []\n\
for elem in {temp_list}:\n\
    elem = str(elem)\n\
    {intermediate_list}.append(int(elem[unk_idx]))\n\
{intermediate_list} = list(set({intermediate_list}))\n'.format(a=a_name, b=b_name, intermediate_list=new_list_name, temp_list=temp_lname)
                            else:
                                new_var_name = self.operand_names.pop(0)
                                self.list_stack.push(temp_list, temp_lname)
                                self.operand_stack.push(intermediate, new_var_name)
                                self.code_string += '{a} = str({a})\n\
{b} = str({b})\n\
unk_idx = {a}.index({b})\n\
{intermediate} = 0\n\
for elem in {temp_list}:\n\
    elem = str(elem)\n\
    {intermediate} = int(elem[unk_idx])\n'.format(a=a_name, b=b_name, intermediate=new_var_name, temp_list=temp_lname)
                        elif operator_name == '[OP_LIST_DIVIDE_AND_REMAIN]':
                            b, b_name = self.operand_stack.pop()
                            a, a_name = self.operand_stack.pop()
                            b = self.intifint(b)
                            a = self.intifint(a)
                            temp_list, temp_lname = self.list_stack.pop()
                            new_list_name = self.list_names.pop(0)
                            intermediate_list = []
                            a = int(a)
                            b = int(b)
                            if b < 0:
                                b = b + a
                            for i in temp_list:
                                i = int(i)
                                if i%a == b:
                                    intermediate_list.append(i)
                            #print('intermediate_list', intermediate_list)
                            self.code_string += "{intermediate_list} = [] \n\
{a} = int({a})\n\
{b} = int({b})\n\
if {b} < 0:\n\
    {b} = {b} + {a}\n\
for i in {temp_list}:\n\
    i = int(i)\n\
    if i%{a} == {b}:\n\
        {intermediate_list}.append(i)\n".format(intermediate_list=new_list_name, a=a_name, b=b_name, temp_list=temp_lname)
                            self.list_stack.push(temp_list, temp_lname)
                            self.list_stack.push(intermediate_list, new_list_name)
                        elif operator_name == '[OP_LIST_SEARCH_FIXED_DIGIT]':
                            b, b_name = self.operand_stack.pop()
                            a, a_name = self.operand_stack.pop()
                            b = self.intifint(b)
                            a = self.intifint(a)
                            temp_list, temp_lname = self.list_stack.pop()
                            new_list_name = self.list_names.pop(0)
                            intermediate_list = []
                            a = int(a)
                            b = int(b)
                            for i in temp_list:
                                i = int(i)
                                if (i // a) % 10 == b:
                                    intermediate_list.append(i)
                            self.code_string += "{intermediate_list} = [] \n\
{a} = int({a})\n\
{b} = int({b})\n\
for i in {temp_list}:\n\
    i = int(i)\n\
    if (i//{a})%10 == {b}:\n\
        {intermediate_list}.append(i)\n".format(intermediate_list=new_list_name, a=a_name, b=b_name, temp_list=temp_lname)
                            self.list_stack.push(temp_list, temp_lname)
                            self.list_stack.push(intermediate_list, new_list_name)
                        elif operator_name == '[OP_LIST_COND_BIG_SMALL]':
                            target_list, target_name = self.list_stack.pop()
                            condition_list, condition_name = self.list_stack.pop()
                            entity_list, entity_name = self.list_stack.pop()
                            new_list_name = self.list_names.pop(0)

                            from queue import Queue

                            input_dict = {i: cnt for cnt, i in enumerate(entity_list)}

                            adj_mat = [[0 for _ in range(len(entity_list))] for _ in range(len(entity_list))]
                            is_visited = [[0 for _ in range(len(entity_list))] for _ in range(len(entity_list))]

                            que = Queue()

                            iterate_num = len(condition_list)//3

                            for i in range(iterate_num):
                                operand_1 = condition_list[i*3]
                                operand_2 = condition_list[i*3 + 1]

                                operand_1_id = input_dict[operand_1]
                                operand_2_id = input_dict[operand_2]
                                
                                operator = condition_list[i*3+2]

                                if operator == '>':
                                    adj_mat[operand_1_id][operand_2_id] = 1
                                    is_visited[operand_1_id][operand_2_id] = 1
                                    que.put((operand_1_id, operand_2_id))

                                    adj_mat[operand_2_id][operand_1_id] = -1
                                    is_visited[operand_2_id][operand_1_id] = 1
                                    que.put((operand_2_id, operand_1_id))
                                    
                                elif operator == '<':
                                    adj_mat[operand_1_id, operand_2_id] = -1
                                    is_visited[operand_1_id][operand_2_id] = 1
                                    que.put((operand_1_id, operand_2_id))

                                    adj_mat[operand_2_id, operand_1_id] = 1
                                    is_visited[operand_2_id][operand_1_id] = 1
                                    que.put((operand_2_id, operand_1_id))

                            while not que.empty():
                                operand_1, operand_2 = que.get()

                                if adj_mat[operand_1][operand_2] == 1:
                                    for i in range(0, len(entity_list)):
                                        if (adj_mat[operand_1][i] == -1) and (not is_visited[operand_2][i]):
                                            adj_mat[operand_2][i] = -1
                                            adj_mat[i][operand_2] = 1
                                            is_visited[operand_2][i] = 1
                                            is_visited[i][operand_2] = 1
                                            que.put((operand_2, i))
                                            que.put((i, operand_2))
                                    
                                    for i in range(0, len(entity_list)):
                                        if (adj_mat[operand_2][i] == 1) and (not is_visited[operand_1][i]):
                                            adj_mat[operand_1][i] = 1
                                            adj_mat[i][operand_1] = -1
                                            is_visited[operand_1][i] = 1
                                            is_visited[i][operand_1] = 1
                                            que.put((operand_1, i))
                                            que.put((i, operand_1))

                                if adj_mat[operand_1][operand_2] == -1:
                                    for i in range(0, len(entity_list)):
                                        if (adj_mat[operand_1][i] == 1) and (not is_visited[i][operand_2]):
                                            adj_mat[i][operand_2] = -1
                                            adj_mat[operand_2][i] = 1
                                            is_visited[i][operand_2] = 1
                                            is_visited[operand_2][i] = 1
                                            que.put((i, operand_2))
                                            que.put((operand_2, i))
                                    
                                    for i in range(0, len(entity_list)):
                                        if (adj_mat[operand_2][i] == -1) and (not is_visited[operand_1][i]):
                                            adj_mat[operand_1][i] = -1
                                            adj_mat[i][operand_1] = 1
                                            is_visited[i][operand_1] = 1
                                            is_visited[operand_1][i] = 1
                                            que.put(operand_1, i)
                                            que.put(i, operand_1)

                            operand_1 = target_list[0]
                            operand_2 = target_list[1]

                            operand_1_id = input_dict[operand_1]
                            operand_2_id = input_dict[operand_2]

                            if adj_mat[operand_1_id][operand_2_id] == -1:
                                intermediate_list = [operand_2, operand_1]
                            else:
                                intermediate_list = [operand_1, operand_2]

                            self.list_stack.push(intermediate_list, new_list_name)

                            self.code_string += "from queue import Queue\n\
input_dict = dict()\n\
for cnt, i in enumerate({entity_list}):\n\
    input_dict[i] = cnt\n\
adj_mat = []\n\
for _ in range(len({entity_list})):\n\
    temp_list = []\n\
    for _ in range(len({entity_list})):\n\
        temp_list.append(0)\n\
    adj_mat.append(temp_list)\n\
is_visited = []\n\
for _ in range(len({entity_list})):\n\
    temp_list = []\n\
    for _ in range(len({entity_list})):\n\
        temp_list.append(0)\n\
    is_visited.append(temp_list)\n\
que = Queue()\n\
iterate_num = len({condition})//3\n\
for i in range(iterate_num):\n\
    operand_1 = {condition}[i*3]\n\
    operand_2 = {condition}[i*3 + 1]\n\
    operand_1_id = input_dict[operand_1]\n\
    operand_2_id = input_dict[operand_2]\n\
    operator = {condition}[i*3+2]\n\
    if operator == '>':\n\
        adj_mat[operand_1_id][operand_2_id] = 1\n\
        is_visited[operand_1_id][operand_2_id] = 1\n\
        que.put((operand_1_id, operand_2_id))\n\
        adj_mat[operand_2_id][operand_1_id] = -1\n\
        is_visited[operand_2_id][operand_1_id] = 1\n\
        que.put((operand_2_id, operand_1_id))\n\
    elif operator == '<':\n\
        adj_mat[operand_1_id, operand_2_id] = -1\n\
        is_visited[operand_1_id][operand_2_id] = 1\n\
        que.put((operand_1_id, operand_2_id))\n\
        adj_mat[operand_2_id, operand_1_id] = 1\n\
        is_visited[operand_2_id][operand_1_id] = 1\n\
        que.put((operand_2_id, operand_1_id))\n\
while not que.empty():\n\
    operand_1, operand_2 = que.get()\n\
    if adj_mat[operand_1][operand_2] == 1:\n\
        for i in range(0, len({entity_list})):\n\
            if (adj_mat[operand_1][i] == -1) and (not is_visited[operand_2][i]):\n\
                adj_mat[operand_2][i] = -1\n\
                adj_mat[i][operand_2] = 1\n\
                is_visited[operand_2][i] = 1\n\
                is_visited[i][operand_2] = 1\n\
                que.put((operand_2, i))\n\
                que.put((i, operand_2))\n\
        for i in range(0, len({entity_list})):\n\
            if (adj_mat[operand_2][i] == 1) and (not is_visited[operand_1][i]):\n\
                adj_mat[operand_1][i] = 1\n\
                adj_mat[i][operand_1] = -1\n\
                is_visited[operand_1][i] = 1\n\
                is_visited[i][operand_1] = 1\n\
                que.put((operand_1, i))\n\
                que.put((i, operand_1))\n\
    if adj_mat[operand_1][operand_2] == -1:\n\
        for i in range(0, len({entity_list})):\n\
            if (adj_mat[operand_1][i] == 1) and (not is_visited[i][operand_2]):\n\
                adj_mat[i][operand_2] = -1\n\
                adj_mat[operand_2][i] = 1\n\
                is_visited[i][operand_2] = 1\n\
                is_visited[operand_2][i] = 1\n\
                que.put((i, operand_2))\n\
                que.put((operand_2, i))\n\
        for i in range(0, len({entity_list})):\n\
            if (adj_mat[operand_2][i] == -1) and (not is_visited[operand_1][i]):\n\
                adj_mat[operand_1][i] = -1\n\
                adj_mat[i][operand_1] = 1\n\
                is_visited[i][operand_1] = 1\n\
                is_visited[operand_1][i] = 1\n\
                que.put(operand_1, i)\n\
                que.put(i, operand_1)\n\
operand_1 = {target}[0]\n\
operand_2 = {target}[1]\n\
operand_1_id = input_dict[operand_1]\n\
operand_2_id = input_dict[operand_2]\n\
if adj_mat[operand_1_id][operand_2_id] == -1:\n\
    {intermediate_list} = [operand_2, operand_1]\n\
else:\n\
    {intermediate_list}  = [operand_2, operand_1]\n".format(entity_list=entity_name, target=target_name, condition=condition_name, intermediate_list=new_list_name)
                    else:
                        print("not defined")
                    
            else: # if operand - scalar value
                # var_name = self.operand_names.pop(0)
                # self.operand_stack.push(i, var_name)

                var_name = self.operand_names.pop(0)

                if self.is_number(i):
                    i = self.to_float(i)
                    if i == int(i):
                        i = int(i)
                    self.code_string += '{} = {}\n'.format(var_name, i)
                    #if self.is_fraction(i):
                    #    self.code_string += '{var} = round({var}+1e-10, 2)\n'.format(var=var_name)
                    #    i = round(self.to_float(i)+1e-10, 2)
                else:
                    self.code_string += "{} = '{}'\n".format(var_name, i)
                
                self.operand_stack.push(i, var_name)


        result, name = self.operand_stack.pop()
        loc = {}
        # print(self.code_string)
        exec(self.code_string, globals(), loc)
        result = loc[name]

        str(result) # Raise Time out error for error hanlding
        
        try:
            if int(result) != self.to_float(result): # float
                result = '{:.2f}'.format(round(result+1e-10, 2))
                if str(result)[-3:] == ".00":
                    result = int(result[:-3])
                    self.code_string += "print(int(eval('{:.2f}'.format(round(%s+1e-10,2)))))"%name
                else:
                    self.code_string += "print('{:.2f}'.format(round(%s+1e-10,2)))"% name 
            else: # int
                result = int(result)
                self.code_string += 'print(int({}))'.format(name)
        except: # string
            name = name.replace('(', '')
            name = name.replace(')', '')
            self.code_string += 'print({})'.format(name)

        return result, self.code_string

