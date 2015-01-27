__copyright__ = "Copyright (C) 2013 Kristoffer Carlsson"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

"""
Module that contains the method of reading a mesh from a .inp file
generated by Neper.
"""

import re

import numpy

from phon.mesh_objects.element import Element

from phon.mesh_objects.node import Node
from phon.mesh_objects.mesh import Mesh
from phon.mesh_objects.element_set import ElementSet
from phon.mesh_objects.node_set import NodeSet


def read_from_abaqus_inp(filename, verbose=0):
    """
    Reads a mesh file in Abaqus .inp format and stores it into a
    Mesh class object.

    :param filename: The name of the file from where to read the mesh from.
    :type filename: string
    :param verbose: Determines what level of print out to the console.
    :type verbose: 0, 1 or 2
    :return: A mesh class containing the read mesh objects.
    :rtype: :class:`phon.mesh_objects.mesh()`
    :raises ReadInpFileError: If specific syntax error are found.

    """

    with open(filename, "rU") as f:

        # Read mesh objects
        num_elems = 0
        while True:
            start_of_line = f.tell()
            keyword = f.readline().strip().split(",")[0]
            f.seek(start_of_line)

            if keyword == "*Part":
                mesh = _read_part(f, verbose)
            elif keyword == "*Node":
                _read_nodes(f, mesh, verbose)
            elif keyword == "*Element":
                num_elems += _read_elements(f, mesh, num_elems, verbose)
            elif keyword == "*Elset":
                _read_element_set(f, mesh, verbose)
            elif keyword == "*Nset":
                _read_node_set(f, mesh, verbose)
            elif keyword == "*End Part":
                break
            else:
                f.readline()
                continue

        f.close()

        return mesh


def _read_part(f, verbose):
    """Reads the part name and creates a mesh with that name.

    :param f: The file from where to read the nodes from.
    :type f: file object at the nodes
    :param verbose: Determines what level of print out to the console.
    :type verbose: 0, 1 or 2
    :return: Nothing, but has the side effect of setting the pointer
             in the file object f to the line with the next keyword.

    """

    re_part = re.compile("\*Part, name=(.*)")
    line = f.readline()
    match = re_part.match(line)
    if not match:
        raise ReadInpFileError("Error parsing file. Expected '*Part, "
                               "name=XXX', read '" + line + "'.")

    part_name = match.group(1)
    if verbose == 1 or verbose == 2:
        print("Read part with name " + str(part_name))
    # Initiate a mesh class with the same name as the part
    return Mesh(part_name)


def _read_nodes(f, mesh, verbose):
    """Reads nodes from the file.

    :param f: The file from where to read the nodes from.
    :type f: file object at the nodes
    :param mesh: Mesh to insert the read nodes into.
    :type mesh: :class:`Mesh`
    :param verbose: Determines what level of print out to the console.
    :type verbose: 0, 1 or 2
    :return: Nothing, but has the side effect of setting the pointer
             in the file object f to the line with the next keyword.

    """
    line = f.readline()
    if not (line == "*Node\n"):
        raise ReadInpFileError("\nError parsing file. Expected '*Node',"
                               " read '" + line + "'.")

    num_nodes = 0
    while True:
        start_of_line = f.tell()
        line = f.readline()
        if line.strip() == '':
            continue
        if line[0] == '*':
            f.seek(start_of_line)
            return
        num_nodes += 1
        if verbose == 1:
            print ("\rReading nodes, %d nodes read" % num_nodes),
        node_numbers = [to_number(x) for x in line.strip().split(',')]
        node = Node(numpy.array(node_numbers[1:]))
        mesh.nodes[node_numbers[0]] = node
        if verbose == 2:
            print ("Read {0}.\n".format(node))


def _read_elements(f, mesh, num_elems, verbose):
    """Reads elements from the file.

    :param f: The file from where to read the elements from.
    :type f: file object at the elements
    :param mesh: Mesh to insert the read elements into.
    :type mesh: :class:`Mesh`
    :param verbose: Determines what level of print out to the console.
    :type verbose: 0, 1 or 2
    :return: Nothing, but has the side effect of setting the pointer
             in the file object f to the line with the next keyword.

    """
    line = f.readline()
    re_element = re.compile("\*Element, type=(.*)")
    match = re_element.match(line)
    if not match:
        raise ReadInpFileError("\nError parsing file. Expected '*Element, \
        type=XXX', got '" + line + "'.")

    element_name = re_element.match(line).group(1)
    while True:
        start_of_line = f.tell()
        line = f.readline()
        if line.strip() == '':
            continue
        if line[0] == '*':
            f.seek(start_of_line)
            return num_elems
        num_elems += 1
        if verbose == 1:
            print ("\rReading element %s, with id %d."
                   % (element_name, num_elems)),

        element_numbers = [to_number(x) for x in line.strip().split(',')]
        element = Element(element_name, element_numbers[1:])
        mesh.elements[element_numbers[0]] = element


