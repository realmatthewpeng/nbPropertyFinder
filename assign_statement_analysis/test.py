
import numpy as np
import pandas as pd
from pandas import Series,DataFrame
df = pd.read_csv("hotels_data.csv")
__infer_target_1186__4 = df
reveal_type(__infer_target_1186__4)


from datetime import datetime
from dateutil.parser import parse

#parsing string to date time format
def get_datetime(date_str):
    return datetime.strptime(date_str, '%m/%d/%Y %H:%M')

df["DayDiff"] = DataFrame([get_datetime(val) for val in df["Checkin Date"]]) - DataFrame([get_datetime(val) for val in df["Snapshot Date"]])
__infer_target_1187__13 = df['DayDiff']
reveal_type(__infer_target_1187__13)

df["WeekDay"] = DataFrame([get_datetime(val).weekday() for val in df["Checkin Date"]])
__infer_target_1188__14 = df['WeekDay']
reveal_type(__infer_target_1188__14)

df["DiscountDiff"] = df["Original Price"] - df["Discount Price"]
__infer_target_1189__15 = df['DiscountDiff']
reveal_type(__infer_target_1189__15)

df["DiscountPerc"] = (df["DiscountDiff"]/df["Original Price"]) * 100
__infer_target_1190__16 = df['DiscountPerc']
reveal_type(__infer_target_1190__16)


df


#counting and sorting by common hotel name
df["Hotel_Count"] = df.groupby('Hotel Name')['Hotel Name'].transform('count')
__infer_target_1191__2 = df['Hotel_Count']
reveal_type(__infer_target_1191__2)

descending_hotels = df.sort_values(by=['Hotel_Count'],ascending=False).reset_index()
__infer_target_1192__3 = descending_hotels
reveal_type(__infer_target_1192__3)


#getting first 150 hotels  
df_hotels = descending_hotels["Hotel Name"].unique()[:150]
__infer_target_1193__6 = df_hotels
reveal_type(__infer_target_1193__6)

most_common_hotels = descending_hotels[descending_hotels['Hotel Name'].isin(df_hotels)]
__infer_target_1194__7 = most_common_hotels
reveal_type(__infer_target_1194__7)




#counting and sorting by common checking_data
most_common_hotels["Checkin_Count"] = most_common_hotels.groupby('Checkin Date')['Checkin Date'].transform('count')
__infer_target_1195__2 = most_common_hotels['Checkin_Count']
reveal_type(__infer_target_1195__2)

descending_most_common_hotels = most_common_hotels.sort_values(by=['Checkin_Count'],ascending=False).reset_index()
__infer_target_1196__3 = descending_most_common_hotels
reveal_type(__infer_target_1196__3)


#getting first 40 checkins  
common_checkins_list = descending_most_common_hotels["Checkin Date"].unique()[:40]
__infer_target_1197__6 = common_checkins_list
reveal_type(__infer_target_1197__6)

most_checkins = descending_most_common_hotels[descending_most_common_hotels['Checkin Date'].isin(common_checkins_list)]
__infer_target_1198__7 = most_checkins
reveal_type(__infer_target_1198__7)




unique_hotels_names = most_checkins["Hotel Name"].unique()
__infer_target_1199__1 = unique_hotels_names
reveal_type(__infer_target_1199__1)

unique_checkins =  most_checkins["Checkin Date"].unique()
__infer_target_1200__2 = unique_checkins
reveal_type(__infer_target_1200__2)

unique_discount_code =  [1,2,3,4]
__infer_target_1201__3 = unique_discount_code
reveal_type(__infer_target_1201__3)


#creating default data - all combination : checking -hotel - discount code
import itertools
import sys
combs = []
__infer_target_1202__8 = combs
reveal_type(__infer_target_1202__8)

for x in unique_hotels_names:
    for y in unique_checkins:
        for z in unique_discount_code:
            combs.append([x, y,z,sys.maxsize])

# converting the default data to data frame and appending to existing
new_df =  DataFrame.from_records(combs,columns=["Hotel Name","Checkin Date","Discount Code","Discount Price"])
__infer_target_1203__15 = new_df
reveal_type(__infer_target_1203__15)

most_checkins = most_checkins.append(new_df)
__infer_target_1204__16 = most_checkins
reveal_type(__infer_target_1204__16)



# finding minimum  discount price outa  hotel name - checking date - discount code group and fixing data
most_checkins["Discount Price"]= most_checkins.groupby(['Hotel Name','Checkin Date','Discount Code'])["Discount Price"].transform('min')
__infer_target_1205__2 = most_checkins['Discount Price']
reveal_type(__infer_target_1205__2)

most_checkins.drop_duplicates(subset=["Hotel Name","Checkin Date","Discount Code"], inplace=True)
most_checkins.sort_values(by=["Hotel Name","Checkin Date","Discount Code"],ascending=True,inplace=True)
most_checkins['Discount Price'].replace(sys.maxsize, -1, inplace=True)

# taking only needed data
checkin_hotel_discount = most_checkins[["Hotel Name","Checkin Date","Discount Code","Discount Price"]].reset_index()
__infer_target_1206__8 = checkin_hotel_discount
reveal_type(__infer_target_1206__8)




#normalizing only positive numbers, ignoring -1 values
discount_filtered = checkin_hotel_discount[checkin_hotel_discount['Discount Price'] > -1 ]
__infer_target_1207__2 = discount_filtered
reveal_type(__infer_target_1207__2)


