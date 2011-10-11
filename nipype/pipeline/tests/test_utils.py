# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine utils module
"""
import os
from copy import deepcopy
from tempfile import mkdtemp
from shutil import rmtree

from nipype.testing import (assert_equal, assert_true,
                            assert_false)
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu
from nipype.utils.config import config
from nipype.pipeline.utils import merge_dict


def test_identitynode_removal():

    def test_function(arg1, arg2, arg3):
        import numpy as np
        return (np.array(arg1) + arg2 + arg3).tolist()

    wf = pe.Workflow(name="testidentity")

    n1 = pe.Node(niu.IdentityInterface(fields=['a', 'b']), name='src')
    n1.iterables = ('b', [0, 1, 2, 3])
    n1.inputs.a = [0, 1, 2, 3]

    n2 = pe.Node(niu.Select(), name='selector')
    wf.connect(n1, ('a', test_function, 1, -1), n2, 'inlist')
    wf.connect(n1, 'b', n2, 'index')

    n3 = pe.Node(niu.IdentityInterface(fields=['c', 'd']), name='passer')
    n3.inputs.c = [1, 2, 3, 4]
    wf.connect(n2, 'out', n3, 'd')

    n4 = pe.Node(niu.Select(), name='selector2')
    wf.connect(n3, ('c', test_function, 1, -1), n4, 'inlist')
    wf.connect(n3, 'd', n4, 'index')

    fg = wf._create_flat_graph()
    wf._set_needed_outputs(fg)
    eg = pe.generate_expanded_graph(deepcopy(fg))
    yield assert_equal, len(eg.nodes()), 8


def test_outputs_removal():

    def test_function(arg1):
        import os
        file1 = os.path.join(os.getcwd(), 'file1.txt')
        file2 = os.path.join(os.getcwd(), 'file2.txt')
        fp = open(file1, 'wt')
        fp.write('%d' % arg1)
        fp.close()
        fp = open(file2, 'wt')
        fp.write('%d' % arg1)
        fp.close()
        return file1, file2

    out_dir = mkdtemp()
    n1 = pe.Node(niu.Function(input_names=['arg1'],
                              output_names=['file1', 'file2'],
                              function=test_function),
                 base_dir=out_dir,
                 name='testoutputs')
    n1.inputs.arg1 = 1
    n1.config = {'execution': {'remove_unnecessary_outputs': True}}
    n1.config = merge_dict(deepcopy(config._sections), n1.config)
    n1.run()
    yield assert_true, os.path.exists(os.path.join(out_dir,
                                                   n1.name,
                                                   'file1.txt'))
    yield assert_true, os.path.exists(os.path.join(out_dir,
                                                   n1.name,
                                                   'file2.txt'))
    n1.needed_outputs = ['file2']
    n1.run()
    yield assert_false, os.path.exists(os.path.join(out_dir,
                                                   n1.name,
                                                   'file1.txt'))
    yield assert_true, os.path.exists(os.path.join(out_dir,
                                                   n1.name,
                                                   'file2.txt'))
    rmtree(out_dir)
