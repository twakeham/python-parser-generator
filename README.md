Python Parser Generator is an experiment in creating an idiomatic Python parser generator.

Existing solutions are built around C libraries or require custom compilation steps.

Python Parser Generator uses Python's powerful class introspection to create a parser from a class definition.  An example parser -

```python
from ast import AST
from parser import Parser
from action import ActionBase


class Interpreter(ActionBase):
    symbols = {}

    def _program(program):
        """statement_list $$ """
        program.statement_list()

    def _statement_list(statement_list):
        """*statement"""
        for statement in statement_list.statement_set_1:
            statement()

    _statement = " (show | assign | loop | condition) ';' "

    def _loop(loop):
        """'for' ident '=' expr 'to' expr '{' statement_list '}' """
        loopid = loop.ident.regex.value
        start = loop.expr_1()
        end = loop.expr_2()
        step = 1 + (end < start * -2)
        for idx in range(start, end, step):
            Interpreter.symbols[loopid] = idx
            loop.statement_list()

    def _condition(condition):
        """'if' expr 'then' '{' statement_list '}'"""
        if condition.expr():
            condition.statement_list()

    def _show(show):
        """'show' expr"""
        print
        show.expr()

    def _assign(assign):
        '''ident '=' expr'''
        Interpreter.symbols[assign.ident.regex.value] = assign.expr()

    def _expr(expr):
        """cmp *(('<'|'>'|'=='|'!=') cmp)"""
        value = expr.cmp()
        ops = expr.concat_set_1[::2]
        cmps = expr.concat_set_1[1::2]
        for op, cmp in zip(ops, cmps):
            if op.value == '<':
                value = value < cmp()
            elif op.value == '>':
                value = value > cmp()
            elif op.value == '==':
                value = value == cmp()
            elif op.value == '!=':
                value = value != cmp()
        return value

    def _cmp(cmp):
        '''term *(('+'|'-') term)'''
        value = cmp.term()
        ops = cmp.concat_set_1[::2]
        terms = cmp.concat_set_1[1::2]
        for op, term in zip(ops, terms):
            if op.value == '+':
                value += term()
            else:
                value -= term()
        return value

    def _term(term):
        '''factor *(('*'|'/') factor)'''
        value = term.factor()
        ops = term.concat_set_1[::2]
        factors = term.concat_set_1[1::2]
        for op, factor in zip(ops, factors):
            if op.value == '*':
                value *= factor()
            else:
                value /= factor()
        return value

    _factor = '''number | ident | subexpr'''

    def _number(number):
        '''/[0-9]+/'''
        return int(number.regex.value)

    def _ident(ident):
        '''/[a-z][a-z0-9]*/'''
        if Interpreter.symbols.has_key(ident.regex.value):
            return Interpreter.symbols[ident.regex.value]
        raise ValueError('Variable read before write [{0}]'.format(ident.regex.value))

    def _subexpr(subexpr):
        """'(' expr ')'"""
        return subexpr.expr()


p = Parser(Interpreter, ast_node=AST, entry='statement_list')
cst = p.parse('''for x=0 to 10 {
                     a = x * 3;
                     show a;
                     if x + 7 > a then {
                         show x + 7;
                     };
                 };
''')

cst()

```