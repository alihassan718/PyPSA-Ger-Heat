import pandas as pd

def init_heating_sector(n, heat_demand_df):
    """
    Initializes the heating sector by adding heat buses and residential heat loads.

    Parameters
    ----------
    n : pypsa.Network
        The PyPSA network object to modify.
    heat_demand_df : pd.DataFrame
        Hourly heat demand per cluster (columns: buses).
    """
    for bus in heat_demand_df.columns:
        heat_bus = f"{bus} heat"

        if heat_bus not in n.buses.index:
            n.add("Bus", name=heat_bus,
                  x=n.buses.at[bus, 'x'],
                  y=n.buses.at[bus, 'y'],
                  carrier="heat")

        n.add("Load",
              name=f"{bus} heat_residential",
              bus=heat_bus,
              p_set=heat_demand_df[bus],
              carrier="heat")
        
        
def add_biomass_boilers(n, heat_demand_df, fuel_cost, biomass_addition_df, discount_rate=0.07):
    biomass = {
        "carrier": "biomass",
        "tech": "biomass_boiler",
        "capex": 1200,
        "fom": 0.03,
        "vom": 50,
        "efficiency": 0.85,
        "lifetime": 20
    }
    biomass_annuity = discount_rate / (1 - 1 / (1 + discount_rate)**biomass["lifetime"])

    for bus in heat_demand_df.columns:
        heat_bus = f"{bus} heat"
        fuel_bus = f"{bus} {biomass['carrier']}"
        biomass_link = f"{bus} {biomass['tech']}"
        fixed_biomass_link = f"{bus} fixed_biomass_boiler"

        # Add biomass fuel bus if missing
        if fuel_bus not in n.buses.index:
            n.add("Bus", name=fuel_bus, x=n.buses.at[bus, 'x'], y=n.buses.at[bus, 'y'], carrier=biomass["carrier"])

        # Add biomass store if missing
        store_name = f"{bus} biomass_store"
        if store_name not in n.stores.index:
            n.add("Store",
                  name=store_name,
                  bus=fuel_bus,
                  e_nom_extendable=True,
                  e_cyclic=True,
                  carrier=biomass["carrier"],
                  marginal_cost=0,
                  capital_cost=0)

        # Add main biomass boiler (extendable)
        if biomass_link not in n.links.index:
            bus_key = f"{bus} biomass"
            p_nom = biomass_addition_df.loc[bus_key, "p_nom"] if bus_key in biomass_addition_df.index else 0
            capital_cost = biomass["capex"] * biomass_annuity + biomass["capex"] * biomass["fom"]

            n.add("Link",
                  name=biomass_link,
                  bus0=fuel_bus,
                  bus1=heat_bus,
                  efficiency=biomass["efficiency"],
                  p_nom=p_nom,
                  p_nom_extendable=True,
                  capital_cost=capital_cost,
                  marginal_cost=biomass["vom"],
                  carrier=biomass["carrier"])

        # Add fixed biomass boiler
        if fixed_biomass_link not in n.links.index:
            fixed_p_nom = n.links.at[biomass_link, "p_nom"] if biomass_link in n.links.index else 0

            n.add("Link",
                  name=fixed_biomass_link,
                  bus0=fuel_bus,
                  bus1=heat_bus,
                  efficiency=biomass["efficiency"],
                  p_nom=fixed_p_nom,
                  p_nom_extendable=False,
                  capital_cost=0,
                  marginal_cost=0,
                  carrier="heat")
            
def update_fixed_biomass_boilers(n):
    """
    Moves optimized biomass boiler capacity to the fixed biomass boiler link.
    """
    for link in n.links.index:
        if "biomass_boiler" in link and not "fixed" in link:
            fixed_link = link.replace("biomass_boiler", "fixed_biomass_boiler")

            if link in n.links.index and fixed_link in n.links.index:
                added = n.links.at[link, "p_nom_opt"]
                n.links.at[fixed_link, "p_nom"] += added
                n.links.at[link, "p_nom"] = 0
    return n
#need to update the fuel cost of biomass for each year, this funtion will be called in the loop

