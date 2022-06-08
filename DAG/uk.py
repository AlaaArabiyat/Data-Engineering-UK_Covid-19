from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import subprocess
import psycopg2
from collections import Counter
#from matplotlib import pyplot
from numpy import where
#import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import inspect,create_engine
#import folium
#from sklearn.preprocessing import MinMaxScaler
import os
import signal
from subprocess import Popen, STDOUT, PIPE
from tempfile import gettempdir, NamedTemporaryFile
from builtins import bytes
from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.utils.file import TemporaryDirectory
from airflow.utils.operator_helpers import context_to_airflow_vars


def _read_csv_file_preprocessing():
        List_of_days=[]
        for year in range(2020,2022):
            for month in range(1,13):
                for day in range(1,32):
                 month=int(month)
                 if day <=9:
                   day=f'0{day}'

                if month <= 9 :
                  month=f'0{month}'
                List_of_days.append(f'{month}-{day}-{year}')
        def Get_DF_i(Day):
            DF_i=None
            try: 
                URL_Day=f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{Day}.csv'
                DF_day=pd.read_csv(URL_Day)
                DF_day['Day']=Day
                cond=(DF_day.Country_Region=='United Kingdom')
                Selec_columns=['Day','Country_Region', 'Last_Update','Lat', 'Long_', 'Confirmed', 'Deaths', 'Recovered', 'Active','Combined_Key', 'Incident_Rate', 'Case_Fatality_Ratio']
                DF_i=DF_day[cond][Selec_columns].reset_index(drop=True)
            except:
            #print(f'{Day} is not available!')
                pass
            return DF_i
        import time 
        Start=time.time()
        DF_all=[]
        for Day in List_of_days:
            DF_all.append(Get_DF_i(Day))
        End=time.time()
        Time_in_sec=round((End-Start)/60,2)
        print(f'It took {Time_in_sec} minutes to get all data')
        DF_Uk=pd.concat(DF_all).reset_index(drop=True)
        # Create DateTime for Last_Update
        DF_Uk['Last_Updat']=pd.to_datetime(DF_Uk.Last_Update, infer_datetime_format=True)  
        DF_Uk['Day']=pd.to_datetime(DF_Uk.Day, infer_datetime_format=True)  
        #DF_Uk['Case_Fatality_Ratio']=DF_Uk['Case_Fatality_Ratio'].astype(float)
        DF_Uk1=DF_Uk.groupby(['Day', 'Country_Region']).agg({'Confirmed':'sum','Deaths':'sum','Recovered':'sum','Active':'sum'}).reset_index()
        #DF_Uk1.head()
        DF_Uk1["Incident_Rate"] = DF_Uk1["Confirmed"]/100000
        DF_Uk1["Case_Fatality_Ratio"] = (DF_Uk1["Deaths"] / DF_Uk1["Confirmed"])*100
        DF_Uk1.to_csv('/home/sharedVol/uk_data.csv',index=False)

def _push_get_data_to_postgres():
        from sqlalchemy import inspect,create_engine
        import psycopg2
        from datetime import date
        DF_Uk_u_3 = pd.read_csv("/home/sharedVol/Uk_scoring_report.csv")
        DF_Uk_u_2 = pd.read_csv("/home/sharedVol/Uk_scoring_report_NotScaled.csv")
        host="postgres_storage"
        database="csv_db"
        user="psut"
        password="psut2022"
        port='5432'
        engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
        insp = inspect(engine)
        #print(insp.get_table_names())
        today = date.today()
        Day=today.strftime("%d_%m_%Y")
        DF_Uk_u_3.to_sql(f'uk_scoring_report_{Day}', engine,if_exists='replace',index=False)
        DF_Uk_u_2.to_sql(f'uk_scoring_notscaled_report_{Day}', engine,if_exists='replace',index=False)

