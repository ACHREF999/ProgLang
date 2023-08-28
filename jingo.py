# IMPORTS:
import math
import os
import re

from string_with_arrows import string_with_arrows
import string

# Binary Op Basic Tokens Types :

TT_INT = 'TT_INT'
TT_FLOAT = 'FLOAT'
TT_PLUS = 'PLUS'
TT_MINUS = 'MINUS'
TT_MUL = 'MUL'
TT_DIV = 'DIV'
TT_LPAREN = 'LAPERN'
TT_RPAREN = 'RPAREN'
TT_EOF = 'EOF'
TT_POW = 'POW'
TT_IDENTIFIER = 'IDENTIFIER'
TT_KEYWORD = 'KEYWORD'
TT_EQ = 'EQ'
TT_COMMA = 'COMMA'
TT_ARROW = 'ARROW'
TT_STRING = 'STRING'
TT_LSQUARE = 'LSQUARE'
TT_RSQUARE = 'RSQUARE'
TT_EE = 'EE'  # This is double equals used for comparison while the other solly used for assignment expressions

TT_NEQ = 'NE'
TT_LT = 'LT'
TT_GT = 'GT'
TT_LTE = 'GTE'
TT_GTE = 'LTE'

TT_NEWLINE  =   'NEWLINE'
##Constants


DIGITS = '0123456789'

LETTERS = string.ascii_letters

LETTERS_DIGITS = LETTERS + DIGITS

KEYWORDS = [
    'LET',
    'AND',
    'OR',
    'NOT',
    'IF',
    'THEN',
    'ELIF',
    'ELSE',
    'FOR',
    'TO',
    'STEP',
    'WHILE',
    'FUNC',
    'END',
]


##
# ERROR HANDLING
##

class Error:
    def __init__(self, name, details, pos_start, pos_end):
        self.name = name
        self.details = details
        self.pos_start = pos_start
        self.pos_end = pos_end

    def as_string(self):
        res = f'{self.name} : {self.details}'
        res += f'File {(self.pos_start.fn)} , line : {self.pos_start.row + 1} column: {self.pos_start.col} '
        res += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return res


class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__('Illegal Char', details, pos_start, pos_end)


class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__('Invalid Syntax', details, pos_start, pos_end)


class RunTimeError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__('Runtime Error', details, pos_start, pos_end)
        self.context = context

    def as_string(self):
        res = self.generate_traceback()
        res += f'{self.name} : {self.details}'
        res += f'File {(self.pos_start.fn)} , line : {self.pos_start.row + 1} column: {self.pos_start.col} '
        res += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return res

    def generate_traceback(self):
        result = ''
        pos = self.pos_start
        context = self.context

        while context:
            result = f'File:  {pos.fn}, line {str(pos.row + 1)} , in {context.display_name}\n' + result
            pos = context.parent_entry_pos
            context = context.parent

        return 'Traceback (most recent call last ):\n' + result


class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__('Expected Character', details, pos_start, pos_end)


##
# POSITION HANDLING
##

class Position:
    def __init__(self, index, row, col, fn, ftxt):
        self.index = index
        self.row = row
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char=None):
        # if not( self.index < len(current_char) - 1):
        #     return self

        self.index += 1
        self.col += 1

        if (current_char == '\n'):
            self.row += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.index, self.row, self.col, self.fn, self.ftxt)


##
# Tokenizer
##

class Token:
    def __init__(self, type, value=None, pos_start=None, pos_end=None):
        self.type = type
        self.value = value
        if (pos_start):
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()
        if pos_end:
            self.pos_end = pos_end.copy()

    def matches(self, new_type, val):
        return self.type == new_type and self.value == val

    def __repr__(self):
        if self.value: return f'{self.type}:{self.value}'
        return f'{self.type}'


##
# Lexer
##

class Lexer:
    def __init__(self, fn, text):
        self.text = text
        self.fn = fn
        self.pos = Position(-1, 0, 0, fn, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.index] if self.pos.index < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while (self.current_char != None):
            if self.current_char in ' \t':
                self.advance()

            elif self.current_char in ';\n':
                tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
                self.advance()

            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()

            elif self.current_char in DIGITS:
                tokens.append(self.make_number())

            elif self.current_char == '-':
                tokens.append(self.make_minus_or_arrow())
                # tokens.append(Token(TT_MINUS,pos_start=self.pos))
                # self.advance()

            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()

            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())

            elif self.current_char == '"':
                tokens.append(self.make_string())

            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()


            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()

            elif self.current_char == '^':
                tokens.append(Token(TT_POW, pos_start=self.pos))
                self.advance()

            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()

            elif self.current_char == '!':
                token, error = self.make_not_equals()
                if error: return [], error
                tokens.append(token)

            elif self.current_char == '=':
                token, error = self.make_equals()
                if error: return [], error
                tokens.append(token)

            elif self.current_char == '<':
                token, error = self.make_less_than()
                if error: return [], error
                tokens.append(token)

            elif self.current_char == '>':
                token, error = self.make_greater_than()
                if error: return [], error
                tokens.append(token)


            elif self.current_char == ',':
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()


            elif self.current_char == '[':
                tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
                self.advance()


            elif self.current_char == ']':
                tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
                self.advance()


            else:
                pos_start = self.pos.copy()
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{self.current_char}'")

        tokens.append(Token(TT_EOF, pos_start=self.pos))

        return tokens, None

    def make_number(self):
        num_str = ''
        dot_count = 0
        pos_start = self.pos.copy()
        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.' and dot_count > 0:
                # print("unrecognized number ")
                break
            else:

                if self.current_char == '.': dot_count += 1
                num_str += self.current_char

            self.advance()

        if (dot_count == 0):
            return Token(TT_INT, int(num_str), pos_start=pos_start, pos_end=self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start=pos_start, pos_end=self.pos)

    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in LETTERS_DIGITS + '_':
            id_str += self.current_char
            self.advance()

        token_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER

        return Token(token_type, id_str, pos_start, self.pos)

    def make_minus_or_arrow(self):
        token_type = TT_MINUS
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '>':
            self.advance()
            token_type = TT_ARROW

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()
        if self.current_char == '=':
            self.advance()
            return Token(TT_NEQ, pos_start=pos_start, pos_end=self.pos), None

        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "    ' = '  after ( ' ! ' )")

    def make_equals(self):
        pos_start = self.pos.copy()
        self.advance()
        token_type = TT_EQ
        if self.current_char == '=':
            self.advance()
            token_type = TT_EE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos), None

    def make_less_than(self):
        token_type = TT_LT
        pos_start = self.pos.copy()
        # print(self.current_char)
        self.advance()
        if self.current_char == '=':
            self.advance()
            # print(self.current_char)
            # self.advance()

            token_type = TT_LTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos), None

    def make_greater_than(self):
        token_type = TT_GT
        pos_start = self.pos.copy()
        self.advance()
        # print(self.current_char)
        if self.current_char == '=':
            self.advance()

            token_type = TT_GTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos), None

    def make_string(self):
        pos_start = self.pos.copy()

        string_value = ""
        escape_character = False
        self.advance()
        # if not self.current_char == '"':
        #     return
        escaped_characters = {
            'n': '\n',
            't': '\t',
            'j': '\tjingo\t'
        }

        while self.current_char != None and (self.current_char != '"' or escape_character):
            if escape_character:
                string_value += escaped_characters.get(self.current_char, self.current_char)
                escape_character = False
            else:
                if self.current_char == '\\':
                    escape_character = True
                else:
                    string_value += self.current_char
                    escape_character = False
            self.advance()

        self.advance()
        # print(string_value)
        return Token(TT_STRING, string_value, pos_start, self.pos)


