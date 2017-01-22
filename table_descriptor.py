"""
AST nodes for grammar
"""

import re


class Lexeme(object):
    def __init__(self, **attrs):
        super(Lexeme, self).__init__()
        self.__dict__.update(attrs)
        self.type = self.__class__.__name__.lower()
        if hasattr(self, 'init'):
            self.init()

    def __str__(self):
        return '<Lexeme {0} "{1}">'.format(self.__class__.__name__, self.value)


class Rule(Lexeme):
    pass


class Ident(Lexeme):
    def init(self):
        self.type = self.value.lower()


class Literal(Lexeme):
    pass


class PositiveLookahead(Lexeme):
    def __str__(self):
        return '<Lexeme {0} "{1}">'.format(self.__class__.__name__, self.subject)


class NegativeLookahead(Lexeme):
    pass


class Optional(Lexeme):
    pass


class Repeat(Lexeme):
    pass


class OptionalRepeat(Lexeme):
    pass


class Abort(Lexeme):
    pass


class BackReference(Lexeme):
    pass


class Regex(Lexeme):
    def init(self):
        self.re = re.compile(self.value)

    def __str__(self):
        return 'Regex {0}'.format(self.value)


class Option(Lexeme):
    pass


class Concat(Lexeme):
    pass


class EOF(Lexeme):
    value = None


class Empty(Lexeme):
    def init(self):
        self.value = 'empty'
