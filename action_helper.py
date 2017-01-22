from functools import wraps
from error import ImproperlyConfigured


class operator:
    """
    operator decorator allows grammar rules defined in a certain format to be automatically converted to
    correctly associated AST node structure.

    rule -> required optional
    optional -> operator required optional | -
    """
       
    def __init__(self, assoc='left'):
        self.assoc = assoc
        
    def __call__(self, func):
        
        @wraps(func)
        def left(node, *args):
            """
            Rearranges AST for supplied operator node such that it is left associative
            """
            # get the parse table
            table = node.table
            # try to get the requried part and the optional part
            try:
                req, opt = table[func.__name__[1:]].value.value
                operator, req, opt = table[opt.value].value.value[0].value
            except:
                raise ImproperlyConfigured('Operator grammar must be in the form of rule = required optional; optional = operator required optional | -')
            # first operand in expressions, a + b -> a
            operand1 = getattr(node, req.value)()
            # fixes interplay between the two decorators
            if callable(operand1):
                operand1 = operand1()
            # check if the optional is empty
            if getattr(node, opt.value).alt == 1:
                # ..and return the first operand
                return operand1
            # grab the optional
            optoper = getattr(node, opt.value)
            # loop while there is still another optional
            while optoper.alt == 0:
                # get operator
                op = getattr(optoper, operator.value)()
                # get second operand
                operand2 = getattr(optoper, req.value)()
                if callable(operand2):
                    operand2 = operand2()
                # create node
                operand1 = node.ast_node(type=op, left=operand1, right=operand2)
                # set optional to descendant optional
                optoper = getattr(optoper, opt.value)
            # call action func with ast node as argument
            ast_node = func(node, operand1)
            # return the result of the function or the ast node
            return ast_node or operand1
                
        @wraps(func)
        def right(node, *args):
            """
            Rearranges AST for supplied operator node such that it is right associative
            """
            # get the parse table
            table = node.table
            # try to get the requried part and the optional part
            try:
                req, opt = table[func.__name__[1:]].value.value
                operator, req, opt = table[opt.value].value.value[0].value
            except:
                raise ImproperlyConfigured('Operator grammar must be in the form of rule = required optional; optional = operator required optional | -')
            # first operand in expressions, a + b -> a
            operand1 = getattr(node, req.value)()
            # fixes interplay between the two decorators
            if callable(operand1):
                operand1 = operand1()
            # check if the optional is empty
            if getattr(node, opt.value).alt == 1:
                # ..and return the first operand
                return operand1
            # grab the optional
            optoper = getattr(node, opt.value)
            # allocate stack for right associativity
            stack = []
            # loop while there is still another optional
            while optoper.alt == 0:
                # get operator
                op = getattr(optoper, operator.value)()
                # get second operand
                operand2 = getattr(optoper, req.value)()
                # create node
                stack.append([operand2, op])
                # set optional to descendant optional
                optoper = getattr(optoper, opt.value)
            # loop through stacks combining nodes
            while len(stack) > 1:
                right, left = stack.pop(), stack.pop()
                stack.append([node.ast_node(type=right[1], left=left[0], right=right[0]), left[1]])
            # create top level node
            right = stack.pop()
            operand1 = node.ast_node(type=right[1], left=operand1, right=right[0])
            # call action func with ast node as argument
            ast_node = func(node, operand1)
            # return the result of the function or the ast node
            return ast_node or operand1
        
        # return appropriate function wrapper
        if self.assoc == 'left':
            return left
        elif self.assoc == 'right':
            return right
        else:
            raise ValueError('operator assoc argument must be either left or right')


def leaf(func):
    """
    leaf decorator automatically generates a leaf node for terminal symbols
    """
    @wraps(func)
    def wrap(node, *args):
        type = func.__name__[1:]
        if hasattr(node, 'regex'):
            value = node.regex.value
        elif hasattr(node, 'literal'):
            value = node.literal.value
        else:
            raise ImproperlyConfigured('leaf decorator can only be used on terminal symbols')
        ast_node = node.ast_node(type=type, value=value, leaf=True)
        node = func(node, ast_node)
        return node or ast_node
    return wrap

terminal = leaf


def ignore(func):
    """
    decorator to discard this production
    """
    @wraps(func)
    def wrap(node, *args):
        pass
    return wrap