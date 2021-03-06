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
parser.add_argument('--ignore-removed', dest = 'ignore_removed', help = 'Ignore removed symbols', action='store_true')

args = parser.parse_args()

class Callgraph:
    def __init__(self):
        self.nodes = {}
        self.nodes_by_name = {}
        self.deleted_nodes = set()

    def add_removed_node(self, name, order, file, line, column, object_file):
        self.deleted_nodes.add(':'.join([name, order, file, line, column, object_file]))

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
            if args.ignore_removed and node.is_removed:
                continue
            obj =  ' [object file: %s]' % node.object_file if not args.group else ''
            print('Function: ' + str(node) + obj)
            affected = OrderedDict()
            node.dump(0, affected, set(), self)
            print()
            affected = list(affected)
            print('  Affected functions: %d' % len(affected))
            for a in affected:
                print('    ' + str(a))
            print()

    def mark_removed_nodes(self):
        for node in self.nodes.values():
            if node.get_key() in self.deleted_nodes:
                node.is_removed = True

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
        self.is_removed = False

    def location(self):
        return '%s:%d:%d' % (self.file, self.line, self.column)

    def __repr__(self):
        s = '%s/%s (%s)' % (self.name, self.order, self.location())
        if self.is_removed:
            s += ' [REMOVED]'

        return s

    def get_key(self):
        key = ':'.join([self.name, str(self.order), self.location()])
        if not args.group:
            key += ':' + self.object_file

        return key

    def dump_input_edges (self):
        for e in self.input_edges:
            print('  ' + str(e))

    def print_indented(self, indentation, s, end = '\n'):
        print((' ' * indentation) + s, end = end)

    def dump(self, indentation, affected, bt, callgraph):
        bt.add(self)
        indentation += 2
        for e in self.input_edges:
            self.print_indented(indentation, '%s: %s' % (e.optimization, str(e.clone)), end = '')
            affected[e.clone] = None
            if e.clone in bt:
                print (' [RECURSIVE operation]', end = '')
            if e.count > 1:
                print (' [edges: %d]' % e.count, end = '')
            print()
            if not e.clone in bt:
                e.clone.dump(indentation, affected, bt, callgraph)
        bt.remove(self)

class CallgraphEdge:
    def __init__(self, original, clone, optimization):
        self.original = original
        self.clone = clone
        self.optimization = optimization
        self.count = 1

        CallgraphEdge.add_edge_to_list(self.original.input_edges, self.clone.output_edges, self)

    def __repr__(self):
        return '%s <- %s (%s)' % (self.original.name, str(self.clone), self.optimization)

    def __eq__(self, other):
        return self.original == other.original and self.clone == other.clone

    @staticmethod
    def add_edge_to_list(l1, l2, edge):
        try:
            index = l1.index(edge)
            l1[index].count += 1
        except:
            l1.append(edge)
            l2.append(edge)

def contains_symbol (f, symbol):
    contains = False
    l = 'Callgraph clone;' + symbol + ';'

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
        # format:
        #
        # Callgraph removal;__ilog2_u64;159;include/linux/log2.h;40;5
        # Callgraph clone;ovl_setxattr.part.3;1348;fs/overlayfs/inode.c;210;5;<-;ovl_setxattr;1291;fs/overlayfs/inode.c;210;5;optimization:;inlining to
        #
        # new format (GCC 7.1+):
        # Callgraph clone;fls64;28;../arch/x86/include/asm/bitops.h;492;28;__ilog2_u64;100;../include/linux/log2.h;34;5;inlining to
        #
        tokens = line.split(';')

        if tokens[0] == 'Callgraph clone':
            original = CallgraphNode(tokens[1], tokens[2], tokens[3], tokens[4], tokens[5], f)
            original = callgraph.add(original)

            # shift tokens
            tokens = tokens[6:]
            if tokens[0] == '<-':
                tokens = tokens[1:]
                assert tokens[-2] == 'optimization:'

            clone = CallgraphNode(tokens[0], tokens[1], tokens[2], tokens[3], tokens[4], f)
            clone = callgraph.add(clone)

            CallgraphEdge(original, clone, tokens[-1])
        elif tokens[0] == 'Callgraph removal':
           callgraph.add_removed_node(tokens[1], tokens[2], tokens[3], tokens[4], tokens[5], f)

# mark removed nodes
callgraph.mark_removed_nodes()

callgraph.dump(args.symbol)
