from env import *

class Value:
    def __init__(self, value) -> None:
        self.value = value

    def generate(self):
        lst = []
        lst.extend(env.make_SET(self.value))
        return lst

    def get_variables(self):
        return []


class Variable:
    def __init__(self, name) -> None:
        self.name = name

    def generate(self):
        type_ = env.is_declared(self.name)
        lst = []
        env.validate_var(self.name)
        if type_ == 'param':
            lst.append(('LOADI', env.address[self.name]))
        else:
            lst.append(('LOAD', env.address[self.name]))

        return lst

    def get_variables(self):
        return [self.name]


class Addition:
    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right

    def get_variables(self):
        lst = []
        if isinstance(self.left, Variable):
            lst.append(self.left.name)
        if isinstance(self.right, Variable):
            lst.append(self.right.name)
        return lst


    def generate(self):
        left_type = 'value' if isinstance(self.left, Value) else env.is_declared(self.left.name)
        right_type = 'value' if isinstance(self.right, Value) else env.is_declared(self.right.name)
        if left_type != 'value':
            env.validate_var(self.left.name)
        if right_type != 'value':
            env.validate_var(self.right.name)

        left_load = 'LOADI' if left_type == 'param' else 'LOAD'
        left_add = 'ADDI' if left_type == 'param' else 'ADD'
        right_add = 'ADDI' if right_type == 'param' else 'ADD'

        lst = []
        # Value + Value -> simply add two values together and set the result into the ACC
        if left_type == 'value' and right_type == 'value':
            lst.extend(env.make_SET(self.left.value + self.right.value))
        # Variable + Variable -> Load one value and add another (LOAD/ADD for variables, LOADI/ADDI for procedure params)
        elif left_type != 'value' and right_type != 'value':
            if self.left.name == env.acc:
                lst.append((right_add, env.address[self.right.name]))
            elif self.right.name == env.acc:
                lst.append((left_add, env.address[self.left.name]))
            else:
                lst.append((left_load, env.address[self.left.name]))
                lst.append((right_add, env.address[self.right.name]))
        # Variable + Value -> Set value and then add the variable (Ditto)
        else:
            val, var, type_ = (self.left, self.right, right_type) if left_type == 'value' else (self.right, self.left, left_type)
            lst.extend(env.make_SET(val.value))
            if type_ == 'param':
                lst.append(('ADDI', env.address[var.name]))
            else:
                lst.append(('ADD', env.address[var.name]))

        return lst

 

class Subtraction:
    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right

    def get_variables(self):
        lst = []
        if isinstance(self.left, Variable):
            lst.append(self.left.name)
        if isinstance(self.right, Variable):
            lst.append(self.right.name)
        return lst

    def generate(self):
        left_type = 'value' if isinstance(self.left, Value) else env.is_declared(self.left.name)
        right_type = 'value' if isinstance(self.right, Value) else env.is_declared(self.right.name)
        if left_type != 'value':
            env.validate_var(self.left.name)
        if right_type != 'value':
            env.validate_var(self.right.name)

        left_load = 'LOADI' if left_type == 'param' else 'LOAD'
        right_sub = 'SUBI' if right_type == 'param' else 'SUB'

        lst = []
        # Value - Value
        if left_type == 'value' and right_type == 'value':
            lst.extend(env.make_SET(max(self.left.value - self.right.value, 0)))
        # Variable - Variable
        elif left_type != 'value' and right_type != 'value':
            if self.left.name == env.acc:
                lst.append((right_sub, env.address[self.right.name]))
            else:
                lst.append((left_load, env.address[self.left.name]))
                lst.append((right_sub, env.address[self.right.name]))
        # Value - Variable
        elif left_type == 'value':
            lst.extend(env.make_SET(self.left.value))
            lst.append((right_sub, env.address[self.right.name]))
        # Variable - Value
        else:
            lst.extend(env.make_SET(self.right.value))
            lst.append(('STORE', 1))
            lst.append((left_load, env.address[self.left.name]))
            lst.append(('SUB', 1))

        return lst


