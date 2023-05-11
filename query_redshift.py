from dotenv import load_dotenv
import redshift_connector
import os
import pandas as pd

def main():
    query = query_text()
    query_redshift_to_pickle(query)

def query_text():
    return ("""
        select
            statecode
            , case
                when early_voted_date is null then ballot_requested_date
                else null
            end as av_ballot_requested_date

            , case
                when early_voted_date is null then ballot_sent_date
                else null
            end as av_ballot_sent_date

            , case
                when early_voted_date is null then ballot_returned_date
                else null
            end as ballot_returned_date

            , early_voted_date

            , voted_date_2022

            , count(*)
        from dbt_sleblanc.base_avev2022
        where voted_date_2022 < '2022-11-08'
        group by 1,2,3,4,5,6 order by 1,2,3,4,5,6;
    """)

def establish_redshift_connection():
    """ Establish redshift connection using server info and environment variables """
    try:
        print('Attempting Redshift connection...')
        load_dotenv()
        conn = redshift_connector.connect(
             host='172.31.28.159',
             port=5439,
             database='analytics',
             user=os.environ['REDSHIFT_USERNAME'],     # defined in .env file
             password=os.environ['REDSHIFT_PASSWORD']  # defined in .env file
          )
        conn.rollback()
        conn.autocommit = True
        print('Succesful Redshift connection!\n')
        cursor = conn.cursor()
        return cursor
    except Exception as e:
        print('Redshift connection failed (are you on VPN?)\n')
        print(e)

def query_redshift_to_pickle(query):

    cursor = establish_redshift_connection()

    print("Querying Redshift for data...")
    cursor.execute(query);

    df = pd.DataFrame(cursor.fetchall())
    df.columns = ["state", "ballot_requested_date","ballot_sent_date","ballot_returned_date", "early_voted_date", "voted_date", "count"]
    df['state'] = df['state'].str[:2]

    print("Pickling data...")
    df = df.to_pickle('df.pkl')
    print("Done!\n")


if __name__ == "__main__":
    main()
