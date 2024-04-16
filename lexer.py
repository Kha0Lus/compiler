from sly import Lexer

class CmpLexer(Lexer):
    tokens = {PLUS, MINUS, TIMES, DIVIDE, MODULO, EQ, NEQ, LT, GT, LEQ, GEQ, NUM, ID, PROCEDURE, 
              VAR, IS, BEGIN, END, PROGRAM, IF, THEN, ELSE, ENDIF, WHILE, DO, ENDWHILE, UNTIL,
              READ, WRITE, LPAREN, RPAREN, ASSIGN, SEMIC, COMMA, REPEAT}


    ignore = '\t '
    ignore_comment = r'\[[^\[]*\]'
    
    COMMA = r','
    SEMIC =r';'
    PLUS = r'\+'
    MINUS   = r'-'
    NUM = r'\d+'
    TIMES   = r'\*'
    DIVIDE  = r'/'
    MODULO = r'%'
    ASSIGN = r':='
    EQ = r'='
    NEQ  = r'!='
    LEQ = r'<='
    GEQ = r'>='
    LT = r'<'
    GT = r'>'
    LPAREN = r'\('
    RPAREN = r'\)'
    PROCEDURE = r'PROCEDURE'
    VAR = r'VAR'
    IS = r'IS'
    BEGIN = r'BEGIN'
    ENDIF = r'ENDIF'
    ENDWHILE = r'ENDWHILE'
    END = r'END'
    PROGRAM = r'PROGRAM'
    IF = r'IF'
    THEN = r'THEN'
    ELSE = r'ELSE'
    WHILE = r'WHILE'
    DO = r'DO'
    REPEAT = r'REPEAT'
    UNTIL = r'UNTIL'
    READ = r'READ'
    WRITE = r'WRITE'
    ID = r'[_a-z]+'

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += 1

    def NUM(self, t):
        t.value = int(t.value)
        return t


    def error(self, t):
        pass