def update_link_costs(n, year, fuel_cost):
    for link in n.links.index:
        if "biomass_boiler" in link and "fixed" not in link:
            n.links.at[link, "marginal_cost"] = fuel_cost.loc[year, "biomass"]
        elif "gas_boiler" in link:
            n.links.at[link, "marginal_cost"] = fuel_cost.loc[year, "gas"]
        elif "oil_boiler" in link:
            n.links.at[link, "marginal_cost"] = fuel_cost.loc[year, "oil"]
            
            
def remove_expired_biomass_boilers(n, year, removal_biomass_df):
    """
    Removes expired biomass heating capacity from fixed biomass boilers in the current year.

    Parameters
    ----------
    n : pypsa.Network
        The PyPSA network object.

    year : int
        The simulation year (e.g., 2025).

    removal_df : pd.DataFrame
        DataFrame with columns: 'bus', 'carrier', 'p_nom', 'decommissioning_year'.

    Returns
    -------
    n : pypsa.Network
        Updated network with expired fixed biomass capacities removed.
    """
    # Filter only rows with decommissioning in the current year
    expired = removal_biomass_df[removal_biomass_df["year_removed"] == year]

    for _, row in expired.iterrows():
        link_name = f"{row['bus']} fixed_biomass_boiler"
        if link_name in n.links.index:
            old_p_nom = n.links.at[link_name, "p_nom"]
            new_p_nom = max(0, old_p_nom - row["p_nom"])
            n.links.at[link_name, "p_nom"] = new_p_nom
            # 🐦🐦🐦 shouldn't p_nom be added to p_nom_max of extentdable? which is deleted 
            print(f"[{year}] Removed {row['p_nom']} MW from {link_name} (new p_nom = {new_p_nom})")

    return n


def add_gas_boilers(n, heat_demand_df, fuel_cost, gas_addition_df, discount_rate=0.07):
    
    gas = {
        "carrier": "gas",
        "tech": "gas_boiler",
        "capex": 1000,
        "fom": 0.03,
        "vom": 30,
        "efficiency": 0.9,
        "lifetime": 20
    }
    
    gas_annuity = discount_rate / (1 - 1 / (1 + discount_rate)**gas["lifetime"])
    
    for bus in heat_demand_df.columns:
        heat_bus = f"{bus} heat"
        fuel_bus = f"{bus} {gas['carrier']}"
        gas_link = f"{bus} {gas['tech']}"
    
        if gas_link not in n.links.index:
            # Step 1: Capital cost
            capital_cost = gas["capex"] * gas_annuity + gas["capex"] * gas["fom"]
    
            # Step 2: Determine p_nom from gas_addition_df
            bus_key = f"{bus} gas"
            if bus_key in gas_addition_df.index:
                p_nom = gas_addition_df.loc[bus_key, "p_nom"]
            else:
                p_nom = 0  # Or skip this bus if no data
    
            # Step 3: Add the gas boiler
            n.add("Link",
                  name=gas_link,
                  bus0=fuel_bus,
                  bus1=heat_bus,
                  efficiency=gas["efficiency"],
                  p_nom=p_nom,
                  p_nom_extendable=True,
                  capital_cost=capital_cost,
                  marginal_cost = gas["vom"],
                  carrier=gas["carrier"])


def remove_expired_gas_boilers(n, year, removal_gas_df):
    """
    Subtracts expired gas boiler capacity from the main gas boilers and sets p_nom_max
    to allow the model to rebuild it if needed.

    Parameters
    ----------
    n : pypsa.Network
        The PyPSA network object.

    year : int
        The simulation year (e.g., 2025).

    removal_gas_df : pd.DataFrame
        DataFrame with columns: 'bus', 'carrier', 'p_nom', 'year_removed'.

    Returns
    -------
    n : pypsa.Network
        Updated network with expired gas boiler capacities removed but rebuildable.
    """
    expired = removal_gas_df[removal_gas_df["year_removed"] == year]

    for _, row in expired.iterrows():
        link_name = f"{row['bus']} gas_boiler"
        if link_name in n.links.index:
            old_p_nom = n.links.at[link_name, "p_nom"]
            new_p_nom = max(0, old_p_nom - row["p_nom"])
            n.links.at[link_name, "p_nom"] = new_p_nom

            # Set the maximum capacity allowed (rebuildable)
            if "p_nom_max" in n.links.columns:
                n.links.at[link_name, "p_nom_max"] = n.links.at[link_name, "p_nom_max"] + row["p_nom"]
            else:
                n.links["p_nom_max"] = n.links["p_nom"]  # Initialize the column if missing
                n.links.at[link_name, "p_nom_max"] = new_p_nom + row["p_nom"]

            print(f"[{year}] Removed {row['p_nom']} MW from {link_name} (new p_nom = {new_p_nom}, p_nom_max += {row['p_nom']})")

    return n

