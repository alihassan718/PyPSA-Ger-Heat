# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

def create_dummy_burners():
        
    
    # Recreate the DataFrame since previous state was lost
    regional_demand_TWh = {
        "DE0 2 heat": 2.237750e+08 / 1e6,
        "DE0 9 heat": 1.401345e+08 / 1e6,
        "DE0 A heat": 2.693371e+08 / 1e6,
        "DE0 E heat": 1.333434e+08 / 1e6
    }
    
    heating_shares = {
        "gas_burner": 0.55,
        "oil_burner": 0.19,
        "biomass_burner": 0.10,
    }
    
    legacy_techs = ["gas_burner", "oil_burner", "biomass_burner"]
    
    full_lifetimes = {
        "gas_burner": 20,
        "oil_burner": 20,
        "biomass_burner": 25,
    
    }
    
    min_lifetime = {
        "gas_burner": 1,
        "oil_burner": 1,
        "biomass_burner": 1,
    
    }
    
    # Updated capacity factors (midpoints for ranges)
    updated_capacity_factors = {
        "gas_burner": 0.4,
        "oil_burner": 0.4,
        "biomass_burner": 0.4,
    
    }
    
    entries = []
    
    for bus, regional_TWh in regional_demand_TWh.items():
        for tech in legacy_techs:
            tech_share = heating_shares[tech]
            tech_demand_TWh = regional_TWh * tech_share
            n_units = int(np.ceil(tech_demand_TWh))
            lifetimes = np.linspace(min_lifetime[tech], full_lifetimes[tech], n_units, dtype=int)
            for i, life in enumerate(lifetimes):
                demand_TWh_per_unit = tech_demand_TWh / n_units
                p_nom = round(demand_TWh_per_unit * 1e6 / (8760 * updated_capacity_factors[tech]), 2)
                entries.append({
                    "bus": bus,
                    "technology": tech,
                    "unit_id": i + 1,
                    "demand_TWh": demand_TWh_per_unit,
                    "remaining_lifetime": life,
                    "decommissioning_year": 2020 + life,
                    "p_nom": p_nom
                })
    
    df = pd.DataFrame(entries)
    # Step 3: Create 'carrier' column from 'technology'
    df['carrier'] = df['technology'].str.extract(r'(\w+)_burner')
    
    # Step 5: Add 'commissioning_year' using fixed lifetimes
    df['commissioning_year'] = df.apply(
        lambda row: row['decommissioning_year'] - full_lifetimes.get(row['technology'], 0), axis=1)
    df.to_csv('D:/project_h2/data/heating_techs/main_dummy_heating_techs.csv')
    

    # Load the existing technologies file
    
    # Extract the carrier from the 'tech' column (e.g., 'gas_burner' → 'gas')
    df['carrier'] = df['technology'].apply(lambda x: x.split('_')[0])
    
    # Save full version with 'carrier' column added (optional)
    # df.to_csv("data/existing_heating_technologies_with_carrier.csv", index=False)
    
    # Split the dataframe based on carrier type
    df_gas = df[df['carrier'] == 'gas']
    df_oil = df[df['carrier'] == 'oil']
    df_biomass = df[df['carrier'] == 'biomass']
    
    # Save each to a separate file
    df_gas.to_csv("D:/project_h2/data/heating_techs/Gas_Heating_Technologies.csv", index=False)
    df_oil.to_csv("D:/project_h2/data/heating_techs/Oil_Heating_Technologies.csv", index=False)
    df_biomass.to_csv("D:/project_h2/data/heating_techs/Biomass_Heating_Technologies.csv", index=False)

    return

