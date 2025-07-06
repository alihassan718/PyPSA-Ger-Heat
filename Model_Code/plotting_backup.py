# -*- coding: utf-8 -*-
"""
© Anas Abuzayed 2025

This module contains functions for visualization and plotting of results, such as
pie charts for generation mixes, bar charts for installations, and geographic maps
of the PyPSA network.
"""

import pypsa
import glob
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import matplotlib as mpl
from matplotlib.offsetbox import AnchoredText
import numpy as np
import os
import yaml


def pie_exp(data):
    df = pd.DataFrame({'carrier': ['gas', 'CCGT', 'OCGT', 'biomass',
                                   'coal', 'lignite', 'nuclear', 'offwind-ac',
                                   'offwind-dc', 'oil', 'onwind', 'ror',
                                   'solar', 'H2-local', 'H2-import',
                                   'fuel cell', 'electrolysis', 'imports_exports'],
                         'exp':[0,0,0,0,0,0,0,0.1,0.1,0,
                                0.1,0.1,0.1,0.1,0.1,
                                0.1,0.1,0.1]})
    d=[]
    for i in range(len(data)):
        d.append(list(df.exp[df.carrier==data.index[i]])[0])
    return d

def pie_chart(n,year,clusters,colors):
    """ 
    Generates a pie chart of generation shares by carrier for the specified year.

    Parameters:
    -----------
    n : Network
        The network object containing generator data.
    year : int
        The year for which the generation shares are calculated.

    Returns:
    --------
    float
        The percentage of generation from renewable sources.
    """
    
    p_by_carrier = pd.DataFrame(
        index=n.generators_t.p[
            n.generators.index [(n.generators.carrier!='load')
                                &
                           (n.generators.carrier!='H2')
                           &
                           (n.generators.carrier!='gas')
                           & (n.generators.carrier!='imports_exports') 
                           & (n.generators.carrier!= 'imports_exports_conv') 
                           & (n.generators.carrier!= 'imports_exports_res')]].columns, 
        columns=['p_by_carrier'])
    p_by_carrier.p_by_carrier= n.generators_t.p.sum()
    p_by_carrier.p_by_carrier*=int(8760/len(n.snapshots))
    
    new_gen=pd.DataFrame(p_by_carrier.groupby(
        n.generators.carrier).sum())
    new_gen.columns=['gens']
    
    indices=[elem for elem in n.links.index if 'CCGT' in elem]
    new_gen.loc['CCGT','gens']=n.links_t.p1[indices].sum().sum()*-1
    indices=[elem for elem in n.links.index if 'OCGT' in elem]
    new_gen.loc['OCGT','gens']=n.links_t.p1[indices].sum().sum()*-1
    
    
    new_gen.loc['H2-import','gens']=n.generators_t.p[
        n.generators.index[n.generators.carrier=='H2']].sum().sum()

    indices=[elem for elem in n.links.index if 'electrolysis' in elem]
    new_gen.loc['H2-local','gens']=n.links_t.p1[indices].sum().sum()*-1

    perc=(new_gen.loc['solar']+new_gen.loc['onwind']+new_gen.loc['offwind-ac']+
          new_gen.loc['offwind-dc']+new_gen.loc['ror'])/new_gen.sum()

    new_gen=new_gen[(new_gen/new_gen.sum())>0.01].dropna()
    

    colors = [colors[col] for col in new_gen.index]
    explode = pie_exp(new_gen)
    
    fig=plt.figure(figsize=(40, 10))
    plt.title('Generation shares year {} \n Renewables={}%'.format(year,round(perc*100,3)[0]),fontsize=20)
    patches, texts,junk = plt.pie(list(new_gen.gens),explode=explode, colors=colors,
                             autopct='%1.1f%%', shadow=True, startangle=140)
    plt.legend(patches, new_gen.index, loc="best")
    directory = 'Results/'+str(clusters)
    plt.savefig(f'{directory}/All Generation year {year}', dpi=300, bbox_inches='tight')
    plt.show()
    

    return round(perc*100,3)[0]

