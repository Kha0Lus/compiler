import sys

LIMIT = 2**63

class Env:
    def __init__(self) -> None:
        self.params = []
        self.variables = []
        self.address = {}
        self.jump = None
        # Each procedure is stored as a dictionary with following keys:
        # start -> address of first parameter
        # end -> address of last parameter
        # jump -> address containing line to jump after procedure ends
        # address -> line at which given procedure begins
        self.procedures = {}
        self.is_set = {}
        self.is_used = {}
        self.next_address = 7 # First 5 cells will be reserved for temporary values when computing mult/div/mod, 6th cell is for set
        self.current_proc = ""
        self.loop_depth = 0
        self.next_line = 1
        self.line = 0
        self.outfile = ""
        self.acc = ''
        self.block = ''


    def declare_variables(self, v):
        variables = []
        if v:
            for variable in v:
                variables.append(variable.name)
                self.is_set[variable.name] = False
                self.is_used[variable.name] = False
                self.address[variable.name] = self.next_address
                self.next_address += 1

        # Check if every variable is unique
        for i in range(1, len(variables)):
            if variables[i] in variables[:i]:
                sys.exit(f"ERROR: Duplicate of variable definition {variables[i]} in main program!")

        self.variables = variables


    def declare_procedure(self, name):
        self.current_proc = name
        self.procedures[name] = {}

  
    def declare_proc_params(self, p):
        params = []
        self.procedures[self.current_proc]['start'] = self.next_address
        if p:
            for param in p:
                params.append(param.name)
                self.is_set[param.name] = True
                self.is_used[param.name] = False
                self.address[param.name] = self.next_address
                self.next_address += 1
        self.procedures[self.current_proc]['end'] = self.next_address - 1

        # Check if every param is unique
        for i in range(1, len(params)):
            if  params[i] in params[:i]:
                sys.exit(f"ERROR: Duplicate of param {params[i]} in {self.current_proc} procedure definition!")
        
        self.params = params


    def declare_proc_variables(self, v):
        variables = []
        if v:
            for variable in v:
                # Check if variable name does not appear in procedures params
                if variable.name in self.params:
                    sys.exit(f"ERROR: Duplicate of param {variable.name} in {self.current_proc} procedure variables definition!")
                variables.append(variable.name)
                self.is_set[variable.name] = False
                self.is_used[variable.name] = False
                self.address[variable.name] = self.next_address
                self.next_address += 1
        self.jump = self.next_address
        self.procedures[self.current_proc]['jump'] = self.next_address
        self.next_address += 1

        # Check if every variable is unique
        for i in range(1, len(variables)):
            if variables[i] in variables[:i]:
                sys.exit(f"ERROR: Duplicate of variable {variables[i]} in {self.current_proc} procedure definition!")

        self.variables = variables


    def finalize_procedure(self, length):
        self.procedures[self.current_proc]['address'] = self.next_line
        self.next_line += length
        self.current_proc = ''
        self.acc = ''


    def get_procedure_info(self, name):
        return (self.procedures[name]['start'], self.procedures[name]['end'], self.procedures[name]['jump'], self.procedures[name]['address'])


    def clear(self):
        self.variables = []
        self.params = []
        self.address = {}
        self.is_set = {}
        self.is_used = {}


    def set_variable(self, name):
        self.is_set[name] = True


    def use_variable(self, name):
        self.is_used[name] = True

    def increase_depth(self):
        self.loop_depth += 1

    def decrease_depth(self):
        self.loop_depth -= 1

    def validate_var(self, name: str):
        """Checks if variable is initialized"""
        if self.loop_depth == 0:
            if not self.is_set[name]:
                sys.exit(f"ERROR: Variable {name} is not initialized!")
            else:
                self.use_variable(name)
        else:
            if not self.is_set[name]:
                print(f"WARNING: Variable {name} might not be initialized!")
            self.use_variable(name)


    def validate_on_loop_end(self):
        for var in self.variables:
            if self.is_used[var] and not self.is_set[var]:
                sys.exit(f"ERROR: Variable {var} was used before being set!")


    def is_declared(self, var):
        """Returns 'param' if var is a procedure parameter, 'var' if it's a variable and None if it isn't declared at all"""
        if var in self.variables:
            return 'var'
        elif var in self.params:
            return 'param'
        sys.exit(f"ERROR: Variable {var} is not defined!")

    def is_power_of_two(self, value):
        temp = bin(value)[2:]
        return temp[0] == '1' and not '1' in temp[1:]

    def should_optimize(self, value):
        temp = len(bin(value)[2:])
        if abs(2**temp - value) <= 3 or abs(2**(temp-1) - value) <= 3:
            return True
        return False

    def set_acc(self, name=None):
        self.acc = name

    def set_block(self, block=None):
        self.block = block

    
    def set_file(self, file_name):
        f=open(file_name,'w')
        f.close()
        self.outfile = file_name

    
    def make_SET(self, value):
        if value < LIMIT:
            return [('SET', value)]
        else:
            temp = int(bin(value)[-62:], 2)
            lst = []
            lst.append(('SET', temp))
            lst.append(('STORE', 6))
            z = value >> 62
            lst.append(('SET', z))
            for _ in range(62):
                lst.append(('ADD', 0))
            lst.append(('ADD', 6))
            return lst


    def to_assembly(self, lst):
        with open(self.outfile, 'a') as file:
            for cmd in lst:
                if cmd[0] == 'JUMP' or cmd[0] == 'JZERO' or cmd[0] == 'JPOS':
                    cmd = (cmd[0], cmd[1] + self.line)
                elif cmd[0] == 'SETPLUS':
                    cmd = ('SET', cmd[1] + self.line)
                elif cmd[0] == 'JUMPX':
                    cmd = ('JUMP', cmd[1])
                elif cmd[0] == 'JUMPBACK':
                    cmd = ('JUMP', self.line - cmd[1])
                elif cmd[0] == 'JPOSBACK':
                    cmd = ('JPOS', self.line - cmd[1])
                elif cmd[0] == 'JZEROBACK':
                    cmd = ('JZERO', self.line - cmd[1])
                file.write(f"{cmd[0]} {cmd[1]}\n")
                self.line += 1


env = Env()
    