def biomass_addition_and_removal(): 
    """
    Created on Thu Jun 26 16:42:46 2025
    
    @author: 86435
    """
    
    import pandas as pd
     # Iss sy upar legacy generator wala part add krna hy agr wohnung wali file sy kam na bna tou.
     # wrna wohnung file sy values ly kr usko iss csv a accordingly bna dena hy
    
    data = pd.read_csv("D:/project_h2/data/heating_techs/Biomass_Heating_Technologies.csv")
    
    
    # Remove ' heat' from bus names
    data['bus'] = data['bus'].str.replace(' heat', '', regex=False)
    
    # Prepare data for removal file
    data.rename(columns={'decommissioning_year': 'year_removed'}, inplace=True)
    removal = data[['year_removed', 'carrier', 'p_nom', 'bus']]
    
    
    # Group and process the data for each removal year
    years_res = sorted(removal.year_removed.unique())
    remove = pd.DataFrame(columns=removal.columns)
    
    for yr in years_res:
        dat = removal[removal.year_removed == yr]
        df = dat.groupby(['year_removed', 'bus', 'carrier']).sum().sum(level=['year_removed', 'bus', 'carrier']).unstack('year_removed').fillna(0).reset_index()
        df['year'] = df.columns[2][1]
        df.columns = ['bus', 'carrier', 'p_nom', 'year_removed']
        remove = pd.concat([df, remove], ignore_index=False)
    
    # Final formatting and save
    remove.index = remove.bus + ' ' + remove.carrier
    output_path = "D:/project_h2/Networks/elec_s_4_ec_lcopt_Co2L-1H-Ep-CCL/biomass_basic_removal_heat.csv"
    remove.to_csv(output_path)
    
    correct = remove.groupby(['carrier', 'bus']).agg({'p_nom': ['sum']})
    correct = correct.stack().reset_index()
    correct = correct[['carrier', 'p_nom', 'bus']]
    correct.index = correct.bus + ' ' + correct.carrier
    
    correct.to_csv("D:/project_h2/Networks/elec_s_4_ec_lcopt_Co2L-1H-Ep-CCL/biomass_basic_addition_heat.csv")
    return
#%%
# -*- coding: utf-8 -*-

def gas_addition_and_removal():
    """
    Created on Thu Jun 26 16:42:46 2025
    
    @author: 86435
    """
    
    import pandas as pd
     # Iss sy upar legacy generator wala part add krna hy agr wohnung wali file sy kam na bna tou.
     # wrna wohnung file sy values ly kr usko iss csv a accordingly bna dena hy
    
    data = pd.read_csv("D:/project_h2/data/heating_techs/Gas_Heating_Technologies.csv")
    
    
    # Remove ' heat' from bus names
    data['bus'] = data['bus'].str.replace(' heat', '', regex=False)
    
    # Prepare data for removal file
    data.rename(columns={'decommissioning_year': 'year_removed'}, inplace=True)
    removal = data[['year_removed', 'carrier', 'p_nom', 'bus']]
    
    
    # Group and process the data for each removal year
    years_res = sorted(removal.year_removed.unique())
    remove = pd.DataFrame(columns=removal.columns)
    
    for yr in years_res:
        dat = removal[removal.year_removed == yr]
        df = dat.groupby(['year_removed', 'bus', 'carrier']).sum().sum(level=['year_removed', 'bus', 'carrier']).unstack('year_removed').fillna(0).reset_index()
        df['year'] = df.columns[2][1]
        df.columns = ['bus', 'carrier', 'p_nom', 'year_removed']
        remove = pd.concat([df, remove], ignore_index=False)
    
    # Final formatting and save
    remove.index = remove.bus + ' ' + remove.carrier
    output_path = "D:/project_h2/Networks/elec_s_4_ec_lcopt_Co2L-1H-Ep-CCL/gas_basic_removal_heat.csv"
    remove.to_csv(output_path)
    
    correct = remove.groupby(['carrier', 'bus']).agg({'p_nom': ['sum']})
    correct = correct.stack().reset_index()
    correct = correct[['carrier', 'p_nom', 'bus']]
    correct.index = correct.bus + ' ' + correct.carrier
    
    correct.to_csv("D:/project_h2/Networks/elec_s_4_ec_lcopt_Co2L-1H-Ep-CCL/gas_basic_addition_heat.csv")
    return