def installed_capacities(n, year, clusters,colors):
    """
    Calculates and plots the installed capacities by carrier for the specified year.

    Parameters:
    -----------
    n : Network
        The network object containing generator and link data.
    year : int
        The year for which the installed capacities are calculated.

    Returns:
    --------
    float
        The percentage of installed capacity from renewable sources.
    """
    
    df = pd.DataFrame({
        'p_nom': n.generators.p_nom[(n.generators.carrier != 'load') &
                                    (n.generators.carrier != 'H2') &
                                    (n.generators.carrier != 'gas') &
                                    (n.generators.carrier != 'imports')],
        'carrier': n.generators.carrier[(n.generators.carrier != 'load') &
                                        (n.generators.carrier != 'H2') &
                                        (n.generators.carrier != 'gas')&
                                        (n.generators.carrier != 'imports') ]
    })

    df =df[~df['carrier'].str.startswith('imports_')]
    
    summation = df.groupby('carrier').sum()
    
    indices = [elem for elem in n.links.index if 'CCGT' in elem]
    summation.loc['CCGT', 'p_nom'] = n.links.loc[indices, 'p_nom'].sum() * n.links.loc[indices, 'efficiency'].mean()
    
    indices = [elem for elem in n.links.index if 'OCGT' in elem]
    summation.loc['OCGT', 'p_nom'] = n.links.loc[indices, 'p_nom'].sum() * n.links.loc[indices, 'efficiency'].mean()
    
    indices = [elem for elem in n.links.index if 'electrolysis' in elem]
    summation.loc['electrolysis', 'p_nom'] = n.links.loc[indices, 'p_nom'].sum() * n.links.loc[indices, 'efficiency'].mean()
    
    indices = [elem for elem in n.links.index if 'fuel cell' in elem]
    summation.loc['fuel cell', 'p_nom'] = n.links.loc[indices, 'p_nom'].sum() * n.links.loc[indices, 'efficiency'].mean()
    
    # Calculate share of renewables
    shares = (summation.loc['solar'] + summation.loc['onwind'] +
              summation.loc['offwind-ac'] + summation.loc['offwind-dc'] +
              summation.loc['ror']) / sum(summation.p_nom)
    
    # Filter out small values for visualization
    summation = summation[(summation / summation.sum()) > 0.01].dropna()
    
    # Plot pie chart
    colors = [colors[col] for col in summation.index]
    explode = pie_exp(summation)
    fig = plt.figure(figsize=(40, 10))
    plt.title('Installed Capacity year {}\n Total= {} GW, Renewables={} %'.format(year,
              round(sum(summation.p_nom) / 1000, 3), round(shares.sum() * 100, 3)), fontsize=20)
    
    patches, texts, junk = plt.pie(list(summation.p_nom), explode=explode, colors=colors,
                                   autopct='%1.1f%%', shadow=True, startangle=140, textprops={'color': "w"})
    plt.legend(patches, summation.index, loc="best")

    directory = 'Results/'+str(clusters)
    if not os.path.exists(directory):
        os.makedirs(directory)

    
    # Save the figure
    plt.savefig(f'{directory}/Installation_Shares_year_{year}.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return round(shares * 100, 3)

def storage_installation(n,bar,year):
    """ Updates the bar DataFrame with the installed storage capacities by carrier for the specified year.

    Parameters:
    -----------
    n : Network
        The network object containing storage unit data.
    bar : pd.DataFrame
        DataFrame to update with the storage installation data.
    year : int
        The year for which the storage capacities are being calculated and updated.

    Returns:
    --------
    pd.DataFrame
        Updated DataFrame with storage installation capacities by carrier.
        """ 

    stores=pd.DataFrame({'p_nom':n.storage_units.p_nom,'carrier':n.storage_units.carrier})
    summation=stores.groupby('carrier').sum()
    
    
    for p in range(len(summation.index)):
        bar.loc[year,summation.index[p]]=summation.loc[summation.index[p]][0] ## in MW

    bar=bar.sort_index(axis=0,ascending=True)

    return bar

def Gen_Bar(n,bar,year):
    """
    Updates the bar DataFrame with generation data by energy carrier for the specified year.

    This function calculates the generation for each carrier and updates the DataFrame with 
    the values for CCGT, OCGT, hydrogen-ready, electrolysis, and fuel cell contributions.

    Parameters:
    -----------
    n : Network
        The network object containing generator and link data.
    bar : pd.DataFrame
        DataFrame to update with the generation data by carrier.
    year : int
        The year for which the generation data is calculated.

    Returns:
    --------
    pd.DataFrame
        Updated DataFrame with generation values by carrier for the specified year.
        """
    new_gen = n.generators_t.p.groupby(n.generators.carrier,axis=1).sum().sum()
    
    
    bar.loc[year]=abs(new_gen/1e6)

    indices=[elem for elem in n.links.index if 'Gas_input' in elem]
    bar.loc[year,'CCGT']=n.links_t.p1[indices].sum().sum()/-1e6

    indices=[elem for elem in n.links.index if 'H2_input' in elem]
    bar.loc[year,'H2-Ready']=n.links_t.p1[indices].sum().sum()/-1e6

    indices=[elem for elem in n.links.index if 'OCGT' in elem]
    bar.loc[year,'OCGT']=n.links_t.p1[indices].sum().sum()/-1e6

    indices=[elem for elem in n.links.index if 'electrolysis' in elem]
    bar.loc[year,'electrolysis']=n.links_t.p1[indices].sum().sum()/-1e6

    indices=[elem for elem in n.links.index if 'fuel cell' in elem]
    bar.loc[year,'fuel cell']=n.links_t.p1[indices].sum().sum()/-1e6

    bar=abs(bar)

    return bar

def Gen_Bar(n,bar,year):
    """
    Updates the bar DataFrame with generation data by energy carrier for the specified year.

    This function calculates the generation for each carrier and updates the DataFrame with 
    the values for CCGT, OCGT, hydrogen-ready, electrolysis, and fuel cell contributions.

    Parameters:
    -----------
    n : Network
        The network object containing generator and link data.
    bar : pd.DataFrame
        DataFrame to update with the generation data by carrier.
    year : int
        The year for which the generation data is calculated.

    Returns:
    --------
    pd.DataFrame
        Updated DataFrame with generation values by carrier for the specified year.
        """
    new_gen = n.generators_t.p.groupby(n.generators.carrier,axis=1).sum().sum()
    
    
    bar.loc[year]=abs(new_gen/1e6)

    indices=[elem for elem in n.links.index if 'Gas_input' in elem]
    bar.loc[year,'CCGT']=n.links_t.p1[indices].sum().sum()/-1e6

    indices=[elem for elem in n.links.index if 'H2_input' in elem]
    bar.loc[year,'H2-Ready']=n.links_t.p1[indices].sum().sum()/-1e6

    indices=[elem for elem in n.links.index if 'OCGT' in elem]
    bar.loc[year,'OCGT']=n.links_t.p1[indices].sum().sum()/-1e6

    indices=[elem for elem in n.links.index if 'electrolysis' in elem]
    bar.loc[year,'electrolysis']=n.links_t.p1[indices].sum().sum()/-1e6

    indices=[elem for elem in n.links.index if 'fuel cell' in elem]
    bar.loc[year,'fuel cell']=n.links_t.p1[indices].sum().sum()/-1e6

    bar=abs(bar)

    return bar

def Inst_Bar(n,bar,year):
    
    df=pd.DataFrame({'p_nom':n.generators.p_nom[n.generators.carrier!='load'],'carrier':n.generators.carrier[n.generators.carrier!='load']})
    summation=df.groupby('carrier').sum()
    
    for p in range(len(summation.index)):
        bar.loc[year,summation.index[p]]=summation.loc[summation.index[p]][0]/10**3

    bar=bar.sort_index(axis=0,ascending=True)
    
    
    indices=[elem for elem in n.links.index if 'CCGT' in elem]
    bar.loc[year,'CCGT']=n.links.loc[indices,'p_nom'].sum() * n.links.loc[indices,'efficiency'].mean()/1e3

    indices=[elem for elem in n.links.index if 'OCGT' in elem]
    bar.loc[year,'OCGT']=n.links.loc[indices,'p_nom'].sum() * n.links.loc[indices,'efficiency'].mean()/1e3

    indices=[elem for elem in n.links.index if 'H2_input' in elem]
    bar.loc[year,'H2-Ready']=n.links.loc[indices,'p_nom'].sum() * n.links.loc[indices,'efficiency'].mean()/1e3

    indices=[elem for elem in n.links.index if 'electrolysis' in elem]
    bar.loc[year,'electrolysis']=n.links.loc[indices,'p_nom'].sum() * n.links.loc[indices,'efficiency'].mean()/1e3

    indices=[elem for elem in n.links.index if 'fuel cell' in elem]
    bar.loc[year,'fuel cell']=n.links.loc[indices,'p_nom'].sum() * n.links.loc[indices,'efficiency'].mean()/1e3

    return bar

def Bar_to_PNG(bar,name,bar_type,colors):
    
#    bar=bar.sort_index(axis=0,ascending=True)
    
    cols = list(bar.columns.values) 
    cols.pop(cols.index('solar')) 
    cols.pop(cols.index('offwind-dc'))
    cols.pop(cols.index('offwind-ac'))
    cols.pop(cols.index('onwind'))
    cols.pop(cols.index('ror'))
    cols.pop(cols.index('oil'))
    cols.pop(cols.index('coal'))
    cols.pop(cols.index('lignite'))

    if bar_type =='Generation':
        unit='TWh'
        # bar*=int(8760/len(n.snapshots))
        bar= bar[ ['lignite','coal', 'oil'] + cols + ['ror','offwind-ac','offwind-dc','onwind','solar']]

    if bar_type =='Installation':
        unit='GW'
        bar= bar [ ['lignite','coal', 'oil'] + cols + ['ror','offwind-ac','offwind-dc','onwind','solar']]

    try: 
        bar.drop('H2',axis=1,inplace=True)
        bar.drop('gas',axis=1,inplace=True)
        bar.drop('load',axis=1,inplace=True)

    except:
        pass
    ax = bar.plot(figsize=(40, 10), kind='bar', stacked=True,
                  color=[colors[col] for col in bar.columns],
                  fontsize=15)
    ax.set_xlabel("Years", fontsize=15)
    ax.set_ylabel("{} [{}]".format(bar_type, unit), fontsize=15)
    ax.grid()
    ax.set_title('{} shares'.format(bar_type), fontsize=30)
    plt.savefig('{}/{} Bar Plot'.format(name, bar_type), dpi=300, bbox_inches='tight')
    bar.to_csv('{}/{}_Bar.csv'.format(name, bar_type))


def Storage_Bar (bar,name,colors):
    colors = [colors[col] for col in bar.columns]
    
    ax = (bar/10e2).plot(figsize=(40, 10),kind='bar', stacked=True,color=colors,fontsize=15)
    ax.set_xlabel("Years",fontsize=15)
    ax.set_ylabel("Installation [GW]",fontsize=15)
    ax.grid()
    plt.legend(fontsize=20)
    ax.set_title('Large Scale Storage in Germany',fontsize=30)
    plt.savefig('{}/Storage Bar Plot '.format(name), dpi=300, bbox_inches='tight')
    bar.to_csv('{}/Storage_Bar.csv'.format(name))


def Country_Map(n,year,config,clusters):
    opts = config['plotting']
    map_figsize = [10,10]#opts['map']['figsize']
    map_boundaries = opts['map']['boundaries']
    to_rgba = mpl.colors.colorConverter.to_rgba

    line_colors = {'cur': "purple",
                   'exp': mpl.colors.rgb2hex(to_rgba("red", 0.7), True)}
    tech_colors = opts['tech_colors']
    gen_c=n.generators.copy()
    gen_c.drop(n.generators.index[(n.generators.carrier=='load')
                                  |(n.generators.carrier=='H2')|
                                  (n.generators.carrier=='gas')|
                                  (n.generators.carrier== 'imports_exports')|
                                  (n.generators.carrier == 'imports_exports_conv')|
                                  (n.generators.carrier == 'imports_exports_res')],inplace=True)
    
    indices=[elem for elem in n.links.index if 'CCGT' in elem]
    indices.extend([elem for elem in n.links.index if 'OCGT' in elem])
    links_c=n.links.loc[
        indices,['bus1','p_nom','efficiency','carrier']].copy()
    
    links_c['p_nom']*=links_c['efficiency']
    links_c.rename(columns={'bus1':'bus'},inplace=True)
    
    gen_c= pd.concat([gen_c,links_c])
    bus_sizes = (gen_c.groupby(['bus', 'carrier']).p_nom.sum())
    line_widths_exp =  n.lines.s_nom_opt

    attribute='p_nom'
    linewidth_factor = opts['map'][attribute]['linewidth_factor']
    bus_size_factor  = opts['map'][attribute]['bus_size_factor']
    
    bus=[]
    car=[]
    for i in bus_sizes.index:
        bus.append(i[0])
        car.append(i[1])
    txt=pd.DataFrame({'Bus':bus,'Carrier':car,'P':bus_sizes})
    txt.index=range(len(bus))
    txt.drop(txt.index[(txt.Carrier=='H2')|(txt.Carrier=='gas')],inplace=True)
    
    # summation=txt.groupby('Bus').sum()
    shares=txt.groupby('Carrier').P.sum()
    res=(shares['solar']+shares['offwind-ac']+shares['offwind-dc']+shares['onwind'])/shares.sum()
    

    map_boundaries=[5,15,46,55]
    n_plo=n.copy()

    fig, ax = plt.subplots(figsize=map_figsize, subplot_kw={"projection": ccrs.PlateCarree()})
    n_plo.plot(line_widths=line_widths_exp/linewidth_factor,
               title='Installation Distribution, RES = {}%'.format(round(res*100,3)),
               line_colors=pd.Series(line_colors['exp'], n_plo.lines.index),
               bus_sizes=bus_sizes/(2.5*bus_size_factor),
               bus_colors=tech_colors,
               boundaries=map_boundaries,
               geomap=True,color_geomap=True,
               ax=ax)
    ax.add_artist(AnchoredText("{}".format(year), loc=2))
    ax.set_aspect('equal')
    ax.axis('off')
    directory = 'Results/'+str(clusters)
    plt.savefig(f'{directory}/Installation Map {year}', bbox_inches='tight')
    plt.show()

########################################################################## Heating sector

import os
import matplotlib.pyplot as plt

def pie_chart_heat_capacity(n, year, clusters, colors):
    """
    Plot heating capacity shares (including CHP/CCGT links with heat outputs).
    
    Parameters
    ----------
    n : pypsa.Network
        The PyPSA network object.
    year : int
        Year used in the title and filename.
    clusters : int or str
        Identifier for output directory.
    colors : dict
        Mapping of carriers to color codes.
    """
    # Identify links connected to heat buses
    heating_links = []

    for link_name, row in n.links.iterrows():
        if 'bus1' in row.index and isinstance(row['bus1'], str) and 'heat' in row['bus1']:
            heating_links.append(link_name)
        if 'bus2' in row.index and isinstance(row['bus2'], str) and 'heat' in row['bus2']:
            heating_links.append(link_name)
    
    heating_links_df = n.links.loc[heating_links]

    # Sum installed capacities by carrier
    p_by_carrier = heating_links_df.groupby("carrier")["p_nom_opt"].sum()

    # Filter out carriers with very small contributions (<1%)
    p_by_carrier = p_by_carrier[(p_by_carrier / p_by_carrier.sum()) > 0.01]
    
    # Replacing AC with Heat Pump
    p_by_carrier.index = p_by_carrier.index.str.replace("AC", "heat pump")
    # Assign colors
    plot_colors = [colors.get(c, 'green') for c in p_by_carrier.index]

    # Plot pie chart with legend
    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(p_by_carrier, colors=plot_colors, autopct='%1.1f%%',
        shadow=True, startangle=140)

    ax.legend(wedges, p_by_carrier.index, title="Heating Tech", loc="best")
    ax.set_title(f"Heating Capacity Shares {year}", fontsize=18)

    # Save figure
    directory = f"Results/{clusters}"
    os.makedirs(directory, exist_ok=True)
    fig.savefig(f"{directory}/Heating_Capacity_Share_{year}.png", dpi=300, bbox_inches='tight')
    plt.show()
    

    
    
def plot_heating_supply_shares(n, year, clusters, colors):
    """
    This function visualizes the share of total heat supply delivered by each heating technology (carrier) in a given year.
    It identifies all links in the network that deliver heat—those connected to heat buses—and calculates the total energy 
    supplied via those links over the simulation period. The function aggregates this energy by the link's carrier (e.g., gas,
    biomass, heat pump) to determine how much each technology contributed to meeting heat demand.

    Parameters
    ----------
    n : pypsa.Network
        The PyPSA network object.
    year : int
        Year for title and file name.
    clusters : int or str
        Clustering identifier for output directory.
    colors : dict
        Mapping of carriers to color codes.
    """
    heating_links = []

    for link_name, row in n.links.iterrows():
        if isinstance(row.get("bus1", ""), str) and "heat" in row["bus1"]:
            heating_links.append(link_name)
        elif isinstance(row.get("bus2", ""), str) and "heat" in row["bus2"]:
            heating_links.append(link_name)

    # Aggregate heat output by carrier
    p_by_carrier = {}

    for link in heating_links:
        carrier = n.links.at[link, "carrier"]
        if "bus1" in n.links.columns and "heat" in n.links.at[link, "bus1"]:
            power = -n.links_t.p1[link].sum()
        elif "bus2" in n.links.columns and "heat" in n.links.at[link, "bus2"]:
            power = -n.links_t.p2[link].sum()
        else:
            continue

        p_by_carrier[carrier] = p_by_carrier.get(carrier, 0) + power

    p_by_carrier = pd.Series(p_by_carrier)
    p_by_carrier = p_by_carrier[(p_by_carrier / p_by_carrier.sum()) > 0.01]
    # Replacing AC with Heatpump for legends
    p_by_carrier.index = p_by_carrier.index.str.replace("AC", "heat pump")

    plot_colors = [colors.get(c, "green") for c in p_by_carrier.index]

    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        p_by_carrier,
        colors=plot_colors,
        autopct='%1.1f%%',
        shadow=True,
        startangle=140
    )
    
    ax.legend(wedges, p_by_carrier.index, title="Heating Tech", loc="upper left", bbox_to_anchor=(1, 0.5))
    ax.set_title(f"Heating Share {year}", fontsize=18)
    fig.tight_layout()


    directory = f'Results/{clusters}'
    os.makedirs(directory, exist_ok=True)
    plt.savefig(f"{directory}/Heating_Share_{year}.png", dpi=300, bbox_inches='tight')
    plt.show()



