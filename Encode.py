#!/usr/bin/env python3

import os
import argparse
from enum import Enum
from pathlib import Path
from functools import cmp_to_key
from typing import Dict, List, Set
from pgmpy.readwrite import BIFReader


class SelectorVariableTypeEnum(Enum):
    NONE = 1
    ONE = 2
    NEW = 3


class CircuitTypeEnum(Enum):
    nwDNNF = 1
    dDNNF = 2
    sdDNNF = 3


TMP_FILE_PATH: str = "tmp.txt"
circuit_type_enum_names = [ct.name for ct in CircuitTypeEnum]
selector_variable_type_enum_names = [svt.name for svt in SelectorVariableTypeEnum]


def print_title() -> None:
    print("                                                  ")
    print("                      Bels                        ")
    print("                     encoder                      ")
    print("                                                  ")


def input_file_path_parser(path: str) -> str:
    """
    Check if the input file exists and try to open it
    :param path: the path of the input file
    :return: the path
    :raises ArgumentTypeError: if the input file does not exist or cannot be opened
    """

    if not path.endswith(".bif"):
        raise argparse.ArgumentTypeError(f"The input file name must end with `.bif`!")

    path_tmp = Path(path)

    # The input file does not exist
    if not path_tmp.exists():
        raise argparse.ArgumentTypeError(f"The input file ({path}) doesn't exist!")

    try:
        with open(path_tmp, "r", encoding="utf-8") as _:
            pass
    except Exception as err:
        raise argparse.ArgumentTypeError(f"The input file ({path}) cannot be opened! ({str(err)})")

    return path


def output_file_path_parser(path: str) -> str:
    """
    Try to create an empty output file
    :param path: the path of the output file
    :return: the path
    :raises ArgumentTypeError: if the output file creation fails or the output file already exists
    """

    path_tmp = Path(path)

    # The output file already exists
    if path_tmp.exists():
        raise argparse.ArgumentTypeError(f"The output file ({path}) already exists. Please delete it or choose another name for the output file!")

    try:
        with open(path_tmp, "w", encoding="utf-8") as _:
            pass
    except Exception as err:
        raise argparse.ArgumentTypeError(f"An error occurred while creating the output file ({path})! ({str(err)})")

    # Check if the output file has been created
    if path_tmp.exists():
        path_tmp.unlink()
        return path

    raise argparse.ArgumentTypeError(f"An error occurred while creating the output file ({path})!")


def create_parser() -> argparse.ArgumentParser:
    # Create the parser
    parser_tmp = argparse.ArgumentParser(prog="Encode.py",
                                         description="Bels encoder",
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter  # default values are shown in the help
                                         )

    # Add arguments
    parser_tmp.add_argument("input_file",
                            action="store",
                            type=input_file_path_parser,
                            help="name of the input file (must end with `.bif`)")

    parser_tmp.add_argument("output_file",
                            action="store",
                            type=output_file_path_parser,
                            help="name of the output file where the CNF formula will be saved")

    parser_tmp.add_argument("-ct",
                            "--circuit_type",
                            action="store",
                            default=CircuitTypeEnum.nwDNNF.name,
                            type=str,
                            choices=circuit_type_enum_names,
                            help="circuit type")

    return parser_tmp


"""
Variables
"""
variable_counter: int = 1
number_of_clauses: int = 0
number_of_variables: int = 0

number_of_ones: int = 0
number_of_zeros: int = 0
number_of_shrinks: int = 0
number_of_independent_variables: int = 0

saved_clauses: Set[str] = set()

"""
Parameters
"""
determinism: bool = False
indicator_clauses: bool = True
add_minor_clauses: bool = False
context_specific_independence: bool = False
constraint_clauses_for_leaf_variables: bool = False
selector_variable_type: SelectorVariableTypeEnum = SelectorVariableTypeEnum.NONE


def get_name_for_mapping(variable_arg: str, state_arg: str) -> str:
    assert variable_arg in variables_bayesian_network
    assert state_arg in states_bayesian_network[variable_arg]

    return variable_arg + "_____" + state_arg


def get_variable_for_name(variable_arg: str, state_arg: str) -> str:
    name_tmp: str = get_name_for_mapping(variable_arg, state_arg)

    assert name_tmp in mapping_from_variable_state_to_variable_index

    return mapping_from_variable_state_to_variable_index[name_tmp]