##
# ParseResult
##

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.last_registered_advance_count = 0
        self.advance_count = 0
        self.to_reverse_count = 0

    def register_advancement(self):
        self.last_registered_advance_count = 1
        self.advance_count += 1

    def register(self, res):
        self.last_registered_advance_count = res.advance_count
        self.advance_count += res.advance_count
        if res.error: self.error = res.error
        return res.node

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.advance_count == 0:
            self.error = error
        return self

    def try_register(self,res):
        if res.error :
            self.to_reverse_count = res.advance_count
            return None
        return self.register(res)


##
# PARSER
##


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_index = -1
        self.current_token = None
        self.advance()

    def advance(self):
        self.token_index += 1
        self.update_current_token()
        return self.current_token

    def reverse(self,reverse_count=1):
        self.token_index -=reverse_count
        self.update_current_token()
        return self.current_token

    def update_current_token(self):
        if self.token_index >=0 and self.token_index < len(self.tokens):
            self.current_token = self.tokens[self.token_index]

    def parse(self):
        res = self.statements()
        print(self.current_token)
        if not res.error and self.current_token.type != TT_EOF:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected an Operator '+','-','*','/' .\n "
            ))
        return res

    def call(self):
        res = ParseResult()
        atom = res.register(self.atom())
        if res.error: return res
        if self.current_token.type == TT_LPAREN:
            res.register_advancement()
            self.advance()
            arg_nodes = []

            if self.current_token.type == TT_RPAREN:
                res.register_advancement()
                self.advance()
            else:
                arg_nodes.append(res.register(self.expr()))
                if res.error:  return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'Expected "let", int , float , identifier , "+","-", "(", "["  or "not" from call \n '))

                while self.current_token.type == TT_COMMA:
                    res.register_advancement()
                    self.advance()
                    arg_nodes.append(res.register(self.expr()))
                    if res.error: return res

                if self.current_token.type != TT_RPAREN:
                    return res.failure(InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end,
                        'Expected " , " or " ) " '
                    ))
                res.register_advancement()
                self.advance()
            return res.success(CallNode(atom, arg_nodes))
        return res.success(atom)

    def statements(self):
        res = ParseResult()
        statements = []
        pos_start = self.current_token.pos_start.copy()

        while self.current_token.type == TT_NEWLINE :
            res.register_advancement()
            self.advance()

        statement = res.register(self.expr())
        print(statement)
        if res.error : return res
        statements.append(statement)
        more_statements = True
        while True:
            newline_count = 0
            while self.current_token.type == TT_NEWLINE :
                res.register_advancement()
                self.advance()
                newline_count += 1

            if newline_count == 0 :
                more_statements = False

            if not more_statements : break

            statement = res.try_register(self.expr())
            print("try statement :",end="\t\t")
            print(statement)
            if not statement:
                self.reverse(res.to_reverse_count)
                more_statements = False
                continue
            statements.append(statement)

        return res.success(ListNode(
            statements,
            pos_start,
            self.current_token.pos_end.copy()
        ))

    def atom(self):
        res = ParseResult()
        token = self.current_token

        if (token.type in (TT_INT, TT_FLOAT)):
            res.register_advancement()
            self.advance()
            return res.success(NumberNode(token))

        if token.type == TT_STRING:
            res.register_advancement()
            self.advance()
            return res.success(StringNode(token))

        elif token.type == TT_IDENTIFIER:
            res.register_advancement()
            self.advance()
            return res.success(VarAccessNode(token))

        elif token.type == TT_LPAREN:
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            if self.current_token.type == TT_RPAREN:
                res.register_advancement()
                self.advance()
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end, "Expected ')' "
                ))

        elif token.type == TT_LSQUARE:
            list_expr = res.register(self.list_expr())
            if res.error: return res

            return res.success(list_expr)

        elif token.matches(TT_KEYWORD, 'IF'):
            if_expr = res.register(self.if_expr())
            if res.error: return res
            return res.success(if_expr)

        elif token.matches(TT_KEYWORD, 'FOR'):
            for_expr = res.register(self.for_expr())
            if res.error: return res
            return res.success(for_expr)

        elif token.matches(TT_KEYWORD, 'WHILE'):
            while_expr = res.register(self.while_expr())
            if res.error: return res
            return res.success(while_expr)

        elif token.matches(TT_KEYWORD, 'FUNC'):
            func_def = res.register(self.func_def())
            if res.error: return res
            return res.success(func_def)

        return res.failure(InvalidSyntaxError(
            token.pos_start, token.pos_end,
            "Expected an Operator '+' , identifier  ,'-' , '*' , '/' , ' [ '  , 'IF', 'FOR', 'WHILE', 'FUNC'     . "
        ))

    def list_expr(self):
        res = ParseResult()
        element_nodes = []
        pos_start = self.current_token.pos_start.copy()

        if self.current_token.type != TT_LSQUARE:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'Expected " [ " '
            ))
        res.register_advancement()
        self.advance()

        if self.current_token.type == TT_RSQUARE:
            res.register_advancement()
            self.advance()
        else:
            element_nodes.append(res.register(self.expr()))
            if res.error: return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'Expected " ] " , " [ " , ... '
            ))
            while self.current_token.type == TT_COMMA:
                res.register_advancement()
                self.advance()
                element_nodes.append(res.register(self.expr()))
                if res.error: return res

            if self.current_token.type != TT_RSQUARE:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'Expected " ] ", "," , ... '
                ))
            res.register_advancement()
            self.advance()
        return res.success(ListNode(
            element_nodes,
            pos_start,
            self.current_token.pos_end.copy()
        ))

    def for_expr(self):
        res = ParseResult()
        if not self.current_token.matches(TT_KEYWORD, 'FOR'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'Expected "FOR" '
            ))
        res.register_advancement()
        self.advance()

        if self.current_token.type != TT_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'Expected Identifier'
            ))

        var_name = self.current_token
        res.register_advancement()
        self.advance()

        if self.current_token.type != TT_EQ:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'Expected "=" '
            ))
        res.register_advancement()
        self.advance()

        start_value = res.register(self.expr())
        if res.error: return res

        if not self.current_token.matches(TT_KEYWORD, 'TO'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'Expected \'TO\''
            ))

        res.register_advancement()
        self.advance()

        end_value = res.register(self.expr())

        if res.error: return res

        if self.current_token.matches(TT_KEYWORD, 'STEP'):
            res.register_advancement()
            self.advance()

            step_value = res.register(self.expr())
            if res.error: return res
        else:
            step_value = None

        if not self.current_token.matches(TT_KEYWORD, 'THEN'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'Expected \' THEN \' '
            ))


        res.register_advancement()
        self.advance()
        if self.current_token.type == TT_NEWLINE :
            res.register_advancement()
            self.advance()

            body = res.register(self.statements())
            if res.error: return res

            if not self.current_token.matches(TT_KEYWORD,'END'):
                return res.failure(InvalidSyntaxError(
                self.current_token.pos_start,self.current_token.pos_end,
                f"Expected '{'END'}'"
            ))

            res.register_advancement()
            self.advance()

            return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))


        else :
            body = res.register(self.expr())
            if res.error: return res

        return res.success(ForNode(var_name, start_value, end_value, step_value, body,False))

    def while_expr(self):
        res = ParseResult()
        if not self.current_token.matches(TT_KEYWORD, 'WHILE'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'Expected "WHILE" '
            ))

        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())

        if res.error: return res

        if not self.current_token.matches(TT_KEYWORD, 'THEN'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'Expected " THEN " '
            ))

        res.register_advancement()
        self.advance()

        if self.current_token.type == TT_NEWLINE :

            res.register_advancement()
            self.advance()
            body = res.register(self.statements())
            if res.error : return res

            if not self.current_token.matches(TT_KEYWORD,'END'):
                return res.failure(InvalidSyntaxError(
                self.current_token.pos_start,self.current_token.pos_end,
                f"Expected '{'END'}'"
            ))

            return res.success(WhileNode(condition, body,True))

        body = res.register(self.expr())
        if res.error: return res

        return res.success(WhileNode(condition, body,False))

    def func_def(self):
        res = ParseResult()

        if not self.current_token.matches(TT_KEYWORD, 'FUNC'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'Expected "FUNC" '
            ))

        res.register_advancement()
        self.advance()

        if self.current_token.type == TT_IDENTIFIER:
            var_name_token = self.current_token
            res.register_advancement()
            self.advance()
            if self.current_token.type != TT_LPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'EXPECTED " ( " '
                ))

        else:
            var_name_token = None
            if self.current_token.type != TT_LPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'EXPECTED " Identifier " or " ( " '
                ))

        res.register_advancement()
        self.advance()
        arg_name_tokens = []
        if self.current_token.type == TT_IDENTIFIER:
            arg_name_tokens.append(self.current_token)
            res.register_advancement()
            self.advance()
            while self.current_token.type == TT_COMMA:
                res.register_advancement()
                self.advance()
                if self.current_token.type != TT_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end,
                        'Expected " IDENTIFIER "'
                    ))
                arg_name_tokens.append(self.current_token)
                res.register_advancement()
                self.advance()
            if self.current_token.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'Expected " , " OR " ) " '
                ))
        else:
            if self.current_token.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'Expected Identifier or " ) " '
                ))

        res.register_advancement()
        self.advance()

        if self.current_token.type == TT_ARROW:

            res.register_advancement()
            self.advance()
            body_node = res.register(self.expr())
            if res.error: return res
            return res.success(FuncDefNode(
                var_name_token,
                arg_name_tokens,
                body_node,
                False
            ))

        if self.current_token.type != TT_NEWLINE :
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start,self.current_token.pos_end,
                f"Expected '{'-> or a new line'}'"
            ))

        res.register_advancement()
        self.advance()

        print(self.current_token)
        body = res.register(self.statements())
        if re.error : return res


        if not self.current_token.matches(TT_KEYWORD,'END'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start,self.current_token.pos_end,
                f"Expected '{'END'}'"
            ))
        res.register_advancement()
        self.advance()

        return res.success(FuncDefNode(
            var_name_token,
            arg_name_tokens,
            body,
            True
        ))

    def power(self):
        return self.binary_op(self.call, (TT_POW,), self.factor)

    def elif_expr(self):
        return self.if_expr_cases('ELIF')

    def else_expr(self):
        res = ParseResult()
        else_case = None

        if self.current_token.matches(TT_KEYWORD,'ELSE'):
            res.register_advancement()
            self.advance()

            if self.current_token.type == TT_NEWLINE:
                res.register_advancement()
                self.advance()
                statements = res.register(self.statements())
                if res.error: return res
                else_case = (statements , True)
                if self.current_token.matches(TT_KEYWORD,'END'):
                    res.register_advancement()
                    self.advance()
                else :
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_token.pos_start,self.current_token.pos_end,
                            f"Expected '{'END'}'"
            ))

            else :
                expr = res.register(self.expr())
                if res.error : return res
                else_case = (expr,False)

        return res.success(else_case)

    def if_expr_cases(self,keyword):
        res = ParseResult()
        cases = []
        else_case = None

        if not self.current_token.matches(TT_KEYWORD,keyword):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start,self.current_token.pos_end,
                f"Expected '{keyword}'"
            ))

        res.register_advancement()
        self.advance()
        condition = res.register(self.expr())
        if res.error : return res
        if not self.current_token.matches(TT_KEYWORD,'THEN'):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start,self.current_token.pos_end,
                f"Expected '{'THEN'}'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_token.type == TT_NEWLINE :
            res.register_advancement()
            self.advance()
            statements = res.register(self.statements())
            if res.error : return res
            cases.append((condition,statements,True))

            if self.current_token.matches(TT_KEYWORD,'END'):
                res.register_advancement()
                self.advance()
            else:
                all_cases = res.register(self.elif_or_else_expr())
                if res.error : return res
                new_cases , else_case = all_cases
                cases.extend(new_cases)
        else:
            expr = res.register(self.expr())
            if res.error : return res
            cases.append((condition,expr,False))

            all_cases = res.register(self.elif_or_else_expr())
            if res.error: return res
            new_cases , else_case = all_cases
            cases.extend(new_cases)
        return res.success((cases,else_case))


        pass

    def elif_or_else_expr(self):
        res = ParseResult()
        cases , else_case = [],None

        if self.current_token.matches(TT_KEYWORD,'ELIF'):
            all_cases = res.register(self.elif_expr())
            if res.error  : return res
            cases , else_case = all_cases

        else :
            # print("whats app")
            else_case = res.register(self.else_expr())
            if res.error: return res

        return res.success((cases,else_case))

        pass


    def if_expr(self):
        res = ParseResult()
        all_cases = res.register(self.if_expr_cases("IF"))
        if res.error : return res
        cases , else_case = all_cases
        # print(else_case)
        return res.success(IfNode(cases,else_case))

        # cases = []
        # else_case = None
        #
        # if not self.current_token.matches(TT_KEYWORD, 'IF'):
        #     return res.failure(InvalidSyntaxError(
        #         self.current_token.pos_start, self.current_token.pos_end,
        #         'Expected "IF" '
        #     ))
        #
        # res.register_advancement()
        # self.advance()
        #
        # condition = res.register(self.expr())
        # if res.error: return res
        #
        # if not self.current_token.matches(TT_KEYWORD, 'THEN'):
        #     return res.failure(InvalidSyntaxError(
        #         self.current_token.pos_start, self.current_token.pos_end,
        #         'Expected \'THEN\' '
        #     ))
        #
        # res.register_advancement()
        # self.advance()
        # expretion = res.register(self.expr())
        # if res.error: return res
        # cases.append((condition, expretion))
        #
        # while self.current_token.matches(TT_KEYWORD, 'ELIF'):
        #     res.register_advancement()
        #     self.advance()
        #
        #     condition = res.register(self.expr())
        #     if res.error: return res
        #
        #     if not self.current_token.matches(TT_KEYWORD, 'THEN'):
        #         return res.failure(InvalidSyntaxError(
        #             self.current_token.pos_start, self.current_token.pos_end,
        #             'Expected \'THEN\''
        #         ))
        #
        #     res.register_advancement()
        #     self.advance()
        #
        #     expretion = res.register(self.expr())
        #     # remember that self.expr does advance to the next token(s) meaning  you dont register_advancement and advance after u call/register it
        #     if res.error: return res
        #
        #     cases.append((condition, expretion))
        #
        # if self.current_token.matches(TT_KEYWORD, 'ELSE'):
        #     res.register_advancement()
        #     self.advance()
        #     else_case = res.register(self.expr())
        #     if res.error: return res
        #     # a local var dedicated to the else case
        #     # cases for all the (if.cond, if.then) then a var for the else case
        #
        # return res.success(IfNode(cases, else_case))

    def factor(self):
        res = ParseResult()
        token = self.current_token
        if token.type in (TT_PLUS, TT_MINUS):
            res.register_advancement()
            self.advance()
            factor = res.register(self.factor())
            if res.error: return res

            return res.success(UnaryOpNode(token, factor))

        return self.power()

    def term(self):

        return self.binary_op(self.factor, (TT_MUL, TT_DIV))

    def binary_op(self, func_a, op_tokens, func_b=None):
        if func_b == None:
            func_b = func_a

        res = ParseResult()
        # basically a rule is the unit slicer ( what ditermines a unit )
        left = res.register(func_a())
        if res.error: return res
        # the left factor keeps on expanding to be the whole term in the end
        # op_tokens the relation we need between these tokens
        while (self.current_token.type in op_tokens or (
                self.current_token.type, self.current_token.value) in op_tokens):
            op_token = self.current_token
            res.register_advancement()
            self.advance()
            right = res.register(func_b())
            if res.error: return res
            left = BinaryOpNode(left, op_token, right)

        return res.success(left)

    def expr(self):

        res = ParseResult()

        if self.current_token.matches(TT_KEYWORD, 'LET'):
            res.register_advancement()
            self.advance()
            if self.current_token.type != TT_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token,
                    'Expected Identifier'
                ))
            var_name = self.current_token
            res.register_advancement()
            self.advance()

            if self.current_token.type != TT_EQ:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end,
                        'Expected = '
                    )
                )
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            return res.success(VarAssignNode(var_name, expr))

        node = res.register(self.binary_op(self.comp_expr, ((TT_KEYWORD, "and"), (TT_KEYWORD, "or"))))
        if res.error: return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end,
                                                            'Expected "let", int , float , identifier , "+","-", "("  , " [ " , "IF", "FOR", "WHILE", "FUNC" "not" '))

        return res.success(node)

    def comp_expr(self):
        res = ParseResult()
        if self.current_token.matches(TT_KEYWORD, 'NOT'):
            op_token = self.current_token
            res.register_advancement()
            self.advance()

            node = res.register(self.comp_expr())
            if res.error: return res

            return res.success(UnaryOpNode(op_token, node))

        node = res.register(self.binary_op(self.arith_expr, (TT_EE, TT_NEQ, TT_LT, TT_GT, TT_GTE, TT_LTE)))

        if res.error:
            return res.failure(
                InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'Expected int , float , identifier + - (  [ "not" '
        ))

        return res.success(node)

    def arith_expr(self):
        return self.binary_op(self.term, (TT_PLUS, TT_MINUS))


