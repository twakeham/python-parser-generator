class ParserError(SyntaxError):
    def __init__(self, error, desc, token, lexer):
        self.error = error
        self.desc = desc
        self.token = token
        self.lexer = lexer
        
    def __str__(self):
        return '\n\n%s -\n%s\n%s\n%s\n%s%s\nLine:%s Pos:%s' % (self.error, '  ' + self.desc,'-' * (len(self.desc) + 3) , self.lexer.lines[self.token.line_no-1], ' ' * self.token.line_pos, '^' * len(self.token.value), self.token.line_no, self.token.line_pos)