from __future__ import print_function
from __future__ import division
from time import time

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#                           UTILS

import itertools


def memoize(fn):
    """Memoize fn: make it remember the computed value for any argument list"""
    def memoized_fn(*args):
        if not args in memoized_fn.cache:
            memoized_fn.cache[args] = fn(*args)
        return memoized_fn.cache[args]
    memoized_fn.cache = {}
    return memoized_fn

def update(x, **entries):
    """Update a dict; or an object with slots; according to entries.
    >>> update({'a': 1}, a=10, b=20)
    {'a': 10, 'b': 20}
    >>> update(Struct(a=1), a=10, b=20)
    Struct(a=10, b=20)
    """
    if isinstance(x, dict):
        x.update(entries)
    else:
        x.__dict__.update(entries)
    return x

#______________________________________________________________________________
# Queues: LIFOQueue (also known as Stack), FIFOQueue, PriorityQueue

class Queue:

    def __init__(self):
        raise NotImplementedError

    def extend(self, items):
        for item in items: self.append(item)

def LIFOQueue():
    """
    Return an empty list, suitable as a Last-In-First-Out Queue.
    Last-In-First-Out Queues are also called stacks
    """
    return []


import collections # for dequeue
class FIFOQueue(collections.deque):
    """
    A First-In-First-Out Queue.
    """
    def __init__(self):
        collections.deque.__init__(self)
    def pop(self):
        return self.popleft()


import heapq
class PriorityQueue(Queue):
    """
    A queue in which the minimum  element (as determined by f) is returned first.
    The item with minimum f(x) is returned first
    """
    def __init__(self, f=lambda x: x):
        self.A = []  # list of pairs  (f(item), item)
        self.f = f
        self.counter = itertools.count() # unique sequence count
    def append(self, item):
        # thw pair  (f(item), item)  is pushed on the internal heapq
        heapq.heappush(self.A, (self.f(item), next(self.counter), item))
    def __len__(self):
        return len(self.A)
    def __str__(self):
        return str(self.A)
    def pop(self):
        return heapq.heappop(self.A)[2]
        # (self.f(item), item) is returned by heappop
        # (self.f(item), item)[1]   is item
    def __contains__(self, item):
        # Note that on the next line a generator is used!
        # the _ corresponds to f(x)
        return any(x==item for _,_, x in self.A)
    def __getitem__(self, key):
        for _,_, item in self.A:
            if item == key:
                return item
    def __delitem__(self, key):
        for i, (value,count,item) in enumerate(self.A):
            if item == key:
                self.A.pop(i)
                return
#______________________________________________________________________________

class Problem(object):
    """The abstract class for a formal problem.  You should subclass
    this and implement the methods actions and result, and possibly
    __init__, goal_test, and path_cost. Then you will create instances
    of your subclass and solve them with the various search functions."""

    def __init__(self, initial, goal=None):
        """The constructor specifies the initial state, and possibly a goal
        state, if there is a unique goal.  Your subclass's constructor can add
        other arguments."""
        self.initial = initial; self.goal = goal

    def actions(self, state):
        """Return the actions that can be executed in the given
        state. The result would typically be a list, but if there are
        many actions, consider yielding them one at a time in an
        iterator, rather than building them all at once."""
        raise NotImplementedError

    def result(self, state, action):
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""
        raise NotImplementedError

    def goal_test(self, state):
        """Return True if the state is a goal. The default method compares the
        state to self.goal, as specified in the constructor. Override this
        method if checking against a single self.goal is not enough."""
        return state == self.goal

    def path_cost(self, c, state1, action, state2):
        """Return the cost of a solution path that arrives at state2 from
        state1 via action, assuming cost c to get up to state1. If the problem
        is such that the path doesn't matter, this function will only look at
        state2.  If the path does matter, it will consider c and maybe state1
        and action. The default method costs 1 for every step in the path."""
        return c + 1

    def value(self, state):
        """For optimization problems, each state has a value.  Hill-climbing
        and related algorithms try to maximize this value."""
        raise NotImplementedError
