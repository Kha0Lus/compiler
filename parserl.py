from sly import Parser
from lexer import CmpLexer
from env import *
import nodes as nd

class CmpParser(Parser):
    tokens = CmpLexer.tokens



    @_('procedures main')
    def program_all(self, p):
        return nd.Root(p[0], p[1])


    @_('procedures PROCEDURE proc_head IS VAR declarations BEGIN commands END')
    def procedures(self, p):
        p[0].append(nd.Procedure(p[2], p[5], p[7]))
        return p[0]


    @_('procedures PROCEDURE proc_head IS BEGIN commands END')
    def procedures(self, p):
        p[0].append(nd.Procedure(p[2], None, p[5]))
        return p[0]


    @_('empty')
    def procedures(self, p):
        return []


    @_('PROGRAM IS VAR declarations BEGIN commands END')
    def main(self, p):
        return nd.Main(p[3], p[5])


    @_('PROGRAM IS BEGIN commands END')
    def main(self, p):
        return nd.Main(None, p[3])


    @_('commands command')
    def commands(self, p):
        p[0].append(nd.Command(p[1]))
        return p[0]


    @_('command')
    def commands(self, p):
        return [nd.Command(p[0])]


    @_('ID ASSIGN expression SEMIC')
    def command(self, p):
        return nd.Assign(p[0], p[2])


    @_('IF condition THEN commands ELSE commands ENDIF')
    def command(self, p):
        return nd.IfElse(p[1], p[3], p[5])

    
    @_('IF condition THEN commands ENDIF')
    def command(self, p):
        return nd.If(p[1], p[3])


    @_('WHILE condition DO commands ENDWHILE')
    def command(self, p):
        return nd.While(p[1], p[3])

    
    @_('REPEAT commands UNTIL condition SEMIC')
    def command(self, p):
        return nd.Repeat(p[1], p[3])

    
    @_('proc_head SEMIC')
    def command(self, p):
        return nd.ProcedureCall(p[0])


    @_('READ ID SEMIC')
    def command(self, p):
        return nd.Read(p[1])
        

    @_('WRITE value SEMIC')
    def command(self, p):
        return nd.Write(p[1])


    @_('ID LPAREN declarations RPAREN')
    def proc_head(self, p):
        return nd.ProcedureHead(p[0], p[2])


    @_('declarations COMMA ID')
    def declarations(self, p):
        p[0].append(nd.Variable(p[2]))
        return p[0]


    @_('ID')
    def declarations(self, p):
        return [nd.Variable(p[0])]


    @_('value')
    def expression(self, p):
        return p[0]


    @_('value PLUS value')
    def expression(self, p):
        return nd.Addition(p[0], p[2])
        

    @_('value MINUS value')
    def expression(self, p):
        return nd.Subtraction(p[0], p[2])


    @_('value TIMES value')
    def expression(self, p):
        return nd.Multiplication(p[0], p[2])


    @_('value DIVIDE value')
    def expression(self, p):
        return nd.Division(p[0], p[2])


    @_('value MODULO value')
    def expression(self, p):
        return nd.Modulo(p[0], p[2])


    @_('value EQ value')
    def condition(self, p):
        return nd.Equal(p[0], p[2])


    @_('value NEQ value')
    def condition(self, p):
        return nd.NotEqual(p[0], p[2])


    @_('value GT value')
    def condition(self, p):
        return nd.Greater(p[0], p[2])


    @_('value GEQ value')
    def condition(self, p):
        return nd.GreaterEqual(p[0], p[2])


    @_('value LT value')
    def condition(self, p):
        return nd.Lesser(p[0],p[2])


    @_('value LEQ value')
    def condition(self, p):
        return nd.LesserEqual(p[0], p[2])


    @_('ID')
    def value(self, p):
        return nd.Variable(p[0])


    @_('NUM')
    def value(self, p):
        return nd.Value(p[0])


    @_('')
    def empty(self, p):
        pass