def get_new_variable_index() -> int:
    """
    :return: a new variable index
    """
    global variable_counter
    global number_of_variables

    var_tmp = variable_counter

    variable_counter += 1
    number_of_variables += 1

    return var_tmp


def get_selector_variable_for_hard_clauses():
    """
    :return: a/the selector variable for hard clauses + " 0"
    """
    if selector_variable_type == SelectorVariableTypeEnum.NONE:
        return "0\n"
    elif selector_variable_type == SelectorVariableTypeEnum.ONE:
        return str(first_selector_variable) + " 0\n"
    elif selector_variable_type == SelectorVariableTypeEnum.NEW:
        return str(get_new_variable_index()) + " 0\n"
    else:
        raise Exception("Not implemented!")


def create_core_clause(index_states_arg: List[int], variables_arg: List[str], ignored_variables_arg: Set[str] = None) -> str:
    """
    It creates a core clause for the CPT line defined by the arguments.
    :param index_states_arg: represents the current state for each variable
    :param variables_arg: a list of variables
    :param ignored_variables_arg: a set of ignored variables
    :return: a core clause
    """
    # No ignored variables
    if ignored_variables_arg is None:
        ignored_variables_arg = set()

    assert len(index_states_arg) == len(variables_arg)
    assert len(ignored_variables_arg) < len(variables_arg)

    for var_tmp in ignored_variables_arg:
        assert var_tmp in variables_arg

    for k, var_tmp in enumerate(variables_arg):
        assert index_states_arg[k] < len(states_bayesian_network[var_tmp])

    list_tmp: List[str] = []

    for k, var_tmp in enumerate(variables_arg):
        # Ignored variable
        if var_tmp in ignored_variables_arg:
            continue

        state_tmp = states_bayesian_network[var_tmp][index_states_arg[k]]

        list_tmp.append("-" + get_variable_for_name(var_tmp, state_tmp))

    assert list_tmp

    list_tmp = sorted(list_tmp)

    core_clause = ""
    for x in list_tmp:
        core_clause = core_clause + (" " if core_clause else "") + x

    return core_clause


def is_variable_independent(var_index_arg: int, index_states_arg: List[int], variables_arg: List[str], probability_arg: float) -> bool:
    assert var_index_arg < len(variables_arg)
    assert len(index_states_arg) == len(variables_arg)

    index_states_tmp = index_states_arg.copy()

    for k, _ in enumerate(states_bayesian_network[variables_arg[var_index_arg]]):
        index_states_tmp[var_index_arg] = k

        key = create_core_clause(index_states_tmp, variables_arg)

        assert key in probability_dictionary

        if probability_arg != probability_dictionary[key]:
            return False

    return True


def is_variable_independent_recursion(var_index_arg: int, independent_variable_index_list_arg: List[int],
                                      index_states_arg: List[int], variables_arg: List[str], n_arg: int, probability_arg: float) -> bool:
    assert var_index_arg < len(variables_arg)
    assert len(index_states_arg) == len(variables_arg)
    assert n_arg <= len(independent_variable_index_list_arg)
    assert var_index_arg not in independent_variable_index_list_arg

    if n_arg == len(independent_variable_index_list_arg):
        return is_variable_independent(var_index_arg, index_states_arg, variables_arg, probability_arg)
    else:
        assert independent_variable_index_list_arg[n_arg] < len(variables_arg)

        index_states_tmp = index_states_arg.copy()
        var_index = independent_variable_index_list_arg[n_arg]

        for k, _ in enumerate(states_bayesian_network[variables_arg[var_index]]):
            index_states_tmp[var_index] = k

            if not is_variable_independent_recursion(var_index_arg, independent_variable_index_list_arg, index_states_tmp, variables_arg,
                                                     n_arg + 1, probability_arg):
                return False

        return True