class Multiplication:
    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right

    def get_variables(self):
        lst = []
        if isinstance(self.left, Variable):
            lst.append(self.left.name)
        if isinstance(self.right, Variable):
            lst.append(self.right.name)
        return lst

    def generate(self):
        left_type = 'value' if isinstance(self.left, Value) else env.is_declared(self.left.name)
        right_type = 'value' if isinstance(self.right, Value) else env.is_declared(self.right.name)
        if left_type != 'value':
            env.validate_var(self.left.name)
        if right_type != 'value':
            env.validate_var(self.right.name)
        
        lst = []
        # Value * Value
        if left_type == 'value' and right_type == 'value':
            lst.extend(env.make_SET(self.left.value * self.right.value))
        # Variable * Variable
        elif left_type != 'value' and right_type != 'value':
            #  next_address -> higher value (v1)
            #  na + 1       -> lower value (v2)
            #  na + 2       -> 'current' multiplicator (m) (starts with 1, represents a certain power of two)
            #  na + 3       -> result (r), it will initially store higher value
            #
            #  Algorithm:
            #  0) check if either of variables is 0
            #  1) multiply by 2 both v1 and m until m > v2
            #  2) once m > v2, m = half m, v2 = v2 - m, r = v1
            #  3) If m = 0 end
            #  4) check if v2 >= m -> add v1 to r, v2 = v2 - m
            #  5) divide both v1 and m by 2 and repeat from 3)

            left_load = 'LOADI' if left_type == 'param' else 'LOAD'
            right_load = 'LOADI' if right_type == 'param' else 'LOAD'
            left_sub = 'SUBI' if left_type == 'param' else 'SUB'

            high = 1
            low = 2
            m = 3
            result = 4

            # Check if v1/v2 == 0
            if self.left.name != env.acc:
                lst.append((left_load, env.address[self.left.name]))
            lst.append(('JZERO', 3))                                         # v1 == 0 -> ...
            lst.append((right_load, env.address[self.right.name]))
            lst.append(('JPOS', 3))                                          # v2 == 0 -> ...
            lst.append(('SET', 0))
            lst.append(('JUMP', 52))                                       # jump over the rest of the expression

            lst.append((left_sub, env.address[self.left.name]))              # v2 >? v1
            lst.append(('JZERO', 7))                                         # v2 > v1

            # store v1 and v2 in proper addresses
            lst.append((right_load, env.address[self.right.name]))
            lst.append(('STORE', high))
            lst.append(('STORE', result))
            lst.append((left_load, env.address[self.left.name]))
            lst.append(('STORE', low))
            lst.append(('JUMP', 6))

            lst.append((right_load, env.address[self.right.name]))
            lst.append(('STORE', low))                                      # v1 >= v2
            lst.append((left_load, env.address[self.left.name]))
            lst.append(('STORE', high))
            lst.append(('STORE', result))

            # Set 1 to m
            lst.append(('SET', 1))

            # m * 2
            lst.append(('ADD', 0))
            lst.append(('STORE', m))       
            # is m > low?
            lst.append(('SUB', low))
            lst.append(('JPOS', 6))                  # leave the loop

            # high * 2
            lst.append(('LOAD', high))
            lst.append(('ADD', 0))
            lst.append(('STORE', high))
            lst.append(('LOAD', m))
            lst.append(('JUMPBACK', 8))                 # return to the beginning of the loop

            # m / 2, low = low - m, result = high
            lst.append(('LOAD', m))
            lst.append(('HALF', ''))
            lst.append(('STORE', m))
            lst.append(('LOAD', high))
            lst.append(('STORE', result))
            lst.append(('LOAD', low))
            lst.append(('SUB', m))
            lst.append(('STORE', low))

            # is low == 0?
            lst.append(('JPOS', 3))                 # low in ACC
            lst.append(('LOAD', result))
            lst.append(('JUMP', 18))              # leave the expression

            # is low >= m
            lst.append(('LOAD', m))
            lst.append(('SUB', low))
            lst.append(('JPOS', 7)) 

            # if low >= m, low = low - m, result = result + high
            lst.append(('LOAD', result))
            lst.append(('ADD', high))
            lst.append(('STORE', result))
            lst.append(('LOAD', low))
            lst.append(('SUB', m))
            lst.append(('STORE', low)) 

            # Divide high and m by 2
            lst.append(('LOAD', m))
            lst.append(('HALF', ''))
            lst.append(('STORE', m))
            lst.append(('LOAD', high))
            lst.append(('HALF', ''))
            lst.append(('STORE', high))
            lst.append(('LOAD', low))
            lst.append(('JUMPBACK', 19))

        # Variable * Value / Value * Variable
        else:
            value = self.left if isinstance(self.left, Value) else self.right
            if value is self.left:
                var = self.right.name
                type_ = right_type
            else:
                var = self.left.name
                type_ = left_type
            value = value.value

            load = 'LOADI' if type_ == 'param' else 'LOAD'
            add = 'ADDI' if type_ == 'param' else 'ADD'
            sub = 'SUBI' if type_ == 'param' else 'SUB'

            high = 1
            low = 2
            m = 3
            result = 4

            # Various optimizations for multiplication
            if value == 0:
                lst.append(('SET', 0))
                return lst
            elif value == 1:
                if var != env.acc:
                    lst.append((load, env.address[var]))
                return lst
            elif env.is_power_of_two(value):
                length = len(bin(value)[2:]) - 1
                if var != env.acc:
                    lst.append((load, env.address[var]))
                for _ in range(0, length):
                    lst.append(('ADD', 0))
                return lst
            elif value in range(3, 16):
                if var != env.acc:
                    lst.append((load, env.address[var]))
                for _ in range (1, value):
                    lst.append((add, env.address[var]))
                return lst
            elif env.should_optimize(value):
                t = len(bin(value)[2:])
                length = t - 1
                if var != env.acc:
                    lst.append((load, env.address[var]))
                for _ in range(0, length):
                    lst.append(('ADD', 0))
                temp = 2**t - value
                if temp <= 3:
                    lst.append(('ADD', 0))
                    for _ in range(temp):
                        lst.append((sub, env.address[var]))
                temp = value - 2**(t-1)
                if temp <= 3:
                    for _ in range(temp):
                        lst.append((add, env.address[var]))
                return lst

            # store v1 and v2 in proper addresses
            if var != env.acc:
                lst.append((load, env.address[var]))
            lst.append(('STORE', high))
            lst.append(('STORE', result))
            lst.extend(env.make_SET(value))
            lst.append(('STORE', low))

            # Set 1 to m
            lst.append(('SET', 1))

            # m * 2
            lst.append(('ADD', 0))
            lst.append(('STORE', m))       
            # is m > low?
            lst.append(('SUB', low))
            lst.append(('JPOS', 6))                  # leave the loop

            # high * 2
            lst.append(('LOAD', high))
            lst.append(('ADD', 0))
            lst.append(('STORE', high))
            lst.append(('LOAD', m))
            lst.append(('JUMPBACK', 8))                 # return to the beginning of the loop

            # m / 2, low = low - m, result = high
            lst.append(('LOAD', m))
            lst.append(('HALF', ''))
            lst.append(('STORE', m))
            lst.append(('LOAD', high))
            lst.append(('STORE', result))
            lst.append(('LOAD', low))
            lst.append(('SUB', m))
            lst.append(('STORE', low))

            # is low == 0?
            lst.append(('JPOS', 3))                 # low in ACC
            lst.append(('LOAD', result))
            lst.append(('JUMP', 18))              # leave the expression

            # is low >= m
            lst.append(('LOAD', m))
            lst.append(('SUB', low))
            lst.append(('JPOS', 7)) 

            # if low >= m, low = low - m, result = result + high
            lst.append(('LOAD', result))
            lst.append(('ADD', high))
            lst.append(('STORE', result))
            lst.append(('LOAD', low))
            lst.append(('SUB', m))
            lst.append(('STORE', low)) 

            # Divide high and m by 2
            lst.append(('LOAD', m))
            lst.append(('HALF', ''))
            lst.append(('STORE', m))
            lst.append(('LOAD', high))
            lst.append(('HALF', ''))
            lst.append(('STORE', high))
            lst.append(('LOAD', low))
            lst.append(('JUMPBACK', 19))

        return lst

    