# Nodes


class NumberNode:
    def __init__(self, token):
        self.token = token
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end

    def __repr__(self):
        return f'{self.token}'


class StringNode:
    def __init__(self, token):
        self.token = token
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end

    def __repr__(self):
        return f'{self.token}'


class VarAccessNode:
    def __init__(self, var_name_token):
        self.var_name_token = var_name_token
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.var_name_token.pos_end


class VarAssignNode:
    def __init__(self, var_name_token, value_node):
        self.var_name_token = var_name_token
        self.value_node = value_node
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.var_name_token.pos_end


class BinaryOpNode:
    def __init__(self, left_node, op_token, right_node):
        self.left_node = left_node
        self.op_token = op_token
        self.right_node = right_node
        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f'({self.left_node} , {self.op_token}  , {self.right_node})'


class UnaryOpNode:
    def __init__(self, op_token, node):
        self.op_token = op_token
        self.node = node

        self.pos_start = self.op_token.pos_start
        self.pos_end = self.node.pos_end

    def __repr__(self):
        return f'({self.op_token} , {self.node})'



class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case
        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (self.else_case or self.cases[len(self.cases) - 1])[0].pos_end


class ForNode:
    def __init__(self, var_name_token, start_value_node, end_value_node, step_value_node, body_node,should_return_null):
        self.var_name_token = var_name_token
        self.start_value_node = start_value_node
        self.end_value_node = end_value_node
        self.step_value_node = step_value_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.body_node.pos_end