def normalize_data(x):
    diff = max(x) - min(x)
    __infer_target_1208__5 = diff
    reveal_type(__infer_target_1208__5)

    if(diff == 0):
        return 0
    else:
        return (round( ( x - min(x) ) / ( max(x) - min(x) ) * 100 ))

discount_filtered_grouped = discount_filtered.groupby('Hotel Name')['Discount Price']
__infer_target_1209__11 = discount_filtered_grouped
reveal_type(__infer_target_1209__11)

discount_filtered["Normal"] = discount_filtered_grouped.transform(normalize_data) 
__infer_target_1210__12 = discount_filtered['Normal']
reveal_type(__infer_target_1210__12)


discount_synth = checkin_hotel_discount[checkin_hotel_discount['Discount Price'] == -1 ]
__infer_target_1211__14 = discount_synth
reveal_type(__infer_target_1211__14)

discount_synth["Normal"] = -1
__infer_target_1212__15 = discount_synth['Normal']
reveal_type(__infer_target_1212__15)


#checkin_hotel_discount
normal_dataFrame = discount_synth.append(discount_filtered)
__infer_target_1213__18 = normal_dataFrame
reveal_type(__infer_target_1213__18)

normal_dataFrame.sort_values(by=["Hotel Name","Checkin Date","Discount Code"],ascending=True,inplace=True)
normal_dataFrame


# NOTES
# We had an issue with N/A values.
# There were few possiboles reasons for this problem.
# One Posibility is that we had one row per hotel name (the rest were -1 and weren't included in this data frame ) and the calculate of max value less min value gave as zero.
# Another posibility is that all the rows of the hotels were equal and the maximun and minimum value price were equal.
# We solved this issue by checking if the maximum and minimum value of hotel names group by is 0, and return 0 and not calculating and dividing by 0.


# building list out of each value of hotel name
rows = []
__infer_target_1214__2 = rows
reveal_type(__infer_target_1214__2)

def createRow(x):    
    new_list = x.tolist()
    __infer_target_1215__4 = new_list
    reveal_type(__infer_target_1215__4)

    new_list.insert(0,x.name)
    rows.append(new_list)
    
#converting the list to multi-columns data frame
normal_dataFrame.groupby("Hotel Name")["Normal"].transform( createRow )  # group by returns for each hotel a list of his normalized prices
vector = pd.DataFrame.from_records(rows)
__infer_target_1216__10 = vector
reveal_type(__infer_target_1216__10)


# NOTES
# Vector - each row represents a hotel along with his 160 normalized prices



#importing clustering libaries 
from scipy.cluster.hierarchy import dendrogram, linkage 
from matplotlib import pyplot as plt
from scipy import cluster
shc = cluster.hierarchy
__infer_target_1217__5 = shc
reveal_type(__infer_target_1217__5)


#preproccesing data for clustering
labels = vector.values[:,0]
__infer_target_1218__8 = labels
reveal_type(__infer_target_1218__8)

data = vector.values[:,1:160]
__infer_target_1219__9 = data
reveal_type(__infer_target_1219__9)

plt.figure(figsize=(20, 10))  
plt.title("Clustering Hotels")  

# "ward" - minimizes the variance between clusters, that means that each two clusters were combine if their variance is close to each other 
Z = shc.linkage(data, method='ward')
__infer_target_1220__14 = Z
reveal_type(__infer_target_1220__14)

dend = shc.dendrogram(Z, labels=labels) 
__infer_target_1221__15 = dend
reveal_type(__infer_target_1221__15)

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
__infer_target_1222__4 = cluster
reveal_type(__infer_target_1222__4)

clusters = cluster.fit_predict(vector.values[:,1:160])  
__infer_target_1223__5 = clusters
reveal_type(__infer_target_1223__5)


hotels = pd.DataFrame.from_records(vector.values)
__infer_target_1224__7 = hotels
reveal_type(__infer_target_1224__7)


hotels["cluster"] = clusters
__infer_target_1225__9 = hotels['cluster']
reveal_type(__infer_target_1225__9)

hotels = hotels[[0,"cluster"]]
__infer_target_1226__10 = hotels
reveal_type(__infer_target_1226__10)

hotels.sort_values(by=["cluster"],ascending=True,inplace=True)

hotels["Count"] = hotels.groupby("cluster")[0].transform("count")
__infer_target_1227__13 = hotels['Count']
reveal_type(__infer_target_1227__13)

hotels

# NOTES
# In order to understand our data and get a cleaer picture of out data, we have mapped the hotel names to clusters in a data frame.  


from sklearn.decomposition import PCA
from sklearn.datasets import load_iris
from sklearn.cluster import AgglomerativeClustering


pca = PCA(n_components=2).fit(data)
__infer_target_1228__6 = pca
reveal_type(__infer_target_1228__6)

pca_2d = pca.transform(data)
__infer_target_1229__7 = pca_2d
reveal_type(__infer_target_1229__7)


cluster = AgglomerativeClustering(n_clusters=3, affinity='euclidean', linkage='ward')  
__infer_target_1230__9 = cluster
reveal_type(__infer_target_1230__9)

cluster.fit_predict(pca_2d)  

plt.figure(figsize=(10, 7))  
plt.scatter(pca_2d[:,0],pca_2d[:,1],c=cluster.labels_, cmap='rainbow')  


