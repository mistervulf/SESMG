import shapefile
import pandas as pd

def add_timesystem_to_scenario_file(timesystem_parameters):
    df_timesystem = pd.DataFrame([[
        timesystem_parameters['start_date'],
        timesystem_parameters['end_date'],
        timesystem_parameters['temporal_resolution'],
        timesystem_parameters['periods']
    ]],
        columns=['start date',
                 'end date',
                 'temporal resolution',
                 'periods'])
    return df_timesystem

def add_pv_to_scenario_file(shapefile, df_bus, df_links, df_sources, pv_parameters, bus_parameters):
    '''adds photovoltaic systems and the corresponding buses to the bus and source dataframes.'''

    # renames variable
    sf = shapefile

    for i in range(len(sf.records())):
        rec = sf.record(i)
        # Liest den Wert 'pv_monet' aus der shape-Datei aus
        pv_potential = rec['pv_monet']

        # Wird ausgeführt, wenn pv_potential größer 0 bzw. ungleich 'none' ist. => Also wenn es ein PV potential gibt
        if pv_potential:

            # Checks if the bus related to the pv system is already listed in the buses data frame. if not, the bus will be added
            # to the bus-dataframe
            contain_check = 'electricity_bus_' + str(rec['Siedlung']) in df_bus.values
            if contain_check == False:
                # Soll der Bus noch zum Dataframe hinzugefügt werden, wird hier ein entsprechender Eintrag definiert
                df = pd.DataFrame([[
                    ('electricity_bus_' + str(rec['Siedlung'])),
                    rec['Siedlung'],
                    1,
                    0,
                    1,
                    bus_parameters['electricity_shortage_costs'],
                    'x',
                ]],
                    columns=['label',
                             'comments',
                             'active',
                             'excess',
                             'shortage',
                             'shortage costs /(CU/kWh)',
                             'excess costs /(CU/kWh)']
                )

                # Der Eintrag wird zum bus-dataframe hizugefügt
                df_bus = df_bus.append(df, sort=False)


            contain_check = 'electricity_pv_bus_' + str(rec['Siedlung']) in df_bus.values
            if contain_check == False:
                # Soll der Bus noch zum Dataframe hinzugefügt werden, wird hier ein entsprechender Eintrag definiert
                df = pd.DataFrame([[
                    ('electricity_pv_bus_' + str(rec['Siedlung'])),
                    rec['Siedlung'],
                    1,
                    1,
                    0,
                    0,
                    bus_parameters['pv_excess_costs'],
                ]],
                    columns=['label',
                             'comments',
                             'active',
                             'excess',
                             'shortage',
                             'shortage costs /(CU/kWh)',
                             'excess costs /(CU/kWh)']
                )
                # Der Eintrag wird zum bus-dataframe hizugefügt
                df_bus = df_bus.append(df, sort=False)

                # Adds conection (link) to the main electricity bus
                df = pd.DataFrame([[
                                        ('pv_bus_electricity_bus_link_' + str(rec['Siedlung'])),
                                        rec['Siedlung'],
                                        1,
                                        'electricity_pv_bus_' + str(rec['Siedlung']),
                                        'electricity_bus_' + str(rec['Siedlung']),
                                        'directed',
                                        1,
                                        9999999999999999,
                                        0,
                                        0,
                                        0,
                                        0
                                        ]],
                                        columns=['label',
                                                 'comments',
                                                 'active',
                                                 'bus_1',
                                                 'bus_2',
                                                 '(un)directed',
                                                 'efficiency',
                                                 'existing capacity /(kW)',
                                                 'min. investment capacity /(kW)',
                                                 'max. investment capacity /(kW)',
                                                 'variable costs /(CU/kWh)',
                                                 'periodical costs /(CU/(kW a))',
                                                 ])
                # Der Eintrag wird zum link-dataframe hizugefügt
                df_links = df_links.append(df, sort=False)



            # Adds the photovoltaic-system with its properties to the sources-dataframe
            df = pd.DataFrame([[
                ('pv_system_' + str(rec['fid'])),
                rec['fid'],
                1,
                'electricity_pv_bus_' + str(rec['Siedlung']),
                'photovoltaic',
                pv_parameters['pv_variable_costs'],
                0,
                0,
                rec['pv_monet'],
                pv_parameters['pv_periodical_costs'],
                'x',
                'x',
                pv_parameters['pv_technology_database'],
                pv_parameters['pv_inverter_database'],
                pv_parameters['pv_modul_model'],
                pv_parameters['pv_inverter_model'],
                rec['pv_azimuth'],
                rec['pv_tilt'],
                pv_parameters['pv_albedo'],
                pv_parameters['pv_altitude'],
                pv_parameters['pv_latitude'],
                pv_parameters['pv_longitude']
            ]],
                columns=['label',
                         'comments',
                         'active',
                         'output',
                         'technology',
                         'variable costs /(CU/kWh)',
                         'existing capacity /(kW)',
                         'min. investment capacity /(kW)',
                         'max. investment capacity /(kW)',
                         'periodical costs /(CU/(kW a))',
                         'Turbine Model (Windpower ONLY)',
                         'Hub Height (Windpower ONLY)',
                         'technology database (PV ONLY)',
                         'inverter database (PV ONLY)',
                         'Modul Model (PV ONLY)',
                         'Inverter Model (PV ONLY)',
                         'Azimuth (PV ONLY)',
                         'Surface Tilt (PV ONLY)',
                         'Albedo (PV ONLY)',
                         'Altitude (PV ONLY)',
                         'Latitude (PV ONLY)',
                         'Longitude (PV ONLY)'])
            df_sources = df_sources.append(df, sort=False)


    return (df_bus, df_sources, df_links)