class WhileNode:
    def __init__(self, condition_node, body_node,should_return_null):
        self.condition_node = condition_node
        self.body_node = body_node
        self.pos_start = self.condition_node.pos_start
        self.pos_end = self.body_node.pos_end
        self.should_return_null= should_return_null


class FuncDefNode:
    def __init__(self, var_name_token, arg_name_tokens, body_node,should_return_null):
        self.var_name_token = var_name_token
        self.arg_name_tokens = arg_name_tokens
        self.body_node = body_node
        self.should_return_null = should_return_null

        if self.var_name_token:
            self.pos_start = self.var_name_token.pos_start
        elif len(self.arg_name_tokens) > 0:
            self.pos_start = self.arg_name_tokens[0].pos_start

        else:
            self.pos_start = self.body_node.pos_start

        self.pos_end = self.body_node.pos_end


class CallNode:
    def __init__(self, node_to_call, arg_nodes):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes

        self.pos_start = node_to_call.pos_start

        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[len(arg_nodes) - 1].pos_end
        else:
            self.pos_end = self.node_to_call.pos_end


class ListNode:
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end


##
# RunTime Result :
##
class RunTimeResult:
    def __init__(self):
        self.value = None
        self.error = None

    def register(self, res):
        if res.error: self.error = res.error
        return res.value

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self


