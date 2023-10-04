#!/usr/bin/env python
# coding: utf-8

# In[1]:


#map geo data source
#https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html
#https://www.parks.ca.gov/?page_id=29682
#iNaturalist sources
#https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.v1.observations.html#pyinaturalist.v1.observations.get_observations
#https://www.inaturalist.org/pages/api+reference

#########################################

#You will need three shape files to create the map.
#Download California_shape_Archive.zip from https://github.com/Floydworks/Tarantulas_Map_iNat/tree/main/shape_files
#Or use wesites in source information (this may require changing the map projections)

#######################################
    


# In[2]:


from pyinaturalist.node_api import get_all_observations
import pandas as pd
import numpy as np
from datetime import date, datetime
import time

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches

print("Libraries imported!")


# In[3]:


#define start time for entire process
start_time = time.time()


# In[4]:


#define function, simplify_observation,  to extract the desired data from the query return list object, Observations.
#returning a newly created dictionary of extracted values, simplified_obs.

def simplify_observation(obs):

    simplified_obs = {}
    
    # Top level values
    simplified_obs['Date'] = obs['observed_on']  
    simplified_obs['Created_Date'] = obs['created_at']
    simplified_obs['Updated_Date'] = obs['updated_at']
    simplified_obs['Location_Name'] = obs['place_guess']
    simplified_obs['Place_ids'] =  obs['place_ids'] 
    simplified_obs['URL'] = obs['uri']
    simplified_obs['quality'] = obs['quality_grade']
                
    # Nested values
    simplified_obs['species_name'] = obs['taxon']['name']
    simplified_obs['coordinates'] = obs['geojson']['coordinates'] 
    simplified_obs['endemic'] = obs['taxon']['endemic']
    simplified_obs['native'] = obs['taxon']['native']
    simplified_obs['threatened'] = obs['taxon']['threatened']
    simplified_obs['threatened'] = obs['taxon']['observations_count']
    
#Name new columns and fill with values extracted from dataset
    
    #split lat, long into separate columns
    for i in range(len(obs['geojson']['coordinates'])):
        #create columns for lat and long separately
        simplified_obs['lat'] =obs['geojson']['coordinates'][0]
        simplified_obs['long'] =obs['geojson']['coordinates'][1]
    
    #split species name into separate columns, 'genus', 'species', and 'variety'
    for i in range(len(obs['taxon']['name'])):
        tn = obs['taxon']['name'] + ' ' + 'none' + ' ' + 'none' #add a space to alleviate name anatomy issues
        #create columns for genus and species separately
        simplified_obs['genus'] =tn.split(' ')[0]
        simplified_obs['species'] =tn.split(' ')[1]
        simplified_obs['variety'] =tn.split(' ')[2]
    
    #Media/photo path columns
    for i in range(len(obs['photos'])):        
        # Change value here if you want more or less than 3 photos 
        if(i<1):
            simplified_obs['photo '+str(i)] = obs['photos'][i]['url'].replace('square', 'original')              

    return simplified_obs


# In[5]:


#Call query through pyinaturalist.node_api, no authentication required
print("This may take a few minutes... For larger exports you may need to get a key from iNaturalist")

start_time_query = time.time()
#use today's date as the maximum date for data retreival
today = date.today()

#assign iNaturalist place IDs (see iNaturalist.org)
PLACES = [14]                    #14= California
#initialize empty list for storing data
Observations = [] 

for p in PLACES:
    
    observations_research = get_all_observations( 
      taxon_id=47423,             # Taxon ID for Aphonopelma spp. Tarantulas
      place_id=[p],               # Location ID from PLACES list
      d1='2018-01-01',            # Get observations from October 1st 2017...
      d2= today,                   # ...through today
      #created_d1= '2023-01-01',
      #created_d2= today,
      #updated_since ='2023-01-01',   #Must be updated since this time
      #radius  =                   #Must be within a {radius} kilometer circle around this lat/lng (lat, lng, radius)
      geo=True,                   # Only get observations with geospatial coordinates
      geoprivacy='open',          # Only get observations with public coordinates (not obscured/private)
      #quality_grade = 'research'  #Only get research grade observations
      
    )
    print("Observations", str(p), "ready!", "This place_id has:", len(observations_research), "observations")
    
    #add queried data, observations_research, to storage list, Observations
    Observations = Observations+observations_research
    
print("Observations concatenated!","There are:", len(Observations), "observations, prior to cleaning your dataset")

query_time = (time.time() - start_time_query)
print("Run time for your api request: %s seconds" % (query_time))


# In[6]:


#apply function (simplify_observation() to each observation in Observations and store in list object
simpleObs = [simplify_observation(obs) for obs in Observations] #returns nested dictionary
print("Observations simplified!")

#convert list object simpleObs to pandas dataframe df_obs
df_obs = pd.DataFrame.from_records(simpleObs)

#export the complete dataset
date_string = str(today.month)+"_"+str(today.day)+"_"+str(today.year)
df_obs.to_csv(f'YOUR FILE PATH{date_string}.csv')


# In[7]:


#clean data and drop certain data

# replace 'none' with NaN
prior_len = len(df_obs)
df_obs = df_obs.replace('none', np.nan)
print(prior_len - len(df_obs), "'none' species names converted to NaN values")

