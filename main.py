"""
main.py

This script serves as the entry point for the network simulation application. It reads a configuration file 
in TOML format, initializes a network simulation using the provided configuration, and performs the simulation.

Usage:
    python main.py config_file

Arguments:
    config_file     Path to the configuration file in TOML format.

Example:
    python3 main.py config.ini

Dependencies:
    - argparse: Used for parsing command-line arguments.
    - configparser: Used for reading the configuration file.

Notes:
- Ensure that the specified configuration file is in TOML format and contains the necessary parameters 
  for the network simulation.
- The 'Network' class from the 'network' module is used to represent and simulate the network.
- The network simulation is prepared, started, and executed using methods of the 'Network' class.
- After the simulation, a plot of the network and its parameters is created and saved to a file.
"""

import argparse
import configparser
import art

from network import Network
from logger import init_logger


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", type=str, help="Configuration TOML file")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config_file)

    LOG_LEVEL = "DEBUG" if config["simulation"]["debug"] == "True" else "INFO"
    init_logger(LOG_LEVEL)

    art.tprint('P2P Cryptocurrency\nNetwork Simulation', font='BifFig')
    print('Welcome to the project!')
    print('\nSelected configuration file: ', args.config_file)

    network = Network(config, type="toml")
    network.show_parameters()
    network.prepare_simulation()
    network.display_network()
    network.start_simulation() # main simulation
    network.display_info()
    network.create_plot()
    network.dump_to_file()

    print("Simulation completed successfully :)")
