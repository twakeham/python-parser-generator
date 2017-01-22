import re

from grammar_ast import *

debug = False
depth = 0


def trace(func):
    def wrap(*args, **kwargs):
        global depth
        print('  ' * depth + '%s entry'.format(func.func_name))
        depth += 1
        # print '  ' * depth + str(args[0].token)
        val = func(*args, **kwargs)
        # print '  ' * depth + str(args[0].token)
        depth -= 1
        print('  ' * depth + '%s exit'.format(func.func_name, val))
        return val

    return wrap if debug else func


class GrammarParser(object):
    def __init__(self, code):
        self._seen = []
        self._state = []
        self.code = code.strip()
        self.matched = None
        self.token = None
        self.cursor = 0
        self.state = 0
        self.line_pos = 1
        self.line = 1
        self.lines = code.split('\n')
        self.end = False

    def advance(self, amount):
        self.cursor += amount
        self.line_pos += amount
        if self.cursor < len(self.code) and self.code[self.cursor] in ' \r\n\t':
            if self.code[self.cursor] == '\n':
                self.line += 1
                self.line_pos = 1
            self.advance(1)
        if self.cursor >= len(self.code) - 1:
            self.end = True

    def push_state(self):
        self._state.append(self.cursor)
        return True

    def pop_state(self):
        self.cursor = self._state.pop()
        return True

    def error(self, msg):
        raise SyntaxError(
            'Expecting {5}, got {0}...\nLine: {1}, Pos: {2}\n{3}\n{4}'.format(self.code[self.cursor:15], self.line,
                                                                              self.line_pos, self.lines[self.line],
                                                                              ' ' * self.line_pos + '^', msg))

    def parse_literal(self, match):
        if self.code[self.cursor:].startswith(match):
            self.advance(len(match))
            return match
        return False

    def parse_regex(self, pattern):
        matchobj = re.match(pattern, self.code[self.cursor:])
        if not matchobj:
            return False
        match = matchobj.group()
        # print '###', pattern, match
        self.advance(len(match))
        return match

    def parse(self):
        rules = self.rules()
        return rules

    @trace
    def rules(self):
        rules = []
        while (1):
            rule = self.rule()
            if rule is not False:
                rules.append(rule)
                continue
            comment = self.comment()
            if comment is False:
                break
        if not self.end:
            self.error('end of file')
        return Rules(value=rules)

    @trace
    def comment(self):
        comment = self.parse_regex('#.*?#')
        if comment is not False:
            self.advance(1)
            return True
        return False

    @trace
    def rule(self):
        self.push_state()
        ident = self.ident()
        if not ident:
            return False
        if self.parse_literal('=') is False:
            self.pop_state()
            return False
        rule = self.option()
        if not rule:
            self.pop_state()
            return False
        directives = self.directive()
        if not self.parse_literal(';'):
            self.pop_state()
            return False
        self._seen.append(ident.value)
        return Rule(name=ident.value, value=rule, directives=directives)

    @trace
    def directive(self):
        self.push_state()
        if self.parse_literal('[') is False:
            return []
        directives = self.directive_list()
        if self.parse_literal(']') is False:
            self.pop_state()
            return []
        return directives

    @trace
    def directive_list(self):
        directive = self.ident()
        if directive is False:
            self.error('ident (in directive string)')
        directives = [directive]
        while (self.parse_literal(',') is not False):
            directives.append(directive)
        return directives

    @trace
    def option(self):
        concat = self.concat()
        options = [concat]
        while (self.parse_literal('|') is not False):
            options.append(self.concat())
        if len(options) == 1:
            return concat
        return Or(value=options)

    @trace
    def concat(self):
        lexemes = [self.lexeme()]
        while (lexemes[-1] is not False):
            lexemes.append(self.lexeme())
        if len(lexemes) == 1:
            self.error('lexeme')
        elif len(lexemes) == 2:
            return lexemes[0]
        else:
            return Concatenate(value=lexemes[:-1])

    @trace
    def lexeme(self):
        self.push_state()
        prefix = self.prefix()
        atom = self.atom()
        if not atom:
            self.pop_state()
            return False
        if prefix is not False:
            prefix.value = atom
            return prefix
        return atom

    @trace
    def prefix(self):
        if self.parse_literal('?='):
            return PositiveLookahead()
        if self.parse_literal('?!='):
            return NegativeLookahead()
        if self.parse_literal('?'):
            return Optional()
        if self.parse_literal('*'):
            return OptionalRepeat()
        if self.parse_literal('+'):
            return Repeat()
        return False

    @trace
    def atom(self):
        self.push_state()
        ident = self.ident()
        if ident is not False:
            return ident
        literal = self.literal()
        if literal is not False:
            return literal
        regex = self.regex()
        if regex is not False:
            return regex
        ref = self.ref()
        if ref is not False:
            return ref
        empty = self.empty()
        if empty is not False:
            return empty
        subexpr = self.subexpr()
        if subexpr is not False:
            return subexpr
        eof = self.eof()
        if eof is not False:
            return eof
        abort = self.abort()
        if abort is not False:
            return abort
        self.pop_state()
        return False

    @trace
    def abort(self):
        re = self.parse_regex('\!\<[^>]*?\>')
        if re is not False:
            return Abort(value=re[2:-1])
        return False

    @trace
    def subexpr(self):
        self.push_state()
        if self.parse_literal('(') is False:
            return False
        subexpr = self.option()
        if not subexpr:
            self.pop_state()
            return False
        if self.parse_literal(')') is False:
            self.pop_state()
            return False
        return subexpr

    @trace
    def ref(self):
        re = self.parse_regex('\{[0-9]+\}')
        if re is not False:
            return BackReference(value=re[1:-1])
        return False

    @trace
    def empty(self):
        empty = self.parse_literal('-')
        if empty:
            return Empty()
        return False

    @trace
    def regex(self):
        self.push_state()
        if self.parse_literal('/') is False:
            return False
        pos = self.cursor
        regex = ''
        while True:
            if regex and regex[-1] == '\\' and self.code[pos] == '/':
                regex = regex[:-1] + '/'
            elif self.code[pos] == '/':
                break
            else:
                regex += self.code[pos]
            pos += 1
        if regex == '':
            self.pop_state()
            return False
        self.advance(pos - self.cursor)
        if self.parse_literal('/') is False:
            self.pop_state()
            return False
        return Regex(value=regex)

    @trace
    def literal(self):
        self.push_state()
        if self.parse_literal("'") is False:
            return False
        pos = self.cursor
        literal = ''
        while True:
            if literal and literal[-1] == '\\' and self.code[pos] == "'":
                literal = literal[:-1] + "/"
            elif self.code[pos] == "'":
                break
            else:
                literal += self.code[pos]
            pos += 1
        if literal == '':
            self.pop_state()
            return False
        self.advance(pos - self.cursor)
        if self.parse_literal("'") is False:
            self.pop_state()
            return False
        return Literal(value=literal)

    @trace
    def ident(self):
        id = self.parse_regex('[a-zA-Z_][a-zA-Z0-9_]*')
        if id is not False:
            return Ident(value=id)
        return False

    @trace
    def eof(self):
        if self.parse_literal('$$'):
            return EOF(value=None)
        return False


# p = GrammarParser()
# grammar = """
# statement =  *((show | assign) ';') ;
# statement_list = *statement;
# show = 'show' expr;
# ssign = ident '=' expr;
# actor = number | ident | subexpr;
# term = factor *(('*'|'/') factor);
# expr = term *(('+'|'-') term);
# ident = /[a-z][a-z0-9]*/;
# subexpr = '(' expr ')';
# number = /[0-9]+/;
# """
# ast = p.parse(grammar)
# for key, val in ast.iteritems():#
# print '[{0} {1}]'.format(key, val.graph())

# print ast
