#!/usr/bin/env python3

import os
import random
import argparse
from pathlib import Path
from typing import List, Union


def positive_int_or_none_parser(value: Union[int, str], percentage: bool, at_least_two: bool) -> Union[int, None]:
    """
    Check if the value is a (positive) number (int) or None
    :raises ArgumentTypeError: if the value is invalid
    """

    # None
    if isinstance(value, str) and value.lower() == "none":
        return None

    try:
        value = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"\"{value}\" has an invalid type ({type(value)}); int is expected!")

    # Number
    if value <= 0:
        raise argparse.ArgumentTypeError(f"\"{value}\" must be positive!")

    if at_least_two and value == 1:
        raise argparse.ArgumentTypeError(f"\"{value}\" must be at least 2!")

    if percentage and value > 100:
        raise argparse.ArgumentTypeError(f"\"{value}\" must be at most 100!")

    return value


def seed_parser(value: Union[int, str]) -> int:
    return positive_int_or_none_parser(value, False, False)


def at_least_two_int_parser(value: Union[int, str]) -> int:
    # None
    if isinstance(value, str) and value.lower() == "none":
        raise argparse.ArgumentTypeError(f"\"{value}\" has an invalid type ({type(value)}); int is expected!")

    return positive_int_or_none_parser(value, False, True)


def percentage_parser(value: Union[int, str]) -> int:
    # None
    if isinstance(value, str) and value.lower() == "none":
        raise argparse.ArgumentTypeError(f"\"{value}\" has an invalid type ({type(value)}); int is expected!")

    return positive_int_or_none_parser(value, True, False)


def output_file_path_parser(path: str) -> str:
    """
    Try to create an empty output file
    :param path: the path of the output file
    :return: the path
    :raises ArgumentTypeError: if the output file creation fails or the output file already exists
    """

    if not path.endswith(".bif"):
        raise argparse.ArgumentTypeError(f"The output file name must end with `.bif`!")

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
    parser_tmp = argparse.ArgumentParser(prog="Generate.py",
                                         description="Bels generator",
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter  # default values are shown in the help
                                         )

    # Add arguments
    parser_tmp.add_argument("output_file",
                            action="store",
                            type=output_file_path_parser,
                            help="name of the output file where the generated BN will be saved (must end with `.bif`)")

    parser_tmp.add_argument("-tls",
                            "--top_layer_size",
                            action="store",
                            default=5,
                            type=at_least_two_int_parser,
                            metavar="[positive number (at least 2)]",
                            help="top layer size")

    parser_tmp.add_argument("-bls",
                            "--bottom_layer_size",
                            action="store",
                            default=5,
                            type=at_least_two_int_parser,
                            metavar="[positive number (at least 2)]",
                            help="bottom layer size")

    parser_tmp.add_argument("-ds",
                            "--domain_size",
                            action="store",
                            default=2,
                            type=at_least_two_int_parser,
                            metavar="[positive number (at least 2)]",
                            help="domain size")

    parser_tmp.add_argument("-d",
                            "--density",
                            action="store",
                            default=100,
                            type=percentage_parser,
                            metavar="[positive number (0, 100]]",
                            help="density")

    parser_tmp.add_argument("-s",
                            "--seed",
                            action="store",
                            default=None,
                            type=seed_parser,
                            metavar="[big positive number | None]",
                            help="seed (ignored for fully dense BNs): if set to `None`, a new seed will be randomly generated")

    return parser_tmp


def get_bayesian_network_name() -> str:
    """
    :return: the Bayesian network name
    """

    if randomness:
        if number_of_diseases != number_of_symptoms:
            return str(number_of_diseases) + "_" + str(number_of_symptoms) + "_" + str(diseases_domain_size) + "_" + str(density) + "_" + str(seed)
        else:
            return str(number_of_diseases) + "_" + str(diseases_domain_size) + "_" + str(density) + "_" + str(seed)
    else:
        if number_of_diseases != number_of_symptoms:
            return str(number_of_diseases) + "_" + str(number_of_symptoms) + "_" + str(diseases_domain_size) + "_" + str(density)
        else:
            return str(number_of_diseases) + "_" + str(diseases_domain_size) + "_" + str(density)


def create_disease_name(position: int) -> str:
    """
    :return: the disease name
    """
    assert (position >= 0)
    assert (position < len(diseases))

    return "Disease_" + str(position + 1)


def create_disease_value(position_1: int, position_2: int) -> str:
    """
    :return: the disease value
    """
    assert (position_1 >= 0)
    assert (position_2 >= 0)
    assert (position_1 < len(diseases))
    assert (position_2 < diseases[position_1])

    return "value_d_" + str(position_1 + 1) + "_" + str(position_2 + 1)


def create_symptom_name(position: int) -> str:
    """
    :return: the symptom name
    """
    assert (position >= 0)
    assert (position < len(symptoms))

    return "Symptom_" + str(position + 1)


def create_symptom_value(position_1: int, position_2: int) -> str:
    """
    :return: the symptom value
    """
    assert (position_1 >= 0)
    assert (position_2 >= 0)
    assert (position_1 < len(symptoms))
    assert (position_2 < symptoms[position_1])

    return "value_s_" + str(position_1 + 1) + "_" + str(position_2 + 1)