class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def get(self, name):
        value = self.symbols.get(name, None)
        if value == None and self.parent:
            return self.parent.get(name)
        return value

    def set(self, name, value):
        self.symbols[name] = value

    def remove(self, name):
        del self.symbols[name]


class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None


##
# VALUES
##
class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def added_to(self, num):
        return None, self.illegal_operation(num)

    def subbed_by(self, num):
        return None, self.illegal_operation(num)

    def multed_by(self, num):
        return None, self.illegal_operation(num)

    def dived_by(self, num):
        return None, self.illegal_operation(num)

    def powed_by(self, num):
        return None, self.illegal_operation(num)

    def get_comparison_eq(self, num):
        return None, self.illegal_operation(num)

    def get_comparison_ne(self, num):
        return None, self.illegal_operation(num)

    def get_comparison_lt(self, num):
        return None, self.illegal_operation(num)

    def get_comparison_lte(self, num):
        return None, self.illegal_operation(num)

    def get_comparison_gt(self, num):
        return None, self.illegal_operation(num)

    def get_comparison_gte(self, num):
        return None, self.illegal_operation(num)

    def anded_by(self, num):
        return None, self.illegal_operation(num)

    def ored_by(self, num):
        return None, self.illegal_operation(num)

    def notted(self):
        return None, self.illegal_operation()

    def is_true(self):
        return False

    def execute(self, args):
        return None, self.illegal_operation()

    def copy(self):
        raise Exception('No Copy Method Defined Inside The \'Value\' Class ')

    def illegal_operation(self, other=None):
        if not other: other = self
        return RunTimeError(
            self.pos_start, other.pos_end,
            'Illegal Operation',
            self.context
        )


