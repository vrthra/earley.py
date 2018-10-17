class State(object):
    def __init__(self, name, expr, dot, origin):
        self.name, self.expr, self.dot, self.origin = name, expr, dot, origin
        self.end_column = None
    def finished(self): return self.dot >= len(self.expr)
    def shift(self): return State(self.name, self.expr, self.dot+1, self.origin)
    def symbol(self): return self.expr[self.dot]

    def _t(self): return (self.name, self.expr, self.dot, self.origin)
    def __hash__(self): return hash((self.name, self.expr))
    def __eq__(self, other): return  self._t() == other._t()
    def __repr__(self): return str(self)
    def __str__(self): return self.name +':= '+ ' '.join([str(p) for p in self.expr])

class Column(object):
    def __init__(self, token):
        self.token = token
        self.states = []
        self._unique = set()
    def add(self, state):
        if state in self._unique: return
        self._unique.add(state)
        state.end_column = self
        self.states.append(state)
    def __repr__(self):
        return str((self.token, self.states))

def predict(col, sym):
    for prod in grammar[sym]:
        col.add(State(sym, tuple(prod), 0, col))

def scan(col, state, token):
    if token == col.token:
        col.add(state.shift())

def complete(col, state):
    for st in state.origin.states:
        if not st.finished() and state.name == st.symbol():
            col.add(st.shift())


def parse(text, grammar, start):
    table = [Column(tok) for tok in ([None] + list(text))]
    alts = grammar[start]
    table[0].add(State(start, tuple(alts[0]), 0, table[0]))

    for i, col in enumerate(table):
        for state in col.states:
            if state.finished():
                complete(col, state)
            else:
                term = state.symbol()
                if term in grammar:
                    predict(col, term)
                else:
                    if i + 1 < len(table):
                        scan(table[i+1], state, term)
    for st in table[-1].states:
        if st.name == start and st.finished(): return st
    raise ValueError("parsing failed")


#----------------------

class Node(object):
    def __init__(self, value, children):
        self.value = value
        self.children = children
    def print_(self, level = 0):
        print("  " * level + str(self.value))
        for child in self.children:
            child.print_(level + 1)


def build_trees(state, g):
    nts = [i for i in state.expr if i in g]
    return build_trees_helper([], state, len(nts) - 1, state.end_column, g)

def build_trees_helper(children, state, rule_index, end_column, g):
    if rule_index < 0:
        return [Node(state, children)]
    elif rule_index == 0:
        origin = state.origin
    else:
        origin = None
    
    rule = state.expr[rule_index]
    outputs = []
    for st in end_column.states:
        if st is state:
            break
        if st is state or not st.finished() or st.name != rule:
            continue
        if origin is not None and st.origin != origin:
            continue
        for sub_tree in build_trees(st, g):
            for node in build_trees_helper([sub_tree] + children, state, rule_index - 1, st.origin, g):
                outputs.append(node)
    return outputs

START = '^'
grammar = {
        START:[['<expr>']],
        '<sym>': [['a'], ['b'], ['c'], ['d']],
        '<op>': [['+']],
        '<expr>': [
            ['<sym>'],
            ['<expr>', '<op>', '<expr>']]
        }
import sys
text = sys.argv[1]
parsed = parse(text, grammar, START)
forest = build_trees(parsed, grammar)
for tree in forest:
    tree.print_()