def add_electricity_demands_to_scenario_file(shapefile, df_bus, df_sinks, demand_parameters, bus_parameters):
    '''adds electricity demands and the corresponding buses to the bus and source dataframes.'''
    sf =  shapefile

    for i in range(len(sf.records())):
        rec = sf.record(i)

        inhabitants = rec['inhabitant']
        housing_units = rec['housing_un']

        if housing_units == 1:
            specific_demands = demand_parameters['demand_single_family_building']
        else:
            specific_demands = demand_parameters['demand_multi_family_building']

        # Die If-Schleife filtert leere Einträge und setzt für diese Element das Ergebnis auf 0
        if inhabitants and housing_units:
            # Berechnung des jährlichen Elektrizitätsbedarfs
            demand_per_unit = specific_demands[round((inhabitants/housing_units), 0)]
            annual_electricity_demand = housing_units * demand_per_unit
        else:
            annual_electricity_demand = 0

        # Existiert ein Elektrizitätsbedarf, sollen die entsprechenden Einträge in die Dataframes aufgenommen werden
        if annual_electricity_demand:
            # Checks if the bus related to the demand is already listed in the buses data frame. if not, the bus will be
            # added to the bus-dataframe
            contain_check = 'electricity_bus_' + str(rec['Siedlung']) in df_bus.values
            if contain_check == False:
                # Soll der Bus noch zum Dataframe hinzugefügt werden, wird hier ein entsprechender Eintrag definiert
                df = pd.DataFrame([[
                    ('electricity_bus_' + str(rec['Siedlung'])),
                    rec['Siedlung'],
                    1,
                    1,
                    1,
                    bus_parameters['electricity_shortage_costs'],
                    bus_parameters['electricity_excess_costs'],
                ]],
                    columns=['label',
                             'comments',
                             'active',
                             'excess',
                             'shortage',
                             'shortage costs /(CU/kWh)',
                             'excess costs /(CU/kWh)']
                )

                # Der Eintrag wird zum bus-dataframe hizugefügt
                df_bus = df_bus.append(df, sort=False)

            # Fügt den Bedarf als sink zum sinks-dataframe hinzu
            df = pd.DataFrame([[
                                    ('electricity_demand_' + str(rec['fid'])),
                                    rec['fid'],
                                    1,
                                    'electricity_bus_' + str(rec['Siedlung']),
                                    demand_parameters['residential_load_profile'],
                                    'x',
                                    annual_electricity_demand,
                                    rec['inhabitant'],
                                    demand_parameters['building_class'],
                                    demand_parameters['wind_class'],
                                    1
                                    ]],
                                    columns=['label',
                                             'comments',
                                             'active',
                                             'input',
                                             'load profile',
                                             'nominal value /(kW)',
                                             'annual demand /(kWh/a)',
                                             'occupants [RICHARDSON]',
                                             'building class [HEAT SLP ONLY]',
                                             'wind class [HEAT SLP ONLY]',
                                             'fixed'])
            df_sinks = df_sinks.append(df, sort=False)

    return (df_bus, df_sinks)

