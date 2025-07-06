import pandas as pd


tech_data = {
    "technology": ["oil_burner", "heat_pump", "biomass_burner", "gas_burner", "coal_burner"],
                
                    "capex": [1050, 800, 1200, 1000, 900],
                "lifetime": [20, 20, 20, 20, 20],
                "efficiency": [0.9, 3, 0.85, 0.92, 0.88],
                "fom": [0.02, 0.02, 0.03, 0.02, 0.025],
                "vom": [70, 0, 50, 60, 45],
                "carrier": ["oil", "AC", "biomass", "gas", "coal"],
                "cop": [None, 3, None, None, None],
                "renewable": [0, 1, 1, 0, 0],
                "p_nom_max": [180112, 5058, 180644, 50000, 60000], #69112, 11058, 27644, 138224
                "p_nom_min": [0, 0, 0, 0, 0]
}

tech_df = pd.DataFrame(tech_data)
def init_heating_sector(n, heat_demand_df, discount_rate=0.04):

    # Add heat buses and loads
    for bus in heat_demand_df.columns:
        heat_bus = f"{bus} heat"
        if heat_bus not in n.buses.index:
            n.add("Bus", heat_bus, x=n.buses.at[bus, 'x'], y=n.buses.at[bus, 'y'], carrier="heat")
        n.add("Load", f"{bus} heat_residential", bus=heat_bus, p_set=heat_demand_df[bus], carrier="heat")
        # when 1% increment of electricity is applied, this load is also affected





# Updated link-adding loop with individual additions for clarity

def update_heating_technologies(n, year, heat_demand_df, discount_rate=0.04):
    # Calculate annuity
    r = discount_rate
    tech_df["annuity"] = r / (1 - 1 / (1 + r) ** tech_df["lifetime"])
    peak_heat_demand = heat_demand_df.max().sum()

    for _, row in tech_df.iterrows():
        technology = row["technology"]
        carrier = row["carrier"] #this is not effective because carrier names for links show up as 
  #link's name instead of carrier so added manual change of names later

        capex = row["capex"]
        efficiency = row["efficiency"]
        annuity = row["annuity"]
        fom = row["fom"]
        vom = row["vom"]
        cop = row.get("cop", None)
        p_nom_max = row["p_nom_max"]

        for bus in heat_demand_df.columns:
            heat_bus = f"{bus} heat"
            name = f"{bus} {technology}"

            if technology == "heat_pump":
                if year <= 2022:
                    max_share = 0.04 + 0.015 * (year - 2020)
                elif year <= 2025:
                    max_share = 0.04 + 0.015 * (year - 2020)
                elif year <= 2030:
                    max_share = 0.04 + 0.015 * 3 + 0.03 * (year - 2025)
                else:
                    max_share = 1.0
                p_nom_max = p_nom_max * max_share
            else:
                p_nom_max = p_nom_max

            capital_cost = capex * annuity + capex * fom
            tech_efficiency = cop if pd.notnull(cop) else efficiency

# Adding biomass and oil Buses for adding links, heatpump is connected to already existed AC buses,
# and gas link is added on already existed gas buses whose fuel source is gas_import generator

            if carrier == "gas": 
                fuel_bus = f"{bus} gas" 
            elif technology == "heat_pump":  #what if i do carrier = AC 
                fuel_bus = bus
            else:
                fuel_bus = f"{bus} {carrier}"
                if fuel_bus not in n.buses.index:
                    n.add("Bus", name=fuel_bus, carrier=carrier,
                          x=n.buses.at[bus, 'x'], y=n.buses.at[bus, 'y'])
                    
 #Adding BIOMASS store if applicable
                # === BIOMASS ===
                if carrier == "biomass":
                    store_bus = f"{bus} biomass store"
                    store_name = f"{fuel_bus} store"
            
                    if store_bus not in n.buses.index:
                        n.add("Bus", name=store_bus, carrier="biomass",
                              x=n.buses.at[bus, 'x'], y=n.buses.at[bus, 'y'])
            
                    if store_name not in n.stores.index:
                        n.add("Store",
                              name=store_name,
                              bus=store_bus,
                              e_nom=1e6,
                              e_initial=1e6,
                              e_cyclic=True,
                              carrier="biomass")
            
                        n.add("Link",
                              name=f"{bus} biomass_supply",
                              bus0=store_bus,
                              bus1=fuel_bus,
                              efficiency=1.0,
                              p_nom_extendable=True,
                              marginal_cost=0.0,
                              carrier="biomass")
            
                # === OIL ===
                if carrier == "oil":
                    store_bus = f"{bus} oil store"
                    store_name = f"{fuel_bus} store"
            
                    if store_bus not in n.buses.index:
                        n.add("Bus", name=store_bus, carrier="oil",
                              x=n.buses.at[bus, 'x'], y=n.buses.at[bus, 'y'])
            
                    if store_name not in n.stores.index:
                        n.add("Store",
                              name=store_name,
                              bus=store_bus,
                              e_nom=1e6,
                              e_initial=1e6,
                              e_cyclic=True,
                              carrier="oil")

                        n.add("Link",
                              name=f"{bus} oil_supply",
                              bus0=store_bus,
                              bus1=fuel_bus,
                              efficiency=1.0,
                              p_nom_extendable=True,
                              marginal_cost=0.0,
                              carrier="oil")
