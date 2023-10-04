import sys, os
sys.path.append(os.path.join(sys.path[0],'..'))
from core.src.experiment import Experiment
from core.src.util import import_flows_parameters_from_csv
from core.src.preset_networks import OneCrossroadNetwork

if __name__ == '__main__':
    """
    Expérience dans laquelle on teste simplement le réseau à double carrefour fully connected implémenté dans networks.py.
    Les véhicules doivent être capable d'arriver de n'importe quelle direction et de pouvoir aller dans n'importe laquelle.
    Des détetecteurs sont installés sur le trajet pour évaluer le nombre de véhicule arrivant sur un feu, et modifient son comportement.
    """

    params_file = "../../csv/parameters/simple_carrefour.csv"

    lane_length = 100
    gt_value = 30
    yt_value = 3
    speed_value = 30

    network = OneCrossroadNetwork()

    e = Experiment('test_detecteurs',
                   network=network.simple_crossroad_fully_connected_network,
                   routes=network.simple_crossroad_fully_connected_multi_flow,
                   detectors=network.detecteurs_numeriques_simple_carrefour)

    # Variables de réseau
    e.set_variable('default_len', lane_length)
    e.set_variable('default_speed', speed_value)
    e.set_variable('default_green_time', gt_value)
    e.set_variable('default_yellow_time', yt_value)
    e.set_variable('boolean_detector_length', 7.5)

    load_vector, coeff_matrix = import_flows_parameters_from_csv(params_file)

    nb_ticks = 300       # Nombre de ticks par période de flux

    # Variables de flux
    e.set_variable('coeff_matrix', coeff_matrix)
    e.set_variable('load_vector', load_vector)
    e.set_variable("params_file", params_file)
    e.set_variable('nb_ticks', nb_ticks)

    # Temps de simulation
    e.set_simulation_time(nb_ticks * (len(load_vector) + 1) + 1) # x * nb_ticks du durée + 1* nb_ticks pour observer la dernière configuration

    # Variables Traci
    e.set_variable('min_duration_tl', 10)
    e.set_variable('max_duration_tl', 30)
    e.set_variable('seuil_vehicules', 8)

    for i in range(5):

        e.run_traci(network.feux_a_seuils_communicants_sans_anticipation_simple_carrefour)

        e.exportResultsToFile("../../csv/exp_traci.csv", sampling_rate=50)

        e.cleanFiles(delete_summary=True, delete_queue=True)