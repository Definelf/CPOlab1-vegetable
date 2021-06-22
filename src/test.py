import unittest
from discrete_event import *
import math

class SexpTest(unittest.TestCase):

    def test_tokenize(self):
        e = Sexp()
        program = "(begin (define r 10) (* pi (* r r)))"
        self.assertEqual(e.tokenize(program), ['(', 'begin', '(', 'define', 'r', '10', ')', '(', '*', 'pi', '(', '*', 'r', 'r', ')', ')', ')'])

    # include: test_atom, test_read_from_tokens
    def test_parse(self):
        exp = Sexp()
        self.assertRaises(SyntaxError, lambda: exp.parse(''))
        try: exp.parse('(print r 10))')
        except SyntaxError as e:
            self.assertEqual(e.args[0], 'unexpected )')
        program = "(begin (define r 10) (* pi (* r r)))"
        self.assertEqual(exp.parse(program), ['begin', ['define', 'r', 10], ['*', 'pi', ['*', 'r', 'r']]])

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


if __name__ == '__main__':
    unittest.main()