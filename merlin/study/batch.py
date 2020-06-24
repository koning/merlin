###############################################################################
# Copyright (c) 2019, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
# Written by the Merlin dev team, listed in the CONTRIBUTORS file.
# <merlin@llnl.gov>
#
# LLNL-CODE-797170
# All rights reserved.
# This file is part of Merlin, Version: 1.6.1.
#
# For details, see https://github.com/LLNL/merlin.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
###############################################################################

"""
This module parses the batch section of the yaml specification.

Currently only the batch worker launch for slurm, lsf or flux
are implemented.

"""
import logging
import os
import sys

from merlin.utils import get_yaml_var
from maestrowf.interfaces.script.slurmscriptadapter import SlurmScriptAdapter
from maestrowf.interfaces.script.lsfscriptadapter import LSFScriptAdapter
from maestrowf.datastructures.core.study import StudyStep

LOG = logging.getLogger(__name__)


def batch_check_parallel(spec):
    """
    Check for a parallel batch section in the yaml file.
    """
    parallel = False

    try:
        batch = spec.batch
    except AttributeError:
        raise Exception("The batch section is required in the specification file.")

    btype = get_yaml_var(batch, "type", "local")
    if btype != "local":
        parallel = True

    return parallel


def get_batch_type(default=None):
    """
    Determine which batch scheduler to use.

    :param default: (str) The default batch scheduler to use if a scheduler
        can't be determined. The default is slurm.
    :returns: (str) The batch name (available options: slurm, flux, lsf).
    """
    if default is None:
        default = "slurm"

    if "SYS_TYPE" not in os.environ:
        return default

    if "toss3" in os.environ["SYS_TYPE"]:
        return "slurm"

    if "blueos" in os.environ["SYS_TYPE"]:
        return "lsf"

    return default


def get_node_count(default=1):
    """
    Determine a default node count based on the environment.

    :param default: (int) The number of nodes to return if a node count from
        the environment cannot be determined.
    :param returns: (int) The number of nodes to use.
    """
    if "SLURM_JOB_NUM_NODES" in os.environ:
        return int(os.environ["SLURM_JOB_NUM_NODES"])

    # LSB systems reserve one node for launching
    if "LSB_HOSTS" in os.environ:
        nodes = set(os.environ["LSB_HOSTS"].split())
        n_batch_nodes = len(nodes) - 1
        return n_batch_nodes
    elif "LSB_MCPU_HOSTS" in os.environ:
        nodes = os.environ["LSB_MCPU_HOSTS"].split()
        n_batch_nodes = len(nodes) // 2 - 1
        return n_batch_nodes

    return default


def get_batch_variables(spec, batch):
    """
      The configuration in the batch section of the merlin spec
      is used to create the worker launch line, which may be
      different from a simulation launch.

      spec (spec): The merlin spec
      batch (dict): An optional batch override from the worker config

    """
    if batch is None:
        try:
            batch = spec.batch
        except AttributeError:
            raise Exception("The batch section is required in the specification file.")

    nbatch = {}
    nbatch["bank"] = get_yaml_var(batch, "bank", "")
    nbatch["host"] = get_yaml_var(batch, "host", "")
    nbatch["nodes"] = get_yaml_var(batch, "nodes", None)
    nbatch["queue"] = get_yaml_var(batch, "queue", "")
    nbatch["type"] = get_yaml_var(batch, "type", "local")
    nbatch["walltime"] = get_yaml_var(batch, "walltime", "")
    nbatch["shell"] = get_yaml_var(batch, "shell", "bash")

    return nbatch


def get_merlin_batch_variables(spec, batch):
    """
      The configuration in the batch section of the merlin spec
      is used to create the worker launch line, which may be
      different from a simulation launch. This function contains
      all of the merlin specific flags.

      spec (spec): The merlin spec
      batch (dict): An optional batch override from the worker config

    """
    if batch is None:
        try:
            batch = spec.batch
        except AttributeError:
            raise Exception("The batch section is required in the specification file.")

    nbatch = {}
    nbatch["launch_pre"] = get_yaml_var(batch, "launch_pre", "")
    nbatch["launch_args"] = get_yaml_var(batch, "launch_args", "")
    nbatch["worker_launch"] = get_yaml_var(batch, "worker_launch", "")
    nbatch["flux_path"] = get_yaml_var(batch, "flux_path", "")
    nbatch["flux_opts"] = get_yaml_var(batch, "flux_start_opts", "")
    nbatch["flux_exec_workers"] = get_yaml_var(batch, "flux_exec_workers", True)

    return nbatch


