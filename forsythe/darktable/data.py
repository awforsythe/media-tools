import re
import struct
import binascii

__struct_attrs_regex__ = re.compile(r'\w+ (\w+[,|;]\s*)+')
__struct_attr_types__ = {
    'float': ('f', float),
    'int': ('i', int)
}

class Struct(object):

    def __init__(self):
        self._fmt = ''
        self._names = []
        attrs = getattr(self, '__attrs__') if hasattr(self, '__attrs__') else ''
        for match in __struct_attrs_regex__.finditer(''.join(attrs.splitlines())):
            tokens = match.group(0).replace(',', '').replace(';', '').split()
            type_name, attr_names = tokens[0], tokens[1:]
            if type_name not in __struct_attr_types__:
                raise AttributeError("Unsupported struct attribute type '%s'" % type_name)
            fmt_char, default = __struct_attr_types__[type_name]
            self._fmt += fmt_char * len(attr_names)
            for attr_name in attr_names:
                self._names.append(attr_name)
                setattr(self, attr_name, default())

    def summarize(self):
        lines = [name]
        for attr_name in self._names:
            lines.append('- %s: %r' % (attr_name, getattr(self, attr_name)))
        return '\n'.join(lines)

    def encode(self):
        args = [getattr(self, attr_name) for attr_name in self._names]
        return str(binascii.hexlify(struct.pack(self._fmt, *args)), 'utf-8')

    @classmethod
    def decode(cls, s):
        obj = cls()
        for attr_name, value in zip(obj._names, struct.unpack(obj._fmt, binascii.unhexlify(s))):
            setattr(obj, attr_name, value)
        return obj
