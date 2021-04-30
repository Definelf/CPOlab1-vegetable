from __future__ import division
from collections import OrderedDict, namedtuple
import copy
import math
import operator as op

event = namedtuple("Event", "clock node var val")
source_event = namedtuple("SourceEvent", "var val latency")

class Input_checker(object):

    def arg_type(num_args, type_args):
        def trace(func):
            def traced(self, *args, **kwargs):
                if type(args[num_args - 1]) == type_args:
                    return func(self, *args, **kwargs)
                else:
                    return 'Input error!'

            return traced

        return trace

    def arg_zero(func):
        def arg_zerod(self, *args, **kwargs):
            if len(kwargs) == 0:
                return func(self, *args, **kwargs)
            else:
                return 'Input error!'

        return arg_zerod

    def data_len(func):
        def data_lend(self, *args, **kwargs):
            if len(args) == 3:
                return func(self, *args, **kwargs)
            else:
                return 'Input error!', None

        return data_lend

class DiscreteEvent(object):
    def __init__(self, name="anonymous"):
        self.name = name
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()
        self.nodes = []
        self.state_history = []
        self.inter_state_history = []
        self.event_history = []

    @Input_checker.arg_type(1, str)
    def input_port(self, name, latency=1):
        self.inputs[name] = latency

    @Input_checker.arg_type(1, str)
    def output_port(self, name, latency=1):
        self.outputs[name] = latency

    @Input_checker.arg_type(1, str)
    def add_node(self, name, function):
        node = Node(name, function)
        self.nodes.append(node)
        return node

    @Input_checker.arg_type(2, int)
    def _source_events2events(self, source_events, clock):
        events = []
        for se in source_events:
            source_latency = clock + se.latency + self.inputs.get(se.var, 0)
            if se.var in self.outputs:
                target_latency = self.outputs[se.var]
                events.append(event(
                    clock=source_latency + target_latency,
                    node=None,
                    var=se.var,
                    val=se.val))
            for node in self.nodes:
                if se.var in node.inputs:
                    target_latency = node.inputs[se.var]
                    events.append(event(
                        clock=clock + source_latency + target_latency,
                        node=node,
                        var=se.var,
                        val=se.val))
        return events

    @Input_checker.arg_type(1, list)
    def _pop_next_event(self, events):
        assert len(events) > 0
        events = sorted(events, key=lambda e: e.clock)
        event = events.pop(0)
        return event, events

    @Input_checker.arg_zero
    def _state_initialize(self):
        env = {}
        for var in self.inputs:
            env[var] = None
        return env

    @Input_checker.data_len
    def execute(self, *source_events, limit=100, events=None):
        if events is None: events = []
        all_state = self._state_initialize()
        port_state = {}
        inter_state = {}
        clock = 0
        self.all_state_history = [(clock, copy.copy(all_state))]
        self.port_state_history = [(clock, copy.copy(port_state))]
        self.inter_state_history = [(clock, copy.copy(inter_state))]
        while (len(events) > 0 or len(source_events) > 0) and limit > 0:
            limit -= 1
            new_events = self._source_events2events(source_events, clock)
            events.extend(new_events)
            if len(events) == 0: break
            event, events = self._pop_next_event(events)
            all_state[event.var] = event.val
            if (event.var in self.inputs) or (event.var in self.outputs):
                port_state[event.var] = event.val
            else:
                inter_state[event.var] = event.val
            clock = event.clock
            source_events = event.node.activate(all_state) if event.node else []
            self.all_state_history.append((clock, copy.copy(all_state)))
            self.port_state_history.append((clock, copy.copy(port_state)))
            self.inter_state_history.append((clock, copy.copy(inter_state)))
            self.event_history.append(event)
        if limit == 0: return 'limit reached', None  # print("limit reached")
        return port_state, inter_state

    @Input_checker.arg_zero
    def visualize(self):
        res = []
        res.append("digraph G {")
        res.append("  rankdir=LR;")
        for v in self.inputs:
            res.append("  {}[shape=rarrow];".format(v))
        for v in self.outputs:
            res.append("  {}[shape=rarrow];".format(v))
        for i, n in enumerate(self.nodes):
            res.append('  n_{}[label="{}"];'.format(i, n.name))
        for i, n in enumerate(self.nodes):
            for v in n.inputs:
                if v in self.inputs:
                    res.append('  {} -> n_{};'.format(v, i))
            for j, n2 in enumerate(self.nodes):
                if i == j: continue
                for v in n.inputs:
                    if v in n2.outputs:
                        res.append('  n_{} -> n_{}[label="{}"];'.format(j, i, v))
            for v in n.outputs:
                if v in self.outputs:
                    res.append('  n_{} -> {};'.format(i, v))
        res.append("}")
        return "\n".join(res)

class Sexp(DiscreteEvent):

    Symbol = str  # A Lisp Symbol is implemented as a Python str
    List = list  # A Lisp List is implemented as a Python list
    Number = (int, float)  # A Lisp Number is implemented as a Python int or float

    def __init__(self):
        DiscreteEvent.__init__(self)
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

class Node(object):
    def __init__(self, name, function):
        self.function = function
        self.name = name
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()

    def __repr__(self):
        return "{} inputs: {} outputs: {}".format(self.name, self.inputs, self.outputs)

    @Input_checker.arg_type(1, str)
    def input(self, name, latency=1):
        assert name not in self.inputs
        self.inputs[name] = latency

    @Input_checker.arg_type(1, str)
    def output(self, name, latency=1):
        assert name not in self.outputs
        self.outputs[name] = latency

    @Input_checker.arg_type(1, dict)
    def activate(self, state):
        args = []
        for v in self.inputs:
            args.append(state.get(v, None))
        try:
            res = self.function(*args)
        except:
            res = self.function
        if not isinstance(res, tuple):
            res = (res,)
        output_events = []
        for var, val in zip(self.outputs, res):
            latency = self.outputs[var]
            output_events.append(source_event(var, val, latency))
            return output_events