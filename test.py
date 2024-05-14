
import numpy as np
import pandas as pd
from pandas import Series,DataFrame
df = pd.read_csv("hotels_data.csv")

from datetime import datetime
from dateutil.parser import parse

#parsing string to date time format
def get_datetime(date_str):
    return datetime.strptime(date_str, '%m/%d/%Y %H:%M')

df["DayDiff"] = DataFrame([get_datetime(val) for val in df["Checkin Date"]]) - DataFrame([get_datetime(val) for val in df["Snapshot Date"]])
df["WeekDay"] = DataFrame([get_datetime(val).weekday() for val in df["Checkin Date"]])
df["DiscountDiff"] = df["Original Price"] - df["Discount Price"]
df["DiscountPerc"] = (df["DiscountDiff"]/df["Original Price"]) * 100

df
__infer_target_31__18 = df
reveal_type(__infer_target_31__18)



#counting and sorting by common hotel name
df["Hotel_Count"] = df.groupby('Hotel Name')['Hotel Name'].transform('count')
descending_hotels = df.sort_values(by=['Hotel_Count'],ascending=False).reset_index()

#getting first 150 hotels  
df_hotels = descending_hotels["Hotel Name"].unique()[:150]
most_common_hotels = descending_hotels[descending_hotels['Hotel Name'].isin(df_hotels)]



#counting and sorting by common checking_data
most_common_hotels["Checkin_Count"] = most_common_hotels.groupby('Checkin Date')['Checkin Date'].transform('count')
descending_most_common_hotels = most_common_hotels.sort_values(by=['Checkin_Count'],ascending=False).reset_index()

#getting first 40 checkins  
common_checkins_list = descending_most_common_hotels["Checkin Date"].unique()[:40]
most_checkins = descending_most_common_hotels[descending_most_common_hotels['Checkin Date'].isin(common_checkins_list)]



unique_hotels_names = most_checkins["Hotel Name"].unique()
unique_checkins =  most_checkins["Checkin Date"].unique()
unique_discount_code =  [1,2,3,4]

#creating default data - all combination : checking -hotel - discount code
import itertools
import sys
combs = []
for x in unique_hotels_names:
    for y in unique_checkins:
        for z in unique_discount_code:
            combs.append([x, y,z,sys.maxsize])

# converting the default data to data frame and appending to existing
new_df =  DataFrame.from_records(combs,columns=["Hotel Name","Checkin Date","Discount Code","Discount Price"])
most_checkins = most_checkins.append(new_df)


# finding minimum  discount price outa  hotel name - checking date - discount code group and fixing data
most_checkins["Discount Price"]= most_checkins.groupby(['Hotel Name','Checkin Date','Discount Code'])["Discount Price"].transform('min')
most_checkins.drop_duplicates(subset=["Hotel Name","Checkin Date","Discount Code"], inplace=True)
most_checkins.sort_values(by=["Hotel Name","Checkin Date","Discount Code"],ascending=True,inplace=True)
most_checkins['Discount Price'].replace(sys.maxsize, -1, inplace=True)

# taking only needed data
checkin_hotel_discount = most_checkins[["Hotel Name","Checkin Date","Discount Code","Discount Price"]].reset_index()



#normalizing only positive numbers, ignoring -1 values
discount_filtered = checkin_hotel_discount[checkin_hotel_discount['Discount Price'] > -1 ]

def normalize_data(x):
    diff = max(x) - min(x)
    if(diff == 0):
        return 0
    else:
        return (round( ( x - min(x) ) / ( max(x) - min(x) ) * 100 ))

discount_filtered_grouped = discount_filtered.groupby('Hotel Name')['Discount Price']
discount_filtered["Normal"] = discount_filtered_grouped.transform(normalize_data) 

discount_synth = checkin_hotel_discount[checkin_hotel_discount['Discount Price'] == -1 ]
discount_synth["Normal"] = -1

#checkin_hotel_discount
normal_dataFrame = discount_synth.append(discount_filtered)
normal_dataFrame.sort_values(by=["Hotel Name","Checkin Date","Discount Code"],ascending=True,inplace=True)
normal_dataFrame
__infer_target_32__20 = normal_dataFrame
reveal_type(__infer_target_32__20)



# NOTES
# We had an issue with N/A values.
# There were few possiboles reasons for this problem.
# One Posibility is that we had one row per hotel name (the rest were -1 and weren't included in this data frame ) and the calculate of max value less min value gave as zero.
# Another posibility is that all the rows of the hotels were equal and the maximun and minimum value price were equal.
# We solved this issue by checking if the maximum and minimum value of hotel names group by is 0, and return 0 and not calculating and dividing by 0.


# building list out of each value of hotel name
rows = []
def createRow(x):    
    new_list = x.tolist()
    new_list.insert(0,x.name)
    rows.append(new_list)
    
#converting the list to multi-columns data frame
normal_dataFrame.groupby("Hotel Name")["Normal"].transform( createRow )  # group by returns for each hotel a list of his normalized prices
vector = pd.DataFrame.from_records(rows)

# NOTES
# Vector - each row represents a hotel along with his 160 normalized prices



#importing clustering libaries 
from scipy.cluster.hierarchy import dendrogram, linkage 
from matplotlib import pyplot as plt
from scipy import cluster
shc = cluster.hierarchy

#preproccesing data for clustering
labels = vector.values[:,0]
data = vector.values[:,1:160]
plt.figure(figsize=(20, 10))  
plt.title("Clustering Hotels")  

# "ward" - minimizes the variance between clusters, that means that each two clusters were combine if their variance is close to each other 
Z = shc.linkage(data, method='ward')
dend = shc.dendrogram(Z, labels=labels) 
plt.show(dend)


# NOTES
# The purpose of finding groups of hotels with similarity in their pricing policy is to be able 
# to break a vacation into multiple different hotels which gurantees a minimum price.
# The naive solution is finding all the combinations for the desired date range.
# An alternative way is finding the cheapest hotel for the desired date and 
# performing a naive search of all the combinations within the current hotel's cluster, instead of searching all the hotels.



from sklearn.cluster import AgglomerativeClustering

#running the algorithem again in a diffrent way
cluster = AgglomerativeClustering(n_clusters=3, affinity='euclidean', linkage='ward')  
clusters = cluster.fit_predict(vector.values[:,1:160])  

hotels = pd.DataFrame.from_records(vector.values)

hotels["cluster"] = clusters
hotels = hotels[[0,"cluster"]]
hotels.sort_values(by=["cluster"],ascending=True,inplace=True)

hotels["Count"] = hotels.groupby("cluster")[0].transform("count")
hotels
__infer_target_33__14 = hotels
reveal_type(__infer_target_33__14)


# NOTES
# In order to understand our data and get a cleaer picture of out data, we have mapped the hotel names to clusters in a data frame.  


from sklearn.decomposition import PCA
from sklearn.datasets import load_iris
from sklearn.cluster import AgglomerativeClustering


pca = PCA(n_components=2).fit(data)
pca_2d = pca.transform(data)

cluster = AgglomerativeClustering(n_clusters=3, affinity='euclidean', linkage='ward')  
cluster.fit_predict(pca_2d)  

plt.figure(figsize=(10, 7))  
plt.scatter(pca_2d[:,0],pca_2d[:,1],c=cluster.labels_, cmap='rainbow')  


