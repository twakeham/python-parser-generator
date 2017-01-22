from ast import AST
from table_descriptor import *


class Parser:

    def __init__(self, table, node, **options):
        self.code = ""
        self.lines = []
        self.cursor = 0
        self.line = 1
        self.line_pos = 0
        self._state = []

        self.last_match = ''
        self.last_pos = 0
        self.last_line = 0

        self.end = False

        self.entry = options.get('entry', 'expr')
        self.node = node
        self.table = table
        self.node.table = self.table
        self.node.ast_node = options.get('ast_node', AST)

    def initialise(self, code):
        self.code = code + '$'
        self.lines = self.code.split('\n')
        self.cursor = 0
        self.line = 1
        self.line_pos = 0
        self._state = []

        self.last_match = ''
        self.last_pos = 0
        self.last_line = 0

        self.end = False

    def advance(self, amount):
        self.cursor += amount
        self.line_pos += amount
        if self.code[self.cursor] in ' \r\n\t':
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

    def parse_literal(self, literal, parent):
        if self.code[self.cursor:].startswith(literal.value):
            parent.add_child(self.node(type='literal', value=literal.value, leaf=True, line=self.line,
                                       linepos=self.line_pos - len(literal.value)))
            self.advance(len(literal.value))
            self.last_match = literal.value
            self.last_pos = self.line_pos - len(literal.value)
            self.last_line = self.line
            return True
        return False

    def parse_regex(self, regex, parent):
        matchobj = regex.re.match(self.code[self.cursor:])
        if matchobj:
            match = matchobj.group()
            parent.add_child(self.node(type='regex', value=match, leaf=True, line=self.line, linepos=self.line_pos))
            self.advance(len(match))
            self.last_match = match
            self.last_pos = self.line_pos - len(match)
            self.last_line = self.line
            return True
        return False

    def parse_ident(self, ident, parent):
        rule = self.table[ident.value]
        node = self.node(type=ident.value, line=self.line, linepos=self.line_pos)
        if self.parse_lexeme(rule, node):
            parent.add_child(node)
            return True
        return False

    def parse_subexpr(self, subexpr, parent):
        node = self.node(type='subexpr', line=self.line, linepos=self.line_pos)
        if self.parse_lexeme(subexpr.value, node):
            parent.add_child(node)
            return True
        return False

    def parse_optional(self, optional, parent):
        if not self.parse_lexeme(optional.value, parent):
            node = self.node(type=optional.value.type, alt=1, match=False, line=self.line, linepos=self.line_pos)
            empty = self.node(type='empty', value=False)
            node.add_child(empty)
            parent.add_child(node)
        else:
            parent.children[-1].alt = 0
            parent.children[-1].match = True
        return True

    def parse_repeat(self, repeat, parent):
        node = self.node(type=repeat.value.type, line=self.line, linepos=self.line_pos)
        self.push_state()
        while self.parse_lexeme(repeat.value, node):
            self.push_state()
        self.pop_state()
        if not node.children:
            return False
        parent.count = len(node.children)
        setattr(parent, parent.unique_id(repeat.value.type + '_set'), node.children)
        for child in node.children:
            parent.add_child(child)
        return True

    def parse_optional_repeat(self, repeat, parent):
        node = self.node(type=repeat.value.type, line=self.line, linepos=self.line_pos)
        self.push_state()
        while self.parse_lexeme(repeat.value, node):
            self.push_state()
        self.pop_state()
        parent.count = len(node.children)
        setattr(parent, parent.unique_id(repeat.value.type + '_set'), node.children)
        if not node.children:
            empty = self.node(type='empty', value=False, line=self.line, linepos=self.line_pos)
            parent.alt = 1
            parent.add_child(empty)
            return True
        parent.alt = 0
        for child in node.children:
            parent.add_child(child)
        return True

    def parse_positive_lookahead(self, lookahead, parent):
        self.push_state()
        dummy = self.node(type='dummy')
        if self.parse_lexeme(lookahead.value, dummy):
            self.pop_state()
            return True
        self.pop_state()
        return False

    def parse_negative_lookahead(self, lookahead, parent):
        self.push_state()
        dummy = self.node(type='dummy')
        if not self.parse_lexeme(lookahead.value, dummy):
            self.pop_state()
            return True
        self.pop_state()
        return False

    def parse_option(self, option, parent):
        for idx, option in enumerate(option.value):
            self.push_state()
            if self.parse_lexeme(option, parent):
                parent.alt = idx
                return True
            self.pop_state()
        return False

    def parse_concat(self, concat, parent):
        self.push_state()
        for idx, lexeme in enumerate(concat.value):
            if not self.parse_lexeme(lexeme, parent):
                self.pop_state()
                return False
        return True

    def parse_rule(self, rule, parent):
        return self.parse_lexeme(rule.value, parent)

    def parse_lexeme(self, lexeme, parent):
        if isinstance(lexeme, Empty):
            parent.add_child(self.node(type='empty', value=False, line=self.line, linepos=self.line_pos))
            return True
        elif isinstance(lexeme, Literal):
            return self.parse_literal(lexeme, parent)
        elif isinstance(lexeme, Regex):
            return self.parse_regex(lexeme, parent)
        elif isinstance(lexeme, Ident):
            return self.parse_ident(lexeme, parent)
        elif isinstance(lexeme, Option):
            return self.parse_option(lexeme, parent)
        elif isinstance(lexeme, Concat):
            return self.parse_concat(lexeme, parent)
        elif isinstance(lexeme, Optional):
            return self.parse_optional(lexeme, parent)
        elif isinstance(lexeme, Repeat):
            return self.parse_repeat(lexeme, parent)
        elif isinstance(lexeme, OptionalRepeat):
            return self.parse_optional_repeat(lexeme, parent)
        elif isinstance(lexeme, PositiveLookahead):
            return self.parse_positive_lookahead(lexeme, parent)
        elif isinstance(lexeme, NegativeLookahead):
            return self.parse_negative_lookahead(lexeme, parent)
        elif isinstance(lexeme, Rule):
            return self.parse_rule(lexeme, parent)
        elif isinstance(lexeme, EOF):
            return self.end
        elif isinstance(lexeme, Abort):
            raise SyntaxError('{0}\nLine: {1}, Pos: {2}\n{3}\n{4}'.format(lexeme.msg, self.line, self.line_pos,
                                                                          self.lines[self.line - 1],
                                                                          self.line_pos * ' ' + '^'))
        else:
            print('lexeme', lexeme, type(lexeme))
            raise RuntimeError

    def parse(self, code, rule=None):
        self.initialise(code)
        if not rule:
            if not self.entry:
                raise ValueError('Expected rule or grammar entry directive set')
            rule = self.entry
        node = self.node(type=rule)
        if self.parse_lexeme(self.table[rule], node):
            return node
        return False
