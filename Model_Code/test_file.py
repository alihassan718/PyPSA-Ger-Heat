# -*- coding: utf-8 -*-
"""
Created on Wed Jun 11 01:00:09 2025

@author: 86435
"""

# Part of base_functions.py or a new helper file

def convert_fossil_generators_to_links(n, fuel_cost):
    """
    Converts oil, biomass, and coal generators into Links
    with associated fuel buses and stores.
    Applies only to AC buses.

    Parameters:
    -----------
    n : pypsa.Network
        The PyPSA network object to modify
    fuel_cost : pd.DataFrame
        DataFrame containing marginal fuel cost per carrier

    Returns:
    --------
    list
        Names of converted generators (removed from n.generators)
    """
    fossil_carriers = ["oil", "biomass", "coal"]
    converted = []

    for bus in n.buses.index[n.buses.carrier == 'AC']:
        for carrier in fossil_carriers:
            # filter generators at this bus with this carrier
            gens = n.generators[(n.generators.bus == bus) & (n.generators.carrier == carrier)]
            if gens.empty:
                continue

            # Create fuel bus if not exists
            fuel_bus = f"{bus} {carrier}"
            if fuel_bus not in n.buses.index:
                n.add("Bus", fuel_bus, carrier=carrier,
                      x=n.buses.at[bus, 'x'], y=n.buses.at[bus, 'y'])

            # Add store if not exists
            store_name = f"{bus} {carrier} store"
            if store_name not in n.stores.index:
                n.add("Store", name=store_name, bus=fuel_bus,
                      e_nom=1e5, e_nom_extendable=True,
                      e_cyclic=False, marginal_cost=0.0, carrier=carrier)

            # For each generator, replace with a Link
            for gen_name, row in gens.iterrows():
                link_name = f"{bus} {carrier} plant"
                n.add("Link", name=link_name,
                      bus0=fuel_bus, bus1=bus,
                      p_nom=row.p_nom,
                      p_nom_extendable=row.p_nom_extendable,
                      efficiency=row.efficiency,
                      capital_cost=row.get("capital_cost", 0.0),
                      marginal_cost=fuel_cost.loc[2020, carrier],
                      carrier=carrier)
                
                converted.append(gen_name)
                n.remove("Generator", gen_name)

    return converted


def extend_yearly_potential_to_links(n, saved_potential, regional_potential, agg_p_nom_minmax):
    for i in n.links.index[n.links.p_nom_extendable == True]:
        if i not in saved_potential.index:
            saved_potential[i] = n.links.p_nom_max[i]
        value = n.links.p_nom_opt.get(i, 0.0)
        saved_potential[i] = max(saved_potential[i] - value, 0)
        saved_potential[i] = min(saved_potential[i], regional_potential)
        n.links.p_nom_max[i] = saved_potential[i]
    return saved_potential


def apply_co2_price_to_links(n, year, co2price):
    if year <= 2020:
        return
    delta = co2price.loc[year].item() - co2price.loc[year - 1].item()
    for carrier in n.carriers.index[n.carriers.co2_emissions > 0]:
        if carrier in n.links.carrier.values:
            eff = n.links[n.links.carrier == carrier].efficiency.mean()
            price_increase = delta * n.carriers.co2_emissions[carrier] / eff
            n.links.loc[n.links.carrier == carrier, 'marginal_cost'] += price_increase


def phase_out_links(n, carrier, phase_year):
    links = n.links[n.links.carrier == carrier]
    total = links.p_nom.sum()
    yearly = total / (phase_year - 2020)
    dist = []
    for i in links.index:
        dist.append(yearly * links.p_nom.loc[i] / total)
    return links, yearly, dist


def remove_phase_out_links(n, removal_links, yearly_value):
    total_nom = removal_links.p_nom.sum()
    for i in removal_links.index:
        remove = yearly_value * removal_links.p_nom.loc[i] / total_nom
        val = n.links.loc[i, 'p_nom'] - remove
        n.links.loc[i, 'p_nom'] = max(val, 0)



# Insert in Model.py inside the main year loop

# --- Start of yearly loop ---
for year in range(2021, 2051):
    logger.info(f"Running year {year}")

    # Update cost and CO2 price
    mp.update_cost(n, year, cost_factors, fuel_cost)
    mp.update_co2price(n, year, co2price)
    apply_co2_price_to_links(n, year, co2price)

    # Update CO2 limit
    mp.update_co2limit(n, co2lims.co2limit[co2lims.year == year].values[0])

    # Remove phased out gens and links
    mp.delete_old_gens(n, year, removal_data)
    remove_phase_out_links(n, phase_out_removal_links, yearly_phase_out_links)

    # Run optimization
    n.lopf(...)

    # Save fixed capacity from optimized results
    mp.update_const_gens(n)
    mp.update_const_storage(n)

    # Update potentials for generators and links
    saved_potential = mp.Yearly_potential(n, saved_potential, regional_potential, agg_p_nom_minmax)
    saved_potential = extend_yearly_potential_to_links(n, saved_potential, regional_potential, agg_p_nom_minmax)

    # Track/plot/save results as usual

# --- End of loop ---
