# Data-Engineering-UK_Covid-19
## Build Data pipeline for UK covid-19 cases  by using Apache airflow DAGs


# Methodology:

- Prepare the environment by using the docker-compose file ( attached in the repository) images (jupyter/minimal-notebook,Airflow,and postgree).
- Get up-to-date data and preprocessing.
- Draw the relaitonship (Case_Fatality_Ratio,Time), (confirmed cases,Time) , (Active cases,Time) gragh for each relationship.
- Push the csv files to postgress DB
- Build Airflow DAG that contains all above process.


## 1. Prepare the environment by using the docker-compose file

After building the docker-compose file, use the below command:

```sh
docker compose up
```
| App |user|password |Link |
| ------|----|------ | ------ |
| AirFlow-webServer|airflow|airflow |http://localhost:8887/|
| pgAdmin|psut@admin.com|psut2022 |http://localhost:8889/|
| JupyterLab|-|psut2022 |http://localhost:8886/|
| postgress|psut|psut2022 ||


## 2. Get up-to-date data and preprocessing:

#### Build a list of days by using the below snippt ,our expermint the first day is 01-01-2021 until 12-31-2022

```py
List_of_days=[]
for year in range(2021,2022):
  for month in range(1,13):
    for day in range(1,32):
      month=int(month)
      if day <=9:
        day=f'0{day}'

      if month <= 9 :
        month=f'0{month}'
      List_of_days.append(f'{month}-{day}-{year}')
```
#### Build the function to get the data for one day and we will use to get all data for each day in the built list above:

```py
Day='01-01-2022'

def Get_DF_i(Day):
    DF_i=None
    try: 
        URL_Day=f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{Day}.csv'
        DF_day=pd.read_csv(URL_Day)
        DF_day['Day']=Day
        cond=(DF_day.Country_Region=='United Kingdom')
        Selec_columns=['Day','Country_Region', 'Last_Update',
              'Lat', 'Long_', 'Confirmed', 'Deaths', 'Recovered', 'Active',
              'Combined_Key', 'Incident_Rate', 'Case_Fatality_Ratio']
        DF_i=DF_day[cond][Selec_columns].reset_index(drop=True)
    except:
    #print(f'{Day} is not available!')
        pass
    return DF_i

print(Get_DF_i(Day))

Day='02-31-2022'

print(Get_DF_i(Day))
```

#### Get the data for each day in the built list by using the below snippet (which May take a few minutes). In our example, we start from 2021:

```py
import time 

Start=time.time()
DF_all=[]
for Day in List_of_days:
    DF_all.append(Get_DF_i(Day))
End=time.time()
Time_in_sec=round((End-Start)/60,2)
print(f'It took {Time_in_sec} minutes to get all data')
```

#### Preprocessing data such as (add update Date, day, Incident_Rate, Case_Fatality_Ratio to float and aggregation by Day and Country Region:

#### Incident_Rate: Incidence Rate = cases per 100,000 persons.
#### Case_Fatality_Ratio (%): Case-Fatality Ratio (%) = Number recorded deaths / Number cases.

```py
DF_Uk=pd.concat(DF_all).reset_index(drop=True)
# Create DateTime for Last_Update
DF_Uk['Last_Updat']=pd.to_datetime(DF_Uk.Last_Update, infer_datetime_format=True)  
DF_Uk['Day']=pd.to_datetime(DF_Uk.Day, infer_datetime_format=True)  

DF_Uk['Case_Fatality_Ratio']=DF_Uk['Case_Fatality_Ratio'].astype(float)

DF_Uk.head(10)

DF_Uk1=DF_Uk.groupby(['Day', 'Country_Region']).agg({'Confirmed':'sum','Deaths':'sum','Recovered':'sum','Active':'sum'}).reset_index()
print(type(DF_Uk1))
DF_Uk1.head()

DF_Uk1["Incident_Rate"] = DF_Uk1["Confirmed"]/100000
DF_Uk1["Case_Fatality_Ratio"] = (DF_Uk1["Deaths"] / DF_Uk1["Confirmed"])*100
```

### 3. Draw the relaitonship (Case_Fatality_Ratio,Time), (confirmed cases,Time) , (Active cases,Time) gragh for each relationship.

#### Case_Fatality_Ratio,Time

```py
import matplotlib.pyplot as plt 
import matplotlib
font = {'weight' : 'bold',
        'size'   : 18}

matplotlib.rc('font', **font)

plt.figure(figsize=(12,8))
DF_India_u=DF_India.copy()
DF_India_u.index=DF_India_u.Day
DF_India_u['Case_Fatality_Ratio'].plot()
plt.ylabel('Case Fatality Ratio')
plt.grid()
```

