import sys, os
sys.path.append(os.path.join(sys.path[0],'..'))
from core.src.experiment import Experiment
from core.src.util import import_flows_parameters_from_csv
from core.src.preset_networks import OneCrossroadNetwork

if __name__ == "__main__":
    """
    Script permettant d'expérimenter la modification de flux par ajout de flux multiples dans la configuration.
    """

    lane_length = 100
    gt_value = 30
    yt_value = 3
    speed_value = 30

    network = OneCrossroadNetwork()

    e = Experiment('test_multi_flux', network=network.generate_infrastructures, flows=network.generate_flows_with_matrix)

    e.set_parameter('lane_length', lane_length)
    e.set_parameter('max_speed', speed_value)
    e.set_parameter('green_time', gt_value)
    e.set_parameter('yellow_time', yt_value)

    zero = 0.001        # SUMO n'admet pas de flux égal à 0
    
    # coeff_matrix = np.array([[1/12, zero],     # Flux nord -> sud
    #                          [1/12, zero],     # Flux nord -> est
    #                          [1/12, zero],     # Flux nord -> ouest
    #                          [1/12, 2/12],  # Flux est -> sud
    #                          [1/12, 2/12],  # Flux est -> nord
    #                          [1/12, 2/12],  # Flux est -> ouest
    #                          [1/12, zero],     # Flux sud -> est
    #                          [1/12, zero],     # Flux sud -> nord
    #                          [1/12, zero],     # Flux sud -> ouest
    #                          [1/12, 2/12],  # Flux ouest -> sud
    #                          [1/12, 2/12],  # Flux ouest -> est
    #                          [1/12, 2/12]   # Flux ouest -> nord
    #                          ])

    # load_vector = [240*5, 120*5]     # Vecteur de charge

    load_vector, coeff_matrix = import_flows_parameters_from_csv("../../csv/parameters/simple_carrefour.csv")

    nb_ticks = 300       # Nombre de ticks par période de flux

    e.set_parameter('coeff_matrix', coeff_matrix)
    e.set_parameter('load_vector', load_vector)
    e.set_parameter('period_time', nb_ticks)

    e.run(gui=True)

    e.clean_files()
