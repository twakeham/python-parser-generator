class AST(object):
    """
    Represents an AST node
    """
    _stack = []
    
    def __init__(self, **attrs):
        super(AST, self).__init__()
        self.__dict__.update(attrs)
        
    def graph(self):
        if hasattr(self, 'value'):
            return '[{0} {1}]'.format(self.type, self.value)
        elif hasattr(self, 'right'):
            return '[{0} {1} {2}]'.format(self.type, self.left.graph(), self.right.graph())
        else:
            return '[{0} {1}]'.format(self.type, self.left.graph())
        
    def __str__(self):
        return '<AST {0}>'.format(self.type)