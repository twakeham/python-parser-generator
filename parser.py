import types
import inspect

import action as action
import table_parser as tparse
import grammar_parser as gparse
from error import ImproperlyConfigured, GrammarError

class Parser(object):
    def __new__(cls, action_node, **options):
        
        cls.action = action_node
                
        # check that action is a subclass of ActionBase
        if action.ActionBase not in action_node.__bases__:
            raise ImproperlyConfigured('Parse first argument must be ActionBase subclass')
        
        # check that action subclass accepts **kwargs
        if not inspect.getargspec(action_node.__init__).keywords:
            raise ImproperlyConfigured('Parse first argument ActionBase subclass must accept **kwargs')
        
        grammar = cls.generate_grammar(action_node)   
        grammar_parser = gparse.GrammarParser(grammar)
        grammar_rules = grammar_parser.parse()
        grammar_table = grammar_rules.table()

        if not grammar_table:
            print(grammar_parser.last_match, grammar_parser.last_line, grammar_parser.last_pos)
            print(grammar)
            raise GrammarError()
        
        table_parser = tparse.Parser(grammar_table, action_node, **options)
        
        return table_parser
    
    @classmethod    
    def generate_grammar(cls, action=None):
        # construct grammar from action subclass
        if not action:
            action = cls.action
        grammar = []
        for key, value in action.__dict__.iteritems():
            if key.startswith('__'):
                continue
            if key.startswith('_'):
                if callable(value):
                    if hasattr(value, '__doc__'):
                        rule = '{0} = {1};'.format(key[1:], value.__doc__)
                        grammar.append(rule)
                    else:
                        continue
                elif isinstance(value, str):
                    rule = '{0} = {1};'.format(key[1:], value)
                    grammar.append(rule)
        grammar = '\n'.join(grammar)
        return grammar


