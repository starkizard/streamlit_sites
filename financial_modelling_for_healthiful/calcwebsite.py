## TODO
"""
revenues for each type ( 6 sliders , min = 0 ) :  DONE
commision slider ( 0 - 5% , float) , Across the board commision checkbox : DONE
number of years of usage integer input : DONE
ranges for low / med / high / inactivity risk : DONE
base file size (slider from 0 to 500MB) : DONE
edit profile frequency : DONE
profitability feedback
margin graph
"""


from pandas import lreshape
import streamlit as st 
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from torch import are_deterministic_algorithms_enabled, cos


st.set_page_config(layout="wide")

repeating_docs = ["xray", "ip", "consultation", "mri", "bloodTest", "mammogram"]

## DEFAULT DATA


#               0          1          2          3        4        5       6
# value list = [commision, min_value, max_value, freq_l , freq_m , freq_h, value]

costs = {}
costs["xray"] =         [0.01, 200, 600, 0, 1, 1, -1]
costs["ip"] =           [0.01, 5000, 30000, 0, 1, 3, -1]
costs["consultation"] = [0.01, 250, 2500, 1, 3, 6, -1]  
costs["mri"] =          [0.01, 3500, 25000, 0, 1, 2, -1]
costs["bloodTest"] =    [0.01, 215, 850, 1, 3, 7, -1]  
costs["mammogram"] =    [0.01, 2000, 8000, 0, 0.5, 0.5, -1]


# Size in MB per document
# value list  = [source, jpg]

sizes = {}
sizes["xray"] = 14.3
sizes["ip"] = 1.1
sizes["consultation"] = 0.2
sizes["mri"] = 30
sizes["bloodTest"] = 2
sizes["mammogram"] = 19.4
sizes["base_records"] = 30

# # AWS DATA

avg_obj_size_gb =  0.015625
put_cost=0.000005*80
get_cost=0.0000004*80

object_maintenance_cost_pm = 0.0000025*80
gb_storage_cost_pm = 0.0250000000*80
gb_glacier_cost_pm = 0.004*80
dynamodb_cost_pm = 0.2
ec2_cost_pm  = 1
read_pm = 6*30
write_pm = 1*30

s3_rw_cost_pm = read_pm*get_cost + write_pm*put_cost

def plot_line(x, y, y2, ytitle, title, ylinelabel, y2linelabel):
    # Define X and Y variable data
    f = go.Figure()
    f.add_trace(go.Scatter(x=x, y = y, mode = "lines", name = ylinelabel))
    if y2:
        f.add_trace(go.Scatter(x=x, y=y2, mode = "lines", name = y2linelabel))
    f.update_layout(title=title, xaxis_title = "Years", yaxis_title = ytitle)
    return f

error = False
st.title("Financial Modelling")
#risk_patient = st.selectbox("Select Patient Risk Profile",["Low risk", "Medium risk", "High risk"])
with st.expander("Edit risk profile consultation frequencies"):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text("Low risk")
        for i in costs:
            costs[i][3] = st.number_input(f"{i.upper()} visit freq", value = costs[i][3], key= 0)
    with c2:
        st.text("Medium risk")
        for i in costs:
            costs[i][4] = st.number_input(f"{i.upper()} visit freq", value = costs[i][4], key = 1)
    with c3:
        st.text("High risk")
        for i in costs:
            costs[i][5] = st.number_input(f"{i.upper()} visit freq", value = costs[i][5], key = 2)

all_commision = st.checkbox("Enable commision edit for each consultation type")
if all_commision:
    col1, col2, col3 = st.columns(3)
else:
    col1, col2 = st.columns(2)