def add_heat_demands_to_scenario_file(shapefile, df_bus, df_sinks, demand_parameters, bus_parameters):
    '''adds heat demands and the corresponding buses to the bus and source dataframes.'''
    sf = shapefile

    for i in range(len(sf.records())):
        rec = sf.record(i)

        housing_units = rec['housing_un']
        year_of_construction = rec['year_of_co']

        # Die If-Schleife filtert leere Einträge und setzt für diese Element das Ergebnis auf 0
        if rec['Shape_Area'] and demand_parameters['NFA_coefficient'] and rec['floors']:
            net_floor_area = rec['Shape_Area'] * demand_parameters['NFA_coefficient'] * rec['floors']
        else:
            net_floor_area = 0


        demand_sfb = demand_parameters['demand_residential_building']

        demand = 0
        for year in demand_sfb:
            if year_of_construction and year_of_construction >= year:
                specific_demand = demand_sfb[year]

                for units in specific_demand:
                    if housing_units >= 1:
                        demand = specific_demand[units]
                    else:
                        break

            else:
                break

        annual_heat_demand = demand * net_floor_area



        # Existiert ein Wärmebedarf, sollen die entsprechenden Einträge in die Dataframes aufgenommen werden
        if annual_heat_demand:
            # Checks if the heat bus related to the demand is already listed in the buses data frame. if not, the bus will be
            # added to the bus-dataframe
            contain_check = 'heat_bus_' + str(rec['Siedlung']) in df_bus.values
            if contain_check == False:
                # Soll der Bus noch zum Dataframe hinzugefügt werden, wird hier ein entsprechender Eintrag definiert
                df = pd.DataFrame([[
                    ('heat_bus_' + str(rec['Siedlung'])),
                    rec['Siedlung'],
                    1,
                    1,
                    0,
                    'x',
                    bus_parameters['heat_excess_costs'],
                ]],
                    columns=['label',
                             'comments',
                             'active',
                             'excess',
                             'shortage',
                             'shortage costs /(CU/kWh)',
                             'excess costs /(CU/kWh)']
                )

                # Der Eintrag wird zum bus-dataframe hizugefügt
                df_bus = df_bus.append(df, sort=False)

            # Fügt den Bedarf als sink zum sinks-dataframe hinzu
            df = pd.DataFrame([[
                ('heat_demand_' + str(rec['fid'])),
                rec['fid'],
                1,
                'heat_bus_' + str(rec['Siedlung']),
                demand_parameters['residential_load_profile'],
                'x',
                annual_heat_demand,
                rec['inhabitant'],
                demand_parameters['building_class'],
                demand_parameters['wind_class'],
                1
            ]],
                columns=['label',
                         'comments',
                         'active',
                         'input',
                         'load profile',
                         'nominal value /(kW)',
                         'annual demand /(kWh/a)',
                         'occupants [RICHARDSON]',
                         'building class [HEAT SLP ONLY]',
                         'wind class [HEAT SLP ONLY]',
                         'fixed'])
            df_sinks = df_sinks.append(df, sort=False)

    return df_bus, df_sinks