#%%
def oil_addition_and_removal():
    """
    Created on Thu Jun 26 16:42:46 2025
    
    @author: 86435
    """
    
    import pandas as pd
     # Iss sy upar legacy generator wala part add krna hy agr wohnung wali file sy kam na bna tou.
     # wrna wohnung file sy values ly kr usko iss csv a accordingly bna dena hy
    
    data = pd.read_csv("D:/project_h2/data/heating_techs/Oil_Heating_Technologies.csv")
    
    
    # Remove ' heat' from bus names
    data['bus'] = data['bus'].str.replace(' heat', '', regex=False)
    
    # Prepare data for removal file
    data.rename(columns={'decommissioning_year': 'year_removed'}, inplace=True)
    removal = data[['year_removed', 'carrier', 'p_nom', 'bus']]
    
    
    # Group and process the data for each removal year
    years_res = sorted(removal.year_removed.unique())
    remove = pd.DataFrame(columns=removal.columns)
    
    for yr in years_res:
        dat = removal[removal.year_removed == yr]
        df = dat.groupby(['year_removed', 'bus', 'carrier']).sum().sum(level=['year_removed', 'bus', 'carrier']).unstack('year_removed').fillna(0).reset_index()
        df['year'] = df.columns[2][1]
        df.columns = ['bus', 'carrier', 'p_nom', 'year_removed']
        remove = pd.concat([df, remove], ignore_index=False)
    
    # Final formatting and save
    remove.index = remove.bus + ' ' + remove.carrier
    output_path = "D:/project_h2/Networks/elec_s_4_ec_lcopt_Co2L-1H-Ep-CCL/oil_basic_removal_heat.csv"
    remove.to_csv(output_path)
    
    correct = remove.groupby(['carrier', 'bus']).agg({'p_nom': ['sum']})
    correct = correct.stack().reset_index()
    correct = correct[['carrier', 'p_nom', 'bus']]
    correct.index = correct.bus + ' ' + correct.carrier
    
    correct.to_csv("D:/project_h2/Networks/elec_s_4_ec_lcopt_Co2L-1H-Ep-CCL/oil_basic_addition_heat.csv")
    return

# oil_addition_and_removal()

