"""
Some helper functions for the library.
"""

import math
import re
from types import SimpleNamespace


def byte_formatter(value):
    """
    Gets a large integer als value and returns a tuple with the value as
    float and the matching dimension as string, i.e.
    >>> byte_formatter(242981246)
    (242.981246, 'MB')
    Expects positive integer as input. Negative numbers are interpreted
    as positive numbers. values < 1 are interpreted as 0.
    """
    dim = ['B', 'KB', 'MB', 'GB', 'TB']
    value = abs(value)
    if value < 1:
        log = 0
        num = 0
    else:
        log = min(int(math.log10(value) / 3), len(dim))
        num = value / 1000 ** log
    try:
        dimension = dim[log]
    except IndexError:
        dimension = 'PB'
    return num, dimension


def format_num(num, unit='bytes'):
    """
    Returns a human-readable string of a byte-value.
    If 'num' is bits, set unit='bits'.
    """
    num, dim = byte_formatter(num)
    if unit != 'bytes':
        dim += 'it'  # then its Bit by default
    return f'{num:3.1f} {dim}'


class ArgumentNamespace(SimpleNamespace):
    """
    Namespace object that also behaves like a dictionary.
    
    Usecase is as a wrapper for the dictionary returned from
    `FritzConnection.call_action()`. This dictionary has keys named
    "arguments" as described by the AVM documentation, combined with
    values as the corresponding return values. Instances of
    `ArgumentNamespace` can get used to extract a subset of this
    dictionary and transfer the Argument-names to more readable
    ones.

    The class supports both explicit mapping between AVM parameter names and Python
    attribute names, as well as automatic conversion from AVM's MixedCase to Python's
    snake_case format.

    Examples:
        >>> source = {'NewModelName': 'FRITZ!Box 7590', 'NewSerialNumber': '123456'}
        >>> # With explicit mapping
        >>> info = ArgumentNamespace(source, {'model': 'NewModelName'})
        >>> info.model
        'FRITZ!Box 7590'
        
        >>> # Without mapping (automatic conversion)
        >>> info = ArgumentNamespace(source)
        >>> info.model_name
        'FRITZ!Box 7590'
    """

    def __init__(self, source=None, mapping=None, suppress_new=True):
        """
        Initialize the namespace.

        Args:
            source (dict): Source dictionary with AVM parameter names as keys
            mapping (dict): Optional mapping from Python names to AVM parameter names
            suppress_new (bool): If True, removes 'new_' prefix from converted names
        """
        super().__init__()
        if source is None:
            source = {}
            
        if mapping is None:
            # Automatically convert all keys
            mapping = {
                self.rewrite_argument(key, suppress_new): key 
                for key in source.keys()
            }
            
        # Transfer values using the mapping
        for py_name, avm_name in mapping.items():
            if avm_name in source:
                setattr(self, py_name, source[avm_name])

    def __getitem__(self, key):
        """Support dictionary-style access."""
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Support dictionary-style assignment."""
        setattr(self, key, value)

    def __len__(self):
        """Return number of attributes excluding special ones."""
        return len(self.__dict__)

    @staticmethod
    def rewrite_argument(name, suppress_new=True):
        """
        Convert AVM parameter names to Python style names.
        
        Converts MixedCase to snake_case, optionally removing 'new_' prefix.
        
        Args:
            name (str): Name to convert
            suppress_new (bool): If True, removes 'new_' prefix from result
            
        Returns:
            str: Converted name in snake_case format
        """
        # Handle empty or None input
        if not name:
            return name
            
        # First, handle the special case where name is already snake_case
        if '_' in name and name.islower():
            return name
            
        # For "New_" prefix, convert to "new_" and handle suppression
        if name.startswith('New_'):
            name = 'new_' + name[4:]
            if suppress_new:
                name = name[4:]  # Remove 'new_'
            return name.lower()
            
        # Convert CamelCase/MixedCase to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        
        # Handle "New" prefix if present
        if snake_case.startswith('new_') and suppress_new:
            snake_case = snake_case[4:]
            
        return snake_case