def add_gas_heating_to_scenario_file(shapefile, df_bus, df_transformer, gasheating_parameters, bus_parameters):
    sf = shapefile

    for i in range(len(sf.records())):
        rec = sf.record(i)

        # Prüft grob, ob ein Wärmebedarf vorliegt
        if rec['floors']:
            # Checks if the fossil bus related to the demand is already listed in the buses data frame. if not, the bus will be
            # added to the bus-dataframe
            contain_check = 'naturalgas_bus_' + str(rec['Siedlung']) in df_bus.values
            if contain_check == False:
                # Soll der Bus noch zum Dataframe hinzugefügt werden, wird hier ein entsprechender Eintrag definiert
                df = pd.DataFrame([[
                    ('naturalgas_bus_' + str(rec['Siedlung'])),
                    rec['Siedlung'],
                    1,
                    0,
                    1,
                    bus_parameters['naturalgas_shortage_costs'],
                    'x',
                ]],
                    columns=['label',
                             'comments',
                             'active',
                             'excess',
                             'shortage',
                             'shortage costs /(CU/kWh)',
                             'excess costs /(CU/kWh)']
                )

                # Der Eintrag wird zum bus-dataframe hizugefügt
                df_bus = df_bus.append(df, sort=False)

                # Checks if the heat bus related to the demand is already listed in the buses data frame. if not, the bus will be
                # added to the bus-dataframe
                contain_check = 'heat_bus_' + str(rec['Siedlung']) in df_bus.values
                if contain_check == False:

                    # Soll der Bus noch zum Dataframe hinzugefügt werden, wird hier ein entsprechender Eintrag definiert
                    df = pd.DataFrame([['heat_bus_' + str(rec['Siedlung']),rec['Siedlung'],1,1,0,
                                        'x',bus_parameters['heat_excess_costs']]],
                                      columns=['label','comments','active','excess','shortage',
                                               'shortage costs /(CU/kWh)','excess costs /(CU/kWh)'])

                    # Der Eintrag wird zum bus-dataframe hizugefügt
                    df_bus = df_bus.append(df, sort=False)

            contain_check = 'gasheating_transformer_' + str(rec['Siedlung']) in df_transformer.values
            if contain_check == False:
                df = pd.DataFrame([[
                        ('gasheating_transformer_' + str(rec['Siedlung'])),
                        rec['Siedlung'],
                        1,
                        'GenericTransformer',
                        'naturalgas_bus_' + str(rec['Siedlung']),
                        'heat_bus_' + str(rec['Siedlung']),
                         'None',
                         gasheating_parameters['efficiency'],
                        'x',
                        gasheating_parameters['variable_input_costs'],
                        gasheating_parameters['variable_output_costs'],
                        gasheating_parameters['variable_output_costs_2'],
                        0,
                        999999999999999,
                        0,
                        gasheating_parameters['periodical_costs']
                        ]],
                        columns=['label',
                                  'comments',
                                  'active',
                                  'transformer type',
                                  'input',
                                  'output',
                                  'output2',
                                  'efficiency',
                                  'efficiency2',
                                  'variable input costs /(CU/kWh)',
                                  'variable output costs /(CU/kWh)',
                                  'variable output costs 2 /(CU/kWh)',
                                  'existing capacity /(kW)',
                                  'max. investment capacity /(kW)',
                                  'min. investment capacity /(kW)',
                                  'periodical costs /(CU/(kW a))'])

                df_transformer = df_transformer.append(df, sort=False)


    return df_bus, df_transformer

