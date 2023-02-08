import streamlit as st
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

import query_redshift

def main():
    df = pd.read_pickle(f'df.pkl')
    tally, count_var, options, start_date, end_date, yaxis_select, display_df = streamlit_setup(df)
    df = format_dataframe(df, count_var, start_date, end_date, options)
    create_chart(df, tally, count_var, yaxis_select, start_date, end_date)
    display_data(df, display_df, yaxis_select, count_var, tally)

def get_tally_variable_from_sidebar():
    tally = st.sidebar.selectbox("Tally Variable", ('All AVEV Votes','Ballots Requested','Ballots Sent','Ballots Returned','Early Votes In Person'))

    tally_name_conversion = {
    'All AVEV Votes' : 'voted_date',
    'Ballots Requested' : 'ballot_requested_date',
    'Ballots Sent' : 'ballot_sent_date',
    'Ballots Returned' : 'ballot_returned_date',
    'Early Votes In Person' : 'early_voted_date',
    }

    return tally, tally_name_conversion[tally]

def streamlit_setup(df):

    st.markdown(f'''<style>.css-91z34k {{max-width: 65rem; padding:1rem}};</style>''', unsafe_allow_html=True)
    st.markdown(f'''<style>.css-1vq4p4l {{padding:1rem}};</style>''', unsafe_allow_html=True)

    st.markdown('# AVEV Date Review')
    st.markdown('##### Graphing the number of state-level AVEV actions over the 2022 General Election cycle.')
    st.markdown('Use the sidebar (left) to adjust the settings, and contact Sam ([sleblanc@americavotes.org]()) with any questions or concerns.')
    st.sidebar.title('Settings')
    tally, count_var = get_tally_variable_from_sidebar()

    options = st.sidebar.multiselect("Filter by State", df.state.unique(), [s for s in ['GA','MI','PA','WI'] if s in df.state.unique()])

    start_date = st.sidebar.date_input("Start Date", datetime.date(2022, 10, 1))
    end_date = st.sidebar.date_input("End Date", datetime.date(2022, 11, 8))

    yaxis_select = st.sidebar.selectbox("Y-axis", ('Percent of Total Votes',f'Percent of {tally} (AV2EV)','Record Count (AV2EV)'))

    display_df = st.sidebar.checkbox('Display Chart Data')

    return tally, count_var, options, start_date, end_date, yaxis_select, display_df

def create_chart(df, tally, count_var, yaxis_select, start_date, end_date):

    # Create a list of colors to use for each state
    colors = ['orangered', 'Goldenrod', 'Green', 'Blue', 'Lime', 'Maroon', 'Violet', 'Silver', 'Cyan', 'Pink', 'Orange', 'Gray', 'Yellow', 'Brown', 'Blue', 'Black']

    # Create a figure and axis
    fig, ax = plt.subplots()

    yaxis_conversion = {
        'Record Count (AV2EV)' : 'count',
        f'Percent of {tally} (AV2EV)' : 'perc_avev_total',
        'Percent of Total Votes' : 'perc_nyt_total',
    }

    # Loop through each state and plot the data
    for i, state in enumerate(df['state'].unique()):
        # Create a dataframe for each state
        df_state = df[df['state'] == state]
        # Plot the data
        ax.plot(df_state[count_var], df_state[yaxis_conversion[yaxis_select]], color=colors[i], label=state)

        days_between = abs((start_date - end_date).days)

        if days_between < 90:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.TUESDAY))
        elif days_between < 150:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2, byweekday=mdates.TUESDAY))
        else:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=4, byweekday=mdates.TUESDAY))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

        if yaxis_conversion[yaxis_select] == 'count':
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

def format_dataframe(df, count_var, start_date, end_date, options):
    df = df.groupby(['state', count_var]).agg({'count':"sum"}).reset_index()

    df = df[df.state.isin(options)]

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

    return df

def display_data(df, display_df, yaxis_select, count_var, tally):
    # Display dataframe powering plot if checkbox is checked

    yaxis_conversion = {
        'Record Count (AV2EV)' : 'count',
        f'Percent of {tally} (AV2EV)' : 'perc_avev_total',
        'Percent of Total Votes' : 'perc_nyt_total',
    }

    if display_df:
        st.write("#### Dataframe:")
        pivot = pd.pivot_table(df,index=[count_var],columns=['state'],values=[yaxis_conversion[yaxis_select]])

        if yaxis_conversion[yaxis_select] == 'count':
            pivot = pivot.applymap(lambda x: '{:.0f}'.format(x))
        else:
            pivot = pivot.applymap(lambda x: '{:.1f}%'.format(x))

        st.write(pivot)

if __name__ == "__main__":
    main()