def add_oil_boilers(n, heat_demand_df, fuel_cost, oil_addition_df, discount_rate=0.07):

    
    # Oil boiler parameters
    oil = {
        "carrier": "oil",
        "tech": "oil_boiler",
        "capex": 300,   # €/kW
        "fom": 0.03,
        "vom": 5,       # €/MWh
        "efficiency": 0.85,
        "lifetime": 20
        }
        # Ensure 'oil' carrier exists and has a CO₂ emissions value
    if 'oil' in n.carriers.index:
        oil_emissions = n.carriers.at['oil', 'co2_emissions']
    else:
        raise ValueError("'oil' carrier not found in network.carriers")
    
    # Add 'oil_boiler' carrier with the same CO₂ emissions
    if 'oil_boiler' not in n.carriers.index:
        n.add("Carrier", "oil_boiler", co2_emissions=oil_emissions)

    # Annuity calculation for oil
    oil_annuity = discount_rate / (1 - 1 / (1 + discount_rate)**oil["lifetime"])
    
    for bus in heat_demand_df.columns:
        heat_bus = f"{bus} heat"
        fuel_bus = f"{bus} {oil['carrier']}"
        oil_link = f"{bus} {oil['tech']}"
    
        # 1. Fuel Bus
        if fuel_bus not in n.buses.index:
            n.add("Bus", name=fuel_bus,
                  x=n.buses.at[bus, 'x'],
                  y=n.buses.at[bus, 'y'],
                  carrier=oil["carrier"])
    
        # 2. Oil Store
        store_name = f"{bus} oil_store"
        if store_name not in n.stores.index:
            n.add("Store",
                  name=store_name,
                  bus=fuel_bus,
                  e_nom_extendable=True,
                  e_cyclic=True,
                  carrier=oil["carrier"],
                  marginal_cost=0,
                  capital_cost=0)
    
        # 3. Oil boiler Link
        capital_cost = oil["capex"] * oil_annuity + oil["capex"] * oil["fom"]
    
        # Check if the link exists
        if oil_link not in n.links.index:
    
            # Get p_nom from oil_addition_df
            bus_key = f"{bus} oil"
            if bus_key in oil_addition_df.index:
                p_nom = oil_addition_df.loc[bus_key, "p_nom"]
            else:
                p_nom = 0
    
            n.add("Link",
                  name=oil_link,
                  bus0=fuel_bus,
                  bus1=heat_bus,
                  efficiency=oil["efficiency"],
                  p_nom=p_nom,
                  p_nom_extendable=True,
                  capital_cost=capital_cost,
                  marginal_cost= oil["vom"],
                  carrier=oil["carrier"])
    
def remove_expired_oil_boilers(n, year, removal_oil_df):
    """
    Subtracts expired gas boiler capacity from the main gas boilers and sets p_nom_max
    to allow the model to rebuild it if needed.

    Parameters
    ----------
    n : pypsa.Network
        The PyPSA network object.

    year : int
        The simulation year (e.g., 2025).

    removal_gas_df : pd.DataFrame
        DataFrame with columns: 'bus', 'carrier', 'p_nom', 'year_removed'.

    Returns
    -------
    n : pypsa.Network
        Updated network with expired gas boiler capacities removed but rebuildable.
    """
    expired = removal_oil_df[removal_oil_df["year_removed"] == year]

    for _, row in expired.iterrows():
        link_name = f"{row['bus']} oil_boiler"
        if link_name in n.links.index:
            old_p_nom = n.links.at[link_name, "p_nom"]
            new_p_nom = max(0, old_p_nom - row["p_nom"])
            n.links.at[link_name, "p_nom"] = new_p_nom

            # Set the maximum capacity allowed (rebuildable)
            if "p_nom_max" in n.links.columns:
                n.links.at[link_name, "p_nom_max"] = n.links.at[link_name, "p_nom_max"] + row["p_nom"]
            else:
                n.links["p_nom_max"] = n.links["p_nom"]  # Initialize the column if missing
                n.links.at[link_name, "p_nom_max"] = new_p_nom + row["p_nom"]

            print(f"[{year}] Removed {row['p_nom']} MW from {link_name} (new p_nom = {new_p_nom}, p_nom_max += {row['p_nom']})")

    return n
    
    
    