def add_exchange_of_electricity_to_scenario_file(df_bus,df_links, exchange_of_electricity_parameters):

    # Im folgenden wird ein District-Elektrizitäts-Bus erstellt. Die Schleife stellt sicher, dass dies nur geschieht,
    # wenn er noch nicht existiert.
    if 'district_electricity_bus' not in df_bus.values:
        df = pd.DataFrame([['district_electricity_bus','district',1,0,0,'x','x']],
                          columns=['label','comments','active','excess','shortage','shortage costs /(CU/kWh)',
                                   'excess costs /(CU/kWh)'])
        # Der Eintrag wird zum bus-dataframe hizugefügt
        df_bus = df_bus.append(df, sort=False)

    # Die folgende Schleifen-Kombination liest die vorher definierten Einträge des bus-dataframes aus und führt die
    # folgenden Befehle aus, sollte es sich um einen PV-Bus handeln. So werden nur Subsysteme einbezogen, welche
    # PV-Systeme beinhalten
    for i, bus in df_bus.iterrows():
        if 'electricity_pv_bus_' in bus['label']:

            # Directed link from pv electricity bus to district electricity bus
            df = pd.DataFrame([['electricity_' + str(bus['comments']) + '_district_link',bus['comments'],1,bus['label'],
                                'district_electricity_bus','directed',1,9999999999999999,0,0,
                                exchange_of_electricity_parameters['net_costs'],0]],
                               columns=['label','comments','active','bus_1','bus_2','(un)directed','efficiency',
                                        'existing capacity /(kW)','min. investment capacity /(kW)',
                                        'max. investment capacity /(kW)','variable costs /(CU/kWh)',
                                        'periodical costs /(CU/(kW a))'])
            # Der Eintrag wird zum link-dataframe hizugefügt
            df_links = df_links.append(df, sort=False)

            # Directed link from district electricity bus to subsystems electricity bus (if it does not already exist)
            if str('electricity_district_' + str(bus['comments']) + '_link') not in df_links.values:
                df = pd.DataFrame([[('electricity_district_' + str(bus['comments']) + '_link'),
                                    bus['comments'],
                                    1,
                                    'district_electricity_bus',
                                    'electricity_bus_'+str(bus['comments']),
                                    'directed',
                                    1,
                                    9999999999999999,
                                    0,
                                    0,
                                    exchange_of_electricity_parameters['net_costs'],0]],
                                   columns=['label','comments','active','bus_1','bus_2','(un)directed','efficiency',
                                            'existing capacity /(kW)','min. investment capacity /(kW)',
                                            'max. investment capacity /(kW)','variable costs /(CU/kWh)',
                                            'periodical costs /(CU/(kW a))'])
                # Der Eintrag wird zum link-dataframe hizugefügt
                df_links = df_links.append(df, sort=False)

    return df_bus, df_links

def add_battery_storages_to_scenario_file(df_bus, df_storages, storage_parameters, bus_parameters):
    print('placeholder')



