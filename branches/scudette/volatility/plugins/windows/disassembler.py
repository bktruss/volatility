# Volatility
# Copyright (C) 2012 Michael Cohen <scudette@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

"""This module provides the primitives needed to disassemble code using distorm3."""

# This stuff is just here to make pyinstaller pick up on it. Due to the way
# distorm3 uses ctypes, pyinstaller misses the imports. Note that the following
# patch should also be applied to distorm3/__init__.py to support freezing:
#
#    # Guess the DLL filename and load the library.
#    if getattr(sys, "frozen", None):
#        _distorm_path = '.'
#    else:
#        _distorm_path = split(__file__)[0]
try:
    from ctypes import cdll

    cdll.LoadLibrary("distorm3.dll")
except Exception:
    pass

import distorm3

from volatility import obj
from volatility import plugin


class Instruction(obj.BaseObject):
    """An object which represents a single assembly instruction."""

    def __init__(self, instruction_set=None, **kwargs):
        """Decode a single instruction from the current point.

        Args:
          instruction_set: "32bit" or "64bit" or taken from the
             profile.metadata("memroy_model")
        """


class Disassemble(plugin.Command):
    """Disassemble the given address space."""

    __name = "dis"

    def __init__(self, offset=None, address_space=None, length=80, mode=None,
                 suppress_headers=False, **kwargs):
        """Dumps a disassembly of a location.

        Args:
          address_space: The address_space to read from.
          offset: The offset to read from.
          length: The number of instructions (lines) to disassemble.
          mode: The mode (32/64 bit)- if not set taken from profile.
          suppress_headers: If set we do not write headers.
        """
        super(Disassemble, self).__init__(**kwargs)
        self.address_space = address_space or self.session.default_address_space
        self.offset = offset
        self.length = length
        self.suppress_headers = suppress_headers
        self.mode = mode or self.session.profile.metadata("memory_model", "32bit")
        if offset is None:
            raise plugin.PluginError("You must specify an offset to "
                                     "disassemble from.")

        if self.mode == "32bit":
            self.distorm_mode = distorm3.Decode32Bits
        else:
            self.distorm_mode = distorm3.Decode64Bits

    def disassemble(self, offset):
        """Disassemble the number of instructions required.

        Returns:
          A tuple of (Address, Opcode, Instructions).
        """
        data = self.address_space.zread(offset, self.length)
        iterable = distorm3.DecodeGenerator(int(offset), data, self.distorm_mode)
        for (offset, _size, instruction, hexdump) in iterable:
            yield offset, hexdump, instruction

    def render(self, renderer):
        """Disassemble code at a given address.

        Disassembles code starting at address for a number of bytes
        given by the length parameter (default: 128).

        Note: This feature requires distorm, available at
            http://www.ragestorm.net/distorm/

        The mode is '32bit' or '64bit'. If not supplied, the disasm
        mode is taken from the profile.
        """
        renderer.table_header([('Address', "cmd_address", '[addrpad]'),
                               ('Op Codes', "opcode", '<20'),
                               ('Instruction', "instruction", '<40')],
                              suppress_headers=self.suppress_headers)
        for (offset, hexdump, instruction) in self.disassemble(self.offset):
            renderer.table_row(offset, hexdump, instruction)