# def add_heat_pumps(n, heat_demand_df, heatpump_addition_df, discount_rate=0.07):
#     """
#     Adds heat pump links to the network with base p_nom from heatpump_addition_df.

#     Parameters
#     ----------
#     n : pypsa.Network
#         The PyPSA network object.
#     heat_demand_df : pd.DataFrame
#         DataFrame containing hourly heat demand with bus names as columns.
#     heatpump_addition_df : pd.DataFrame
#         DataFrame with columns ['bus', 'carrier', 'p_nom'] containing initial capacities.
#     discount_rate : float
#         Discount rate used for capital cost annuity calculation.
#     """

#     hp = {
#         "tech": "heat_pump",
#         "cop": 3.0,
#         "capex": 800,
#         "fom": 0.02,
#         "vom": 0,
#         "lifetime": 20
#     }


#     hp_annuity = discount_rate / (1 - 1 / (1 + discount_rate)**hp["lifetime"])

#     for bus in heat_demand_df.columns:
#         heat_bus = f"{bus} heat"
#         hp_link = f"{bus} {hp['tech']}"

#         # Step 1: Get p_nom from heatpump_addition_df
#         bus_key = f"{bus} heat_pump"
#         if bus_key in heatpump_addition_df.index:
#             p_nom = heatpump_addition_df.loc[bus_key, "p_nom"]
#         else:
#             p_nom = 0

#         # Step 2: Add the link if not already added
#         if hp_link not in n.links.index:
#             capital_cost = hp["capex"] * hp_annuity + hp["capex"] * hp["fom"]
#             n.add("Link",
#                   name=hp_link,
#                   bus0=bus,            # AC bus
#                   bus1=heat_bus,       # Heat bus
#                   efficiency=hp["cop"],
#                   p_nom=p_nom,
#                   p_nom_extendable=True,
#                   capital_cost=capital_cost,
#                   marginal_cost=hp["vom"],
#                   carrier="heat_pump")
def add_heat_pumps(n, heat_demand_df, heatpump_addition_df, discount_rate=0.07):
    """
    Adds air-source and ground-source heat pump links to the network using base p_nom from heatpump_addition_df,
    and sets p_nom_max to prevent unrealistic expansion.

    Parameters
    ----------
    n : pypsa.Network
        The PyPSA network object.
    heat_demand_df : pd.DataFrame
        DataFrame containing hourly heat demand with bus names as columns.
    heatpump_addition_df : pd.DataFrame
        DataFrame with columns ['bus', 'carrier', 'p_nom'] containing initial capacities.
    discount_rate : float
        Discount rate used for capital cost annuity calculation.
    """