def _data_visualization():
        import matplotlib.pyplot as plt 
        import matplotlib
        from sklearn.preprocessing import MinMaxScaler
        DF_Uk1 = pd.read_csv("/home/sharedVol/uk_data.csv")
        font = {'weight' : 'bold','size'   : 18}
        matplotlib.rc('font', **font)
        plt.figure(figsize=(12,8))
        DF_Uk_u=DF_Uk1.copy()
        DF_Uk_u.index=DF_Uk_u.Day
        DF_Uk_u['Case_Fatality_Ratio'].plot()
        plt.ylabel('Case Fatality Ratio')
        plt.grid()
        plt.savefig('/home/sharedVol/Case_Fatality_Ratio.png')
        plt.figure(figsize=(12,8))
        DF_Uk_u=DF_Uk1.copy()
        DF_Uk_u.index=DF_Uk_u.Day
        DF_Uk_u['Confirmed'].plot()
        plt.ylabel('Confirmed')
        plt.grid()
        plt.savefig('/home/sharedVol/Confirmed.png')
        plt.figure(figsize=(12,8))
        DF_Uk_u=DF_Uk1.copy()
        DF_Uk_u.index=DF_Uk_u.Day
        DF_Uk_u['Active'].plot()
        plt.ylabel('Active')
        plt.grid()
        plt.savefig('/home/sharedVol/Active.png')
        Selec_Columns=['Confirmed','Deaths', 'Recovered', 'Active', 'Incident_Rate','Case_Fatality_Ratio']
        DF_Uk_u_2=DF_Uk_u[Selec_Columns]
        min_max_scaler = MinMaxScaler()
        DF_Uk_u_3 = pd.DataFrame(min_max_scaler.fit_transform(DF_Uk_u_2[Selec_Columns]),columns=Selec_Columns)
        DF_Uk_u_3.index=DF_Uk_u_2.index
        DF_Uk_u_3['Day']=DF_Uk_u.Day
        #DF_Uk_u_3.head(3)
        DF_Uk_u_3[Selec_Columns].plot(figsize=(20,10))
        plt.savefig('/home/sharedVol/Uk_scoring_report.png')
        DF_Uk_u_3.to_csv('/home/sharedVol/Uk_scoring_report.csv')
        DF_Uk_u_2.to_csv('/home/sharedVol/Uk_scoring_report_NotScaled.csv')


def _install_tools():
	
    try:
        import psycopg2
    except:
        subprocess.check_call(['pip', 'install', 'psycopg2-binary'])
        import psycopg2
    
    try:
        from sqlalchemy import inspect,create_engine
    except:
        subprocess.check_call(['pip', 'install', 'sqlalchemy'])
        from sqlalchemy import inspect,create_engine

    try:
        import pandas as pd
    except:
        subprocess.check_call(['pip', 'install', 'pandas'])
        import pandas as pd
    
    try:
        from matplotlib import pyplot
    except:
        subprocess.check_call(['pip', 'install', 'matplotlib'])
        from matplotlib import pyplot
     
    try:
        from sklearn.preprocessing import MinMaxScaler
    except:
        subprocess.check_call(['pip', 'install', 'sklearn'])
        from sklearn.preprocessing import MinMaxScaler




with DAG("uk_covid_19", start_date=datetime(2021, 1, 1),
         schedule_interval="0 0 * * *", catchup=False) as dag:

    install_tools = PythonOperator(
        task_id="install_tools",
        python_callable=_install_tools
    )
    read_csv_file_preprocessing = PythonOperator(
        task_id="read_csv_preprocessing",
        python_callable=_read_csv_file_preprocessing
    )

    push_get_data_to_postgres = PythonOperator(
        task_id="postgress_push_get",
        python_callable=_push_get_data_to_postgres
    )

    data_visualization = PythonOperator(
        task_id="data_visualization",
        python_callable=_data_visualization
    )


    install_tools >> read_csv_file_preprocessing  >> data_visualization >> push_get_data_to_postgres