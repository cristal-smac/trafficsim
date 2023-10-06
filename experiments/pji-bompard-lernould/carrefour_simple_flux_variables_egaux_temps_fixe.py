import sys, os
sys.path.append(os.path.join(sys.path[0],'..'))
from core.src.experiment import Experiment
from core.src.preset_networks import OneCrossroadNetwork
import os

if __name__ == '__main__':
    """
    Expérience dans laquelle on a un carrefour avec deux directions possibles : Ouest -> Est et Sud -> Nord.
    Nous faisons varier uniquement les flux de véhicules.
    """
    output_files = ''
    legend = ''

    network = OneCrossroadNetwork()

    for i in range (11):
        if i != 0:
            output_files += ','
            legend += ','

        t_g = 30

        n_vehicles_h = 100 + 50 * i

        e = Experiment(f'exp_carrefour_simple_flux_variables_egaux_temps_fixe{i}',
                       network=network.generate_infrastructures,
                       routes=network.generate_flows_only_ahead)

        e.set_variable('stop_generation_time', 900)
        e.set_variable('flow_density', n_vehicles_h)
        e.set_variable('lane_length', 100)
        e.set_variable('max_speed', 15)
        e.set_variable('green_time', t_g)
        e.set_variable('yellow_time', 5)

        e.run()

        e.cleanFiles(delete_summary=False, delete_queue=True)

        output_files += f'{e.files["summaryxml"]}'
        legend += f'"Flux = {n_vehicles_h}"'

    os.system('mkdir -p ../../img/flux_variables_egaux_temps_fixe/')
    os.system(f'python $SUMO_HOME/tools/visualization/plot_summary.py -i {output_files} -m meanTravelTime --title "Temps de parcours moyen avec Tv = {t_g}" -o ../../img/flux_variables_egaux_temps_fixe/flux_variables_temps_egaux.png -l {legend}')