# Adding coal
                if carrier == "coal":
                    store_bus = f"{bus} coal store"
                    store_name = f"{fuel_bus} store"
                
                    if store_bus not in n.buses.index:
                        n.add("Bus", name=store_bus, carrier="coal",
                              x=n.buses.at[bus, 'x'], y=n.buses.at[bus, 'y'])
                
                    if store_name not in n.stores.index:
                        n.add("Store",
                              name=store_name,
                              bus=store_bus,
                              e_nom=1e6,
                              e_initial=1e6,
                              e_cyclic=True,
                              carrier="coal")
                
                        n.add("Link",
                              name=f"{bus} coal_supply",
                              bus0=store_bus,
                              bus1=fuel_bus,
                              efficiency=1.0,
                              p_nom_extendable=True,
                              marginal_cost=0.0,
                              carrier="coal")


# Adding links
            # name is name = f"{bus} {technology}"
            if name not in n.links.index:
                n.add("Link", name=name,
                      bus0=fuel_bus, bus1=heat_bus,
                      efficiency=tech_efficiency,
                      p_nom_extendable=True,
                      capital_cost=capital_cost,
                      marginal_cost=vom,
                      carrier=carrier,
                      p_nom_max=p_nom_max,
                      p_nom_min=row["p_nom_min"])
            else:
                n.links.loc[name, "p_nom_max"] = p_nom_max
                

            if technology == "heat_pump":
                if "p_max_pu" not in n.links_t:
                    n.links_t["p_max_pu"] = pd.DataFrame(1.0, index=n.snapshots, columns=n.links.index)
                n.links_t["p_max_pu"].loc[:, name] = 0.5 #1.0 means 100 percent heatpump useability
                    
                ''' 
                          
# Adding fallback backup heaters (one per region)
    if "backup_heat" not in n.carriers.index:
        n.add("Carrier", "backup_heat")

    for bus in heat_demand_df.columns:
        heat_bus = f"{bus} heat"
        name = f"{bus} backup_heater"

        if name not in n.links.index:
            n.add("Link",
                  name=name,
                  bus0=bus,              
                  bus1=heat_bus,         
                  carrier="backup_heat",
                  efficiency=0.9,
                  capital_cost=50000,
                  p_nom_extendable=True,
                  marginal_cost=1e5)'''

    for name in n.links.index:
        if "heat_pump" in name:
            n.links.loc[name, 'carrier'] = 'AC'
        elif "gas_boiler" in name:
            n.links.loc[name, 'carrier'] = 'gas'
        elif "oil_boiler" in name:
            n.links.loc[name, 'carrier'] = 'oil'
        elif "biomass_boiler" in name:
            n.links.loc[name, 'carrier'] = 'biomass'
        elif "coal_burner" in name:
            n.links.loc[name, 'carrier'] = 'coal'
        
        elif "backup_heater" in name:
            n.links.loc[name, 'carrier'] = 'backup_heat'


    return n
"""
The init_heating_sector function initializes the heating layer of a PyPSA network by 
adding dedicated heat buses and associated residential heat loads for each spatial 
location (e.g., region or bus) represented in the heat demand DataFrame. These heat buses 
decouple electricity from thermal energy, enabling more accurate modeling of sector coupling.
 Each bus receives a load time series based on the provided demand data.

The update_heating_technologies function integrates and configures specific heating 
technologies (e.g., heat pumps, gas/oil/biomass boilers) into the network as Link components.
 Using a predefined DataFrame of technical and economic parameters for each technology, 
 it adds the appropriate fuel buses (if missing), sets technology-specific constraints 
 such as efficiency, cost, and installable capacity, and ensures proper classification via 
 the carrier attribute. This function supports dynamic constraint scaling over time 
 (e.g., gradual adoption of heat pumps) and prepares the network for optimization by 
 linking heating supply with demand through sector-coupled links.
"""