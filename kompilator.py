from lexer import CmpLexer
from parserl import CmpParser
from env import env 
import sys


if len(sys.argv) < 3:
    sys.exit("Too few arguments!")

in_file = sys.argv[1]
out_file = sys.argv[2]

env.set_file(out_file)


with open(in_file) as file:
    text = file.read()

    lexer = CmpLexer()
    parser = CmpParser()

    root = parser.parse(lexer.tokenize(text))
    root.generate()

    # print(env.procedures)
    # print(env.address)