class Number(Value):

    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def subbed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def multed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def dived_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RunTimeError(
                    other.pos_start, other.pos_end,
                    'Division By Zero',
                    self.context
                )
            return Number(self.value / other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def powed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def get_comparison_eq(self, other):
        if isinstance(other, Number):
            return Number(int(self.value == other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def get_comparison_ne(self, other):
        if isinstance(other, Number):
            return Number(int(self.value != other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def get_comparison_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def get_comparison_lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value <= other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def get_comparison_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def get_comparison_gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value >= other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def anded_by(self, other):
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def ored_by(self, other):
        if isinstance(other, Number):
            return Number(int(self.value or other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def notted(self):
        return Number(1 if self.value == 0 else 0).set_context(self.context), None

    def is_true(self):
        return self.value != 0

    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return str(self.value)


Number.null = Number(0)
Number.true = Number(1)
Number.false = Number(0)
Number.MATH_PI = Number(math.pi)


class String(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start,
                                                 other.pos_end if (other and other.pos_end) else self.pos_end)

    def multed_by(self, other):
        if isinstance(other, Number):
            return String(self.value * other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def is_true(self):
        return len(self.value) > 0

    def copy(self):
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return f'{self.value}'


class List(Value):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    def added_to(self, other):
        new_list = self.copy()
        new_list.elements.append(other)
        return new_list, None

    def multed_by(self, other):
        if isinstance(other, List):
            new_list = self.copy()
            new_list.elements.extend(other.elements)
            return new_list, None
        else:
            return None, Value.illegal_operation(self, other)

    def subbed_by(self, other):
        if isinstance(other, Number):
            new_list = self.copy()
            try:
                new_list.elements.pop(other.value)
                return new_list, None
            except:
                return None, RunTimeError(
                    other.pos_start, other.pos_end,
                    f'Element at this index {other.value} Could not be removed from the list ',
                    self.context
                )
        else:
            return None, Value.illegal_operation(self, other)

    def dived_by(self, other):
        if isinstance(other, Number):
            try:
                return self.elements[other.value], None
            except:
                return None, RunTimeError(
                    other.pos_start, other.pos_end,
                    f'Element at this index {other.value} Could not be retrieved  from the list ',
                    self.context
                )

        else:
            return None, Value.illegal_operation(self, other)

    def copy(self):
        copy = List(self.elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return f'[{", ".join([str(x) for x in self.elements])} ]'


class BaseFunction(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name or "<anonymous>"

    def generate_new_context(self):
        new_context = Context(self.name, self.context, self.pos_start)

        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        return new_context

    def check_args(self, arg_names, args):
        res = RunTimeResult()
        if len(args) > len(arg_names):
            return res.failure(RunTimeError(
                self.pos_start, self.pos_end,
                f"{len(args) - len(arg_names)}  too many args passed into '{self.name}' ",
                self.context
            ))
        if len(args) < len(arg_names):
            return res.failure(RunTimeError(
                self.pos_start, self.pos_end,
                f"{len(arg_names) - len(args)} too few args passed into '{self.name}' ",
                self.context
            ))
        return res.success(None)

    def populate_args(self, arg_names, args, execution_context):
        for i in range(len(args)):
            arg_name = arg_names[i]
            arg_value = args[i]
            arg_value.set_context(execution_context)
            execution_context.symbol_table.set(arg_name, arg_value)

    def check_and_populate_args(self, arg_names, args, execution_context):
        res = RunTimeResult()
        res.register(self.check_args(arg_names, args))
        if res.error: return res
        self.populate_args(arg_names, args, execution_context)
        return res.success(None)


class Function(BaseFunction):
    def __init__(self, name, body_node, arg_names,should_return_null):
        super().__init__(name)

        self.body_node = body_node
        self.should_return_null = should_return_null
        self.arg_names = arg_names

    def execute(self, args):
        res = RunTimeResult()
        interpreter = Interpreter()
        execution_context = self.generate_new_context()

        res.register(self.check_and_populate_args(self.arg_names, args, execution_context))
        if res.error: return res

        value = res.register(interpreter.visit(self.body_node, execution_context))
        if res.error: return res
        return res.success(Number.null if self.should_return_null else value)

    def copy(self):
        copy = Function(self.name, self.body_node, self.arg_names,self.should_return_null)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<Function {self.name}>"


class BuiltInFunction(BaseFunction):
    def __init__(self, name):
        super().__init__(name)

    def execute(self, args):
        res = RunTimeResult()
        execution_context = self.generate_new_context()
        method_name = f'execute_{self.name}'
        method = getattr(self, method_name, self.no_visit_method)
        res.register(self.check_and_populate_args(method.arg_names, args, execution_context))
        if res.error: return res
        ret = res.register(method(execution_context))
        if res.error: return res
        return res.success(ret)

    def no_visit_method(self, node, context):
        raise Exception(f'No execute_{self.name} methoud defined ')

    def copy(self):
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<built-in function {self.name}>"

    def execute_print(self, execution_context):
        print(str(execution_context.symbol_table.get('value')))
        return RunTimeResult().success(Number.null)

    execute_print.arg_names = ['value']

    def execute_print_return(self, execution_context):
        return RunTimeResult().success(String(str(execution_context.symbol_table.get('value'))))

    execute_print_return.arg_names = ['value']

    def execute_input(self, execution_context):
        text = input()
        return RunTimeResult().success(String(text))

    execute_input.arg_names = []

    def execute_input_int(self, execution_context):
        while True:
            text = input()
            try:
                number = int(text)
                break;
            except ValueError:
                print(f"{text} must be an integer")

        return RunTimeResult().success(Number(number))

    execute_input_int.arg_names = []

    def execute_clear(self, execution_context):
        os.system('cls' if os.name == 'nt' else 'clear')
        return RunTimeResult().success(Number.null)

    execute_clear.arg_names = []

    def execute_is_number(self, execution_context):
        is_number = isinstance(execution_context.symbol_table.get('value'), Number)
        return RunTimeResult().success(Number.true if is_number else Number.false)

    execute_is_number.arg_names = ['value']

    def execute_is_string(self, execution_context):
        is_string = isinstance(execution_context.symbol_table.get("value"), String)
        return RunTimeResult().success(Number.true if is_string else Number.false)

    execute_is_string.arg_names = ['value']

    def execute_is_list(self, execution_context):
        is_list = isinstance(execution_context.symbol_table.get('value'), List)
        return RunTimeResult().success(Number.true if is_list else Number.false)

    execute_is_list.arg_names = ['value']

    def execute_is_function(self, execution_context):
        is_function = isinstance(execution_context.symbol_table.get("value"), BaseFunction)
        return RunTimeResult().success(Number.true if is_function else Number.false)

    execute_is_function.arg_names = ['value']

    def execute_append(self, execution_context):
        list_ = execution_context.symbol_table.get('list')
        value = execution_context.symbol_table.get('value')

        if not isinstance(list_, List):
            return RunTimeResult().failure(RunTimeError(
                self.pos_start, self.pos_end,
                "First argument must be list",
                execution_context
            ))
        list_.elements.append(value)
        return RunTimeResult().success(Number.null)

    execute_append.arg_names = ['list', 'value']

    def execute_pop(self, execution_context):
        list_ = execution_context.symbol_table.get('list')
        index = execution_context.symbol_table.get("index")
        res = RunTimeResult()
        if not isinstance(list_, List):
            return res.failure(RunTimeError(
                self.pos_start, self.pos_end,
                "First Argument must be a list",
                execution_context
            ))

        if not isinstance(index, Number):
            return res.failure(RunTimeError(
                self.pos_start, self.pos_end,
                "Second Argument must be a number",
                execution_context
            ))

        try:
            element = list_.elements.pop()
        except:
            return res.failure(RunTimeError(
                self.pos_start, self.pos_end,
                "Indexing Out Of Bound"
            ))

        return res.success(element)

    execute_pop.arg_names = ['list', 'index']

    def execute_extend(self, execution_context):
        list1 = execution_context.symbol_table.get("list1")
        list2 = execution_context.symbol_table.get("list2")
        res = RunTimeResult()

        if not isinstance(list1, List):
            return res.failure(RunTimeError(
                self.pos_start, self.pos_end,
                "First Argument must be a list",
                execution_context
            ))

        if not isinstance(list2, List):
            return res.failure(RunTimeError(
                self.pos_start, self.pos_end,
                "Second Argument must be a list",
                execution_context
            ))

        list1.elements.extend(list2.elements)
        return res.success(Number.null)

    execute_extend.arg_names = ['list1', 'list2']


BuiltInFunction.print = BuiltInFunction("print")
BuiltInFunction.print_return = BuiltInFunction("print_return")
BuiltInFunction.input = BuiltInFunction("input")
BuiltInFunction.input_int = BuiltInFunction("input_int")
BuiltInFunction.clear = BuiltInFunction("clear")
BuiltInFunction.is_number = BuiltInFunction("is_number")
BuiltInFunction.is_string = BuiltInFunction("is_string")
BuiltInFunction.is_list = BuiltInFunction("is_list")
BuiltInFunction.is_function = BuiltInFunction("is_function")
BuiltInFunction.append = BuiltInFunction("append")
BuiltInFunction.pop = BuiltInFunction("pop")
BuiltInFunction.extend = BuiltInFunction("extend")


class Interpreter:
    def visit(self, node, context):
        # visit binaryopnode -- uniopnode

        method_name = f'visit_{type(node).__name__}'

        method = getattr(self, method_name, self.no_visit_method)
        # this is for getting a method in the object from a string and takes the default method if no method was found
        return method(node, context)

    def no_visit_method(self, node, context):
        raise Exception(f'no visit_{type(node).__name__} method defined')

    def visit_NumberNode(self, node, context):
        return RunTimeResult().success(
            Number(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end))

        # print("Found number node!")

    def visit_BinaryOpNode(self, node, context):
        res = RunTimeResult()
        result = error = None
        left = res.register(self.visit(node.left_node, context))
        right = res.register(self.visit(node.right_node, context))
        if res.error: return res

        if node.op_token.type == TT_PLUS:
            result, error = left.added_to(right)

        elif node.op_token.type == TT_MINUS:
            result, error = left.subbed_by(right)

        elif node.op_token.type == TT_MUL:
            result, error = left.multed_by(right)

        elif node.op_token.type == TT_DIV:
            result, error = left.dived_by(right)

        elif node.op_token.type == TT_POW:
            result, error = left.powed_by(right)

        elif node.op_token.type == TT_EE:
            result, error = left.get_comparison_eq(right)

        elif node.op_token.type == TT_NEQ:
            result, error = left.get_comparison_ne(right)


        elif node.op_token.type == TT_LT:
            result, error = left.get_comparison_lt(right)

        elif node.op_token.type == TT_LTE:
            result, error = left.get_comparison_lte(right)


        elif node.op_token.type == TT_GT:
            result, error = left.get_comparison_gt(right)


        elif node.op_token.type == TT_GTE:
            result, error = left.get_comparison_gte(right)

        elif node.op_token.matches(TT_KEYWORD, "and"):
            result, error = left.anded_by(right)

        elif node.op_token.matches(TT_KEYWORD, "or"):
            result, error = left.ored_by(right)

        if error:
            return res.failure(error)
        else:
            return res.success(result.set_pos(node.pos_start, node.pos_end).set_context(context))

    def visit_UnaryOpNode(self, node, context):
        res = RunTimeResult()
        number = res.register(self.visit(node.node, context))
        if res.error: return res
        error = None
        if node.op_token.type == TT_MINUS:
            number, error = number.multed_by(Number(-1))

        elif node.op_token.matches(TT_KEYWORD, "not"):
            number, error = number.notted()

        if error:
            return res.failure(error)
        else:
            return res.success(number.set_pos(node.pos_start, node.pos_end))

    def visit_VarAccessNode(self, node, context):
        res = RunTimeResult()
        var_name = node.var_name_token.value
        value = context.symbol_table.get(var_name)
        if not value:
            return res.failure(RunTimeError(
                node.pos_start, node.pos_end,
                f'{var_name} is not defined ',
                context
            ))
        value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)

        return res.success(value)

    def visit_VarAssignNode(self, node, context):
        res = RunTimeResult()
        var_name = node.var_name_token.value
        value = res.register(self.visit(node.value_node, context))
        if res.error: return res
        context.symbol_table.set(var_name, value)
        return res.success(value)

    def visit_IfNode(self, node, context):
        res = RunTimeResult()
        for condition, expr ,should_return_null  in node.cases:
            condition_value = res.register(self.visit(condition, context))
            if res.error: return res
            if condition_value.is_true():
                expr_value = res.register(self.visit(expr, context))
                if res.error: return res
                return res.success(Number.null if should_return_null else expr_value)

        if node.else_case:
            expr , should_return_null = node.else_case
            else_value = res.register(self.visit(expr, context))
            if res.error: return res
            return res.success(Number.null if should_return_null else else_value)

        return res.success(Number.null)

    def visit_ForNode(self, node, context):
        res = RunTimeResult()

        elements = []
        start_value = res.register(self.visit(node.start_value_node, context))
        if res.error: return res

        end_value = res.register(self.visit(node.end_value_node, context))
        if res.error: return res

        # body = res.register(self.visit(node.body_node,context))
        # if res.error : return res

        if node.step_value_node:
            step = res.register(self.visit(node.step_value_node, context))
            if res.error: return res
        else:
            # wihtout this we can exit right away from the while loop

            step = Number(1)
            if start_value.value < end_value.value:
                step = Number(1)
            else:
                step = Number(-1)

        i = start_value.value

        if step.value == 0:
            return res.failure(RunTimeError(
                node.pos_start, node.pos_end,
                'STEP value must be none zero',
                context
            ))

        condition = lambda: i < end_value.value
        if step.value < 0:
            condition = lambda: i > end_value.value

        while condition():
            context.symbol_table.set(node.var_name_token.value, Number(i))

            i += step.value
            elements.append(res.register(self.visit(node.body_node, context)))
            if res.error: return res

        return res.success(
            Number.null if node.should_return_null else
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end))

    def visit_WhileNode(self, node, context):
        res = RunTimeResult()
        elements = []

        while True:
            condition = res.register(self.visit(node.condition_node, context))
            if res.error: return res

            if not condition.is_true(): break;

            elements.append(res.register(self.visit(node.body_node, context)))
            if res.error: return res

        return res.success(
            Number.null if node.should_return_null else
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_FuncDefNode(self, node, context):
        res = RunTimeResult()

        func_name = node.var_name_token.value if node.var_name_token else None
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_tokens]

        func_value = Function(func_name, body_node, arg_names,node.should_return_null).set_context(context).set_pos(node.pos_start,
                                                                                            node.pos_end)

        if node.var_name_token: context.symbol_table.set(func_name, func_value)

        return res.success(func_value)

        pass

    def visit_CallNode(self, node, context):
        res = RunTimeResult()
        args = []
        value_to_call = res.register(self.visit(node.node_to_call, context))
        if res.error: return res

        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.error: return res

        ret = res.register(value_to_call.execute(args))
        if res.error: return res
        ret = ret.copy().set_pos(node.pos_start,node.pos_end).set_context(context)
        return res.success(ret)

    def visit_StringNode(self, node, context):
        res = RunTimeResult()
        return res.success(String(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end))

    def visit_ListNode(self, node, context):
        res = RunTimeResult()
        elements = []
        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))
            if res.error: return res

        return res.success(List(elements).set_context(context).set_pos(node.pos_start, node.pos_end))


##Global Context

global_symbol_table = SymbolTable()
global_symbol_table.set("NULL", Number.null)
global_symbol_table.set("TRUE", Number.true)
global_symbol_table.set("FALSE", Number.false)

global_symbol_table.set("MATH_PI", Number.MATH_PI)
global_symbol_table.set("PRINT", BuiltInFunction.print)
global_symbol_table.set("PRINT_RETURN", BuiltInFunction.print_return)
global_symbol_table.set("INPUT", BuiltInFunction.input)
global_symbol_table.set("INPUT_INT", BuiltInFunction.input_int)
global_symbol_table.set("CLEAR", BuiltInFunction.clear)
global_symbol_table.set("IS_NUMBER", BuiltInFunction.is_number)
global_symbol_table.set("IS_STRING", BuiltInFunction.is_string)
global_symbol_table.set("IS_LIST", BuiltInFunction.is_list)
global_symbol_table.set("IS_FUNCTION", BuiltInFunction.is_function)
global_symbol_table.set("APPEND", BuiltInFunction.append)
global_symbol_table.set("POP", BuiltInFunction.pop)
global_symbol_table.set("EXTEND", BuiltInFunction.extend)


def run(fn, text):
    ## Generate Tokens
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error
    ## Generate AST
    parser = Parser(tokens)

    # abstract syntax tree

    ast = parser.parse()
    if ast.error: return None, ast.error

    # interpret the ast
    interpreter = Interpreter()
    context = Context("<program>")
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error