with col1:
    years_of_usage = st.number_input("Enter the years of usage of patient", value = 10)
    risk_of_year = [-1]*years_of_usage
    st.text("Enter Ranges for risk profiling ( Avoid whitespaces )")
    low_risk_range = st.text_input("Low risk ranges", value = "0-1,6-7")
    medium_risk_range = st.text_input("Medium risk ranges", value = "4-5")
    high_risk_range = st.text_input("High risk ranges", value ="3,8-9")
    
    # Overlapping ranges check and ranges input
    low_risk_rangelist, medium_risk_rangelist, high_risk_rangelist = [], [], []
    l_ranges = low_risk_range.split(',')
    m_ranges = medium_risk_range.split(',')
    h_ranges = high_risk_range.split(',')
    overlapping = False
    sizes["base_records"] = st.slider("Enter base records size in MB", 0,500,30)
    def add_to_risk_of_year(ranges,risk):
        global overlapping
        for i in ranges:
            if i == "":
                continue
            if '-' in i:
                l,r = map(int, i.split('-'))
            else:
                l,r = int(i), int(i)

            for j in range(l,r+1):
                if risk_of_year[j]!=-1:
                    overlapping = True
                    break
                else:
                    risk_of_year[j] = risk
    add_to_risk_of_year(l_ranges,0)
    add_to_risk_of_year(m_ranges,1)
    add_to_risk_of_year(h_ranges,2)

    if overlapping:
        st.error('Overlapping found in ranges')
        error = True
with col2:
    for i in costs:
        costs[i][6] = st.slider(f"{i.upper()} cost per visit",0,costs[i][2],costs[i][1])
    if not all_commision:
        commision = st.slider("Commission % per visit", 0.01 , 5.0, 1.0)/100
        for i in costs:
            costs[i][0] = commision
if all_commision:
    with col3:
        for i in costs:
            costs[i][0] = st.slider(f"{i.upper()} commission % per visit", 0.01, 5.0 , 1.0)/100
    

