#!/usr/bin/env python3

import os
import sys
import re
import argparse

from collections import OrderedDict

parser = argparse.ArgumentParser(description='Display call graph transformations done by the GCC compiler.')
parser.add_argument('file_list', metavar = 'FILE_LIST', help = 'File with list of callgraph dump files')
parser.add_argument('--symbol', dest = 'symbol', help = 'Display optimizations just for the symbol')
parser.add_argument('--group', dest = 'group', help = 'Group symbols by name, input source file, line and column', action='store_true')

args = parser.parse_args()

class Callgraph:
    def __init__(self):
        self.nodes = {}
        self.nodes_by_name = {}

    def add(self, node):
        key = node.get_key()
        if not key in self.nodes:
            self.nodes[key] = node

            if not node.name in self.nodes_by_name:
                self.nodes_by_name[node.name] = []

            self.nodes_by_name[node.name].append(node)

        return self.nodes[key]

    def get_by_name(self, name):
        if not name in self.nodes_by_name:
            return []
        else:
            return self.nodes_by_name[name]

    def dump(self, symbol = None):
        items = None
        if symbol != None:
            items = self.get_by_name(symbol)
        else:
            items = sorted(filter(lambda x: len(x.input_edges) > 0, self.nodes.values()), key = lambda x: x.name)

        for node in items:
            obj =  ' [object file: %s]' % node.object_file if not args.group else ''
            print('Function: ' + str(node) + obj)
            affected = OrderedDict()
            node.dump(0, affected, set())
            print()
            affected = list(affected)
            print('  Affected functions: %d' % len(affected))
            for a in affected:
                print('    ' + str(a))
            print()

class CallgraphNode:
    def __init__(self, name, order, file, line, column, object_file):
        self.name = name
        self.order = int(order)
        self.object_file = object_file
        self.file = file
        self.line = int(line)
        self.column = int(column)
        self.output_edges = []
        self.input_edges = []

    def location(self):
        return '%s:%d:%d' % (self.file, self.line, self.column)

    def __repr__(self):
        return '%s/%s (%s)' % (self.name, self.order, self.location())

    def get_key(self):
        key = self.name + ':' + self.location()
        if not args.group:
            key += ':' + self.object_file

        return key

    def dump_input_edges (self):
        for e in self.input_edges:
            print('  ' + str(e))

    def print_indented(self, indentation, s):
        print((' ' * indentation) + s)

    def dump(self, indentation, affected, bt):
        indentation += 2
        for e in self.input_edges:
            self.print_indented(indentation, '%s: %s' % (e.optimization, str(e.clone)))
            if self in bt:
                self.print_indented(indentation, 'Recursion function node')
            else:
                bt.add(self)
                affected[e.clone] = None
                e.clone.dump(indentation, affected, bt)
                bt.remove(self)

class CallgraphEdge:
    def __init__(self, original, clone, optimization):
        self.original = original
        self.clone = clone
        self.optimization = optimization

        self.original.input_edges.append(self)
        self.clone.output_edges.append(self)

    def __repr__(self):
        return '%s <- %s (%s)' % (self.original.name, str(self.clone), self.optimization)

def contains_symbol (f, symbol):
    contains = False
    l = 'Callgraph clone: ' + symbol

    for line in open(f).readlines():
        if line.startswith(l):
            return True

    return False

# read list of all files
files = [x.strip() for x in open(args.file_list).readlines()]

callgraph = Callgraph()

for (i, f) in enumerate(files):
    print('Parsing file (%d/%d): %s' % (i + 1, len(files), f), file = sys.stderr)

    # Fast scan of the file
    if args.symbol != None and not contains_symbol (f, args.symbol):
        continue

    for line in open(f).readlines():
        line = line.strip()
        # format: Callgraph clone: pagefault_enable/1606 (include/linux/uaccess.h:35:60) <- helper_rfc4106_decrypt/3007 (location:arch/x86/crypto/aesni-intel_glue.c:1016:12) (optimization:inlining)
        m = re.match('Callgraph clone: (.*)/(.*) \((.*):(.*):(.*)\) <- (.*)/(.*) \(location:(.*):(.*):(.*)\) \(optimization:(.*)\)', line)
        if m != None:
            original = CallgraphNode(m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), f)
            original = callgraph.add(original)

            clone = CallgraphNode(m.group(6), m.group(7), m.group(8), m.group(9), m.group(10), f)
            clone = callgraph.add(clone)

            CallgraphEdge(original, clone, m.group(11))

callgraph.dump(args.symbol)