def create_disease_probability(position: int) -> str:
    assert (position >= 0)
    assert (position < len(diseases))

    tmp: str = "table"
    max_position: int = diseases[position]

    for v in range(max_position):
        if v == 0:
            tmp += " 1.0"
        elif v < max_position - 1:
            tmp += ", 0.0"
        else:
            tmp += ", 0.0;"

    return tmp


def create_symptom_probability(position, positions: List[int]) -> str:
    assert (position >= 0)
    assert (position < len(symptoms))
    assert (len(positions) >= 2)
    for p in positions:
        assert (p >= 0)
        assert (p < len(diseases))

    values: List[int] = []
    for _ in range(len(positions)):
        values.append(0)

    tmp: str = create_symptom_probability_recursion(position, positions, 0, values, "")

    return tmp


def create_symptom_probability_recursion(position, positions: List[int], current_position: int, values: List[int], string: str) -> str:
    # Base case
    if current_position == len(positions):
        string += "  ("
        for k, value in enumerate(values):
            string += create_disease_value(positions[k], value)
            if k < len(values) - 1:
                string += ", "
        string += ")"

        max_position = symptoms[position]
        for k in range(max_position):
            if k == 0:
                string += " 1.0"
            elif k < max_position - 1:
                string += ", 0.0"
            else:
                string += ", 0.0;\n"

        return string

    for v in range(diseases[positions[current_position]]):
        values[current_position] = v
        string = create_symptom_probability_recursion(position, positions, current_position + 1, values, string)

    return string


def print_title() -> None:
    print("                                                  ")
    print("                      Bels                        ")
    print("                    generator                     ")
    print("                                                  ")


if __name__ == '__main__':
    # Title
    print_title()
    print()

    # Parser
    parser = create_parser()
    args = parser.parse_args()

    # Diseases
    number_of_diseases: int = args.top_layer_size
    diseases_domain_size: int = args.domain_size
    # Symptoms
    number_of_symptoms: int = args.bottom_layer_size
    symptoms_domain_size: int = args.domain_size
    # Others
    if args.seed is None:
        seed: int = int.from_bytes(os.urandom(16), 'big')
    else:
        seed: int = args.seed
    density: int = args.density

    random.seed(seed)
    randomness: bool = (density != 100)
    number_of_edges: int = int(number_of_diseases * (density / 100))

    if number_of_edges < 2:
        raise Exception("Small density!")

    path: str = args.output_file

    # Print arguments
    print("Arguments:")
    print("\toutput file: " + path)
    print("\ttop layer size: " + str(number_of_diseases))
    print("\tbottom layer size: " + str(number_of_symptoms))
    print("\tdomain size: " + str(diseases_domain_size))
    print("\tdensity: " + str(density) + "%")
    if randomness:
        print("\tseed: " + str(seed))
    print("Number of edges: " + str(number_of_edges))
    print()

    assert (number_of_edges >= 2)
    assert (diseases_domain_size >= 2)
    assert (symptoms_domain_size >= 2)
    assert (diseases_domain_size == symptoms_domain_size)
    assert (number_of_symptoms * number_of_edges > number_of_diseases)

    # Diseases
    diseases: List[int] = []
    for i in range(number_of_diseases):
        diseases.append(diseases_domain_size)

    # Symptoms
    symptoms: List[int] = []
    for i in range(number_of_symptoms):
        symptoms.append(symptoms_domain_size)

    with open(path, "w", encoding="utf-8") as file:
        file.write("network " + get_bayesian_network_name() + " {}\n")

        # Diseases - variables
        for i, number_of_parameters in enumerate(diseases):
            file.write("variable " + create_disease_name(i) + " {\n")
            file.write("  type discrete [ " + str(number_of_parameters) + " ] { ")
            for j in range(number_of_parameters):
                file.write(create_disease_value(i, j))
                if j != number_of_parameters - 1:
                    file.write(", ")
                else:
                    file.write(" ")
            file.write("};\n")
            file.write("}\n")

        # Symptoms - variables
        for i, number_of_parameters in enumerate(symptoms):
            file.write("variable " + create_symptom_name(i) + " {\n")
            file.write("  type discrete [ " + str(number_of_parameters) + " ] { ")
            for j in range(number_of_parameters):
                file.write(create_symptom_value(i, j))
                if j != number_of_parameters - 1:
                    file.write(", ")
                else:
                    file.write(" ")
            file.write("};\n")
            file.write("}\n")

        # Diseases - probabilities
        for i in range(number_of_diseases):
            file.write("probability ( " + create_disease_name(i) + " ) {\n")
            file.write("  " + create_disease_probability(i) + "\n")
            file.write("}\n")

        # Symptoms - probabilities
        for i in range(number_of_symptoms):
            print(str(i + 1) + "/" + str(number_of_symptoms))
            edges: List[int] = random.sample(range(0, number_of_diseases), number_of_edges)
            edges.sort()
            file.write("probability ( " + create_symptom_name(i) + " |")
            for j, edge in enumerate(edges):
                if j == 0:
                    file.write(" " + create_disease_name(edge))
                else:
                    file.write(", " + create_disease_name(edge))
            file.write(" ) {\n")
            file.write(create_symptom_probability(i, edges))
            file.write("}\n")