# Adjusted ratios: 80% air-source, 20% ground-source
    heat_pumps = {
        "air_source_heat_pump": {
            "cop": 3.0,
            "capex": 2800,
            "fom": 0.02,
            "vom": 80.0,
            "lifetime": 20,
            "national_potential_MW": 16000,   # 80% of 20 GW
            "annual_potential_MW": 1120       # 80% of 1400 MW/year
        },
        "ground_source_heat_pump": {
            "cop": 4.0,
            "capex": 3600,
            "fom": 0.02,
            "vom": 80.0,
            "lifetime": 25,
            "national_potential_MW": 4000,    # 20% of 20 GW
            "annual_potential_MW": 280        # 20% of 1400 MW/year
        }
    }

    # Calculate total regional demand
    regional_heat_demand = heat_demand_df.sum().to_dict()
    total_heat_demand = sum(regional_heat_demand.values())

    for bus in heat_demand_df.columns:
        heat_bus = f"{bus} heat"

        for hp_type, params in heat_pumps.items():
            hp_link = f"{bus} {hp_type}"

            # Financials
            annuity = discount_rate / (1 - 1 / (1 + discount_rate)**params["lifetime"])
            capital_cost = params["capex"] * annuity + params["capex"] * params["fom"]

            # Base capacity
            bus_key = f"{bus} {hp_type}"
            p_nom = heatpump_addition_df.loc[bus_key, "p_nom"] if bus_key in heatpump_addition_df.index else 0

            # Regional and yearly caps
            demand_share = regional_heat_demand[bus] / total_heat_demand
            regional_cap = params["national_potential_MW"] * demand_share
            yearly_cap = params["annual_potential_MW"] * demand_share

            # Final max installable capacity
            p_nom_max = round(min(regional_cap, yearly_cap), 2)

            if hp_link not in n.links.index:
                n.add("Link",
                      name=hp_link,
                      bus0=bus,
                      bus1=heat_bus,
                      efficiency=params["cop"],
                      p_nom=p_nom,
                      p_nom_max=p_nom_max,
                      p_nom_extendable=True,
                      capital_cost=capital_cost,
                      marginal_cost=params["vom"],
                      carrier=hp_type)
    # # Define both heat pump types
    # heat_pumps = {
    #     "air_source_heat_pump": {
    #         "cop": 3.0,
    #         "capex": 2800,
    #         "fom": 0.02,
    #         "vom": 80.0,
    #         "lifetime": 20,
    #         "max_multiplier": 5  # max 3x of base
    #     },
    #     "ground_source_heat_pump": {
    #         "cop": 4.0,
    #         "capex": 3600,
    #         "fom": 0.02,
    #         "vom": 80.0,
    #         "lifetime": 25,
    #         "max_multiplier": 3  # more constrained
    #     }
    # }
    # max_gshp_capacity=8000
    
    # for bus in heat_demand_df.columns:
    #     heat_bus = f"{bus} heat"

    #     for hp_type, params in heat_pumps.items():
    #         hp_link = f"{bus} {hp_type}"

    #         # Get annuity and capital cost
    #         annuity = discount_rate / (1 - 1 / (1 + discount_rate)**params["lifetime"])
    #         capital_cost = params["capex"] * annuity + params["capex"] * params["fom"]

    #         # Lookup base p_nom
    #         bus_key = f"{bus} {hp_type}"
    #         if bus_key in heatpump_addition_df.index:
    #             p_nom = heatpump_addition_df.loc[bus_key, "p_nom"]
    #         else:
    #             p_nom = 0

    #         p_nom_max = round(min(p_nom * params["max_multiplier"], max_gshp_capacity), 2)
    #         # p_nom_max = round(p_nom * params["max_multiplier"], 2)

    #         if hp_link not in n.links.index:
    #             n.add("Link",
    #                   name=hp_link,
    #                   bus0=bus,              # From electricity bus
    #                   bus1=heat_bus,         # To heat bus
    #                   efficiency=params["cop"],
    #                   p_nom=p_nom,
    #                   p_nom_max=p_nom_max,
    #                   p_nom_extendable=True,
    #                   capital_cost=capital_cost,
    #                   marginal_cost=params["vom"],
    #                   carrier=hp_type)

def remove_expired_heatpumps(n, year, removal_hp_df):
    """
    Removes expired air- and ground-source heat pump capacities from the network
    and updates p_nom and p_nom_max so the model can rebuild the removed capacity if needed.

    Parameters
    ----------
    n : pypsa.Network
        The PyPSA network object.

    year : int
        The simulation year (e.g., 2025).

    removal_hp_df : pd.DataFrame
        DataFrame with columns: 'bus', 'carrier', 'p_nom', 'year_removed'.

    Returns
    -------
    n : pypsa.Network
        Updated network with expired heat pump capacities removed.
    """
    expired = removal_hp_df[removal_hp_df["year_removed"] == year]

    for _, row in expired.iterrows():
        tech = row["carrier"]  # carrier is either 'air_source_heat_pump' or 'ground_source_heat_pump'
        link_name = f"{row['bus']} {tech}"

        if link_name in n.links.index:
            old_p_nom = n.links.at[link_name, "p_nom"]
            new_p_nom = max(0, old_p_nom - row["p_nom"])
            n.links.at[link_name, "p_nom"] = new_p_nom

            # Update or initialize p_nom_max
            if "p_nom_max" in n.links.columns:
                n.links.at[link_name, "p_nom_max"] = n.links.at[link_name, "p_nom_max"] + row["p_nom"]
            else:
                n.links["p_nom_max"] = n.links["p_nom"]
                n.links.at[link_name, "p_nom_max"] = new_p_nom + row["p_nom"]

            print(f"[{year}] Removed {row['p_nom']} MW from {link_name} (new p_nom = {new_p_nom}, p_nom_max += {row['p_nom']})")

    return n