def _read_element_set(f, mesh, verbose=0):
    """Reads element sets from the file.

    :param f: The file from where to read the element sets from.
    :type f: file object at the element sets
    :param mesh: Mesh to insert the read nodes into.
    :type mesh: :class:`Mesh`
    :param verbose: Determines what level of print out to the console.
    :type verbose: 0, 1 or 2
    :return: Nothing, but has the side effect of setting the pointer
             in the file object f to the line with the next keyword.

    """
    line = f.readline()
    re_element_set = re.compile("\*Elset, elset=(.*)")
    match = re_element_set.match(line)
    if not match:
        raise ReadInpFileError("Error parsing file. Expected '*Elset, "
                               "elset=X', got '" + line + "'.")

    element_set_name = re_element_set.match(line).group(1)

    if element_set_name.startswith("edge"):
        dim = 1
    elif element_set_name.startswith("face"):
        dim = 2
    elif element_set_name.startswith("poly"):
        dim = 3
    else:
        dim = None
    if verbose == 1 or verbose == 2:
        print ("\rReading element set {0:s}.".format(element_set_name)),

    full_str = ""
    if element_set_name.endswith("generate"):
        element_set_name = element_set_name[0:-10]
        element_set = ElementSet(element_set_name, dim)
        line = f.readline().strip()
        generate_info = [to_number(x) for x in line.split(',')]
        start, stop, step = generate_info[
                                0], generate_info[1], generate_info[2]
        element_set.ids = range(start, stop + 1, step)
        mesh.element_sets[element_set_name] = element_set
        return
    else:
        element_set = ElementSet(element_set_name, dim)
        while True:
            start_of_line = f.tell()
            line = f.readline()
            if line.strip() == '':
                continue
            if line[0] == '*':
                element_list = full_str.split(',')
                element_list = [item for item in element_list if item]
                element_set.ids = [to_number(x) for x in element_list]
                mesh.element_sets[element_set_name] = element_set
                f.seek(start_of_line)
                return
                # Read element ids until empty line
            full_str += line.strip() + ","


def _read_node_set(f, mesh, verbose=0):
    """Reads node sets from the file.

    :param f: The file from where to read the node sets from.
    :type f: file object at the node sets
    :param mesh: Mesh to insert the read nodes sets into.
    :type mesh: :class:`Mesh`
    :param verbose: Determines what level of print out to the console.
    :type verbose: 0, 1 or 2
    :return: Nothing, but has the side effect of setting the pointer
             in the file object f to the line with the next keyword.

    """
    line = f.readline()
    re_node_set = re.compile("\*Nset, nset=(.*)")
    match = re_node_set.match(line)
    if not match:
        raise ReadInpFileError("Error parsing file. Expected '*Nset, "
                               "nset=X', got '" + line + "'.")
    node_set_name = re_node_set.match(line).group(1)
    if verbose == 1 or verbose == 2:
        print ("\rReading node set {0:s}.".format(node_set_name)),
    full_str = ""
    if node_set_name.endswith("generate"):
        node_set_name = node_set_name[0:-10]
        node_set = NodeSet(node_set_name)
        line = f.readline().strip()
        generate_info = [to_number(x) for x in line.split(',')]
        start, stop, step = generate_info[
                                0], generate_info[1], generate_info[2]
        node_set.ids = range(start, stop + 1, step)
        mesh.node_sets[node_set_name] = node_set
        return
    else:
        node_set = NodeSet(node_set_name)
        while True:
            start_of_line = f.tell()
            line = f.readline()
            if line.strip() == '':
                continue
            if line[0] == '*':
                # Remove empty strings
                node_list = full_str.split(',')
                # Remove empty strings
                node_list = [item for item in node_list if item]
                node_set.ids = [to_number(x) for x in node_list]
                mesh.node_sets[node_set_name] = node_set
                f.seek(start_of_line)
                return
            full_str += line.strip() + ","


class ReadInpFileError(Exception):
    """
    Base class for errors in the :mod:`read_from_neper_inp` module.

    """

    def __init__(self, status):
        Exception.__init__(self, status)
        self.status = status

    def __str__(self):
        """Return a string representation of the :exc:`ReadInpFileError()`."""
        return str(self.status)


def to_number(number):
    """
    Converts a string to a int if possible, else a float.

    :param number: The string to convert to a number
    :type number: string

    :return: The converted number
    :rtype: : int or float depending on the format of the string

    """
    try:
        return int(number)
    except ValueError:
        return float(number)