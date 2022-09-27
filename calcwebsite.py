import streamlit as st 
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go


st.set_page_config(layout="wide")

repeating_docs = ["xray", "ip", "consultation", "mri", "bloodTest", "mammogram"]

## DEFAULT DATA


#               0          1          2          3        4        5
# value list = [commision, min_value, max_value, freq_l , freq_m , freq_h]

costs = {}
costs["xray"] =         [0.01, 200, 600, 0, 1, 1]
costs["ip"] =           [0.01, 5000, 30000, 0, 1, 3]
costs["consultation"] = [0.01, 250, 2500, 1, 3, 6]  
costs["mri"] =          [0.01, 3500, 25000, 0, 1, 2]
costs["bloodTest"] =    [0.01, 215, 850, 1, 3, 7]  
costs["mammogram"] =    [0.01, 2000, 8000, 0, 0.5, 0.5]

lower_bound_l = 0
higher_bound_l = 0
lower_bound_m = 0
higher_bound_m = 0
lower_bound_h = 0
higher_bound_h = 0

for i in costs:

    lower_bound_l += costs[i][1] * costs[i][3] * costs[i][0]
    higher_bound_l += costs[i][2] * costs[i][3] * costs[i][0]

    lower_bound_m += costs[i][1] * costs[i][4] * costs[i][0]
    higher_bound_m += costs[i][2] * costs[i][4] * costs[i][0]

    lower_bound_h += costs[i][1] * costs[i][5] * costs[i][0]
    higher_bound_h += costs[i][2] * costs[i][5] * costs[i][0]


#Revenues
revenues_l = []
revenues_m = []
revenues_h = []

for i in range(1,101):
    revenues_m.append(lower_bound_m*i)
    revenues_h.append(lower_bound_h*i)
    revenues_l.append(lower_bound_l*i) ## EDIT HERE

# Size in MB per document
# value list  = [source, jpg]

sizes = {}
sizes["xray"] = [14.3, 5.3]
sizes["ip"] = [1.1, 4.8]
sizes["consultation"] = [0.2, 1.6]
sizes["mri"] = [30, 30]
sizes["bloodTest"] = [2, 16]
sizes["mammogram"] = [19.4, 2.6]
sizes["base_records"] = [30, 30]

# AWS DATA

avg_obj_size_gb =  0.015625
put_cost=0.000005*80
get_cost=0.0000004*80

object_maintenance_cost_pm = 0.0000025*80
gb_storage_cost_pm = 0.0250000000*80
dynamodb_cost_pm = 0.2
ec2_cost_pm  = 1
read_pm = 6*30
write_pm = 1*30

s3_rw_cost_pm = read_pm*get_cost + write_pm*put_cost


##### FUNCTIONS ########


def cal_tot_size_1y_mb(risk):
    '''
    risk : low : 0 , med : 1, hi : 2
    '''
    tot_size_1y = []
    for i in range(2):
        sz = 0
        for doc in repeating_docs:
            sz += sizes[doc][i]*costs[doc][risk+3]
        # sz += sizes["base_records"][i]
        tot_size_1y.append(sz) 
    return tot_size_1y

def calc_object_count(tot_size_1y_mb):
    object_count = []
    for i in range(2):
        size = tot_size_1y_mb[i]
        obj_count = [((j*size + sizes["base_records"][i])/1024)/avg_obj_size_gb for j in range(1,101)]
        object_count.append(obj_count)
    return object_count

def calc_s3_cost_maintain(object_count):
    s3_cost_maintain = []
    for i in range(2):
        obj_count = object_count[i]
        s3_cost_mntn = [obj_count[j]*object_maintenance_cost_pm*12 for j in range(100)]
        s3_cost_maintain.append(s3_cost_mntn)
    return s3_cost_maintain

def calc_s3_cost_storage(tot_size_1y_mb):
    s3_cost_storage = []
    for i in range(2):
        sz = tot_size_1y_mb[i]
        s3_cost_strg = [(sz/1024)*gb_storage_cost_pm*12*j + sizes["base_records"][i]*gb_storage_cost_pm*12/1024 for j in range(1,101)]
        s3_cost_storage.append(s3_cost_strg)
    return s3_cost_storage


def calc_total_cost(risk):
    tot_size_1y_mb = cal_tot_size_1y_mb(risk)
    object_count = calc_object_count(tot_size_1y_mb)

    #PER YEAR, range from 1 till 100 , nested for SOURCE, JPG
    s3_cost_maintain = calc_s3_cost_maintain(object_count)
    s3_cost_storage = calc_s3_cost_storage(tot_size_1y_mb)

    total_cost = []
    for i in range(2):
        maintain, storage = s3_cost_maintain[i], s3_cost_storage[i]
        tot_cost = [ maintain[j]+storage[j]+ (dynamodb_cost_pm*12) + (ec2_cost_pm*12) + (s3_rw_cost_pm*12) for j in range(100)]
        total_cost.append(tot_cost)
    return total_cost