#%%
def dummy_heatpumps():
    # Regional residential heat demand in MWh (converted to TWh)
    regional_demand_TWh = {
        "DE0 2 heat": 2.237750e+08 / 1e6,
        "DE0 9 heat": 1.401345e+08 / 1e6,
        "DE0 A heat": 2.693371e+08 / 1e6,
        "DE0 E heat": 1.333434e+08 / 1e6
    }

    # Define heat pump share projections from 2020 to 2050
    years = np.arange(2020, 2051)
    share_projection = pd.Series(index=years, dtype=float)

    # Set known targets
    share_projection[2020] = 0.02
    share_projection[2023] = 0.079
    share_projection[2030] = 0.24
    share_projection[2040] = 0.38
    share_projection[2050] = 0.48

    # Interpolate missing years
    share_projection = share_projection.interpolate(method='linear')

    # Assumptions
    cop_air = 3.0
    cop_gr = 4.0
    capacity_factor = 0.35
    lifetime_air = 20
    lifetime_gr = 25

    entries = []

    for bus, annual_demand in regional_demand_TWh.items():
        for year in years:
            total_share = share_projection[year]
            air_share = 0.9 if year <= 2030 else 0.7
            ground_share = 1 - air_share

            # AIR-SOURCE
            air_demand_TWh = annual_demand * total_share * air_share
            air_p_nom = round((air_demand_TWh * 1e6 / cop_air) / (8760 * capacity_factor), 2)

            # AIR-SOURCE
            n_units_air = int(round(air_demand_TWh * 1e6 / 20000))  # 20,000 kWh per home
            entries.append({
                "bus": bus,
                "technology": "air_source_heat_pump",
                "year_added": year,
                "heat_share": total_share * air_share,
                "demand_TWh": air_demand_TWh,
                "p_nom": air_p_nom,
                "p_nom_max": round(air_p_nom * 1.2, 2),
                "n_units": n_units_air,
                "remaining_lifetime": lifetime_air,
                "decommissioning_year": year + lifetime_air,
                "carrier": "air_source_heat_pump"
            })


            # GROUND-SOURCE
            ground_demand_TWh = annual_demand * total_share * ground_share
            ground_p_nom = round((ground_demand_TWh * 1e6 / cop_gr) / (8760 * capacity_factor), 2)

            # GROUND-SOURCE
            n_units_gr = int(round(ground_demand_TWh * 1e6 / 20000))  # 20,000 kWh per home
            entries.append({
                "bus": bus,
                "technology": "ground_source_heat_pump",
                "year_added": year,
                "heat_share": total_share * ground_share,
                "demand_TWh": ground_demand_TWh,
                "p_nom": ground_p_nom,
                "p_nom_max": round(ground_p_nom * 1.2, 2),
                "n_units": n_units_gr,
                "remaining_lifetime": lifetime_gr,
                "decommissioning_year": year + lifetime_gr,
                "carrier": "ground_source_heat_pump"
            })


    df_hp = pd.DataFrame(entries)
    
    df_hp.to_csv("D:/project_h2/data/heating_techs/dummy_heatpumps.csv", index=False)
    
    return
        
dummy_heatpumps()
#%%

import pandas as pd
def heatpump_addition_and_removal():
    # Load the updated dummy heatpump data with both air and ground source types
    data = pd.read_csv("D:/project_h2/data/heating_techs/dummy_heatpumps.csv")

    # Clean bus names: remove ' heat' if present
    data['bus'] = data['bus'].str.replace(' heat', '', regex=False)

    # Prepare data for removal
    data.rename(columns={'decommissioning_year': 'year_removed'}, inplace=True)
    removal = data[['year_removed', 'carrier', 'p_nom', 'bus']]

    # Group and structure data for removal file
    years_res = sorted(removal.year_removed.unique())
    remove = pd.DataFrame(columns=removal.columns)

    for yr in years_res:
        dat = removal[removal.year_removed == yr]
        df = dat.groupby(['year_removed', 'bus', 'carrier']).sum().sum(level=['year_removed', 'bus', 'carrier']).unstack('year_removed').fillna(0).reset_index()
        df['year'] = df.columns[2][1]
        df.columns = ['bus', 'carrier', 'p_nom', 'year_removed']
        remove = pd.concat([df, remove], ignore_index=False)

    # Final formatting and save
    remove.index = remove.bus + ' ' + remove.carrier
    removal_path = "D:/project_h2/Networks/elec_s_4_ec_lcopt_Co2L-1H-Ep-CCL/heatpump_basic_removal_heat.csv"
    remove.to_csv(removal_path)

    # Create and save addition file
    base_year = 2020
    correct = data[data["year_added"] == base_year].groupby(['carrier', 'bus']).agg({'p_nom': 'sum'}).reset_index()

    # correct = remove.groupby(['carrier', 'bus']).agg({'p_nom': ['sum']})
    # correct = correct.stack().reset_index()
    # correct = correct[['carrier', 'p_nom', 'bus']]
    # correct.index = correct.bus + ' ' + correct.carrier

    addition_path = "D:/project_h2/Networks/elec_s_4_ec_lcopt_Co2L-1H-Ep-CCL/heatpump_basic_addition_heat.csv"
    correct.to_csv(addition_path)


    return removal_path, addition_path

# Run the function to create the files
heatpump_addition_and_removal()

