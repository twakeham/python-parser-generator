class ActionBase(object):
    """
    Base class of all parsers - defines actions to be taken against rule provided in docstring.
    Method and class variable names prepended with underscore (_) are considered to be parse
    rules. Methods are expected to provide a docstring with the appropriate productions while class
    variables values are considered to be grammar rules.  Action methods take a single argument which
    provides accessors to each lexeme in the rule.
    """

    def __init__(self, **attrs):
        self.children = []
        self.__dict__.update(attrs)
        if hasattr(self, 'init'):
            self.init(**attrs)
        
    def __str__(self):
        return '<NODE {0}>'.format(self.type)
    
    def __call__(self):
        desc = getattr(self, 'action_proc_format', '_{0}')
        type = getattr(self, 'type')
        func = getattr(self, desc.format(type), None)
        if func and callable(func):
            return func()
        else:
            if getattr(self, 'leaf', False):
                return self.value
            return self.children[0]()
    
    def graph(self):
        """
        Generates a human readable form of the AST - can also be fed into PhpSyntaxTree for a
        graph visualisation.
        :return: AST graph in printable format
        """
        return '[{0} {1}]'.format(self.type, ''.join([child.graph() for child in self.children])) if not hasattr(self, 'value') else '[{0} {1}]'.format(self.type, self.value)

    def add_child(self, child):
        self.children.append(child)
        if not hasattr(self, child.type):
            setattr(self, child.type, child)
        setattr(self, self.unique_id(child.type), child)

    def unique_id(self, id):
        for x in range(1, 50, 1):
            uid = '{0}_{1}'.format(id, x)
            if not hasattr(self, uid):
                return uid