#______________________________________________________________________________

class Node:

    def __init__(self, state, parent=None, action=None, path_cost=0):
        "Create a search tree Node, derived from a parent by an action."
        update(self, state=state, parent=parent, action=action,
               path_cost=path_cost, depth=0)
        if parent:
            self.depth = parent.depth + 1

    def __repr__(self):
        return "<Node %s>" % (self.state,)

    def expand(self, problem):
        "List the nodes reachable in one step from this node."
        return [self.child_node(problem, action)
                for action in problem.actions(self.state)]

    def child_node(self, problem, action):
        next = problem.result(self.state, action)
        return Node(next, # next is a state
                    self, # parent is a node
                    action, # from this state to next state 
                    problem.path_cost(self.path_cost, self.state, action, next)
                    )

    def solution(self):
        "Return the sequence of actions to go from the root to this node."
        return [node.action for node in self.path()[1:]]

    def path(self):
        "Return a list of nodes forming the path from the root to this node."
        node, path_back = self, []
        while node:
            path_back.append(node)
            node = node.parent
        return list(reversed(path_back))

    # We want for a queue of nodes in breadth_first_search or
    # astar_search to have no duplicated states, so we treat nodes
    # with the same state as equal. [Problem: this may not be what you
    # want in other contexts.]

    def __eq__(self, other):
        return isinstance(other, Node) and self.state == other.state

    def __hash__(self):
        return hash(self.state)

#______________________________________________________________________________

# Uninformed Search algorithms

def graph_search(problem, frontier):
    """
    Search through the successors of a problem to find a goal.
    The argument frontier should be an empty queue.
    If two paths reach a state, only use the first one. [Fig. 3.7]
    Return
        the node of the first goal state found
        or None is no goal state is found
    """
    assert isinstance(problem, Problem)
    frontier.append(Node(problem.initial))
    explored = set() # initial empty set of explored states
    while frontier:
        node = frontier.pop()
        if problem.goal_test(node.state):
            return node
        explored.add(node.state)
        # Python note: next line uses of a generator
        frontier.extend(child for child in node.expand(problem)
                        if child.state not in explored
                        and child not in frontier)
    return None

def depth_first_graph_search(problem):
    "Search the deepest nodes in the search tree first."
    return graph_search(problem, LIFOQueue())


def breadth_first_graph_search(problem):
    "Graph search version of BFS.  [Fig. 3.11]"
    return graph_search(problem, FIFOQueue())

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def best_first_graph_search(problem, f):
    """
    Search the nodes with the lowest f scores first.
    You specify the function f(node) that you want to minimize; for example,
    if f is a heuristic estimate to the goal, then we have greedy best
    first search; if f is node.depth then we have breadth-first search.
    There is a subtlety: the line "f = memoize(f, 'f')" means that the f
    values will be cached on the nodes as they are computed. So after doing
    a best first search you can examine the f values of the path returned.
    """
    f = memoize(f)
    node = Node(problem.initial)
    bestNodes = [node, None, None]
    t0 = time()
    frontier = PriorityQueue(f)
    frontier.append(node)
    explored = set()
    t0 = time()
    bestH = 1000000
    while frontier:
        node = frontier.pop()
<<<<<<< Updated upstream
        for i in range(3):
            if bestNodes[i] is None or f(node) < f(bestNodes[i]):
                bestNodes[i] = node
                break
        if (time() - t0 > 60):
            return bestNodes
=======
        if problem.h(node) < bestH:
            best = node
            bestH = problem.h(node)
        t1 = time()
        if t1 - t0 > 60:
            return best
>>>>>>> Stashed changes
        explored.add(node.state)
        for child in node.expand(problem):
            if child.state not in explored and child not in frontier:
                frontier.append(child)
            elif child in frontier:
                incumbent = frontier[child] # incumbent is a node
                if f(child) < f(incumbent):
                    del frontier[incumbent]
                    frontier.append(child)
    return best