#%%
def dummy_solar_thermal():
    # Regional residential heat demand in MWh (converted to TWh)
    regional_demand_TWh = {
        "DE0 2 heat": 2.237750e+08 / 1e6,
        "DE0 9 heat": 1.401345e+08 / 1e6,
        "DE0 A heat": 2.693371e+08 / 1e6,
        "DE0 E heat": 1.333434e+08 / 1e6
    }

    # Define solar thermal share projections from 2020 to 2050
    years = np.arange(2020, 2051)
    share_projection = pd.Series(index=years, dtype=float)

    # Set known targets
    share_projection[2020] = 0.01
    share_projection[2050] = 0.10

    # Interpolate missing years
    share_projection = share_projection.interpolate(method='linear')

    # Assumptions
    capacity_factor = 0.15  # Typical for solar thermal systems in Germany
    lifetime = 25
    cop = 1.0  # For thermal systems, efficiency is not COP-based, assume 100%

    entries = []

    for bus, annual_demand in regional_demand_TWh.items():
        for year in years:
            share = share_projection[year]
            solar_demand_TWh = annual_demand * share
            p_nom = round((solar_demand_TWh * 1e6) / (8760 * capacity_factor), 2)
            n_units = int(round(solar_demand_TWh * 1e6 / 20000))  # assume 20,000 kWh per installation

            entries.append({
                "bus": bus,
                "technology": "solar_thermal",
                "year_added": year,
                "heat_share": share,
                "demand_TWh": solar_demand_TWh,
                "p_nom": p_nom,
                "p_nom_max": round(p_nom * 1.2, 2),
                "n_units": n_units,
                "remaining_lifetime": lifetime,
                "decommissioning_year": year + lifetime,
                "carrier": "solar_thermal"
            })

    df_solar = pd.DataFrame(entries)
    output_path = "D:/project_h2/data/heating_techs/dummy_solar_thermal.csv"
    df_solar.to_csv(output_path, index=False)


dummy_solar_thermal()


def solar_thermal_addition_and_removal():
    # Load the dummy solar thermal dataset
    data = pd.read_csv("D:/project_h2/data/heating_techs/dummy_solar_thermal.csv")

    # Clean bus names: remove ' heat' if present
    data['bus'] = data['bus'].str.replace(' heat', '', regex=False)

    # Prepare data for removal
    data.rename(columns={'decommissioning_year': 'year_removed'}, inplace=True)
    removal = data[['year_removed', 'carrier', 'p_nom', 'bus']]

    # Group and structure data for removal file
    years_res = sorted(removal.year_removed.unique())
    remove = pd.DataFrame(columns=removal.columns)

    for yr in years_res:
        dat = removal[removal.year_removed == yr]
        df = dat.groupby(['year_removed', 'bus', 'carrier']).sum().sum(level=['year_removed', 'bus', 'carrier']).unstack('year_removed').fillna(0).reset_index()
        df['year'] = df.columns[2][1]
        df.columns = ['bus', 'carrier', 'p_nom', 'year_removed']
        remove = pd.concat([df, remove], ignore_index=False)

    # Final formatting and save
    remove.index = remove.bus + ' ' + remove.carrier
    removal_path = "D:/project_h2/Networks/elec_s_4_ec_lcopt_Co2L-1H-Ep-CCL/solar_thermal_basic_removal_heat.csv"
    remove.to_csv(removal_path)

    # Create and save addition file
    correct = remove.groupby(['carrier', 'bus']).agg({'p_nom': ['sum']})
    correct = correct.stack().reset_index()
    correct = correct[['carrier', 'p_nom', 'bus']]
    correct.index = correct.bus + ' ' + correct.carrier
    addition_path = "D:/project_h2/Networks/elec_s_4_ec_lcopt_Co2L-1H-Ep-CCL/solar_thermal_basic_addition_heat.csv"
    correct.to_csv(addition_path)

    return removal_path, addition_path

solar_thermal_addition_and_removal()

