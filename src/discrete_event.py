from __future__ import division
from collections import OrderedDict, namedtuple
import copy
import math
import operator as op


class Sexp():

    Symbol = str  # A Lisp Symbol is implemented as a Python str
    List = list  # A Lisp List is implemented as a Python list
    Number = (int, float)  # A Lisp Number is implemented as a Python int or float

    def __init__(self):
        self.global_env = self.standard_env()

    def parse(self, program):
        "Read a Scheme expression from a string."
        return self.read_from_tokens(self.tokenize(program))

    def tokenize(self, s):
        "Convert a string into a list of tokens."
        return s.replace('(', ' ( ').replace(')', ' ) ').split()

    def read_from_tokens(self, tokens):
        "Read an expression from a sequence of tokens."
        if len(tokens) == 0:
            raise SyntaxError('unexpected EOF while reading')
        token = tokens.pop(0)
        if '(' == token:
            L = []
            while tokens[0] != ')':
                L.append(self.read_from_tokens(tokens))
            tokens.pop(0)  # pop off ')'
            return L
        elif ')' == token:
            raise SyntaxError('unexpected )')
        else:
            return self.atom(token)

    def atom(self, token):
        "Numbers become numbers; every other token is a symbol."
        try:
            return int(token)
        except ValueError:
            try:
                return float(token)
            except ValueError:
                return self.Symbol(token)

    ################ Environments

    def standard_env(self):
        "An environment with some Scheme standard procedures."
        env = self.Env()
        env.update(vars(math))  # sin, cos, sqrt, pi, ...
        env.update({
            '+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv,
            '>': op.gt, '<': op.lt, '>=': op.ge, '<=': op.le, '=': op.eq,
            'print': print,
            'and': op.and_,
            'or': op.or_,
            'not': op.not_,
        })
        return env

    class Env(dict):
        "An environment: a dict of {'var':val} pairs, with an outer Env."
        def __init__(self, parms=(), args=(), outer=None):
            self.update(zip(parms, args))
            self.outer = outer

        def find(self, var):
            "Find the innermost Env where var appears."
            return self if (var in self) else self.outer.find(var)

    ################ Procedures

    class Procedure(object):
        "A user-defined Scheme procedure."
        def __init__(self, parms, body, env):
            self.parms, self.body, self.env = parms, body, env

        def __call__(self, *args):
            return self.eval(self.body, self.Env(self.parms, args, self.env))

    ################ eval

    def eval(self, x, env=None):
        "Evaluate an expression in an environment."
        if env == None:
            env = self.global_env
        if isinstance(x, self.Symbol):  # variable reference
            return env.find(x)[x]
        elif not isinstance(x, self.List):  # constant literal
            return x
        elif x[0] == 'if':  # (if test conseq alt)
            (_, test, conseq, alt) = x
            exp = (conseq if self.eval(test, env) else alt)
            return self.eval(exp, env)
        elif x[0] == 'define' or x[0] == 'print':  # (define var exp)
            (_, var, exp) = x
            env[var] = self.eval(exp, env)
        elif x[0] == 'lambda':  # (lambda (var...) body)
            (_, parms, body) = x
            return self.Procedure(parms, body, env)
        else:  # (proc arg...)
            proc = self.eval(x[0], env)
            args = [self.eval(exp, env) for exp in x[1:]]
            # print("proc: ",proc,", *args: ",args)
            return proc(*args)
