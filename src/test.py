import unittest
from discrete_event import *
import math

class SexpTest(unittest.TestCase):

    def test_parse(self):
        e = Sexp()
        program = "(begin (define r 10) (* pi (* r r)))"
        self.assertEqual(e.parse(program), ['begin', ['define', 'r', 10], ['*', 'pi', ['*', 'r', 'r']]])

    def test_tokenize(self):
        e = Sexp()
        program = "(begin (define r 10) (* pi (* r r)))"
        self.assertEqual(e.tokenize(program), ['(', 'begin', '(', 'define', 'r', '10', ')', '(', '*', 'pi', '(', '*', 'r', 'r', ')', ')', ')'])

    def test_read_from_tokens(self):
        exp = Sexp()
        self.assertRaises(SyntaxError, lambda: exp.parse(''))
        try: exp.read_from_tokens(['(', 'print', 'r', '10', ')', ')'])
        except SyntaxError as e:
            self.assertEqual(e.args[0], 'unexpected )')
        program = ['(', 'define', 'r', '10', ')']
        self.assertEqual(exp.read_from_tokens(program), ['define', 'r', 10])

    def test_atom(self):
        exp = Sexp()
        self.assertEqual(exp.atom('10'), 10)
        self.assertEqual(exp.atom('10.2'), 10.2)
        self.assertEqual(exp.atom('+'), '+')
        self.assertEqual(exp.atom('and'), 'and')

    def test_standard_env(self):
        env = Env()
        env.update(vars(math))  # sin, cos, sqrt, pi, ...
        env.update({
            '+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv,
            '>': op.gt, '<': op.lt, '>=': op.ge, '<=': op.le, '=': op.eq,
            'print': print,
            'and': op.and_,
            'or': op.or_,
            'not': op.not_,
        })
        self.assertEqual(Sexp().standard_env(), env)

    def test_eval(self):
        exp = Sexp()
        # test 'print'
        exp.eval(exp.parse('(print r 10)'))
        exp.eval(exp.parse('(print r1 5)'))
        exp.eval(exp.parse('(print r2 1)'))
        # test '+' '-' '*' '/' 'sin' 'pi'
        self.assertEqual(exp.eval(exp.parse('(+ r (- 2 (* (sin -0.3) (- (* pi (* r r)) (/ r1 r2)))))')),
                         10 + 2 - math.sin(-0.3) * (314.1592653589793-5/1))
        # test '=' '>' '<' 'if'
        self.assertEqual(exp.eval(exp.parse('(if (> (* 11 11) 120) (* 7 6) (= r 10))')), 42)
        self.assertEqual(exp.eval(exp.parse('(if (< (* 11 11) 120) (* 7 6) (= r 10))')), True)
        # test 'and' 'or' 'not'
        self.assertEqual(exp.eval(exp.parse('(and 1 0)')), 0)
        self.assertEqual(exp.eval(exp.parse('(or 1 0)')), 1)
        self.assertEqual(exp.eval(exp.parse('(not 1)')), 0)

class EnvTest(unittest.TestCase):
    def test_find(self):
        e = Env()
        dict = {'+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv}
        e.update(dict)
        self.assertEqual(e.find('-'), e)
        try:  e.find('>')
        except AttributeError as e:
            self.assertEqual(e.args[0], "This arithmetic symbol does not exist")

class test_Procedure(unittest.TestCase):
    def test(self):
        exp = Sexp()
        exp.eval(exp.parse('(define twice (lambda (x) (* 2 x)))'))
        self.assertEqual(exp.eval(exp.parse('(twice 5)')), 10)
        exp.eval(exp.parse('(define repeat (lambda (f) (lambda (x) (f (f x)))))'))
        self.assertEqual(exp.eval(exp.parse('((repeat twice) 10)')), 40)
        self.assertEqual(exp.eval(exp.parse('((repeat (repeat twice)) 10)')), 160)
        self.assertEqual(exp.eval(exp.parse('((repeat (repeat (repeat twice))) 10)')), 2560)
        self.assertEqual(exp.eval(exp.parse('((repeat (repeat (repeat (repeat twice)))) 10)')), 655360)


if __name__ == '__main__':
    unittest.main()