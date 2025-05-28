"""
Some helper functions for the library.
"""

import math
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


def format_rate(num, unit='bytes'):
    """
    Returns a human-readable string of a byte/bits per second.
    If 'num' is bits, set unit='bits'.
    """
    return format_num(num, unit=unit) + '/s'


def format_dB(num):
    """
    Returns a human-readable string of dB. The value is divided
    by 10 to get first decimal digit
    """
    num /= 10
    return f'{num:3.1f} {"dB"}'


class ArgumentNamespace(SimpleNamespace):
    """
    Namespace object that also behaves like a dictionary.

    Usecase is as a wrapper for the dictionary returned from
    `FritzConnection.call_action()`. This dictionary has keys named
    "arguments" as described by the AVM documentation, combined with
    values as the corresponding return values. Instances of
    `ArgumentNamespace` can get used to extract a subset of this
    dictionary and transfer the Argument-names to more readable
    ones. For example consider that `fc` is a FritzConnection instance.
    Then the following call: ::

        result = fc.call_action("DeviceInfo1", "GetInfo")

    will return a dictionary like: ::

        {'NewManufacturerName': 'AVM',
         'NewManufacturerOUI': '00040E',
         'NewModelName': 'FRITZ!Box 7590',
         'NewDescription': 'FRITZ!Box 7590 154.07.29',
         'NewProductClass': 'AVMFB7590',
         'NewSerialNumber': '989BCB2B93B0',
         'NewSoftwareVersion': '154.07.29',
         'NewHardwareVersion': 'FRITZ!Box 7590',
         'NewSpecVersion': '1.0',
         'NewProvisioningCode': '000.044.004.000',
         'NewUpTime': 9516949,
         'NewDeviceLog': 'long string here ...'}

    In case that just the model name and serial number are of interest,
    and should have better names, first define a mapping: ::

        mapping = {
            "modelname": "NewModelName",
            "serial_number": "NewSerialNumber"
        }

    and use this `mapping` with the `result` to create an `ArgumentNamespace`
    instance: ::

        >>> info = ArgumentNamespace(result, mapping)

    The `info` instance can now get used like a namespace object and
    like a dictionary: ::

        >>> info.serial_number
        '989BCB2B93B0'

        >>> info['modelname']
        'FRITZ!Box 7590'

    If no mapping is given, then `ArgumentNamespace` will consume the
    provided dictionary converting all keys from "MixedCase" style to
    "snake_case" removing the leading "new_" (removing "new_" can get
    turned off by setting `suppress_new` to `False`): ::

        >>> info = ArgumentNamespace(result)
        >>> info.up_time
        9516949

    The class provides dictionary-like methods such as `get()`, `keys()`,
    `values()`, and `items()`: ::

        >>> info.get('model_name')
        'FRITZ!Box 7590'
        >>> info.get('not_existing_key', 'default_value')
        'default_value'
        >>> list(info.keys())
        ['model_name', 'serial_number', 'up_time', ...]
        >>> list(info.values())
        ['FRITZ!Box 7590', '989BCB2B93B0', 9516949, ...]
        
    The class also supports containment check with the 'in' operator: ::
    
        >>> 'model_name' in info
        True
        >>> 'non_existent' in info
        False
    """
    def __init__(self, source, mapping=None, suppress_new=True):
        """
        Initialize the ArgumentNamespace with a source dictionary.
        
        Args:
            source: Dictionary with the original data
            mapping: Optional mapping of attribute names to source keys
            suppress_new: Whether to remove 'new_' prefix from attribute names
        """
        if mapping is None:
            # Auto-generate mapping if none provided
            mapping = {}
            for key in source:
                converted_key = self.rewrite_argument(key, suppress_new)
                mapping[converted_key] = key
        
        # Create attributes from source data using the mapping
        kwargs = {name: source[source_key] for name, source_key in mapping.items()}
        super().__init__(**kwargs)

    def __getitem__(self, key):
        """Get an item using dictionary access syntax."""
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Set an item using dictionary access syntax."""
        setattr(self, key, value)

    def __len__(self):
        """Return the number of attributes."""
        return len(self.__dict__)
    
    def __contains__(self, key):
        """Check if a key exists in the namespace."""
        return key in self.__dict__
    
    def __iter__(self):
        """Allow iteration over keys."""
        return iter(self.__dict__)
    
    def __repr__(self):
        """Return a string representation of the namespace."""
        items = [f"{k}={v!r}" for k, v in self.__dict__.items()]
        return f"{self.__class__.__name__}({', '.join(items)})"

    def get(self, key, default=None):
        """
        Return the value for key if key is in the namespace, else default.
        
        Args:
            key: The key to look up
            default: Value to return if key is not found (default: None)
            
        Returns:
            The value for the key if found, else default
        """
        try:
            return self[key]
        except AttributeError:
            return default

    def keys(self):
        """Return a view object containing the keys in the namespace."""
        return self.__dict__.keys()

    def values(self):
        """Return a view object containing the values in the namespace."""
        return self.__dict__.values()

    def items(self):
        """Return a view object containing (key, value) pairs in the namespace."""
        return self.__dict__.items()
    
    def update(self, *args, **kwargs):
        """
        Update the namespace with a dictionary, another namespace, or keyword arguments.
        
        Args:
            *args: A dictionary or another ArgumentNamespace to update from
            **kwargs: Keyword arguments to update from
        """
        if args:
            other = args[0]
            if isinstance(other, dict):
                for key, value in other.items():
                    setattr(self, key, value)
            elif isinstance(other, ArgumentNamespace):
                for key, value in other.__dict__.items():
                    setattr(self, key, value)
            else:
                raise TypeError(f"Expected dict or ArgumentNamespace, got {type(other).__name__}")
        
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    @staticmethod
    def rewrite_argument(name, suppress_new=True):
        """
        Rewrite `name` from MixedCase to snake_case. So i.e. "MixedCase"
        would converted to "mixed_case". The result may start with
        "new_" in case of AVM standard argument names. if `suppress_new`
        is `True` the prefix "new_" will get removed.
        
        Args:
            name: The name to convert
            suppress_new: Whether to remove the 'new_' prefix
            
        Returns:
            The name in snake_case format
        """
        # Convert MixedCase to snake_case
        chars = []
        for i, char in enumerate(name):
            if i > 0 and char.isupper() and not name[i-1].isupper():
                chars.append('_')
            chars.append(char.lower())
        
        result = ''.join(chars)
        
        # Handle special case for names starting with "new_"
        if suppress_new and result.startswith("new_"):
            result = result[4:]  # Remove 'new_'
            
        return result
