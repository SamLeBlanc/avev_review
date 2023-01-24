import streamlit as st
st.markdown(f'''<style>
    .css-91z34k {{max-width: 65rem; padding:1rem}};
</style>''', unsafe_allow_html=True)
st.markdown(f'''<style>
    .css-1vq4p4l {{padding:1rem}};
</style>''', unsafe_allow_html=True)

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = [8, 5]

from datetime import datetime, timedelta
import matplotlib.dates as mdates
import datetime

import warnings
warnings.filterwarnings('ignore')

import warnings
warnings.filterwarnings('ignore')

# def establish_redshift_connection():
#     """ Establish redshift connection using server info and environment variables """
#     try:
#         print('Attempting Redshift connection...')
#         load_dotenv()
#         conn = redshift_connector.connect(
#              host='172.31.28.159',
#              port=5439,
#              database='analytics',
#              user=os.environ['REDSHIFT_USERNAME'],     # defined in .env file
#              password=os.environ['REDSHIFT_PASSWORD']  # defined in .env file
#           )
#         conn.rollback()
#         conn.autocommit = True
#         print('Succesful Redshift connection!\n')
#         cursor = conn.cursor()
#         return cursor
#     except Exception as e:
#         print('Redshift connection failed (are you on VPN?)\n')
#         print(e)
#
# query = """
# select statecode, ballot_requested_date, ballot_sent_date, ballot_returned_date, early_voted_date, voted_date, count(*)
# from avev2022._av2ev_final_std
# group by 1,2,3,4,5,6 order by 1,2,3,4,5,6;
# """
#
# cursor = establish_redshift_connection()
#
# df = query_redshift_to_df_with_col_names(cursor, query, ["state", "ballot_requested_date","ballot_sent_date","ballot_returned_date", "early_voted_date", "voted_date", "count"])
#
# df = df.to_pickle('df.pkl')

st.title('AVEV Date Review')

st.sidebar.title('Settings')

tally = st.sidebar.selectbox(
    "Tally",
    ('All AVEV Votes','Ballots Requested','Ballots Sent','Ballots Returned','Early Votes In Person',))

def get_tally_name(tally):
    if tally == 'All AVEV Votes':
        return 'voted_date'
    if tally == 'Ballots Requested':
        return 'ballot_requested_date'
    if tally == 'Ballots Sent':
        return 'ballot_sent_date'
    if tally == 'Ballots Returned':
        return 'ballot_returned_date'
    if tally == 'Early Votes In Person':
        return 'early_voted_date'

count_var = get_tally_name(tally)

df = pd.read_pickle(f'df.pkl')

df = df.groupby(['state',count_var]).agg({'count':"sum"}).reset_index()

options = st.sidebar.multiselect("Filter by State", df.state.unique(), [s for s in ['GA','MI','PA','WI'] if s in df.state.unique()])
df = df[df.state.isin(options)]

start_date = st.sidebar.date_input("Start Date", datetime.date(2022, 10, 1))
end_date = st.sidebar.date_input("End Date", datetime.date(2022, 11, 8))

yaxis_select = st.sidebar.selectbox("Y-axis", ('Percent of Total Votes (NYT)',f'Percent of {tally} (AV2EV)','Record Count (AV2EV)'))

display_df = st.sidebar.checkbox('Display Chart Data')

df[count_var] = pd.to_datetime(df[count_var]).dt.date

# Get cumulative sum of vote_dates by state and voted_date
df = df.groupby(['state', count_var]).sum().groupby(level=0).cumsum().reset_index()

# Total number of votes, NYT
total_votes_nyt = { 'AZ': 2572097, 'CO': 2500130, 'FL': 7757859, 'GA': 3935924, 'ID': 590890, 'ME': 676819, 'MI': 4461925, 'MN': 2509632, 'MT': 495920, 'NC': 3771409, 'NH': 620511, 'NM': 712256, 'NV': 1020850, 'OH': 4131603, 'PA': 5368021, 'WI': 2647652 }

total_avev = df.groupby('state')['count'].max().to_dict()

# Join total_votes to df
df = df.join(pd.DataFrame.from_dict(total_votes_nyt, orient='index').reset_index().rename(columns={'index':'state', 0:'total_votes_nyt'}).set_index('state'), on='state')

df = df.join(pd.DataFrame.from_dict(total_avev, orient='index').reset_index().rename(columns={'index':'state', 0:'total_avev'}).set_index('state'), on='state')

df['perc_nyt_total'] = 100*df['count']/df['total_votes_nyt']
df['perc_avev_total'] = 100*df['count']/df['total_avev']

# Trim the dataframe to only include dates in Q4
df = df[df[count_var] <= end_date]
df = df[df[count_var] >= start_date]

# Create a list of colors to use for each state
colors = ['orangered', 'Goldenrod', 'Green', 'Blue', 'Lime', 'Maroon', 'Violet', 'Silver', 'Cyan', 'Pink', 'Orange', 'Gray', 'Yellow', 'Brown', 'Blue', 'Black']

# Create a figure and axis
fig, ax = plt.subplots()

def get_yaxis_var(yaxis_select):
    if yaxis_select == 'Record Count (AV2EV)':
        return 'count'
    if yaxis_select == f'Percent of {tally} (AV2EV)':
        return 'perc_avev_total'
    if yaxis_select == 'Percent of Total Votes (NYT)':
        return 'perc_nyt_total'

# Loop through each state and plot the data
for i, state in enumerate(df['state'].unique()):
    # Create a dataframe for each state
    df_state = df[df['state'] == state]
    # Plot the data
    ax.plot(df_state[count_var], df_state[get_yaxis_var(yaxis_select)], color=colors[i], label=state)
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.TUESDAY))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    if get_yaxis_var(yaxis_select) == 'count':
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    else:
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}%'))

# Set the title and labels
ax.set_xlabel('Date')
ax.set_ylabel(yaxis_select)
ax.set_title(f'{tally} by State and Date')

# Set the legend
ax.legend()

# Display grid lines
plt.grid(linestyle='-', color='lightgrey', alpha=0.4)

# Show the plot
st.pyplot(fig)

# Display dataframe powering plot if checkbox is checked
if display_df:
    st.write("### Dataframe:")
    pivot = pd.pivot_table(df,index=[count_var],columns=['state'],values=[get_yaxis_var(yaxis_select)])

    if get_yaxis_var(yaxis_select) == 'count':
        pivot = pivot.applymap(lambda x: '{:.0f}'.format(x))
    else:
        pivot = pivot.applymap(lambda x: '{:.1f}%'.format(x))

    st.write(pivot)