def batch_worker_launch(spec, com, nodes=None, batch=None):
    """
      The configuration in the batch section of the merlin spec
      is used to create the worker launch line, which may be
      different from a simulation launch.

      spec (spec): The merlin spec
      com (str): The command to launch with batch configuration
      nodes (int): The number of nodes to use in the batch launch
      batch (dict): An optional batch override from the worker config

    """
    nbatch = get_batch_variables(spec, batch)
    nbatch.update(get_merlin_batch_variables(spec, batch))

    btype = nbatch["type"]

    # A jsrun submission cannot be run under a parent jsrun so
    # all non flux lsf submissions need to be local.
    if btype == "local" or "lsf" in btype:
        return com

    if nodes is None:
        # Use the value in the batch section
        nodes = nbatch["nodes"]

    # Get the number of nodes from the environment if unset
    if nodes is None or nodes == "all":
        nodes = get_node_count(default=1)

    bank = nbatch["bank"]
    queue = nbatch["queue"]
    shell = nbatch["shell"]
    launch_pre = nbatch["launch_pre"]
    launch_args = nbatch["launch_args"]
    worker_launch = nbatch["worker_launch"]
    walltime = nbatch["walltime"]

    if btype == "flux":
        launcher = get_batch_type()
    else:
        launcher = get_batch_type()

    launchs = worker_launch
    if not launchs:
        if btype == "slurm" or launcher == "slurm":
            launchs = f"srun --mpi=none -N {nodes} -n {nodes}"
            if queue:
                launchs += f" -p {queue}"
        if launcher == "lsf":
            launchs = f"jsrun -a 1 -c ALL_CPUS -g ALL_GPUS --bind=none -n {nodes}"

    launchs += f" {launch_args}"

    # Allow for any pre launch manipulation, e.g. module load
    # hwloc/1.11.10-cuda
    if launch_pre:
        launchs = f"{launch_pre} {launchs}"

    worker_cmd = f"{launchs} {com}"

    if btype == "flux":
        flux_path = nbatch[ "flux_path"]
        flux_opts = nbatch[ "flux_start_opts"]
        flux_exec_workers = nbatch["flux_exec_workers"]

        flux_exec = ""
        if flux_exec_workers:
            flux_exec = "flux exec"

        if "/" in flux_path:
            flux_path += "/"

        flux_exe = os.path.join(flux_path, "flux")

        launch = (
            f"{launchs} {flux_exe} start {flux_opts} {flux_exec} `which {shell}` -c"
        )
        worker_cmd = f'{launch} "{com}"'

    return worker_cmd


def batch_create_script(spec, worker_list, merlin_info_dir, output_dir, monitor_flag):
    """
    Create and submit a batch submission script

    spec (spec): The merlin spec
    worker_list (list): The list of the worker commands
    output_dir (str): The optional script output_dir, will not submit if this is set
    """
    if not batch_check_parallel(spec):
        raise Exception("merlin run-workers: No batch script is available for local batch type.")

    nbatch = get_batch_variables(spec, None)

    nbatch["workers"] = worker_list
    nbatch["merlin_info_dir"] = merlin_info_dir
    nbatch["output_dir"] = output_dir
    nbatch["monitor_flag"] = monitor_flag

    if nbatch["type"] == "flux":
        nbatch["type"] = get_batch_type()

    bscript = MerlinBatch(**nbatch)

    if output_dir is None:
        pass
        #bscript.execute()

def adapter_factory(batch_type, kwargs):
    if batch_type == "slurm":
        return SlurmScriptAdapter(**kwargs)
    elif "lsf" in batch_type:
        return LSFScriptAdapter(**kwargs)
    else:
        raise Exception(f"MerlinBatch: The batch type ,{batch_type}, is not implemented.")


class MerlinBatch:
    def __init__(self, **kwargs):
        nodes = kwargs.pop("nodes", None)
        workers = kwargs.pop("workers", [])
        shell = kwargs.get("shell", "bash")
        monitor_flag= kwargs.pop("monitor_flag", False)
        self.output_dir = kwargs.pop("output_dir", None)
        self.merlin_info_dir = kwargs.pop("merlin_info_dir", None)

        batch_type = kwargs.get("type","") 
        self.mbscript = adapter_factory(batch_type, kwargs)

        script_args = ["bank", "host", "queue", "reservation"]
        for k in script_args:
            kwargs.pop(k, None)

        self.mstep = StudyStep()
        self.mstep.name = "merlin_workers"
        self.mstep.run["cmd"]  = self.create_cmd(workers, shell, monitor_flag)

        if nodes:
            self.mstep.run["nodes"] = nodes

        self.mbscript._write_script(".", self.mstep)

        print(self.mbscript.__dict__)
        print(kwargs)
        #print(self.mstep.run["cmd"])

    def set_shell_paths(self, shell):
        mer_path = os.path.dirname(sys.executable)
        shpath = f"export PATH={mer_path}:$PATH\n"
        if "csh" in shell:
            shpath = f"set path ({mer_path} $path)\n"
        return shpath

    def create_cmd(self, workers, shell, monitor_flag):
        cmd = self.set_shell_paths(shell)
        cmd += "\n"
        cmd += " &\n".join(workers)
        cmd += "\n\n"
        if monitor_flag:
            cmd += "merlin monitor\n"

        return cmd
