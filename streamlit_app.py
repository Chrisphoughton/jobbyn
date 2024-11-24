import streamlit as st
import pandas as pd
import numpy as np
from google.cloud import bigquery
import altair as alt
from openai import OpenAI

# Initialize the BigQuery client with the service account
# service_account_info = "jobbyn-a159f5cec022.json"
# client = bigquery.Client.from_service_account_json(service_account_info)

# # Initialize the BigQuery client with the service account
service_account_info = st.secrets["gcp_service_account"]
client = bigquery.Client.from_service_account_info(service_account_info)

# openAiClient = OpenAI(api_key='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')

openAi_info = st.secrets["openai"]["api_key"]
openAiClient = OpenAI(api_key=openAi_info)

st.set_page_config(
    page_title="Jobbyn",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

#initialize session state
if "df_options" not in st.session_state:
    st.session_state.df_options = None

if "user_experience" not in st.session_state:
    st.session_state.user_experience = None

if "job_skills" not in st.session_state:
    st.session_state.job_skills = None

if "job_responsibilities" not in st.session_state:
    st.session_state.job_responsibilities = None

seniority_map = { "1": "1. Entry Level", "2": "2. Junior Level", "3": "3. Associate Level", "4": "4. Manager Level ", "5": "5. Director Level", "6": "6. Executive Level", "7": "7. Senior Executive Level "}

# Function to query BigQuery and cache the result
@st.cache_data
def loading_lookups(query):
    query_job = client.query(query)
    dataframe = query_job.result().to_dataframe()
    #make senorty a string
    dataframe["seniority"] = dataframe["seniority"].astype(str)
    dataframe["seniority"] = dataframe["seniority"].map(seniority_map)
    #make mapped_role title case
    
    return dataframe

def loading_data(query):
    query_job = client.query(query)
    dataframe = query_job.result().to_dataframe()
    #append https:// if posting_url does not have it
    dataframe["posting_url"] = dataframe["posting_url"].apply(lambda x: x if x.startswith("http") else "https://www." + x)
    dataframe["seniority"] = dataframe["seniority"].map(seniority_map)
    dataframe["mapped_role"] = dataframe["mapped_role"].str.title()
    dataframe["metro_area"] = dataframe["metro_area"].str.title()
    #reorder columsn to have posting_url after job_id
    dataframe = dataframe[['job_id','jobtitle_raw','posting_url', 'mapped_role', 'ultimate_parent_company_name', 'metro_area', 'state', 'location', 'rics_k50', 'seniority', 'total_compensation', 'remote_type', 'post_date']]
   
    return dataframe

def loading_skill(query):
    query_job = client.query(query)
    dataframe = query_job.result().to_dataframe()
    #set "" to None
    dataframe["skills"] = dataframe["skills"].apply(lambda x: None if x == "" else x)
    
   
    return dataframe

def loading_responsibilities(query):
    query_job = client.query(query)
    dataframe = query_job.result().to_dataframe()
    #set "" to None
    dataframe["responsibilities"] = dataframe["responsibilities"].apply(lambda x: None if x == "" else x)
    
   
    return dataframe

# Your SQL query
lookups_query = """
    SELECT DISTINCT mapped_role, rics_k50, metro_area, seniority FROM `jobbyn.jobbyn.jobsUpdated`
"""

# Use the cached function to get data
df_lookups = loading_lookups(lookups_query)
#make seniority a string
df_lookups["seniority"] = df_lookups["seniority"].astype(str)


st.image("jobbynLogo.jpg", width = 340)


# Get unique list of metro_area and sort them
with st.sidebar:
    locations = df_lookups["metro_area"].unique()
    locations.sort()
    locationsAllFlag = st.checkbox("Select All Locations")
    if locationsAllFlag:
        locationOptions = locations
        st.multiselect("Select your Locations", locations,disabled=True,placeholder="All Locations Selected")
    else:
        locations = [loc.title() for loc in locations]
        locationOptions = st.multiselect("Select your Locations", locations)
        locationOptions = [loc.lower() for loc in locationOptions]
    st.divider()

    #filter industries based on selected locations
    df_lookups = df_lookups[df_lookups["metro_area"].isin(locationOptions)]
    industries = df_lookups["rics_k50"].unique()
    #remove null values
    industries = [industry for industry in industries if industry is not None]
    industries.sort()
    industriesAllFlag = st.checkbox("Select All Industries")
    if industriesAllFlag:
        industryOptions = industries
        st.multiselect("Select your Industries", industries,disabled=True,placeholder="All Industries Selected")
    else:
        industryOptions = st.multiselect("Select your Industries", industries)
    st.divider()

    #filter job families based on selected locations
    df_lookups = df_lookups[df_lookups["rics_k50"].isin(industryOptions)]
    jobFamilies = df_lookups["mapped_role"].unique()
    jobFamilies.sort()
    jobFamiliesAllFlag = st.checkbox("Select All Job Families")
    if jobFamiliesAllFlag:
        jobOptions = jobFamilies
        st.multiselect("Select your Job Families", jobFamilies,disabled=True,placeholder="All Job Families Selected")
    else:
        jobFamilies = [job.title() for job in jobFamilies]
        jobOptions = st.multiselect("Select your Job Families", jobFamilies)
        jobOptions = [job.lower() for job in jobOptions]
    st.divider()

    #filter seniority based on selected job families and locations
    df_lookups = df_lookups[df_lookups["mapped_role"].isin(jobOptions)]
    seniority = df_lookups["seniority"].unique()
    seniority.sort()
    seniorityAllFlag = st.checkbox("Select All Seniority Levels")
    if seniorityAllFlag:
        seniorityOptions = seniority
        st.multiselect("Select your Seniority Levels", seniority,disabled=True,placeholder="All Seniority Levels Selected")
    else:
        seniorityOptions = st.multiselect("Select your Seniority Levels", seniority)
    #for seniority options take the first leftmost digit and convert to number
    seniorityOptions = [seniority[0] for seniority in seniorityOptions]

    st.divider()

    formatted_location_options = ', '.join(f"'{loc}'" for loc in locationOptions) if len(locationOptions)>0 else "''"
    formatted_job_options = ', '.join(f"'{job}'" for job in jobOptions) if len(jobOptions)>0 else "''"
    formatted_seniority_options = ', '.join(f"'{seniority}'" for seniority in seniorityOptions) if len(seniorityOptions)>0 else "''"
    formatted_industry_options = ', '.join(f"'{industry}'" for industry in industryOptions) if len(industryOptions)>0 else "''"

    data_query = f"""
        SELECT * FROM `jobbyn.jobbyn.jobsUpdated`
        WHERE metro_area IN ({formatted_location_options}) AND mapped_role IN ({formatted_job_options}) AND seniority IN ({formatted_seniority_options}) AND rics_k50 IN ({formatted_industry_options})
    """

    searchButton = st.button("Search for Jobs",disabled=True if (len(locationOptions) == 0 or len(jobOptions) == 0 or len(seniorityOptions) == 0 or len(industryOptions) == 0 or len(df_lookups) > 100000) else False)
    #if either of the options are empty, return an empty dataframe
    if len(df_lookups) > 100000:
        st.caption("Too many options selected, please narrow your search")
    if len(locationOptions) == 0 or len(jobOptions) == 0 or len(seniorityOptions) == 0 or len(industryOptions) == 0:
        st.caption("Please select at least one option for each category")
    

t1, t2 = st.tabs(["Job Search", "Your Experiences"])
with t1:
    if searchButton:
        df_options = loading_data(data_query)
        df_options = df_options
        st.session_state["df_options"] = df_options  # Store DataFrame in session state

    if st.session_state["df_options"] is not None:
    
    
        df_options = st.session_state["df_options"]
        company_count = df_options.groupby("ultimate_parent_company_name").size().reset_index(name="Count")
        company_count.rename(columns={"ultimate_parent_company_name": "Company"}, inplace=True)

        role_count = df_options.groupby("mapped_role").size().reset_index(name="Count")
        role_count.rename(columns={"mapped_role": "jobFamily"}, inplace=True)

        chart = alt.Chart(company_count).mark_bar().encode(
            x=alt.X("Count:Q", title="Number of Jobs"),
            y=alt.Y("Company:N", title="Company", sort="-x"),
            tooltip=["Company", "Count"],
            color=alt.value("#004481")
        ).configure_axis(
            domain=False,
            grid=False,
            titleFontSize=12,
            labelOverlap=True,
            labelLimit=300,
        ).properties(
            width=700,
            title="Company Count" 
        )

        chart2 = alt.Chart(role_count).mark_bar().encode(
            x=alt.X("Count:Q", title="Number of Jobs"),
            y=alt.Y("jobFamily:N", title="Job Family", sort="-x"),
            tooltip=["jobFamily", "Count"],
            color=alt.value("#004481")
        ).configure_axis(
            domain=False,
            grid=False,
            titleFontSize=12,
            labelOverlap=True,
            labelLimit=300,
            
        ).properties(
            width=700,
            title="Job Family" 
        )
        with st.expander("Summary", expanded=False):
            c1, c2 = st.columns([1, 1])
            with c1:
                with st.container(height=600):
                    st.altair_chart(chart, use_container_width=True)
            
            with c2:
                with st.container(height=600):
                    st.altair_chart(chart2, use_container_width=True)
        #get dataframe from session state

        event = st.dataframe(
            df_options,
            column_config={
                "jobtitle_raw": st.column_config.TextColumn("Job Title"),
                "mapped_role": st.column_config.TextColumn("Job Family"),
                "ultimate_parent_company_name": st.column_config.TextColumn("Company"),
                "metro_area": st.column_config.TextColumn("Metro Area"),
                "state": st.column_config.TextColumn("State"),
                "location": st.column_config.TextColumn("Location"),
                "rics_k50": st.column_config.TextColumn("Industry"),
                "seniority": st.column_config.TextColumn("Seniority"),
                "total_compensation": st.column_config.NumberColumn("Total Compensation"),
                "remote_type": st.column_config.TextColumn("Remote Type"),
                "post_date": st.column_config.TextColumn("Posted Date"),
                "job_id": st.column_config.TextColumn("Job ID"),
                "posting_url": st.column_config.LinkColumn("Posting Link", display_text="🔗"),
            },
            use_container_width=True,
            selection_mode="single-row",
            on_select="rerun",
            hide_index=True
        )
        if event["selection"]["rows"]:
            
            row = event["selection"]["rows"][0]
            #filter df_options based on the selected row
            if row is not None:
                st.divider()
                job_and_company = df_options[df_options.index == row]["jobtitle_raw"].values[0] + " at " + df_options[df_options.index == row]["ultimate_parent_company_name"].values[0]
                st.write(job_and_company)
                selected_job_id = df_options[df_options.index == row]["job_id"].values[0]
                skills_query = f"""
                    SELECT skills FROM `jobbyn.jobbyn.skill`
                    WHERE job_id = {selected_job_id}
                """
                skills = loading_skill(skills_query)

                responsibilities_query = f"""
                    SELECT responsibilities FROM `jobbyn.jobbyn.responsibilities`
                    WHERE job_id = {selected_job_id}
                """
                responsibilities = loading_responsibilities(responsibilities_query)

                c1,c2 = st.columns([1,1])
                with c1:
                    with st.container(border=True):
                        st.caption("Skills")
                        st.session_state["job_skills"] = skills["skills"].values[0]
                        st.write(st.session_state["job_skills"])
                with c2:
                    with st.container(border=True):
                        st.caption("Responsibilities")
                        st.session_state["job_responsibilities"] = responsibilities["responsibilities"].values[0]
                        st.write(st.session_state["job_responsibilities"])
                

                st.divider()
                if st.button("🤖 Tailor your Experience to the job"):
                    if st.session_state["user_experience"]:
                        # OpenAI API Prompt
                        prompt = f"""

                        Job title and company:
                        {job_and_company}


                        Job Posting Skills: 
                        {st.session_state["job_skills"]}

                        Job Posting Responsibilities:
                        {st.session_state["job_responsibilities"]}


                        User's Experience:
                        {st.session_state["user_experience"]}

                        Update the user's experience to better align with the job's skills and responsibilities. Maintain authenticity while highlighting relevant accomplishments and transferable skills. Ensure the tone is professional and tailored for a resume.
                        """
                        with st.container(border=True):
                            with st.chat_message("ai"):
                                try:
                                    # Call OpenAI API
                                    response = openAiClient.chat.completions.create(
                                        model="gpt-4o",  # Or "text-davinci-003"
                                        messages=[{"role": "system", "content": "You are a helpful assistant that is aiding the user in updating their work experience based on the job posting. They will provide you skills and their current experiences and you need to update their experiences to better align with the job posting."},
                                                {"role": "user", "content": prompt}],
                                        temperature=1,
                                        max_tokens=500,
                                        stream=True
                                    )

                                    # Display Updated Experience
                                    st.write_stream( response)

                                except Exception as e:
                                    st.error(f"Error generating updated experience: {e}")
                    else:
                        st.warning("Please fill out your Your Experiences before generating.")


                
                
        else:
            st.caption("Select a row to show skills, responsibilites and to tailor your resume")
    
    with t2:
      
        user_experience = st.text_area("Enter your experiences here", height=500)
        st.session_state["user_experience"] = user_experience