if not error:
    # DO ALL CALC HERE
    
    # calc tot size for 1 year for each risk profile
    low_1y_size , medium_1y_size, high_1y_size = 0, 0, 0
    for i in repeating_docs:
        low_1y_size += sizes[i]*costs[i][3]
        medium_1y_size += sizes[i]*costs[i][4]
        high_1y_size += sizes[i]*costs[i][5]
    
    lmh_risk_size = [low_1y_size, medium_1y_size, high_1y_size]
    
    # calc cum_tot_size for every year
    cum_tot_size = [0]
    for i in range(years_of_usage):
        if risk_of_year[i] == -1:
            cum_tot_size.append(cum_tot_size[-1])
        else:
            cum_tot_size.append(cum_tot_size[-1]+lmh_risk_size[risk_of_year[i]])
    

    ## adding base records
    for i in range(1,years_of_usage+1):
        cum_tot_size[i] += sizes["base_records"]

    # st.write("TOTAL CUMULATIVE SIZE")
    # st.write(cum_tot_size)

    # calc cum_object_count for every year
    cum_object_count = []
    for i in cum_tot_size:
        cum_object_count.append(i/16)
    
    # calc cost_s3_maintain
    cost_s3_maintain = []
    for i in cum_object_count:
        cost_s3_maintain.append(i*object_maintenance_cost_pm*12)
    
    # st.write("Per year maintenance cost")
    # st.write(cost_s3_maintain)

    # calc total s3_maintenance_cost
    cost_s3_total_maintain = [0]
    for i in cost_s3_maintain[1:]:
        cost_s3_total_maintain.append(cost_s3_total_maintain[-1] + i)
    
    # st.write("Cumulative maintenance cost")
    # st.write(cost_s3_total_maintain)
    
    # calc cost_s3_storage per year
    cost_s3_storage = []
    for idx,i in enumerate(cum_tot_size):
        if risk_of_year[idx-1] == -1:
            cost_s3_storage.append(gb_glacier_cost_pm*12*i/1024)
        else:
            cost_s3_storage.append(gb_storage_cost_pm*12*i/1024)
    
    # st.write("per year s3 storage cost")
    # st.write(cost_s3_storage)

    # cum tot storage 
    cost_s3_total_storage = [0]
    for i in cost_s3_storage[1:]:
        cost_s3_total_storage.append(cost_s3_total_storage[-1] + i)
    
    # st.write("cumulative s3 storage cost")
    # st.write(cost_s3_total_storage)

    #calc read/write cost
    cost_s3_rw = [0]
    for i in range(1,years_of_usage+1):
        cost_s3_rw.append(i*s3_rw_cost_pm*12)

    # st.write("Cumulative read/write cost")
    # st.write(cost_s3_rw)

    #calc dynamodb cost 
    cost_dynamodb = [0]
    for i in range(1,years_of_usage+1):
        cost_dynamodb.append(i*dynamodb_cost_pm*12)

    # st.write("Cumulative dynamoDB cost")
    # st.write(cost_dynamodb)

    #calc ec2 cost 
    cost_ec2 = [0]
    for i in range(1,years_of_usage+1):
        cost_ec2.append(i*ec2_cost_pm*12)

    # st.write("Cumulative ec2 cost")
    # st.write(cost_ec2)


    #total_cost
    total_cost = []
    for i in range(len(cost_s3_total_storage)):
        total_cost.append(cost_s3_total_maintain[i] + cost_s3_total_storage[i] + cost_s3_rw[i] + cost_dynamodb[i] + cost_ec2[i])
    
    # st.write("Total cost")
    # st.write(total_cost)

    #calc revenue per year for risk profile
    revenue_py_l, revenue_py_m, revenue_py_h = 0, 0, 0
    for i in costs:
        revenue_py_l += costs[i][0] * costs[i][6] * costs[i][3]
        #st.write(revenue_py_l)
        revenue_py_m += costs[i][0] * costs[i][6] * costs[i][4]
        revenue_py_h += costs[i][0] * costs[i][6] * costs[i][5]
    
    lmh_revenue_py = [revenue_py_l, revenue_py_m, revenue_py_h]
    #st.write(lmh_revenue_py)
    cum_tot_revenue = [0]
    for i in range(years_of_usage):
        if risk_of_year[i] == -1:
            cum_tot_revenue.append(cum_tot_revenue[-1])
        else:
            cum_tot_revenue.append(cum_tot_revenue[-1]+lmh_revenue_py[risk_of_year[i]])
    
    #st.write((cum_tot_revenue))

    cum_tot_profits = []
    for i in range(years_of_usage+1):
        cum_tot_profits.append(cum_tot_revenue[i]-total_cost[i])

    margin_for_year = [0]
    for i in range(2,years_of_usage+1):
        if (cum_tot_revenue[i]-cum_tot_revenue[i-1]) == 0:
            margin_for_year.append(0)
        else:
            margin_for_year.append( (cum_tot_profits[i] - cum_tot_profits[i-1])/(cum_tot_revenue[i]-cum_tot_revenue[i-1]) )
    



    col1, col2 = st.columns(2)
    with col1:
        st.header("Revenue")
        f = plot_line([i for i in range(len(cum_tot_revenue))], cum_tot_revenue, None, "Cumulative revenue", "Total revenue till year", None, None)
        st.plotly_chart(f)
    with col2:
        st.header("Expenses")
        f = plot_line([i for i in range(len(total_cost))], total_cost, None, "Cumulative expenses", "Total Costs till year", None, None)
        st.plotly_chart(f)

    col1_, col2_ = st.columns(2)
    with col1_:
        st.header("Profits")
        f = plot_line([i for i in range(len(cum_tot_profits))], cum_tot_profits, None, "Cumulative profits", "Total Profit till year", None, None)
        st.plotly_chart(f)
    with col2_:
        st.header("Margin for year")
        f = plot_line([i for i in range(len(margin_for_year))], margin_for_year, None, "Margin for year ", "Margin ratio per year", None, None)
        st.plotly_chart(f)

    if(cum_tot_profits[-1] > 0):
        st.success("PROFITABLE SCENARIO")
    else:
        st.error("LOSS MAKING SCENARIO")