def shapefile_converter(shapefile_residential,
                        shapfile_non_residential,
                        weather_data_path,
                        timesystem_parameters,
                        bus_parameters,
                        pv_active,
                        pv_parameters,
                        electricity_demand_parameters,
                        heat_demand_parameters,
                        gasheating_parameters,
                        gh_active,
                        exchange_of_electricity_parameters,
                        eoe_active):


    # Import shapefile containing information about residential Buildings in the district
    # sf_residential = shapefile.Reader("shapefiles/Wohngebaeude.shp")
    # sf_non_residential = shapefile.Reader("shapefiles/Nicht_Wohngebaeude.shp")
    sf_residential = shapefile.Reader(shapefile_residential)
    sf_non_residential = shapefile.Reader(shapfile_non_residential)

    # Imports weather-data-xlsx-file and formats it for the needs of the Spreadsheet Energy System Model Generator
    df_weatherdata = pd.read_excel(weather_data_path)
    df_weatherdata = df_weatherdata.rename(columns = {"Unnamed: 0":""})
    df_weatherdata = df_weatherdata.set_index("")



    # Defines timesystem parameters
    # timesystem_parameters={
    #     'start_date' : '2012-01-01 00:00:00',
    #     'end_date' : '2012-12-30 23:00:00',
    #     'temporal_resolution' : 'h',
    #     'periods' : 8760
    #     }

    # Defines default bus parameters
    # bus_parameters={
    #     'electricity_excess_costs' : -0.1,
    #     'electricity_shortage_costs' : 0.30,
    #     'heat_excess_costs': 0,
    #     'naturalgas_shortage_costs' : 0.07,
    #     'pv_excess_costs' : -0.1
    #     }

    # # Defines default photovoltaic parameters
    # pv_parameters={
    #             'pv_variable_costs' : 0,
    #             'pv_periodical_costs' : 90,
    #             'pv_technology_database' : 'SandiaMod',
    #             'pv_inverter_database' : 'sandiainverter',
    #             'pv_modul_model' : 'Panasonic_VBHN235SA06B__2013_',
    #             'pv_inverter_model' : 'ABB__MICRO_0_25_I_OUTD_US_240__240V_',
    #             'pv_albedo' : 0.2,
    #             'pv_altitude' : 50,
    #             'pv_latitude' : 50,
    #             'pv_longitude' : 7
    #             }

    # Defines demand parameters
    # electricity_demand_parameters={
    #             'residential_load_profile' : 'h0',
    #             'building_class' : 11,
    #             'wind_class' : 0,
    #             'demand_single_family_building' : {1:2300, 2:3000, 3:3600, 4:4000, 5:5000},
    #             'demand_multi_family_building' : {1:1400, 2:2000, 3:2600, 4:3000, 5:3600}
    # }

    # heat_demand_parameters={
    #     'NFA_coefficient' : 0.9,
    #     'demand_residential_building' : {1000:{1:247,2:238,3:212,7:182,13:169},
    #                                       1919:{1:254,2:236,3:211,7:178,13:153},
    #                                       1949:{1:236,2:219,3:192,7:166,13:140},
    #                                       1979:{1:175,2:168,3:155,7:152,13:118},
    #                                       1991:{1:131,2:127,3:127,7:114,13:101},
    #                                       2001:{1:83,2:88,3:80,7:76,13:69},
    #                                       2009:{1:48,2:46,3:46,7:53,13:54}
    #                                       },
    #     'residential_load_profile' : 'efh',
    #     'building_class': 11,
    #     'wind_class': 0,
    # }

    # gasheating_parameters={
    #     'efficiency' : 0.85,
    #     'variable_input_costs':0,
    #     'variable_output_costs':0,
    #     'variable_output_costs_2':0,
    #     'periodical_costs':0
    # }

    # if eoe_active == True:
    #     exchange_of_electricity_parameters={
    #         'net_costs': 0.1438
    #     }

    storage_parameters={}

    # Defines Bus-DataFrame. Columns match the columns of the SESMG-scenario-file
    df_bus = pd.DataFrame(columns=['label',
                                   'comments',
                                   'active',
                                   'excess',
                                   'shortage',
                                   'shortage costs /(CU/kWh)',
                                   'excess costs /(CU/kWh)'])

    # Defines Source-DataFrame. Columns match the columns of the SESMG-scenario-file
    df_sources = pd.DataFrame(columns=['label',
                                       'comments',
                                       'active',
                                       'output',
                                       'technology',
                                       'variable costs /(CU/kWh)',
                                       'existing capacity /(kW)',
                                       'min. investment capacity /(kW)',
                                       'max. investment capacity /(kW)',
                                       'periodical costs /(CU/(kW a))',
                                       'Turbine Model (Windpower ONLY)',
                                       'Hub Height (Windpower ONLY)',
                                       'technology database (PV ONLY)',
                                       'inverter database (PV ONLY)',
                                       'Modul Model (PV ONLY)',
                                       'Inverter Model (PV ONLY)',
                                       'Azimuth (PV ONLY)',
                                       'Surface Tilt (PV ONLY)',
                                       'Albedo (PV ONLY)',
                                       'Altitude (PV ONLY)',
                                       'Latitude (PV ONLY)',
                                       'Longitude (PV ONLY)'])

    # Defines Sink-DataFrame. Columns match the columns of the SESMG-scenario file
    df_sinks = pd.DataFrame(columns=['label',
                                       'comments',
                                       'active',
                                       'input',
                                       'load profile',
                                       'nominal value /(kW)',
                                       'annual demand /(kWh/a)',
                                       'occupants [RICHARDSON]',
                                       'building class [HEAT SLP ONLY]',
                                       'wind class [HEAT SLP ONLY]',
                                       'fixed'])

    # Creates DataFrames. Each dataframe will later be saved as one sheet in the scenario.xlsx-file of the
    # Spreadsheet Energy System Model Generator
    df_timesystem = add_timesystem_to_scenario_file(timesystem_parameters=timesystem_parameters)

    df_transformer = pd.DataFrame(columns=['label',
                                       'comments',
                                       'active',
                                       'transformer type',
                                       'input',
                                       'output',
                                       'output2',
                                       'efficiency',
                                       'efficiency2',
                                       'variable input costs /(CU/kWh)',
                                       'variable output costs /(CU/kWh)',
                                        'variable output costs 2 /(CU/kWh)',
                                        'existing capacity /(kW)',
                                        'max. investment capacity /(kW)',
                                        'min. investment capacity /(kW)',
                                        'periodical costs /(CU/(kW a))'])

    df_storages = pd.DataFrame(columns=['label',
                                       'comments',
                                       'active',
                                       'bus',
                                       'existing capacity /(kWh)',
                                       'min. investment capacity /(kWh)',
                                       'max. investment capacity /(kWh)',
                                       'periodical costs /(CU/(kWh a))',
                                       'capacity inflow',
                                       'capacity loss',
                                       'efficiency inflow',
                                        'initial capacity',
                                        'capacity min',
                                        'capacity max',
                                        'variable input costs',
                                        'variable output costs'])

    df_links = pd.DataFrame(columns=['label',
                                       'comments',
                                       'active',
                                       'bus_1',
                                       'bus_2',
                                       '(un)directed',
                                       'efficiency',
                                       'existing capacity /(kW)',
                                       'min. investment capacity /(kW)',
                                       'max. investment capacity /(kW)',
                                       'variable costs /(CU/kWh)',
                                        'periodical costs /(CU/(kW a))',
                                     ])


    df_timeseries = pd.DataFrame(columns=['timestamp'])

    # Adds several component types to the dataframes, based on the parameters saved in the shape-file and defined in the
    # parameter dictionaries above.

    # PV-Systems on residential buildings roofs
    # pv_active = True
    if pv_active == True:
        df_bus, df_sources, df_links = add_pv_to_scenario_file(shapefile=sf_residential,
                                                             df_bus=df_bus,
                                                             df_sources=df_sources,
                                                             df_links=df_links,
                                                             pv_parameters=pv_parameters,
                                                             bus_parameters=bus_parameters)

    # PV-systems on non-residential buildings roofs
    df_bus, df_sources, df_links = add_pv_to_scenario_file(shapefile=sf_non_residential,
                                                 df_bus=df_bus,
                                                 df_sources=df_sources,
                                                 df_links=df_links,
                                                 pv_parameters=pv_parameters,
                                                 bus_parameters=bus_parameters)

    df_bus, df_sinks = add_electricity_demands_to_scenario_file(shapefile=sf_residential,
                                                                  df_bus=df_bus,
                                                                  df_sinks=df_sinks,
                                                                  demand_parameters=electricity_demand_parameters,
                                                                  bus_parameters=bus_parameters)

    df_bus, df_sinks = add_heat_demands_to_scenario_file(shapefile=sf_residential,
                                                         df_bus=df_bus,
                                                         df_sinks=df_sinks,
                                                         demand_parameters=heat_demand_parameters,
                                                         bus_parameters=bus_parameters)

    if gh_active == True:
        df_bus, df_transformer = add_gas_heating_to_scenario_file(shapefile=sf_residential,
                                                                  df_bus=df_bus,
                                                                  df_transformer=df_transformer,
                                                                  gasheating_parameters=gasheating_parameters,
                                                                  bus_parameters=bus_parameters)

    if eoe_active == True:
        df_bus, df_links = add_exchange_of_electricity_to_scenario_file(df_bus=df_bus,
                                                                        df_links=df_links,
                                                                        exchange_of_electricity_parameters=exchange_of_electricity_parameters)

    # Prints the creates dataframes
    # print(df_timesystem)
    # print(df_bus)
    # print(df_sinks)
    # print(df_sources)
    # print(df_transformer)

    # Create .xlsx-file and saves it. The thereby created xlsx-file fits the needs of the Spreadsheet Energy System
    # Model Generator
    writer = pd.ExcelWriter('shape_scenario.xlsx')
    df_timesystem.to_excel(writer,sheet_name='timesystem')
    df_bus.to_excel(writer, sheet_name='buses')
    df_sinks.to_excel(writer, sheet_name='sinks')
    df_sources.to_excel(writer, sheet_name='sources')
    df_transformer.to_excel(writer, sheet_name='transformers')
    df_storages.to_excel(writer, sheet_name='storages')
    df_links.to_excel(writer, sheet_name='links')
    df_timeseries.to_excel(writer, sheet_name='time_series')
    df_weatherdata.to_excel(writer, sheet_name='weather data')
    writer.save()

    print('Scenario-file succesfully created.')