def add_solar_thermal(n, heat_demand_df, solar_addition_df, discount_rate=0.07):
    """
    Adds solar thermal systems to the network using solar_thermal_source buses and infinite supply stores.

    Parameters
    ----------
    n : pypsa.Network
        The PyPSA network object.
    heat_demand_df : pd.DataFrame
        DataFrame containing hourly heat demand with bus names as columns.
    solar_addition_df : pd.DataFrame
        DataFrame with columns ['bus', 'carrier', 'p_nom'] containing initial capacities.
    discount_rate : float
        Discount rate used for capital cost annuity calculation.
    """

    # Solar thermal parameters
    capex = 500  # EUR/kW
    fom = 0.01
    vom = 0.0
    lifetime = 25
    efficiency = 0.5
    max_full_load_hours = 500  # ~500 FLH annually

    # Calculate annuity and capital cost
    annuity = discount_rate / (1 - 1 / (1 + discount_rate)**lifetime)
    capital_cost = capex * annuity + capex * fom

    for bus in heat_demand_df.columns:
        heat_bus = f"{bus} heat"
        solar_bus = f"{bus} solar_thermal_source"
        link_name = f"{bus} solar_thermal"

        # Add solar thermal source bus if not already there
        if solar_bus not in n.buses.index:
            n.add("Bus", name=solar_bus, carrier="solar_thermal")

        # Add infinite supply store at solar_thermal_source bus
        if f"{bus} solar_thermal_store" not in n.stores.index:
            n.add("Store",
                  name=f"{bus} solar_thermal_store",
                  bus=solar_bus,
                  e_nom=1e6,  # very large value
                  e_nom_extendable=False,
                  marginal_cost=0.0,
                  carrier="solar_thermal")

        # Get installed capacity from data
        bus_key = f"{bus} solar_thermal"
        p_nom = solar_addition_df.loc[bus_key, "p_nom"] if bus_key in solar_addition_df.index else 0

        # Max capacity per regional bus (based on FLH)
        p_nom_max = round((max_full_load_hours / 8760) * 1e3, 2)

        # Add link from solar thermal source to heat bus
        if link_name not in n.links.index:
            n.add("Link",
                  name=link_name,
                  bus0=solar_bus,
                  bus1=heat_bus,
                  efficiency=efficiency,
                  p_nom=p_nom,
                  p_nom_max=p_nom_max,
                  p_nom_extendable=True,
                  capital_cost=capital_cost,
                  marginal_cost=vom,
                  carrier="solar_thermal")

    return "Solar thermal source buses, stores, and links added to network."

def remove_expired_solar_thermal(n, year, removal_df):
    """
    Removes expired solar thermal units from the PyPSA network for a given year.

    Parameters
    ----------
    n : pypsa.Network
        The PyPSA network object.
    year : int
        The current model year to check for decommissioned technologies.
    removal_df : pd.DataFrame
        DataFrame containing ['year_removed', 'carrier', 'p_nom', 'bus'].
    """
    # Filter for expired solar thermal units in the given year
    expired = removal_df[(removal_df["carrier"] == "solar_thermal") & (removal_df["year_removed"] == year)]

    for _, row in expired.iterrows():
        link_name = f"{row['bus']} {row['carrier']}"

        if link_name in n.links.index:
            current_capacity = n.links.at[link_name, "p_nom"]
            new_capacity = max(current_capacity - row["p_nom"], 0)
            n.links.at[link_name, "p_nom"] = new_capacity

    return f"Expired solar thermal units removed for {year}."
