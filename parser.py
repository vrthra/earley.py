import re
RE_NONTERMINAL = re.compile(r'(<[a-zA-Z_]*>)')
def split_tokens(rule): return [i for i in re.split(RE_NONTERMINAL, rule) if i != ''] or ['']

def show_col(col, i):
    print("chart[%d]"%i)
    for state in col.states:
        print(state, "\t", [s.c for s in state.children])
    print()

counter = 0
class State(object):
    def __init__(self, name, expr, dot, start_column):
        global counter
        self.name, self.expr, self.dot, self.start_column, self.children = name, expr, dot, start_column, []
        self.c = counter
        counter += 1
    def finished(self): return self.dot >= len(self.expr)
    def shift(self, bp=None):
        s = State(self.name, self.expr, self.dot+1, self.start_column)
        s.children = self.children[:]
        return s
    def symbol(self): return self.expr[self.dot]

    def _t(self): return (self.name, self.expr, self.dot, self.start_column)
    def __hash__(self): return hash((self.name, self.expr))
    def __eq__(self, other): return  self._t() == other._t()
    def __str__(self): return ("(S%d)   " % self.c) + self.name +':= '+ ' '.join([str(p) for p in [*self.expr[:self.dot],'|', *self.expr[self.dot:]]])
    def __repr__(self): return str(self)

class Column(object):
    def __init__(self, i, token):
        self.token, self.states, self._unique = token, [], {}
        self.i = i
    def add(self, state, bp=None):
        if state in self._unique:
            if bp: state.children.append(bp)
            return
        self._unique[state] = state
        if bp: state.children.append(bp)
        self.states.append(state)
    def __repr__(self):
        return "%s chart[%d] %s" % (self.token, self.i, str(self.states))

def predict(col, sym, grammar):
    for alt in grammar[sym]:
        if alt == ['']:
            col.add(State(sym, tuple([]), 0, col))
        else:
            col.add(State(sym, tuple(alt), 0, col))

def scan(col, state, token):
    if token == col.token:
        col.add(state.shift())

def complete(col, state, grammar):
    for st in state.start_column.states:
        if st.finished(): continue
        sym = st.symbol()
        if state.name != sym: continue
        assert sym in grammar
        col.add(st.shift(), state)

# http://courses.washington.edu/ling571/ling571_fall_2010/slides/parsing_earley.pdf
# https://github.com/tomerfiliba/tau/blob/master/earley3.py
# http://loup-vaillant.fr/tutorials/earley-parsing/recogniser
def parse(words, grammar, start):
    alt = tuple(*grammar[start])
    chart = [Column(i,tok) for i,tok in enumerate([None, *words])]
    chart[0].add(State(start, alt, 0, chart[0]))

    for i, col in enumerate(chart):
        for state in col.states:
            if state.finished():
                complete(col, state, grammar)
            else:
                sym = state.symbol()
                if sym in grammar:
                    predict(col, sym, grammar)
                else:
                    if i + 1 >= len(chart): continue
                    scan(chart[i+1], state, sym)
    return chart

START = '<start>'
#grammar = {
#        START:['<expr>'],
#        '<sym>': ['a', 'b', 'c', 'd'],
#        '<op>': ['+', '-'],
#        '<expr>': ['<sym>', '<expr><op><expr>']
#        }
grammar = {'<start>': [['<expr>']],
 '<expr>': [['<term>', '<expr_>']],
 '<expr_>': [['+', '<expr>'], ['-', '<expr>'], ['']],
 '<term>': [['<factor>', '<term_>']],
 '<term_>': [['*', '<term>'], ['/', '<term>'], ['']],
 '<factor>': [['+', '<factor>'],
  ['-', '<factor>'],
  ['(', '<expr>', ')'],
  ['<int>']],
 '<int>': [['<integer>', '<integer_>']],
 '<integer_>': [[''], ['.', '<integer>']],
 '<integer>': [['<digit>', '<I>']],
 '<I>': [['<integer>'], ['']],
 '<digit>': [['0'],
  ['1'],
  ['2'],
  ['3'],
  ['4'],
  ['5'],
  ['6'],
  ['7'],
  ['8'],
  ['9']]}
#
#grammar = {
#        START:['<expr>'],
#        '<sym>': ['a', 'b', 'c', 'd'],
#        '<expr>': ['<sym>', '<expr>+<expr>', '<expr>-<expr>']
#        }
#
#grammar = {
#        START: ['<S>'],
#        '<S>': ['<NP><VP>'],
#        '<PP>': ['<P><NP>'],
#        '<VP>': ['<V><NP>', '<VP><PP>'],
#        '<P>': ['with'],
#        '<V>': ['saw'],
#        '<NP>': ['<NP><PP>', '<N>'],
#        '<N>': ['astronomers', 'ears', 'stars', 'telescopes']
#        }


#grammar = {'<start>': ['<expr>'],
# '<expr>': ['<term>+<expr>', '<term>-<expr>', '<term>'],
# '<term>': ['<factor>*<term>', '<factor>/<term>', '<factor>'],
# '<factor>': ['+<factor>',
#  '-<factor>',
#  '(<expr>)',
#  '<integer>',
#  '<integer>.<integer>'],
# '<integer>': ['<digit><integer>', '<digit>'],
# '<digit>': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']}
new_grammar = grammar #{k: [split_tokens(e) for e in grammar[k]] for k in grammar}

import sys
text = sys.argv[1]
table = parse(list(text), new_grammar, START)
state, *states = [st for st in table[-1].states if st.name == START and st.finished()]
assert not states

def process_expr(expr, children, grammar):
    lst = []
    nt_counter = 0
    for i in expr:
        if i not in grammar:
            lst.append((i,[]))
        else:
            lst.append(node_translator(children[nt_counter], grammar))
            nt_counter += 1
    return lst

def node_translator(state, grammar):
    return (state.name, process_expr(state.expr, state.children, grammar))

print(node_translator(state, grammar))