def get_independent_variables(index_states_arg: List[int], variables_arg: List[str], probability_arg: float) -> Set[str]:
    assert len(index_states_arg) == len(variables_arg)

    independent_variable_index_list: List[int] = []

    for k, _ in enumerate(variables_arg):
        if is_variable_independent(k, index_states_arg, variables_arg, probability_arg):
            independent_variable_index_list.append(k)

    def compare(index_1: int, index_2: int) -> int:
        number_of_states_1 = len(states_bayesian_network[variables_arg[index_1]])
        number_of_states_2 = len(states_bayesian_network[variables_arg[index_2]])

        if number_of_states_1 < number_of_states_2:
            return 1
        elif number_of_states_1 > number_of_states_2:
            return -1
        else:
            return variables_arg[index_1] < variables_arg[index_2]

    independent_variable_index_list = sorted(independent_variable_index_list, key=cmp_to_key(compare))

    if not independent_variable_index_list:
        return set()

    if len(independent_variable_index_list) == 1:
        return {variables_arg[independent_variable_index_list[0]]}

    valid_independent_variable_index_list: List[int] = [independent_variable_index_list[0]]

    for k, var_index in enumerate(independent_variable_index_list):
        if k == 0:
            continue

        if is_variable_independent_recursion(var_index, valid_independent_variable_index_list, index_states_arg, variables_arg, 0, probability_arg):
            valid_independent_variable_index_list.append(var_index)

    independent_variables: Set[str] = set()
    for var_index in valid_independent_variable_index_list:
        independent_variables.add(variables_arg[var_index])

    return independent_variables


def create_minor_clauses(core_clause: str, parameter_variable: int) -> str:
    """
    Creates minor clauses from the core clause
    :param core_clause: a core clause
    :param parameter_variable: the parameter variable of the core clause
    :return: minor clauses
    """
    global number_of_clauses

    core_clause_list = core_clause.split(" ")

    minor_clauses_string: str = ""

    for k in range(len(core_clause_list)):
        assert core_clause_list[k][0] == "-"
        variable_tmp = core_clause_list[k][1:]
        minor_clauses_string += variable_tmp + " -" + str(parameter_variable) + " 0\n"

        number_of_clauses += 1

    return minor_clauses_string


def create_parameter_clauses(index_states_arg: List[int], variables_arg: List[str], n_arg: int):
    global number_of_ones
    global number_of_zeros
    global number_of_clauses
    global number_of_shrinks
    global number_of_independent_variables

    assert n_arg < len(variables_arg)

    states = states_bayesian_network[variables_arg[n_arg]]

    if n_arg == (len(variables_arg) - 1):
        for k, _ in enumerate(states):
            index_states_tmp = index_states_arg.copy()
            index_states_tmp.append(k)

            assert len(index_states_tmp) == len(variables_arg)

            core_clause = create_core_clause(index_states_tmp, variables_arg)

            assert core_clause in probability_dictionary

            probability = probability_dictionary[core_clause]

            if determinism and probability == 1:
                number_of_ones += 1
                continue

            # Context-specific independence
            if context_specific_independence:
                independent_variables: Set[str] = get_independent_variables(index_states_tmp, variables_arg, probability)
            else:
                independent_variables: Set[str] = set()

            # if independent_variables:
            #     for m, var_tmp in enumerate(variables_arg):
            #         print(var_tmp + " (" + states_bayesian_network[var_tmp][index_states_tmp[m]] + ")", end=" ")
            #     print("- " + str(independent_variables))

            if len(variables_arg) == 1:
                independent_variables = set()

            if len(variables_arg) == len(independent_variables):
                assert variables_arg[-1] in independent_variables
                independent_variables.remove(variables_arg[-1])

            assert len(variables_arg) > len(independent_variables)

            if not independent_variables:
                tmp_file.write("c " + str(probability) + "\n")
                tmp_file.write(core_clause)
            else:
                number_of_shrinks += 1
                number_of_independent_variables += len(independent_variables)

                core_clause_reduced = create_core_clause(index_states_tmp, variables_arg, independent_variables)

                if core_clause_reduced in saved_clauses:
                    continue

                saved_clauses.add(core_clause_reduced)

                tmp_file.write("c " + str(probability) + "\n")
                tmp_file.write(core_clause_reduced)

                core_clause = core_clause_reduced

            parameter_variable: int = 0

            if determinism and probability == 0:
                number_of_zeros += 1
                tmp_file.write(get_selector_variable_for_hard_clauses())
            else:
                parameter_variable = get_new_variable_index()
                tmp_file.write(" " + str(parameter_variable) + " 0\n")

            number_of_clauses += 1

            # Minor clauses
            if add_minor_clauses:
                assert (parameter_variable != 0)

                tmp_file.write(create_minor_clauses(core_clause, parameter_variable))
    else:
        for k, _ in enumerate(states):
            index_states_tmp = index_states_arg.copy()
            index_states_tmp.append(k)

            create_parameter_clauses(index_states_tmp, variables_arg, n_arg + 1)