#drop observations with no species name
#prior_len = len(df_obs)
#df_obs = df_obs.dropna(subset=['species'])
#print(prior_len-len(df_obs), "observations had no species name")

#drop observations with no genus name
prior_len = len(df_obs)
df_obs = df_obs.dropna(subset=['genus'])
print(prior_len-len(df_obs), "observations had no genus name")

#drop observations with no date
prior_len = len(df_obs)
df_obs = df_obs.dropna(subset=['Date'])
print(prior_len - len(df_obs), "observations had no date")

#drop observations below research grade
#prior_len = len(df_obs)
#df_obs = df_obs[df_obs["quality"].str.contains("needs_id|casual") == False]
#print(prior_len-len(df_obs), "oservations were below research grade")


# In[8]:


df_obs.reset_index(inplace = True)
print('There are:', len(df_obs), 'observations in the dataset.')
display(df_obs.head(3))


# In[ ]:


# Make a map of California with county borders, tarantula observations, state parks, and wilderness areas.


# In[12]:


#city DICTIONARY 
city_info_dict =  {
                   "San Jose": {"place_id":"","region": "south bay", 'lat_long':(37.2959622,-121.8160962)},
                   "Los Angeles": {"place_id":"","region": "southern", 'lat_long':(34.020479,-118.4117325)},
                   "Sacramento": {"place_id":"","region": "northern", 'lat_long':(38.6594734, -121.21373)},
                   }

#create dataframe of city information
city_info_df = pd.DataFrame.from_dict(city_info_dict, orient='index').reset_index()
city_info_df = city_info_df.rename(columns={'index':'city'})

display(city_info_df)


# In[10]:


#define shape file paths

CA_counties_shp = 'YOUR FILE PATH/CA_Counties_TIGER2016_4269.shp'
CA_wilderness_areas = 'YOUR FILE PATH/Wilderness_Areas_122721_EPSG4269_CALIFORNIA.shp'
CA_state_parks = 'YOUR FILE PATH/ParkBoundaries_EPSG4269_CALIFORNIA.shp'

# initialize an axis
fig, ax = plt.subplots(figsize=(15,12))

# plot map on axis
#California Counties outline
shape = gpd.read_file(CA_counties_shp)
#shape = shape[shape['COUNTYFP'].isin(['019','027','107'])]

#Wilderness areas outlines
wilderness = gpd.read_file(CA_wilderness_areas)
# find specific park(s)
#wilderness = wilderness[wilderness['NAME_ABBRE'].str.contains("Kings_Canyon")] 

#State parks areas outlines
state_parks = gpd.read_file(CA_state_parks)

shape.plot(color="lightgrey", edgecolor='darkgrey',ax=ax)
wilderness.plot(color="lightgreen", alpha=.6, ax=ax) #edgecolor='darkgreen',
state_parks.plot(color="yellow", alpha=1, ax=ax) #edgecolor='gold',

#define observation x and y using lat and long from the iNat observations
x = df_obs['lat']
y = df_obs['long']
#plot the tarantula observations
plt.scatter(x, y, c= "blue", alpha=1, s=2.5)

#add major cities to the map
#manually place each city and adjust text position to avoid observation points
plt.text((city_info_df.loc[city_info_df['city'] == 'San Jose', 'lat_long'].iloc[0][1])+.22, 
           (city_info_df.loc[city_info_df['city'] == 'San Jose', 'lat_long'].iloc[0][0]), 
         'San Jose', color = 'black', fontsize=15)
plt.text((city_info_df.loc[city_info_df['city'] == 'Los Angeles', 'lat_long'].iloc[0][1])-2.5,
           (city_info_df.loc[city_info_df['city'] == 'Los Angeles', 'lat_long'].iloc[0][0]),
         'Los Angeles', color = 'black', fontsize=15)
plt.text((city_info_df.loc[city_info_df['city'] == 'Sacramento', 'lat_long'].iloc[0][1]),
           (city_info_df.loc[city_info_df['city'] == 'Sacramento', 'lat_long'].iloc[0][0]),
         'Sacramento', color = 'black', fontsize=15)
    
#give the plot a title and position the title 
first_year = '2018'
last_year = 'present'
plt.title(f"Tarantula observations in California\n{first_year} to {last_year}", 
          fontsize = 20, weight='bold', loc = 'left', y=1.01)

#add grid
#ax.grid(b=True, alpha=0.5)

#add legend
blue_point = mlines.Line2D([], [], color='blue', marker='.', linestyle='None',
                          markersize=15, label='observations')
grey_line = mlines.Line2D([], [], color='grey', marker='',
                          markersize=15, label='county borders')
yellow_patch = mpatches.Patch(color='yellow', label='State Parks')
green_patch = mpatches.Patch(color='lightgreen', label='Wlderness Areas')
ax.legend(handles=[blue_point, grey_line, yellow_patch, green_patch],
          frameon=False,
          loc='upper right', bbox_to_anchor=(0.9, 0.95),
          #title='Legend', title_fontsize=18,
          fontsize = 12)

#save the figure
plt.savefig('YOUR FILE PATH/tarantualas_california.png', dpi=300)

#display the plot
plt.show()


# In[11]:


print("Run time for your api request: %s seconds" % (query_time))
print("Run time total: %s seconds" % (time.time() - start_time))