def pie_chart_electric_gen(n, year, clusters, colors):
    """
    Plots the electricity-only generation shares, excluding heating-related links.

    Parameters:
    -----------
    n : Network
        The PyPSA network.
    year : int
        The year for which the plot is generated.
    clusters : int
        Number of clusters.
    colors : dict
        Mapping of carriers to colors.

    Returns:
    --------
    None
    """
    # Filter out heating-related links
    heating_links = pd.read_csv("data/heating_technologies.csv")["carrier"].dropna().unique()
    electricity_generators = n.generators[n.generators.carrier != 'load']

    # Sum electricity generation by carrier
    p_by_carrier = electricity_generators.groupby('carrier').apply(
        lambda g: n.generators_t.p[g.index].sum().sum() * (8760 / len(n.snapshots))
    )

    # Add CCGT and OCGT generation from links (excluding heating)
    for tech in ['CCGT', 'OCGT']:
        indices = [link for link in n.links.index if tech in link]
        p_by_carrier.loc[tech] = -n.links_t.p1[indices].sum().sum() * (8760 / len(n.snapshots))

    # Remove heating carriers
    p_by_carrier = p_by_carrier[~p_by_carrier.index.isin(heating_links)]
    
    # Filter small contributions
    p_by_carrier = p_by_carrier[(p_by_carrier / p_by_carrier.sum()) > 0.01]

    # Plot
    plot_colors = [colors.get(c, 'grey') for c in p_by_carrier.index]
    plt.figure(figsize=(8, 6))
    plt.pie(p_by_carrier, labels=p_by_carrier.index, colors=plot_colors, autopct='%1.1f%%', shadow=True, startangle=140)
    plt.title(f"Generation Share Only Electricity {year}", fontsize=18)
    plt.tight_layout()
    
    directory = 'Results/'+str(clusters)
    if not os.path.exists(directory):
        os.makedirs(directory)
    plt.savefig(f"{directory}/Electricity_Generation_Share_{year}.png", dpi=300, bbox_inches='tight')
    plt.show()
