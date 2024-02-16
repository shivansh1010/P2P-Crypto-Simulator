
import argparse
import numpy as np
from constants import *
from network import Network
from events import Event, EventQueue
from node import Node
import time
import configparser


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('config_file', type=str, help='Configuration TOML file')
    # parser.add_argument('n', type=int, help='No. of nodes')
    # parser.add_argument('z1', type=float, help='Fraction of low cpu nodes')
    # parser.add_argument('txn_time', type=int, help='Transaction time in ms')
    # parser.add_argument('mining_time', type=int, help='Mining time in ms')
    # parser.add_argument('execution_time', type=int, help='Simulation time units')

    args = parser.parse_args()
   
    # if (5 <= len(vars(args)) < 5):
    #     parser.error("Provide 5 arguments:\n"
    #                  "No. of nodes\n"
    #                  "Fraction of low cpu nodes\n"
    #                  "Transaction time in ms\n"
    #                  "Mining time in ms\n"
    #                  "Simulation time units\n"
    #                 )

    # n = args.n
    # z0 = 0.5 
    # z1 = args.z1
    # txn_time = args.txn_time
    # mining_time = args.mining_time
    # execution_time = args.execution_time

    # print("n:", n)
    # print("z1:", z1)
    # print("txn_time:", txn_time)
    # print("mining_time:", mining_time)
    # print("execution_time:", execution_time)

    # configtoml = args.c
    config = configparser.ConfigParser()
    # config.read('config.ini')
    config.read(args.config_file)
    # print(args.config_file)

    # print(config.sections())
    # print(config['simulation'])

    network = Network(config, type='toml')
    network.show_parameters()
    network.prepare_simulation()
    network.display_network()
    network.start_simulation()
    network.create_plot()


