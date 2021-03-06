__author__ = 'darakna'
# Volatility
# Copyright (C) 2007-2013 Volatility Foundation
#
# This file is part of Volatility.
#
# Volatility is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Volatility is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Volatility.  If not, see <http://www.gnu.org/licenses/>.
#

"""
@author:       Andrew Case
@license:      GNU General Public License 2.0
@contact:      atcuno@gmail.com
@organization:
"""
import volatility.obj as obj
import volatility.plugins.mac.common as common
import volatility.debug as debug

class mac_pslist(common.AbstractMacCommand):
    """ List Running Processes """

    def __init__(self, config, *args, **kwargs):
        common.AbstractMacCommand.__init__(self, config, *args, **kwargs)
        self._config.add_option('PID', short_option = 'p', default = None, help = 'Operate on these Process IDs (comma-separated)', action = 'store', type = 'str')

    def calculate(self):
        common.set_plugin_members(self)

        pidlist = None

        try:
            if self._config.PID:
                pidlist = [int(p) for p in self._config.PID.split(',')]
        except:
            pass

        p = self.addr_space.profile.get_symbol("_allproc")

        procsaddr = obj.Object("proclist", offset = p, vm = self.addr_space)
        proc = obj.Object("proc", offset = procsaddr.lh_first, vm = self.addr_space)
        seen = []

        while proc.is_valid():

            if proc.obj_offset in seen:
                debug.warning("Recursive process list detected (a result of non-atomic acquisition). Use mac_tasks or mac_psxview)")
                break
            else:
                seen.append(proc.obj_offset)

            if not pidlist or proc.p_pid in pidlist:
                yield proc

            proc = proc.p_list.le_next.dereference()

    def render_text(self, outfd, data):
        self.table_header(outfd, [("Offset", "[addrpad]"),
                          ("Name", "20"),
                          ("Pid", "8"),
                          ("Uid", "8"),
                          ("Gid", "8"),
                          ("PGID", "8"),
                          ("Bits", "12"),
                          ("DTB", "#018x"),
                          ("Start Time", "")])

        for proc in data:
            if not proc.is_valid() or len(proc.p_comm) == 0:
                continue

            # Strip the "TASK_MAP_" prefix from the enumeration
            bit_string = str(proc.task.map.pmap.pm_task_map or '')[9:]

            self.table_row(outfd, proc.v(),
                                  proc.p_comm,
                                  str(proc.p_pid),
                                  str(proc.p_uid),
                                  str(proc.p_gid),
                                  str(proc.p_pgrpid),
                                  bit_string,
                                  proc.task.dereference_as("task").map.pmap.pm_cr3,
                                  proc.start_time())


