fossil_tech_data = {
    "technology": ["oil_burner", "biomass_burner", "gas_burner"],
    "capex": [1050, 1200, 1000],
    "lifetime": [20, 20, 20],
    "efficiency": [0.9, 0.85, 0.92],
    "fom": [0.02, 0.03, 0.02],
    "vom": [70, 50, 60],
    "carrier": ["oil", "biomass", "gas"],
    "cop": [None, None, None],
    "renewable": [0, 1, 0],
    "p_nom_min": [0, 0, 0],
    "p_nom_max": [49102.21, 9820.44, 135031.07]
}
fossil_df = pd.DataFrame(fossil_tech_data)