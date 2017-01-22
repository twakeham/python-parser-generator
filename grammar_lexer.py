import sys
import string

string.alpha_ = string.ascii_letters + '_'
string.ident = string.alpha_ + string.digits


class Token(object):
    eof = 'END-OF-FILE'
    eol = 'END-OF-LINE'
    ident = 'IDENT'
    id = 'NODE-ID'
    list_separator = 'LIST-SEP'

    ellipsis = 'ELLIPSIS'
    repeat = 'ONE-OR-MORE'
    optrepeat = 'ZERO-OR-MORE'
    exclude = 'EXCLUDE'
    option = 'OPTION'
    optional = 'OPTIONAL'

    gt = '>'
    lt = '<'

    empty = 'EMPTY'

    assign = 'ASSIGN'

    lparen = 'LPAREN'
    rparen = 'RPAREN'

    lbrace = 'LBRACE'
    rbrace = 'RBRACE'

    lbracket = 'LSQR'
    rbracket = 'RSQR'

    literal = 'LITERAL'
    regex = 'REGEX'

    token = 'TOKEN-ID'

    terminator = 'END-OF-RULE'

    def __init__(self, type, value, line_no, line_pos, **kwargs):
        self.type = type
        self.value = value
        self.line_pos = line_pos - len(value)
        self.line_no = line_no

        for key, val in kwargs.iteritems():
            setattr(self, key, val)

    def __str__(self):
        return '<%s value:%s line:%s pos:%s>' % (self.type.upper(), self.value, self.line_no, self.line_pos)


class Lexer(object):
    def __init__(self, code):
        super(Lexer, self).__init__()

        self.code = code
        self.cursor = 0
        self.tokens = []

        self.lines = code.split('\n')
        self.line_no = 1
        self.line_pos = 0

    def get_next_char(self):
        self.cursor += 1
        self.line_pos += 1
        if self.cursor > len(self.code):
            return '$'

        return self.code[self.cursor - 1]

    def tokenise(self):
        char = self.get_next_char()
        while char != '$':

            match = ''

            # whitespace tokens
            if char in ' \t\r\n':
                if char in '\r\n':
                    self.line_no += 1
                    self.line_pos = 0
                char = self.get_next_char()

            # comment
            elif char in '#':
                while char not in '\n':
                    # this gets to the \n
                    char = self.get_next_char()

            # identifier token
            elif char in string.alpha_:
                match = char
                char = self.get_next_char()
                token_type = Token.ident
                while char in string.ident:
                    match += char
                    char = self.get_next_char()
                    # if match in Token.keyword_ops or match in Token.keywords:
                    # token_type = match
                self.tokens.append(Token(token_type, match, self.line_no, self.line_pos))

            # token identifier
            elif char in '<':
                match = ''
                char = self.get_next_char()
                while char in string.ident:
                    match += char
                    char = self.get_next_char()
                if char != '>':
                    raise SyntaxError(
                        'Unexpected character %s, expected > while scanning token id string'.format(char, self.line_no,
                                                                                                    self.line_pos))
                char = self.get_next_char()
                self.tokens.append(Token(Token.token, match, self.line_no, self.line_pos))

            # empty
            elif char == '.':
                char = self.get_next_char()
                if char != '.':
                    raise SyntaxError(
                        'Unexpected character %s, expected > while scanning token id string'.format(char, self.line_no,
                                                                                                    self.line_pos))
                self.tokens.append(Token(Token.ellipsis, '..', self.line_no, self.line_pos))
                char = self.get_next_char()

            # empty
            elif char == '-':
                self.tokens.append(Token(Token.empty, char, self.line_no, self.line_pos))
                char = self.get_next_char()

            # zero or more
            elif char == '*':
                self.tokens.append(Token(Token.optrepeat, char, self.line_no, self.line_pos))
                char = self.get_next_char()

            # one or more
            elif char == '+':
                self.tokens.append(Token(Token.repeat, char, self.line_no, self.line_pos))
                char = self.get_next_char()

            # exclude
            elif char == '^':
                self.tokens.append(Token(Token.exclude, char, self.line_no, self.line_pos))
                char = self.get_next_char()

            # option
            elif char == '|':
                self.tokens.append(Token(Token.option, char, self.line_no, self.line_pos))
                char = self.get_next_char()

            # assign
            elif char == '=':
                self.tokens.append(Token(Token.assign, char, self.line_no, self.line_pos))
                char = self.get_next_char()

            # optional
            elif char == '?':
                self.tokens.append(Token(Token.optional, char, self.line_no, self.line_pos))
                char = self.get_next_char()

            # parentheses
            elif char == '(':
                self.tokens.append(Token(Token.lparen, char, self.line_no, self.line_pos))
                char = self.get_next_char()

            elif char == ')':
                self.tokens.append(Token(Token.rparen, char, self.line_no, self.line_pos))
                char = self.get_next_char()

            # braces
            elif char == '{':
                self.tokens.append(Token(Token.lbrace, char, self.line_no, self.line_pos))
                char = self.get_next_char()

            elif char == '}':
                self.tokens.append(Token(Token.rbrace, char, self.line_no, self.line_pos))
                char = self.get_next_char()

            elif char in '[':
                match = ''
                char = self.get_next_char()
                while char in (string.ident + ', '):
                    match += char
                    char = self.get_next_char()
                if char != ']':
                    raise SyntaxError(
                        'Unexpected character %s, expected ] while scanning directive string'.format(char))
                char = self.get_next_char()
                self.tokens.append(Token(Token.id, match, self.line_no, self.line_pos))

            # list seperator
            elif char == ',':
                self.tokens.append(Token(Token.list_separator, char, self.line_no, self.line_pos))
                char = self.get_next_char()

            # list seperator
            elif char == ';':
                self.tokens.append(Token(Token.terminator, char, self.line_no, self.line_pos))
                char = self.get_next_char()

            # string literal
            elif char == "'":
                match = ''
                char = self.get_next_char()
                # need to take into account escaped single quote
                while char not in "'":
                    if char in '$':
                        raise SyntaxError('Unexpected character EOF while scanning literal string\n'.format(match))
                    match += char
                    # escaped single quote
                    if char == '\\':
                        char = self.get_next_char()
                        if char != "'":
                            match += '\\'
                        match += char
                    char = self.get_next_char()
                # skip the trailing '
                char = self.get_next_char()
                self.tokens.append(Token(Token.literal, match, self.line_no, self.line_pos))

            elif char == "/":
                match = ''
                char = self.get_next_char()
                while char not in "/":
                    if char in '$':
                        raise SyntaxError('Unexpected character EOF while scanning regular expression')
                    match += char
                    # escaped backslash
                    if char == '\\':
                        char = self.get_next_char()
                        if char != '/':
                            match += '\\'
                        match += char
                    char = self.get_next_char()
                # skip the trailing /
                char = self.get_next_char()
                self.tokens.append(Token(Token.regex, match, self.line_no, self.line_pos))

            # error
            else:
                raise SyntaxError(
                    'Unexpected character %s on line %s position %s' % (char, self.line_no, self.line_pos))

        self.tokens.append(Token(Token.eof, char, self.line_no, self.line_pos))
        self.tokens.append(Token(Token.eof, char, self.line_no, self.line_pos))
        return self.tokens


# with open('equ.grammar') as f:
#	grammar = f.read()

# lex = Lexer(grammar)
# lex.tokenise()
# for token in lex.tokens:
#	print token
