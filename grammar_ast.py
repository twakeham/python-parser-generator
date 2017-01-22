import table_descriptor as descriptor

#===============================================================================
# 
#            BASE NODE
#   
#===============================================================================


class Node(object):
           
    def __init__(self, **attributes):
        """Class initialiser, takes any number of keyword arguments
           and returns Node instance.  Keyword arguments are transformed
           into instance attributes"""
           
        super(Node, self).__init__()
        self.__dict__.update(attributes)   
            
    def __str__(self):
        """Overload string typecasts.  Returns a string representation of
           the Node instance. """
        return '{0}({1})'.format(self.__class__.__name__, getattr(self, 'value', 'Undefined'))
                                                                           
    def graph(self):
        """Outputs a bracketed node representation for feeding into 
           PHPSyntaxTree to get a visual graph of the parse tree"""
           
        if type(getattr(self, 'value')) == list:
            return '[{0} {1}]'.format(self.__class__.__name__, ' '.join(['{0}'.format(value.graph()) for value in self.value]))
        elif hasattr(self, 'leaf'):
            return '[{0} {1}]'.format(self.__class__.__name__, self.value)
        else:
            return '[{0} {1}]'.format(self.__class__.__name__, self.value.graph())


#===============================================================================
# 
#            PRIMARY GROUPS
#   
#===============================================================================


class Rules(Node):
    _inst = None
    
    def __init__(self, **attrs):
        super(Rules, self).__init__(**attrs)
        Rules._inst = self
    
    def _node_id(self):
        return 'rules'
    
    def bnf(self):
        return '\n'.join([rule for rule in self.value])
    
    def table(self):
        table = {}
        for rule in self.value:
            table[rule.name] = rule.table()  
        return table


class Rule(Node):    
    
    def bnf(self):
        directive = '[{0}]'.format(', '.join(self.directives)) if self.directives != [] else ''
        return '{0} = {1} {2};'.format(self.name, self.value.bnf(), directive)
        
    def table(self):
        return descriptor.Rule(name=self.name, value=self.value.table(), directive=self.directives)


#===============================================================================
# 
#            OPERATORS
#   
#===============================================================================


class Or(Node):
    
    def bnf(self):
        return ' | '.join([child.bnf() for child in self.value])
    
    def table(self):
        return descriptor.Option(value=[child.table() for child in self.value])


class Concatenate(Node):
    
    def bnf(self):
        return ' '.join([child.bnf() for child in self.value])
    
    def table(self):
        return descriptor.Concat(value=[child.table() for child in self.value])
    
#===============================================================================
# 
#            OPERATORS
#   
#===============================================================================


class Optional(Node):
    
    def bnf(self):
        return '!{0}'.format(self.value.bnf())
                  
    def table(self):
        return descriptor.Optional(value=self.value.table())


class Repeat(Node):
    
    def bnf(self):
        return '+{0}'.format(self.value.bnf())
    
    def table(self):
        return descriptor.Repeat(value=self.value.table())


class OptionalRepeat(Node):
    
    def bnf(self):
        return '*{0}'.format(self.value.bnf())
    
    def table(self):
        return descriptor.OptionalRepeat(value=self.value.table())


class PositiveLookahead(Node):
    
    def bnf(self):
        return '?={0}'.format(self.value.bnf())
    
    def table(self):
        return descriptor.PositiveLookahead(value=self.value.table())


class NegativeLookahead(Node):
    
    def bnf(self):
        return '?={0}'.format(self.value.table())
    
    def table(self):
        return descriptor.NegativeLookahead(value=self.value.table())


#===============================================================================
# 
#            TERMINALS
#   
#===============================================================================


class Abort(Node):
    leaf = True
    
    def bnf(self):
        return '<!{0}>'.format(self.value)
    
    def table(self):
        return descriptor.Abort(value=self.value)


class BackReference(Node):
    leaf = True
    
    def bnf(self):
        return "\{{0}\}".format(self.value)
    
    def table(self):
        return descriptor.BackReference(value=self.value)


class Literal(Node):
    leaf = True
        
    def bnf(self):
        return "'{0}'".format(self.value)
    
    def table(self):
        return descriptor.Literal(value=self.value)


class Regex(Node):
    leaf = True
    count = 0 
    
    def bnf(self):
        return "/{0}/".format(self.value)
    
    def table(self):
        return descriptor.Regex(value=self.value)


class Ident(Node):
    leaf = True
    _seen = []
    
    def __init__(self, **attributes):
        super(Ident, self).__init__(**attributes)
        Ident._seen.append(self.value)
 
    def bnf(self):
        return self.value
        
    def table(self):
        return descriptor.Ident(value=self.value)


class Empty(Node):
    leaf = True
    
    def bnf(self):
        return '-'
    
    def table(self):
        return descriptor.Empty()


class EOF(Node):
    leaf = True
    
    def bnf(self):
        return '$$'
    
    def table(self):
        return descriptor.EOF()
