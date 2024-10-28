import streamlit as st
import pandas as pd
import numpy as np
from google.cloud import bigquery

# Initialize the BigQuery client with the service account
service_account_info = st.secrets["gcp_service_account"]
client = bigquery.Client.from_service_account_info(service_account_info)

st.set_page_config(
    page_title="Jobbyn",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "# This is a header. This is an *extremely* cool app!"
        
    }
)

# Function to query BigQuery and cache the result
@st.cache_data
def loading_lookups(query):
    # Run the query and load results into a DataFrame
    query_job = client.query(query)
    dataframe = query_job.result().to_dataframe()
    return dataframe

def loading_data(query):
    # Run the query and load results into a DataFrame
    query_job = client.query(query)
    dataframe = query_job.result().to_dataframe()
    return dataframe

# Your SQL query
lookups_query = """
    SELECT DISTINCT mapped_role, rics_k50, metro_area FROM `jobbyn.jobbyn.jobs`
"""

# Use the cached function to get data
df_lookups = loading_lookups(lookups_query)




st.title("Jobbyn")
st.subheader(
    "Please follow instructions to get the best job for you"
)
st.divider()

#get unique list of metro_area and sort them
locations = df_lookups["metro_area"].unique()
locations.sort()
#make location proper case
locations = [loc.title() for loc in locations]
locationOptions = st.multiselect(
    "Select your Locations",
    locations,
)
#convert locations to lower case
locationOptions = [loc.lower() for loc in locationOptions]

#filter the data based on the selected locations
df_lookups = df_lookups[df_lookups["metro_area"].isin(locationOptions)]
#get unique list of job families and sort them
jobFamilies = df_lookups["mapped_role"].unique()
jobFamilies.sort()
#make job families proper case
jobFamilies = [job.title() for job in jobFamilies]

jobOptions = st.multiselect(
    "Select your Job Families",
    jobFamilies,
)
#convert job families to lower case
jobOptions = [job.lower() for job in jobOptions]

# Format the lists as strings for SQL IN clause
formatted_location_options = ', '.join(f"'{loc}'" for loc in locationOptions) if locationOptions else "''"
formatted_job_options = ', '.join(f"'{job}'" for job in jobOptions) if jobOptions else "''"

#query where location and job family are selected
data_query = f"""
    SELECT * FROM `jobbyn.jobbyn.jobs`
    WHERE metro_area IN ({formatted_location_options}) AND mapped_role IN ({formatted_job_options})
   
"""



c1, c2 = st.columns([4, 1])
with c2:
    searchButton = st.button("Search for Jobs")
st.divider()
if searchButton:
    df_options = loading_data(data_query)
    #drop job_id column
    df_options = df_options.drop(columns=["job_id"])
    #title case all column values
   
    #create horizontal bar chart of companies and rename to company and count to number of jobs
    companyCount = df_options["ultimate_parent_company_name"].value_counts()
    companyCount.index.name = "Company"
    companyCount.name = "Number of Jobs"
    st.bar_chart(companyCount,horizontal=True, use_container_width=True)
    st.dataframe(df_options, 
                 column_config={
                     "jobtitle_raw":st.column_config.TextColumn("Job Title"),
                        "mapped_role":st.column_config.TextColumn("Job Family"),
                        "ultimate_parent_company_name":st.column_config.TextColumn("Company"),
                        "metro_area":st.column_config.TextColumn("Metro Area"),
                        "state":st.column_config.TextColumn("State"),
                        "location":st.column_config.TextColumn("Location"),
                        "rics_k50":st.column_config.TextColumn("Industry"),
                        "seniority":st.column_config.TextColumn("Seniority"),
                        "total_compensation":st.column_config.NumberColumn("Total Compensation"),
                        "remote_type":st.column_config.TextColumn("Remote Type"),
                        "post_date":st.column_config.TextColumn("Posted Date"),
                        
                    },
                 use_container_width =True, 
                 hide_index=True)


