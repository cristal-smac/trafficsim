import sys, os

from core.src.experiment import Experiment
from core.src.util import import_flows_parameters_from_csv
from core.src.preset_networks import SquareNetwork

sys.path.append(os.path.join(sys.path[0],'..'))


if __name__ == '__main__':
    """
    Expérience dans laquelle on teste simplement le réseau carré implémenté dans networks.py.
    Les véhicules doivent être capable d'arriver de n'importe quelle direction et de pouvoir aller dans n'importe laquelle.
    """

    params_file = "../../csv/parameters/simple_carrefour.csv"

    flow_value = 100
    lane_length = 100
    gt_value = 30
    yt_value = 3
    speed_value = 30
    nb_roads_by_side = 2

    network = SquareNetwork()

    e = Experiment(f'test_reseau_fully_connected', 
                    network=network.square_crossroad_network,
                    routes=network.square_crossroad_routes,
                    additionals=network.no_additionals)


    load_vector, coeff_matrix = import_flows_parameters_from_csv(params_file)

    nb_ticks = 300       # Nombre de ticks par période de flux

    # Variables de flux
    e.set_variable('coeff_matrix', coeff_matrix)
    e.set_variable('load_vector', load_vector)
    e.set_variable("params_file", params_file)
    e.set_variable('nb_ticks', nb_ticks)
    
    e.set_variable('default_len', lane_length)
    e.set_variable('default_speed', speed_value)
    e.set_variable('default_green_time', gt_value)
    e.set_variable('default_yellow_time', yt_value)
    e.set_variable('default_flow', flow_value)
    e.set_variable('nb_roads_by_side', nb_roads_by_side)

    e.set_simulation_time(3601)

    e.run(gui=True)

    e.cleanFiles(delete_summary=True, delete_queue=True)