class Division:
    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right

    def get_variables(self):
        lst = []
        if isinstance(self.left, Variable):
            lst.append(self.left.name)
        if isinstance(self.right, Variable):
            lst.append(self.right.name)
        return lst


    def generate(self):
        left_type = 'value' if isinstance(self.left, Value) else env.is_declared(self.left.name)
        right_type = 'value' if isinstance(self.right, Value) else env.is_declared(self.right.name)
        if left_type != 'value':
            env.validate_var(self.left.name)
        if right_type != 'value':
            env.validate_var(self.right.name)

        lst = []
        # Value / Value
        if left_type == 'value' and right_type == 'value':
            if self.right.value == 0:
                lst.append(('SET', 0))
            else:
                lst.extend(env.make_SET(self.left.value // self.right.value))
        # Variable / Variable
        elif left_type != 'value' and right_type != 'value':
            #  next_address -> higher value (v1)
            #  na + 1       -> lower value (v2)
            #  na + 2       -> 'current' multiplicator (m) (starts with 1, represents a certain power of two)
            #  na + 3       -> result (r), it will initially store higher value
            #  na + 4       -> count
            #
            #  Algorithm:
            #  -1) check if either of  variables is 0
            #   0) check if v1 > v2
            #  1) multiply by 2 both v2 and m while v2 >= v1
            #  2) once v1 > v2, half m, result = m, half m,  half v2, count = v2, half v2
            #  3) if m == 0 end
            #  4) check if v2 + count <= v1 -> result += m, count += v2
            #  5) divide both v2 and m by 2 and repeat from 3) 

            left_load = 'LOADI' if left_type == 'param' else 'LOAD'
            right_load = 'LOADI' if right_type == 'param' else 'LOAD'
            left_sub = 'SUBI' if left_type == 'param' else 'SUB'

            high = 1
            low = 2
            m = 3
            result = 4
            count = 5

            # check if v1/v2 == 0
            if self.left.name != env.acc:
                lst.append((left_load, env.address[self.left.name]))
            lst.append(('JZERO', 3))                                         # v1 == 0 -> ...
            lst.append((right_load, env.address[self.right.name]))
            lst.append(('JPOS', 3))                                          # v2 == 0 -> ...
            lst.append(('SET', 0))
            lst.append(('JUMP', 47))                                       # jump over the rest of the expression

            # check if v1 >= v2
            lst.append((left_sub, env.address[self.left.name]))
            lst.append(('JPOSBACK', 3))             # if v1 < v2 jump back and set 0

            # store v1 and v2 in proper addresses
            lst.append(('SET', 1))
            lst.append(('STORE', m))
            lst.append((left_load, env.address[self.left.name]))
            lst.append(('STORE', high))
            lst.append((right_load, env.address[self.right.name]))
            lst.append(('ADD', 0))              # I save one m/2 instruction by putting one low*2 here
            lst.append(('STORE', low))

            # while high >= low, low is in ACC
            lst.append(('SUB', high))
            lst.append(('JPOS', 8))          # leave the loop
            lst.append(('LOAD', m))
            lst.append(('ADD', 0))
            lst.append(('STORE', m))
            lst.append(('LOAD', low))
            lst.append(('ADD', 0))
            lst.append(('STORE', low))
            lst.append(('JUMPBACK',8 ))
            
            # set other variables
            lst.append(('LOAD', low))
            lst.append(('HALF', ''))
            lst.append(('STORE', count))
            lst.append(('HALF', ''))
            lst.append(('STORE', low))
            lst.append(('LOAD', m))
            lst.append(('STORE', result))
            lst.append(('HALF', ''))
            lst.append(('STORE', m))

            # while m > 0
            lst.append(('JZERO', 18))

            # is low + count > high?
            lst.append(('LOAD', low))
            lst.append(('ADD', count))
            lst.append(('SUB', high))
            lst.append(('JPOS', 7))
            lst.append(('LOAD', result))
            lst.append(('ADD', m))
            lst.append(('STORE', result))
            lst.append(('LOAD', count))
            lst.append(('ADD', low))
            lst.append(('STORE', count))

            lst.append(('LOAD', low))
            lst.append(('HALF', ''))
            lst.append(('STORE', low))
            lst.append(('LOAD', m))
            lst.append(('HALF', ''))
            lst.append(('STORE', m))
            lst.append(('JUMPBACK', 17))        # return to the beginning of while

            lst.append(('LOAD', result))
        
        # Value / Variable
        elif left_type == 'value':
            value = self.left.value
            var = self.right.name

            load = 'LOADI' if right_type == 'param' else 'LOAD'

            high = 1
            low = 2
            m = 3
            result = 4
            count = 5

            # Is Value = 0?
            if value == 0:
                lst.append(('SET', 0))
            else:
                # set value 
                lst.extend(env.make_SET(value))
                lst.append(('STORE', high))
                # check if var == 0                                      # var == 0 -> ...
                lst.append((load, env.address[var]))
                lst.append(('JPOS', 3))                                         
                lst.append(('SET', 0))
                lst.append(('JUMP', 45))                                       # jump over the rest of the expression

                # check if v1 >= v2
                lst.append(('SUB', high))
                lst.append(('JPOSBACK', 3))             # if v1 < v2 jump back and set 0

                # store v1 and v2 in proper addresses
                lst.append(('SET', 1))
                lst.append(('STORE', m))
                lst.append((load, env.address[var]))
                lst.append(('ADD', 0))              # I save one m/2 instruction by putting one low*2 here
                lst.append(('STORE', low))

                # while high >= low, low is in ACC
                lst.append(('SUB', high))
                lst.append(('JPOS', 8))          # leave the loop
                lst.append(('LOAD', m))
                lst.append(('ADD', 0))
                lst.append(('STORE', m))
                lst.append(('LOAD', low))
                lst.append(('ADD', 0))
                lst.append(('STORE', low))
                lst.append(('JUMPBACK',8 ))
                
                # set other variables
                lst.append(('LOAD', low))
                lst.append(('HALF', ''))
                lst.append(('STORE', count))
                lst.append(('HALF', ''))
                lst.append(('STORE', low))
                lst.append(('LOAD', m))
                lst.append(('STORE', result))
                lst.append(('HALF', ''))
                lst.append(('STORE', m))

                # while m > 0
                lst.append(('JZERO', 18))

                # is low + count > high?
                lst.append(('LOAD', low))
                lst.append(('ADD', count))
                lst.append(('SUB', high))
                lst.append(('JPOS', 7))
                lst.append(('LOAD', result))
                lst.append(('ADD', m))
                lst.append(('STORE', result))
                lst.append(('LOAD', count))
                lst.append(('ADD', low))
                lst.append(('STORE', count))

                lst.append(('LOAD', low))
                lst.append(('HALF', ''))
                lst.append(('STORE', low))
                lst.append(('LOAD', m))
                lst.append(('HALF', ''))
                lst.append(('STORE', m))
                lst.append(('JUMPBACK', 17))        # return to the beginning of while

                lst.append(('LOAD', result))

        # Variable / Value
        else:
            value = self.right.value
            var = self.left.name

            load = 'LOADI' if left_type == 'param' else 'LOAD'

            high = 1
            low = 2
            m = 3
            result = 4
            count = 5

            # Is Value = 0?
            if value == 0:
                lst.append(('SET', 0))
            elif env.is_power_of_two(value):
                length = len(bin(value)[2:]) - 1
                if var != env.acc:
                    lst.append((load, env.address[var]))
                for _ in range(0, length):
                    lst.append(('HALF', ''))
            else:
                # set value 
                lst.extend(env.make_SET(value))
                lst.append(('STORE', low))

                # check if var == 0                                      # var == 0 -> ...
                lst.append((load, env.address[var]))
                lst.append(('STORE', high))
                lst.append(('JPOS', 3))                                         
                lst.append(('SET', 0))
                lst.append(('JUMP', 46))                                       # jump over the rest of the expression

                # check if v1 >= v2
                lst.append(('LOAD', low))
                lst.append(('SUB', high))
                lst.append(('JPOSBACK', 4))             # if v1 < v2 jump back and set 0

                # store v1 and v2 in proper addresses
                lst.append(('SET', 1))
                lst.append(('STORE', m))
                lst.append(('LOAD', low))
                lst.append(('ADD', 0))              # I save one m/2 instruction by putting one low*2 here
                lst.append(('STORE', low))

                # while high >= low, low is in ACC
                lst.append(('SUB', high))
                lst.append(('JPOS', 8))          # leave the loop
                lst.append(('LOAD', m))
                lst.append(('ADD', 0))
                lst.append(('STORE', m))
                lst.append(('LOAD', low))
                lst.append(('ADD', 0))
                lst.append(('STORE', low))
                lst.append(('JUMPBACK',8 ))
                
                # set other variables
                lst.append(('LOAD', low))
                lst.append(('HALF', ''))
                lst.append(('STORE', count))
                lst.append(('HALF', ''))
                lst.append(('STORE', low))
                lst.append(('LOAD', m))
                lst.append(('STORE', result))
                lst.append(('HALF', ''))
                lst.append(('STORE', m))

                # while m > 0
                lst.append(('JZERO', 18))

                # is low + count > high?
                lst.append(('LOAD', low))
                lst.append(('ADD', count))
                lst.append(('SUB', high))
                lst.append(('JPOS', 7))
                lst.append(('LOAD', result))
                lst.append(('ADD', m))
                lst.append(('STORE', result))
                lst.append(('LOAD', count))
                lst.append(('ADD', low))
                lst.append(('STORE', count))

                lst.append(('LOAD', low))
                lst.append(('HALF', ''))
                lst.append(('STORE', low))
                lst.append(('LOAD', m))
                lst.append(('HALF', ''))
                lst.append(('STORE', m))
                lst.append(('JUMPBACK', 17))        # return to the beginning of while

                lst.append(('LOAD', result))

        return lst



class Modulo:
    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right

    def get_variables(self):
        lst = []
        if isinstance(self.left, Variable):
            lst.append(self.left.name)
        if isinstance(self.right, Variable):
            lst.append(self.right.name)
        return lst

    def generate(self):
        left_type = 'value' if isinstance(self.left, Value) else env.is_declared(self.left.name)
        right_type = 'value' if isinstance(self.right, Value) else env.is_declared(self.right.name)
        if left_type != 'value':
            env.validate_var(self.left.name)
        if right_type != 'value':
            env.validate_var(self.right.name)

        lst = []
        # Value % Value
        if left_type == 'value' and right_type == 'value':
            if self.right.value == 0:
                lst.append(('SET', 0))
            else:
                lst.extend(env.make_SET(self.left.value % self.right.value))
        # Variable / Variable
        elif left_type != 'value' and right_type != 'value':
            #  next_address -> higher value (v1)
            #  na + 1       -> lower value (v2)
            #  na + 2       -> 'current' multiplicator (m) (starts with 1, represents a certain power of two)
            #  na + 3       -> result (r), it will initially store higher value
            #  na + 4       -> count
            #
            #  Algorithm:
            #  Pretty much the same as with division, safe for returning v1-v3 instead of quotient

            left_load = 'LOADI' if left_type == 'param' else 'LOAD'
            right_load = 'LOADI' if right_type == 'param' else 'LOAD'
            left_sub = 'SUBI' if left_type == 'param' else 'SUB'

            high = 1
            low = 2
            m = 3
            result = 4
            count = 5

            # check if v1/v2 == 0
            if self.left.name != env.acc:
                lst.append((left_load, env.address[self.left.name]))
            lst.append(('JZERO', 3))                                         # v1 == 0 -> ...
            lst.append((right_load, env.address[self.right.name]))
            lst.append(('JPOS', 3))                                          # v2 == 0 -> ...
            lst.append(('SET', 0))
            lst.append(('JUMP', 51))                                       # jump over the rest of the expression

            # check if v1 >= v2
            lst.append((left_sub, env.address[self.left.name]))
            lst.append(('JPOS', 2))             # if v1 < v2 set v1 as the result
            lst.append(('JUMP', 3))
            lst.append((left_load, env.address[self.left.name]))
            lst.append(('JUMP', 46))

            # store v1 and v2 in proper addresses
            lst.append(('SET', 1))
            lst.append(('STORE', m))
            lst.append((left_load, env.address[self.left.name]))
            lst.append(('STORE', high))
            lst.append((right_load, env.address[self.right.name]))
            lst.append(('ADD', 0))              # I save one m/2 instruction by putting one low*2 here
            lst.append(('STORE', low))

            # while high >= low, low is in ACC
            lst.append(('SUB', high))
            lst.append(('JPOS', 8))          # leave the loop
            lst.append(('LOAD', m))
            lst.append(('ADD', 0))
            lst.append(('STORE', m))
            lst.append(('LOAD', low))
            lst.append(('ADD', 0))
            lst.append(('STORE', low))
            lst.append(('JUMPBACK',8 ))
            
            # set other variables
            lst.append(('LOAD', low))
            lst.append(('HALF', ''))
            lst.append(('STORE', count))
            lst.append(('HALF', ''))
            lst.append(('STORE', low))
            lst.append(('LOAD', m))
            lst.append(('STORE', result))
            lst.append(('HALF', ''))
            lst.append(('STORE', m))

            # while m > 0
            lst.append(('JZERO', 18))

            # is low + count > high?
            lst.append(('LOAD', low))
            lst.append(('ADD', count))
            lst.append(('SUB', high))
            lst.append(('JPOS', 7))
            lst.append(('LOAD', result))
            lst.append(('ADD', m))
            lst.append(('STORE', result))
            lst.append(('LOAD', count))
            lst.append(('ADD', low))
            lst.append(('STORE', count))

            lst.append(('LOAD', low))
            lst.append(('HALF', ''))
            lst.append(('STORE', low))
            lst.append(('LOAD', m))
            lst.append(('HALF', ''))
            lst.append(('STORE', m))
            lst.append(('JUMPBACK', 17))        # return to the beginning of while

            lst.append((left_load, env.address[self.left.name])) # read v1
            lst.append(('SUB', count))
        
        # Value % Variable
        elif left_type == 'value':
            value = self.left.value
            var = self.right.name

            load = 'LOADI' if right_type == 'param' else 'LOAD'

            high = 1
            low = 2
            m = 3
            result = 4
            count = 5

            if value == 0:
                lst.append(('SET', 0))
            else:
                # set value 
                lst.extend(env.make_SET(value))
                lst.append(('STORE', high))

                # check if var == 0                                       
                lst.append((load, env.address[var]))          # var == 0
                lst.append(('JPOS', 3))                                         
                lst.append(('SET', 0))
                lst.append(('JUMP', 50))                                       # jump over the rest of the expression

                # check if value > variable
                lst.append((load, env.address[var]))
                lst.append(('SUB', high))
                lst.append(('JPOS', 2))             # if v1 < v2 set v1 as the result
                lst.append(('JUMP', 3))
                lst.append(('LOAD', high))
                lst.append(('JUMP', 44))

                # store v1 and v2 in proper addresses
                lst.append(('SET', 1))
                lst.append(('STORE', m))
                lst.append((load, env.address[var]))
                lst.append(('ADD', 0))              # I save one m/2 instruction by putting one low*2 here
                lst.append(('STORE', low))

                # while high >= low, low is in ACC
                lst.append(('SUB', high))
                lst.append(('JPOS', 8))          # leave the loop
                lst.append(('LOAD', m))
                lst.append(('ADD', 0))
                lst.append(('STORE', m))
                lst.append(('LOAD', low))
                lst.append(('ADD', 0))
                lst.append(('STORE', low))
                lst.append(('JUMPBACK',8 ))
                
                # set other variables
                lst.append(('LOAD', low))
                lst.append(('HALF', ''))
                lst.append(('STORE', count))
                lst.append(('HALF', ''))
                lst.append(('STORE', low))
                lst.append(('LOAD', m))
                lst.append(('STORE', result))
                lst.append(('HALF', ''))
                lst.append(('STORE', m))

                # while m > 0
                lst.append(('JZERO', 18))

                # is low + count > high?
                lst.append(('LOAD', low))
                lst.append(('ADD', count))
                lst.append(('SUB', high))
                lst.append(('JPOS', 7))
                lst.append(('LOAD', result))
                lst.append(('ADD', m))
                lst.append(('STORE', result))
                lst.append(('LOAD', count))
                lst.append(('ADD', low))
                lst.append(('STORE', count))

                lst.append(('LOAD', low))
                lst.append(('HALF', ''))
                lst.append(('STORE', low))
                lst.append(('LOAD', m))
                lst.append(('HALF', ''))
                lst.append(('STORE', m))
                lst.append(('JUMPBACK', 17))        # return to the beginning of while

                lst.extend(env.make_SET(value)) # read v1
                lst.append(('SUB', count))
        # Variable % Value
        else:
            value = self.right.value
            var = self.left.name

            load = 'LOADI' if left_type == 'param' else 'LOAD'

            high = 1
            low = 2
            m = 3
            result = 4
            count = 5

            if value == 0:
                lst.append(('SET', 0))
            else:
                # set value
                lst.extend(env.make_SET(value))
                lst.append(('STORE', low))

                # check if var == 0                                       
                lst.append((load, env.address[var]))          # var == 0
                lst.append(('STORE', high))
                lst.append(('JPOS', 3))                                         
                lst.append(('SET', 0))
                lst.append(('JUMP', 50))                                       # jump over the rest of the expression

                # check if value > variable
                lst.append(('LOAD', low))
                lst.append(('SUB', high))
                lst.append(('JPOS', 2))             # if v1 < v2 set v1 as the result
                lst.append(('JUMP', 3))
                lst.append(('LOAD', high))
                lst.append(('JUMP', 44))

                # store v1 and v2 in proper addresses
                lst.append(('SET', 1))
                lst.append(('STORE', m))
                lst.append(('LOAD', low))
                lst.append(('ADD', 0))              # I save one m/2 instruction by putting one low*2 here
                lst.append(('STORE', low))

                # while high >= low, low is in ACC
                lst.append(('SUB', high))
                lst.append(('JPOS', 8))          # leave the loop
                lst.append(('LOAD', m))
                lst.append(('ADD', 0))
                lst.append(('STORE', m))
                lst.append(('LOAD', low))
                lst.append(('ADD', 0))
                lst.append(('STORE', low))
                lst.append(('JUMPBACK',8 ))
                
                # set other variables
                lst.append(('LOAD', low))
                lst.append(('HALF', ''))
                lst.append(('STORE', count))
                lst.append(('HALF', ''))
                lst.append(('STORE', low))
                lst.append(('LOAD', m))
                lst.append(('STORE', result))
                lst.append(('HALF', ''))
                lst.append(('STORE', m))

                # while m > 0
                lst.append(('JZERO', 18))

                # is low + count > high?
                lst.append(('LOAD', low))
                lst.append(('ADD', count))
                lst.append(('SUB', high))
                lst.append(('JPOS', 7))
                lst.append(('LOAD', result))
                lst.append(('ADD', m))
                lst.append(('STORE', result))
                lst.append(('LOAD', count))
                lst.append(('ADD', low))
                lst.append(('STORE', count))

                lst.append(('LOAD', low))
                lst.append(('HALF', ''))
                lst.append(('STORE', low))
                lst.append(('LOAD', m))
                lst.append(('HALF', ''))
                lst.append(('STORE', m))
                lst.append(('JUMPBACK', 17))        # return to the beginning of while

                lst.append((load, env.address[var])) # read v1
                lst.append(('SUB', count))

        return lst



class Equal:
    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right

    def generate(self):
        # x == y    ===  (x >= y) and (x <= y)  ===  !(x > y) and !(x < y)
        # LOAD x
        # SUB y
        # JPOS ...
        # LOAD y
        # SUB x
        # JPOS ...
        left_type = 'value' if isinstance(self.left, Value) else env.is_declared(self.left.name)
        right_type = 'value' if isinstance(self.right, Value) else env.is_declared(self.right.name)
        if left_type != 'value':
            env.validate_var(self.left.name)
        if right_type != 'value':
            env.validate_var(self.right.name)

        left_load = 'LOADI' if left_type == 'param' else 'LOAD'
        right_load = 'LOADI' if right_type == 'param' else 'LOAD'
        left_sub = 'SUBI' if left_type == 'param' else 'SUB'
        right_sub = 'SUBI' if right_type == 'param' else 'SUB'
        
        lst = []
        # Value == Value
        if left_type == 'value' and right_type == 'value':
            lst.append(self.left.value == self.right.value)
        # Variable == Variable
        elif left_type != 'value' and right_type != 'value':
            if self.left.name == env.acc and env.block != 'while':
                lst.append((right_sub, env.address[self.right.name]))
                lst.append(('JPOS', None))
                lst.append((right_load, env.address[self.right.name]))
                lst.append((left_sub, env.address[self.left.name]))
                lst.append(('JPOS', None))
            elif self.right.name == env.acc and env.block != 'while':
                lst.append((left_sub, env.address[self.left.name]))
                lst.append(('JPOS', None))
                lst.append((left_load, env.address[self.left.name]))
                lst.append((right_sub, env.address[self.right.name]))
                lst.append(('JPOS', None))
            else:
                lst.append((right_load, env.address[self.right.name]))
                lst.append((left_sub, env.address[self.left.name]))
                lst.append(('JPOS', None))

                lst.append((left_load, env.address[self.left.name]))
                lst.append((right_sub, env.address[self.right.name]))
                lst.append(('JPOS', None))
        # Value == Variable 
        elif left_type == 'value':
            if self.left.value == 0:
                if self.right.name != env.acc or env.block == 'while':
                    lst.append((right_load, env.address[self.right.name]))
                    env.set_acc(self.right.name)
                lst.append(('dunno', None)) # used later in if statement
                return lst

            lst.extend(env.make_SET(self.left.value))
            lst.append(('STORE', 1))
            lst.append((right_sub, env.address[self.right.name]))      
            lst.append(('JPOS', None))

            lst.append((right_load, env.address[self.right.name]))
            lst.append(('SUB', 1))
            lst.append(('JPOS', None))
        # Variable == Value
        else:
            if self.right.value == 0:
                if self.left.name != env.acc or env.block == 'while':
                    lst.append((left_load, env.address[self.left.name]))
                    env.set_acc(self.left.name)
                lst.append(('dunno', None)) # used later in if statement
                return lst

            lst.extend(env.make_SET(self.right.value))
            lst.append(('STORE', 1))
            lst.append((left_sub, env.address[self.left.name]))      
            lst.append(('JPOS', None))
            
            lst.append((left_load, env.address[self.left.name]))
            lst.append(('SUB', 1))
            lst.append(('JPOS', None))

        env.set_acc()
        return lst



class NotEqual:
    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right

    def generate(self):
        # x != y    ===  (x > y) or (x < y)
        # LOAD x
        # SUB y
        # JPOS 4 // we can skip next check
        # LOAD y
        # SUB x
        # JZERO ...
        left_type = 'value' if isinstance(self.left, Value) else env.is_declared(self.left.name)
        right_type = 'value' if isinstance(self.right, Value) else env.is_declared(self.right.name)
        if left_type != 'value':
            env.validate_var(self.left.name)
        if right_type != 'value':
            env.validate_var(self.right.name)

        left_load = 'LOADI' if left_type == 'param' else 'LOAD'
        right_load = 'LOADI' if right_type == 'param' else 'LOAD'
        left_sub = 'SUBI' if left_type == 'param' else 'SUB'
        right_sub = 'SUBI' if right_type == 'param' else 'SUB'

        lst = []
        # Value != Value
        if left_type == 'value' and right_type == 'value':
            lst.append(self.left.value != self.right.value)
        # Variable != Variable
        elif left_type != 'value' and right_type != 'value':
            if self.left.name == env.acc and env.block != 'while':
                lst.append((right_sub, env.address[self.right.name]))
                lst.append(('JPOS', 4))
                lst.append((right_load, env.address[self.right.name]))
                lst.append((left_sub, env.address[self.left.name]))
                lst.append(('JZERO', None))
            elif self.right.name == env.acc and env.block != 'while':
                lst.append((left_sub, env.address[self.left.name]))
                lst.append(('JZERO', None))
                lst.append((left_load, env.address[self.left.name]))
                lst.append((right_sub, env.address[self.right.name]))
                lst.append(('JPOS', 4))
            else:
                lst.append((left_load, env.address[self.left.name]))
                lst.append((right_sub, env.address[self.right.name]))
                lst.append(('JPOS', 4))

                lst.append((right_load, env.address[self.right.name]))
                lst.append((left_sub, env.address[self.left.name]))
                lst.append(('JZERO', None))
        # Value != Variable 
        elif left_type == 'value':
            if self.left.value == 0:
                if self.right.name != env.acc or env.block == 'while':
                    lst.append((right_load, env.address[self.right.name]))
                    env.set_acc(self.right.name)
                lst.append(('dunno', None)) # used later in if statement
                return lst

            lst.extend(env.make_SET(self.left.value))
            lst.append(('STORE', 1))
            lst.append((right_sub, env.address[self.right.name]))
            lst.append(('JPOS', 4))
            
            lst.append((right_load, env.address[self.right.name]))
            lst.append(('SUB', 1))
            lst.append(('JZERO', None))
        # Variable != Value
        else:
            if self.right.value == 0:
                if self.left.name != env.acc or env.block == 'while':
                    lst.append((left_load, env.address[self.left.name]))
                    env.set_acc(self.left.name)
                lst.append(('dunno', None)) # used later in if statement
                return lst

            lst.extend(env.make_SET(self.right.value))
            lst.append(('STORE', 1))
            lst.append((left_sub, env.address[self.left.name]))
            lst.append(('JPOS', 4))
            
            lst.append((left_load, env.address[self.left.name]))
            lst.append(('SUB', 1))
            lst.append(('JZERO', None))

        env.set_acc()
        return lst


class Lesser:
    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right

    def generate(self):
        # x < y
        # LOAD y
        # SUB x
        # JZERO ...
        left_type = 'value' if isinstance(self.left, Value) else env.is_declared(self.left.name)
        right_type = 'value' if isinstance(self.right, Value) else env.is_declared(self.right.name)
        if left_type != 'value':
            env.validate_var(self.left.name)
        if right_type != 'value':
            env.validate_var(self.right.name)

        right_load = 'LOADI' if right_type == 'param' else 'LOAD'
        left_sub = 'SUBI' if left_type == 'param' else 'SUB'
        
        lst = []
        # Value < Value
        if left_type == 'value' and right_type == 'value':
            lst.append(self.left.value < self.right.value)
        # Variable < Variable
        elif left_type != 'value' and right_type != 'value':
            if self.right.name != env.acc or env.block == 'while':
                lst.append((right_load, env.address[self.right.name]))
            lst.append((left_sub, env.address[self.left.name]))
            lst.append(('JZERO', None))
        # Value < Variable 
        elif left_type == 'value':
            lst.extend(env.make_SET(self.left.value))
            lst.append(('STORE', 1))
            lst.append((right_load, env.address[self.right.name]))
            lst.append(('SUB', 1))
            lst.append(('JZERO', None))
        # Variable < Value
        else:
            lst.extend(env.make_SET(self.right.value))
            lst.append((left_sub, env.address[self.left.name]))
            lst.append(('JZERO', None))
        
        env.set_acc()
        return lst


class LesserEqual:
    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right

    def generate(self):
        # x <= y  ===  !(x > y)
        # LOAD x
        # SUB y
        # JPOS ...
        left_type = 'value' if isinstance(self.left, Value) else env.is_declared(self.left.name)
        right_type = 'value' if isinstance(self.right, Value) else env.is_declared(self.right.name)
        if left_type != 'value':
            env.validate_var(self.left.name)
        if right_type != 'value':
            env.validate_var(self.right.name)

        left_load = 'LOADI' if left_type == 'param' else 'LOAD'
        right_sub = 'SUBI' if right_type == 'param' else 'SUB'

        lst = []
        # Value >= Value
        if left_type == 'value' and right_type == 'value':
            lst.append(self.left.value >= self.right.value)
        # Variable >= Variable
        elif left_type != 'value' and right_type != 'value':
            if self.left.name != env.acc or env.block == 'while': 
                lst.append((left_load, env.address[self.left.name]))
            lst.append((right_sub, env.address[self.right.name]))
            lst.append(('JPOS', None))
        # Variable >= Value 
        elif right_type == 'value':
            lst.extend(env.make_SET(self.right.value))
            lst.append(('STORE', 1))
            lst.append((left_load, env.address[self.left.name]))
            lst.append(('SUB', 1))
            lst.append(('JPOS', None))
        # Value >= Variable
        else:
            lst.extend(env.make_SET(self.left.value))
            lst.append((right_sub, env.address[self.right.name]))
            lst.append(('JPOS', None))
        
        env.set_acc()
        return lst


class Greater:
    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right

    def generate(self):
        # x > y
        # LOAD x
        # SUB y 
        # JZERO ...
        left_type = 'value' if isinstance(self.left, Value) else env.is_declared(self.left.name)
        right_type = 'value' if isinstance(self.right, Value) else env.is_declared(self.right.name)
        if left_type != 'value':
            env.validate_var(self.left.name)
        if right_type != 'value':
            env.validate_var(self.right.name)

        left_load = 'LOADI' if left_type == 'param' else 'LOAD'
        right_sub = 'SUBI' if right_type == 'param' else 'SUB'
        
        lst = []
        # Value > Value
        if left_type == 'value' and right_type == 'value':
            lst.append(self.left.value > self.right.value)
        # Variable > Variable
        elif left_type != 'value' and right_type != 'value':
            if self.left.name != env.acc or env.block == 'while':
                lst.append((left_load, env.address[self.left.name]))
            lst.append((right_sub, env.address[self.right.name]))
            lst.append(('JZERO', None))
        # Variable > Value 
        elif right_type == 'value':
            lst.extend(env.make_SET(self.right.value))
            lst.append(('STORE', 1))
            lst.append((left_load, env.address[self.left.name]))
            lst.append(('SUB', 1))
            lst.append(('JZERO', None)) 
        # Value > Variable
        else:
            lst.extend(env.make_SET(self.left.value))
            lst.append((right_sub, env.address[self.right.name]))
            lst.append(('JZERO', None))
        
        env.set_acc()
        return lst


class GreaterEqual:
    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right

    def generate(self):
        # x >= y  ===   !(x < y)
        # LOAD y
        # SUB x 
        # JPOS ...
        left_type = 'value' if isinstance(self.left, Value) else env.is_declared(self.left.name)
        right_type = 'value' if isinstance(self.right, Value) else env.is_declared(self.right.name)
        if left_type != 'value':
            env.validate_var(self.left.name)
        if right_type != 'value':
            env.validate_var(self.right.name)
        
        right_load = 'LOADI' if right_type == 'param' else 'LOAD'
        left_sub = 'SUBI' if left_type == 'param' else 'SUB'

        lst = []
        # Value <= Value
        if left_type == 'value' and right_type == 'value':
            lst.append(self.left.value <= self.right.value)
        # Variable <= Variable
        elif left_type != 'value' and right_type != 'value':
            if self.right.name != env.acc or env.block == 'while':
                lst.append((right_load, env.address[self.right.name]))
            lst.append((left_sub, env.address[self.left.name]))
            lst.append(('JPOS', None))
        # Value <= Variable 
        elif left_type == 'value':
            lst.extend(env.make_SET(self.left.value))
            lst.append(('STORE', 1))
            lst.append((right_load, env.address[self.right.name]))
            lst.append(('SUB', 1))
            lst.append(('JPOS', None))
        # Variable <= Value
        else:
            lst.extend(env.make_SET(self.right.value))
            lst.append((left_sub, env.address[self.left.name]))
            lst.append(('JPOS', None))

        env.set_acc()
        return lst


class Assign:
    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right

    def generate(self):
        lst = self.right.generate()

        type_ = env.is_declared(self.left)
        vars = self.right.get_variables()
        if not env.is_set[self.left]:
            if self.left not in vars:
                env.set_variable(self.left)

        env.set_acc(self.left)

        if type_ == 'param':
            lst.append(('STOREI', env.address[self.left]))
        else:
            lst.append(('STORE', env.address[self.left]))

        return lst
        

class Read:
    def __init__(self, id) -> None:
        self.id = id

    def generate(self):
        lst = []
        type_ = env.is_declared(self.id)
        if not type_:
            sys.exit(f"ERROR: Variable {self.id} is not defined!")
        # TODO What if we try to read a procedure parameter? 
        if type_ == 'param':
            pass
        else:
            lst.append(('GET', env.address[self.id]))
            env.set_variable(self.id)
        return lst


class Write:
    def __init__(self, value) -> None:
        self.value = value

    def generate(self):
        lst = []
        type_ = 'value' if isinstance(self.value, Value) else env.is_declared(self.value.name)
        if not type_:
            sys.exit(f"ERROR: Variable {self.id.name} is not defined")
        elif type_ == 'value':
            lst.extend(env.make_SET(self.value.value))
            lst.append(('PUT', 0))
            env.set_acc()
        else:
            env.validate_var(self.value.name)
            lst.append(('PUT', env.address[self.value.name]))

        return lst


class ProcedureHead:
    def __init__(self, name, params) -> None:
        self.name = name
        self.params = params


class ProcedureCall:
    def __init__(self, proc_head) -> None:
        self.name = proc_head.name
        self.params = proc_head.params

    def generate(self):
        variables = []
        types = []
        for variable in self.params:
            types.append(env.is_declared(variable.name) )
            variables.append(variable.name)
            env.set_variable(variable.name)

        # Check if procedure is being called recursively
        if self.name == env.current_proc:
            sys.exit(f"ERROR: Recursive call of a {self.name} procedure!")

        # Check if procedure has been defined
        if self.name not in env.procedures.keys():
            sys.exit(f"ERROR: Procedure {self.name} is not defined!")

        (start, end, jump, address) = env.get_procedure_info(self.name)
        # Check if number of parameters is correct
        if (end - start+1) != len(variables):
            sys.exit(f"ERROR: Incorrect number of parameters in {self.name} procedure call!\nExpected: {end-start+1}\nGiven: {len(variables)}")

        lst = []
        # Prepare parameters for a procedure call
        for i in range(0, end-start+1):
            if types[i] == 'param':
                lst.append(('LOAD', env.address[variables[i]]))
                lst.append(('STORE', start + i))
            else:
                lst.append(('SET', env.address[variables[i]]))
                lst.append(('STORE', start + i))
        # Prepare jump from the procedure
        # x     SET x + 3
        # x+1   STORE [jump_address]
        # x+2   JUMP [procedure_address]
        # x+3   ...
        lst.append(('SETPLUS', 3))
        lst.append(('STORE', jump))
        # Do not add line number for that jump
        lst.append(('JUMPX', address))

        env.set_acc()
        return lst
            


class Command:
    def __init__(self, command) -> None:
        self.command = command

    def generate(self):
        return self.command.generate()


class If:
    def __init__(self, condition, commands) -> None:
        self.condition = condition
        self.commands = commands
        
    def generate(self):
        env.set_block('if')
        env.increase_depth()
        cond_lst = self.condition.generate()
        jump_required = True

        # Check if length of cond_lst is 1 -> condition is True/False
        if len(cond_lst) == 1:
            if cond_lst[0]:
                jump_required = False
            # The condition is false, there is no need of any further processing
            else:
                env.decrease_depth()
                return []
       
        comm_lst = []
        for command in self.commands:
            l = command.generate()
            comm_lst.extend(l)
        length = len(comm_lst)
        if not jump_required:
            env.decrease_depth()
            return comm_lst
        # x     JZERO/JPOS n + 1 -> later it will be replaced with x + (n + 1)
        # x+1   commands...
        # x+2   len(commands) = n
        #  .
        #  .
        #  .
        # x+n   last command
        # x+n+1 target of the jump
    
        # Replace empty jumps with local values (they will later be adjusted to point to correct line)
        # Check if the condition is '==' -> there are two jumps to be filled in this one
        if isinstance(self.condition, Equal):
            if cond_lst[-1][0] == 'dunno':
                cond_lst[-1] = ('JPOS', length + 1)
            else:
                cond_lst[-1] = (cond_lst[-1][0], length + 1)
                cond_lst[-4] = (cond_lst[-4][0], length + 4)
        else:
            if cond_lst[-1][0] == 'dunno':
                cond_lst[-1] = ('JZERO', length + 1)
            else:
                cond_lst[-1] = (cond_lst[-1][0], length + 1)
        cond_lst.extend(comm_lst)
        
        env.decrease_depth()

        env.set_acc()
        return cond_lst
            

class IfElse:
    def __init__(self, condition, commands, else_commands) -> None:
        self.condition = condition
        self.commands = commands
        self.else_commands = else_commands

    def generate(self):
        env.set_block('ifelse')
        env.increase_depth()
        cond_lst = self.condition.generate()
        if_required = True
        else_required = True

        # Check if length of cond_lst is 1 -> condition is True/False
        if len(cond_lst) == 1:
            # If true, leave only if block
            if cond_lst[0]:
                else_required = False
            # Else leave only else block
            else:
                if_required = False
        
        if_lst = []
        else_lst = []
        for command in self.commands:
            l = command.generate()
            if_lst.extend(l)
        if not else_required:
            env.decrease_depth()
            return if_lst
        env.set_acc()
        for command in self.else_commands:
            l = command.generate()
            else_lst.extend(l)
        if not if_required:
            env.decrease_depth()
            return else_lst
        if_length = len(if_lst)
        else_length = len(else_lst)

        # x     JZERO/JPOS n + 2 -> jump to ELSE block
        # x+1   start of IF block                   //len(commands) = n
        # x+2   
        #  .
        #  .
        #  .
        # x+n   end of IF block
        # x+n+1 JUMP over ELSE block (m + 1)
        # x+z+1  (z = n+1) start of ELSE block        //len(else_commands) = m
        # x+z+2 
        #  .
        #  .
        #  .
        # x+z+m  end of ELSE block
        # x+z+m+1 target of the jump before ELSE block    // x+n+1+(m+1)
    
        # Replace empty jumps with local values (they will later be adjusted to point to correct line)
        # Check if the condition is '==' -> there are two jumps to be filled in this one
        if isinstance(self.condition, Equal):
            if cond_lst[-1][0] == 'dunno':
                cond_lst[-1] = ('JPOS', if_length + 2)
            else:
                cond_lst[-1] = (cond_lst[-1][0], if_length + 2)
                cond_lst[-4] = (cond_lst[-4][0], if_length + 5)
        else:
            if cond_lst[-1][0] == 'dunno':
                cond_lst[-1] = ('JZERO', if_length + 2)
            else:
                cond_lst[-1] = (cond_lst[-1][0], if_length + 2)
        cond_lst.extend(if_lst)
        cond_lst.append(('JUMP', else_length + 1))
        cond_lst.extend(else_lst)

        env.decrease_depth()
        env.set_acc()
        return cond_lst


class While:
    def __init__(self, condition, commands) -> None:
        self.condition = condition
        self.commands = commands

    def generate(self):
        env.set_block('while')
        env.increase_depth()
        cond_lst = self.condition.generate()
        cond_length = len(cond_lst)

        # Check if length of cond_lst is 1 -> condition is True/False
        if len(cond_lst) == 1:
            if not cond_lst[0]:
                env.decrease_depth()
                return []
        else:
            comm_lst = []
            for command in self.commands:
                l = command.generate()
                comm_lst.extend(l)
            length = len(comm_lst)

            # x-k+1   start of condition          // len(condition) = k
            #  .
            #  .
            #  .
            # x-1
            # x     JZERO/JPOS n + 2 -> later it will be replaced with x + (n + 2)
            # x+1   commands...
            # x+2   len(commands) = n
            #  .
            #  .
            #  .
            # x+n   last command
            # x+n+1 JUMP back to the beginning of while
            # x+n+2 target of the jump

            # Replace empty jumps with local values (they will later be adjusted to point to correct line)
            # Check if the condition is '==' -> there are two jumps to be filled in this one
            if isinstance(self.condition, Equal):
                if cond_lst[-1][0] == 'dunno':
                    cond_lst[-1] = ('JPOS', length + 2)
                else:
                    cond_lst[-1] = (cond_lst[-1][0], length + 2)
                    cond_lst[-4] = (cond_lst[-4][0], length + 5)
            else:
                if cond_lst[-1][0] == 'dunno':
                    cond_lst[-1] = ('JZERO', length + 2)
                else:
                    cond_lst[-1] = (cond_lst[-1][0], length + 2)
            cond_lst.extend(comm_lst)
            cond_lst.append(('JUMPBACK', length + cond_length))

            env.decrease_depth()
            env.set_acc()
            return cond_lst


class Repeat:
    def __init__(self, commands, condition) -> None:
        self.commands = commands
        self.condition = condition

    def generate(self):
        env.set_acc()
        env.set_block('repeat')
        env.increase_depth()
        comm_lst = []
        for command in self.commands:
            l = command.generate()
            comm_lst.extend(l)
        comm_length = len(comm_lst)

        cond_lst = self.condition.generate()
        cond_length = len(cond_lst)

        if cond_length == 1 and isinstance(cond_lst[0], bool):
            if not cond_lst[0]:
                env.decrease_depth()
                return comm_lst
        else:
            # TODO consider a case where a condition is always true
            if isinstance(self.condition, Lesser) or isinstance(self.condition, Greater):
                cond_lst[-1] = ('JZEROBACK', comm_length + cond_length - 1)
            elif isinstance(self.condition, LesserEqual) or isinstance(self.condition, GreaterEqual):
                cond_lst[-1] = ('JPOSBACK', comm_length + cond_length - 1)
            elif isinstance(self.condition, Equal):
                if cond_lst[-1][0] == 'dunno':
                    cond_lst[-1] = ('JPOSBACK', comm_length + cond_length - 1)
                else:
                    cond_lst[-4] = ('JPOSBACK', comm_length + cond_length - 4)
                    cond_lst[-1] = ('JPOSBACK', comm_length + cond_length - 1)
            elif isinstance(self.condition, NotEqual):
                if cond_lst[-1][0] == 'dunno':
                    cond_lst[-1] = ('JZEROBACK', comm_length + cond_length - 1)
                else:
                    cond_lst[-4] = ('JPOS', 4)
                    cond_lst[-1] = ('JZEROBACK', comm_length + cond_length - 1)
            comm_lst.extend(cond_lst)
            env.decrease_depth()
            return comm_lst


class Main:
    def __init__(self, variables, commands) -> None:
        self.variables = variables
        self.commands = commands

    def generate(self):
        if self.variables:
            env.declare_variables(self.variables)

        lst = []
        for command in self.commands:
            l = command.generate()
            lst.extend(l)
        lst.append(('HALT', ''))
        env.to_assembly(lst)

    

class Procedure:
    def __init__(self, proc_head, variables, commands) -> None:
        self.name = proc_head.name
        self.params = proc_head.params
        self.variables = variables
        self.commands = commands

    def generate(self):
        env.declare_procedure(self.name)
        env.declare_proc_params(self.params)
        env.declare_proc_variables(self.variables)

        lst = []
        for command in self.commands:
            l = command.generate()
            lst.extend(l)
        # Leave the procedure
        lst.append(('JUMPI', env.jump))
        env.clear()
        env.finalize_procedure(len(lst))

        return lst


class Root:
    def __init__(self, procedures, main) -> None:
        self.procedures = procedures
        self.main = main

    def generate(self):
        lst = []
        if self.procedures:
            for procedure in self.procedures:
                l = procedure.generate()
                lst.extend(l)
        else:
            env.next_line = 0
        if lst:
            env.to_assembly([('JUMP', env.next_line)])
            env.to_assembly(lst) 
        self.main.generate()
        
