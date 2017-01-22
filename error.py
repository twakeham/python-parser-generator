class ImproperlyConfigured(Exception):
    pass 


class GrammarError(Exception):
    """
    Thrown by grammar parse when there is an error in the rules
    """
    pass