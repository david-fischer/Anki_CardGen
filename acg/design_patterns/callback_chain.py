"""Implementation of abstract CallChain class.

This is useful, for chaining callbacks of objects, that are not living in the main-thread.
"""

import copy
from typing import Callable, List

import attr


class CallNode:
    """Base class to be used in :attr:`CallChain.members`."""

    next: None

    def receive(self, *args, **kwargs):
        """Receive data from CallChain or another CallNode."""
        self.process(*args, **kwargs)

    def process(self, *args, **kwargs):
        """Process data."""
        self.send(*args, **kwargs)

    def send(self, *args, **kwargs):
        """Send data to next CallNode."""
        if self.next is not None:
            self.next.receive(*args, **kwargs)


@attr.s(auto_attribs=True)
class CallChain:
    """Container for CallNodes.

    Can be initialized with functions or CallNodes as :attr:`nodes`.
    """

    nodes: List[CallNode or Callable] = None

    def __attrs_post_init__(self):
        """Transform functions to `CallNodes` and connect nodes."""
        if self.nodes is None:
            self.nodes = []
        for i, member in enumerate(self.nodes):
            if not isinstance(member, CallNode) and callable(member):
                self.nodes[i] = LambdaNode(function=member)
        self.connect_nodes()

    def connect_nodes(self):
        """Set :attr:`CallNode`.next according to order in :attr:`nodes`."""
        for i, callback_member in enumerate(self.nodes):
            try:
                callback_member.next = self.nodes[i + 1]
            except IndexError:
                callback_member.next = None

    def __call__(self, *args, **kwargs):
        """Call first Node."""
        self.nodes[0].receive(*args, **kwargs)

    def __add__(self, other):
        """Concatenate two :class:`CallChains` by copying and concatenating their nodes."""
        nodes = copy.deepcopy(self.nodes) + copy.deepcopy(other.nodes)
        return self.__class__(nodes=nodes)


@attr.s(auto_attribs=True)
class PrinterNode(CallNode):
    """Print args and kwargs."""

    def send(self, *args, **kwargs):
        """Print args and kwargs."""
        print(f"args: {args}\nkwargs: {kwargs}")


@attr.s(auto_attribs=True)
class LambdaNode(CallNode):
    """Node that only applies :attr:`function` in :meth:`process`."""

    function: Callable

    def process(self, *args, **kwargs):
        """Apply :attr:`function` and send result to next node."""
        self.send(self.function(*args, **kwargs))