def create_probability_dictionary(string_list_arg, variables_arg, n_arg, number_arg, dimension_arg):
    global probability_dictionary

    assert n_arg < len(variables_arg)

    var_tmp = variables_arg[n_arg]
    states = states_bayesian_network[var_tmp]

    if n_arg == (len(variables_arg) - 1):
        for k, state_tmp in enumerate(states):
            probability = values_bayesian_network[var_tmp][k][number_arg]

            string_list_tmp = string_list_arg.copy()
            string_list_tmp.append("-" + get_variable_for_name(var_tmp, state_tmp))

            string_list_tmp = sorted(string_list_tmp)

            key = ""
            for x in string_list_tmp:
                key = key + (" " if key else "") + x

            assert key not in probability_dictionary

            probability_dictionary[key] = probability
    else:
        assert dimension_arg % len(states) == 0

        dimension_arg /= len(states)
        dimension_arg = int(dimension_arg)

        for k, state_tmp in enumerate(states):
            string_list_tmp = string_list_arg.copy()
            string_list_tmp.append("-" + get_variable_for_name(var_tmp, state_tmp))

            create_probability_dictionary(string_list_tmp, variables_arg, n_arg + 1, number_arg + dimension_arg * k, dimension_arg)


def listdir_no_hidden(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f


def reset():
    global variable_counter
    global number_of_clauses
    global number_of_variables
    global number_of_ones
    global number_of_zeros
    global number_of_shrinks
    global number_of_independent_variables
    global saved_clauses

    variable_counter = 1
    number_of_clauses = 0
    number_of_variables = 0

    number_of_ones = 0
    number_of_zeros = 0
    number_of_shrinks = 0
    number_of_independent_variables = 0

    saved_clauses = set()


if __name__ == '__main__':
    # Title
    print_title()
    print()

    # Parser
    parser = create_parser()
    args = parser.parse_args()

    input_file_path: str = args.input_file
    output_file_path: str = args.output_file

    # Print arguments
    print("Arguments:")
    print("\tinput file: " + input_file_path)
    print("\toutput file: " + output_file_path)
    print("\tcircuit type: " + CircuitTypeEnum[args.circuit_type].name)
    print()

    # Parameters
    determinism = False
    add_minor_clauses = False
    indicator_clauses = True
    context_specific_independence = False
    constraint_clauses_for_leaf_variables = False
    selector_variable_type = SelectorVariableTypeEnum.NONE

    # nwDNNF circuits
    if CircuitTypeEnum[args.circuit_type] == CircuitTypeEnum.nwDNNF:
        pass

    # d-DNNF circuits
    if CircuitTypeEnum[args.circuit_type] == CircuitTypeEnum.dDNNF:
        constraint_clauses_for_leaf_variables = True

    # sd-DNNF circuits
    if CircuitTypeEnum[args.circuit_type] == CircuitTypeEnum.sdDNNF:
        constraint_clauses_for_leaf_variables = True
        add_minor_clauses = True

    # Minor clauses
    if add_minor_clauses:
        assert indicator_clauses
        assert constraint_clauses_for_leaf_variables
        assert selector_variable_type == SelectorVariableTypeEnum.NONE

    # Print parameters
    print("Parameters:")
    if determinism:
        print("\tdeterminism")
    if add_minor_clauses:
        print("\tminor clauses")
    if indicator_clauses:
        print("\tindicator clauses")
    if context_specific_independence:
        print("\tcontext-specific independence")
    if constraint_clauses_for_leaf_variables:
        print("\tconstraint clauses for leaf variables")
    print("\tselector variable type: " + selector_variable_type.name)
    print()

    bayesian_network = BIFReader(input_file_path)

    print("The Bayesian network has been parsed")
    print()

    probability_dictionary: Dict[str, float] = dict()
    mapping_from_variable_state_to_variable_index: Dict[str, str] = dict()

    with open(TMP_FILE_PATH, "w", encoding="utf-8") as tmp_file:
        variables_bayesian_network = bayesian_network.get_variables()
        states_bayesian_network = bayesian_network.get_states()
        values_bayesian_network = bayesian_network.get_values()

        assert len(variables_bayesian_network) > 0

        for variable in variables_bayesian_network:
            for state in states_bayesian_network[variable]:
                mapping_from_variable_state_to_variable_index[get_name_for_mapping(variable, state)] = str(get_new_variable_index())

        first_selector_variable = variable_counter
        if selector_variable_type == SelectorVariableTypeEnum.ONE:
            get_new_variable_index()

        # Leaf variables
        leaf_variables: Set[str] = set()
        if not constraint_clauses_for_leaf_variables:
            for variable in variables_bayesian_network:
                leaf_variable: bool = True

                for edge in bayesian_network.get_edges():
                    assert (len(edge) == 2)

                    if edge[0] == variable:
                        leaf_variable = False
                        break

                if leaf_variable:
                    leaf_variables.add(variable)

        # Indicator/constraint clauses
        for variable in variables_bayesian_network:
            # Leaf variable
            if variable in leaf_variables:
                continue

            # Constraint clause
            for state in states_bayesian_network[variable]:
                tmp_file.write(get_variable_for_name(variable, state) + " ")

            tmp_file.write(get_selector_variable_for_hard_clauses())
            number_of_clauses += 1

            # Indicator clauses
            if indicator_clauses:
                number_of_states = len(states_bayesian_network[variable])

                assert number_of_states > 1

                for i in range(number_of_states - 1):
                    for j in range(i + 1, number_of_states):
                        state_i = states_bayesian_network[variable][i]
                        state_j = states_bayesian_network[variable][j]

                        tmp_file.write("-" + get_variable_for_name(variable, state_i) + " -" + get_variable_for_name(variable, state_j) + " " +
                                       get_selector_variable_for_hard_clauses())
                        number_of_clauses += 1

        # Parameter clauses
        for i, variable in enumerate(variables_bayesian_network):
            print("CPT: " + variable)
            table = bayesian_network.get_parents()[variable].copy()

            dimension = 1
            for tmp in table:
                dimension *= len(states_bayesian_network[tmp])

            dimension_copy = dimension * len(states_bayesian_network[variable])

            table.append(variable)

            assert len(table) > 0

            saved_clauses.clear()
            probability_dictionary.clear()

            create_probability_dictionary([], table, 0, 0, dimension)

            assert len(probability_dictionary) == dimension_copy

            # print(probability_dictionary)

            create_parameter_clauses([], table, 0)

            print(str(i + 1) + "/" + str(len(variables_bayesian_network)))

    print()
    print("Number of ones: " + str(number_of_ones))
    print("Number of zeros: " + str(number_of_zeros))
    print("Number of shrinks: " + str(number_of_shrinks))
    print("Number of independent variables: " + str(number_of_independent_variables))
    print()

    # Leaf variables
    print("Leaf variables:", end=" ")
    for leaf_variable in leaf_variables:
        print(leaf_variable, end=" ")
    print()

    with open(TMP_FILE_PATH, 'r', encoding="utf-8") as tmp_file:
        with open(output_file_path, 'w', encoding="utf-8") as output_file:
            # Name
            output_file.write("c " + bayesian_network.get_network_name() + "\n")
            output_file.write("c\n")

            # Parameters
            output_file.write("c Parameters:\n")
            if determinism:
                output_file.write("c \tdeterminism\n")
            if add_minor_clauses:
                output_file.write("c \tminor clauses\n")
            if indicator_clauses:
                output_file.write("c \tindicator clauses\n")
            if context_specific_independence:
                output_file.write("c \tcontext-specific independence\n")
            if constraint_clauses_for_leaf_variables:
                output_file.write("c \tconstraint clauses for leaf variables\n")
            output_file.write("c \tselector variable type: " + selector_variable_type.name + "\n")
            output_file.write("c\n")

            for variable in variables_bayesian_network:
                output_file.write("c " + variable + "\n")
                for state in states_bayesian_network[variable]:
                    output_file.write("c \t" + state + ": " + get_variable_for_name(variable, state) + "\n")

            output_file.write("c selector variables: " + str(first_selector_variable) + ", ...\n")
            output_file.write("c\n")

            output_file.write("p cnf " + str(number_of_variables) + " " + str(number_of_clauses) + "\n")

            output_file.write(tmp_file.read())

    os.remove(TMP_FILE_PATH)
    reset()