![case ratio](https://user-images.githubusercontent.com/102326351/172721188-25501f43-7833-4be5-b025-9ad094690145.PNG)


#### confirmed cases,Time

```py
plt.figure(figsize=(12,8))
DF_Uk_u=DF_Uk1.copy()
DF_Uk_u.index=DF_Uk_u.Day
DF_Uk_u['Confirmed'].plot()
plt.ylabel('Confirmed')
plt.grid()
```
![convermied](https://user-images.githubusercontent.com/102326351/172721385-8f22db8f-a25b-4ddd-8fd1-a47a296b1b3e.PNG)

#### Active cases,Time

```py
plt.figure(figsize=(12,8))
DF_Uk_u=DF_Uk1.copy()
DF_Uk_u.index=DF_Uk_u.Day
DF_Uk_u['Active'].plot()
plt.ylabel('Active')
plt.grid()
```
![active](https://user-images.githubusercontent.com/102326351/172721569-336a7b6f-ad48-405c-91e5-4615c89b5a53.PNG)

#### Transform the following columns using MinMax Scaling to show all fields togther:
```py
'Confirmed','Deaths', 'Recovered', 'Active', 'Incident_Rate','Case_Fatality_Ratio'
```
```py
Selec_Columns=['Confirmed','Deaths', 'Recovered', 'Active', 'Incident_Rate','Case_Fatality_Ratio']
DF_Uk_u_2=DF_Uk_u[Selec_Columns]

DF_Uk_u_2

from sklearn.preprocessing import MinMaxScaler

min_max_scaler = MinMaxScaler()


DF_Uk_u_3 = pd.DataFrame(min_max_scaler.fit_transform(DF_Uk_u_2[Selec_Columns]),columns=Selec_Columns)
DF_Uk_u_3.index=DF_Uk_u_2.index
DF_Uk_u_3['Day']=DF_Uk_u.Day
DF_Uk_u_3.head(3)
```
![min max](https://user-images.githubusercontent.com/102326351/172722248-55e5c659-ef40-4183-a87a-fb15807ab5b8.PNG)

#### Plot all columns together:
```py
DF_Uk_u_3[Selec_Columns].plot(figsize=(20,10))
plt.savefig('/home/sharedVol/Uk_scoring_report.png')
```
![all](https://user-images.githubusercontent.com/102326351/172722813-d520ee2d-299f-409c-9954-53df0e557c95.PNG)

#### Save the scoring records as CSV files DF_Uk_u_2 DF_India_u_3:

```py
DF_Uk_u_3.to_csv('/home/sharedVol/Uk_scoring_report.csv')
DF_Uk_u_2.to_csv('/home/sharedVol/Uk_scoring_report_NotScaled.csv')
```

## 4. Push the csv files to postgress DB:
```py
from sqlalchemy import inspect,create_engine
import psycopg2
#you can check the below values from your docker-compose file
host="postgres_storage"
database="csv_db"
user="psut"
password="psut2022"
port='5432'
engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
insp = inspect(engine)
print(insp.get_table_names())
```

```py
from datetime import date
today = date.today()
Day=today.strftime("%d_%m_%Y")
DF_Uk_u_3.to_sql(f'Uk_scoring_report_{Day}', engine,if_exists='replace',index=False)
DF_Uk_u_2.to_sql(f'Uk_scoring_notscaled_report_{Day}', engine,if_exists='replace',index=False)
insp = inspect(engine)
print(insp.get_table_names())
```

![tables](https://user-images.githubusercontent.com/102326351/172727228-dbfa0281-a81d-4336-bbfc-768a707b61c4.PNG)


you can use the following snippt to check if the tables was uploaded or not :

```py
scores_extracted=pd.read_sql(f"SELECT * FROM uk_scoring_report_{Day}" , engine);
scores_not_scaled_extracted=pd.read_sql(f"SELECT * FROM uk_scoring_notscaled_report_{Day}" , engine);
scores_extracted.head(3)
```
![1](https://user-images.githubusercontent.com/102326351/172727537-ae8c5fed-9e8d-4668-812c-dfc04b724f75.PNG)

```py
scores_not_scaled_extracted.head(3)
```
![2](https://user-images.githubusercontent.com/102326351/172727798-b9e11433-edf9-4956-a509-2cce7a3afe65.PNG)

### 3. DAG airflow :

you can use the dag configuration from repo.

![DAG](https://user-images.githubusercontent.com/102326351/172734204-60af7961-e075-43d6-ad5f-4e17ec66cc84.PNG)