def calc_cumulative_cost(total_cost):
    cumulative_cost = []
    for i in range(2):
        costs = total_cost[i]
        c_cost = [costs[0]]
        for j in range(1,len(costs)):
            c_cost.append(costs[j]+c_cost[-1])
        cumulative_cost.append(c_cost)
    return cumulative_cost

def calc_profits(cumulative_cost, risk):
    if risk == 0:
        revenue = revenues_l[:]
    elif risk == 1:
        revenue = revenues_m[:]
    else:
        revenue = revenues_h[:]
    profits = []
    for i in range(2):
        c_cost = cumulative_cost[i]
        profits_dtype = []
        for j in range(100):
            profits_dtype.append(revenue[j]-c_cost[j])
        profits.append(profits_dtype)
    return profits, revenue


def plot_line(x, y, y2, ytitle, title, ylinelabel, y2linelabel):
    # Define X and Y variable data
    f = go.Figure()
    f.add_trace(go.Scatter(x=x, y = y, mode = "lines", name = ylinelabel))
    f.add_trace(go.Scatter(x=x, y=y2, mode = "lines", name = y2linelabel))
    f.update_layout(title=title, xaxis_title = "Years", yaxis_title = ytitle)
    return f

# def plot_line(x, y, y2, ylabel, title, ylinelabel, y2linelabel):
#     # Define X and Y variable data
#     f = plt.figure()

#     markers_on = np.array([i for i in range(0,101,10)])
#     font1 = {'family':'verdana','color':'black','size':20}

#     axarr = f.add_subplot(1,1,1)
#     plt.plot(x, y,linestyle="solid",linewidth=3,color="green",markevery=markers_on,marker="o",markersize=6,markeredgecolor="white",markerfacecolor="black",label=ylinelabel)
#     if y2:
#         plt.plot(x, y2,linestyle="solid",linewidth=3,color="red",markevery=markers_on,marker="o",markersize=6,markeredgecolor="white",markerfacecolor="black",label=y2linelabel)

#     plt.xlabel("Year",fontdict=font1)  # add X-axis label
#     plt.ylabel(ylabel,fontdict=font1)  # add Y-axis label
#     plt.title(title,fontdict=font1,x=0.49,y=1.05)  # add title
#     plt.legend(loc='best',facecolor="#E0E0E0",edgecolor="black",prop={"size":15})
#     plt.grid(color="dimgrey",alpha=0.5)
#     if y2:
#         for a,b,c in zip(x,y,y2):
#             if a%10==0:
#                 plt.annotate(f"\u20B9{b:.2f}",(a-5,b), fontsize=12)
#                 plt.annotate(f"\u20B9{c:.2f}",(a-5,c), fontsize=12)
#     else:
#         for a,b in zip(x,y):
#             if a%10==0:
#                 plt.annotate(f"\u20B9{b:.2f}",(a-5,b), fontsize=12)
#                 # plt.annotate(f"\u20B9{c:.2f}",(a-5,c), fontsize=12)
#     return f
## MODELLING

st.title("Financial Modelling")
risk_patient = st.selectbox("Select Patient Risk Profile",["Low risk", "Medium risk", "High risk"])

if (risk_patient == "Low risk"):
    total_cost = calc_total_cost(0)
    cumulative_cost = calc_cumulative_cost(total_cost)
    profits, revenue = calc_profits(cumulative_cost, 0)

elif risk_patient == "Medium risk":
    total_cost = calc_total_cost(1)
    cumulative_cost = calc_cumulative_cost(total_cost)
    profits, revenue = calc_profits(cumulative_cost, 1)

else:
    total_cost = calc_total_cost(2)
    cumulative_cost = calc_cumulative_cost(total_cost)
    profits, revenue = calc_profits(cumulative_cost, 2)
    #st.write(cumulative_cost)

col1, col2, col3 = st.columns(3)
with col2:
    st.header("Expenses till Year")
    f = plot_line(np.array([i for i in range(0,101)]) , [0] + cumulative_cost[0], [0] + cumulative_cost[1], "Total cost till year" , f"{risk_patient} patient", "Source format", "JPG format")
    st.plotly_chart(f)
with col1:
    st.header("Revenue till Year")
    f = plot_line(np.array([i for i in range(0,101)]) , [0] + revenue, None, "Total revenue till year" , f"{risk_patient} patient", "Revenue", None)
    st.plotly_chart(f)
with col3:
    st.header("Profit till Year")
    f = plot_line(np.array([i for i in range(0,101)]) , [0] + profits[0] , [0] + profits[1], "Total profit till year", f"{risk_patient} patient", "Source file format", "JPG format")
    st.plotly_chart(f)