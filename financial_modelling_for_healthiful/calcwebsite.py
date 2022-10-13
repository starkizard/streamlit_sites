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
sizes["xray"] = 13.6
sizes["ip"] = 1.5
sizes["consultation"] = 0.234
sizes["mri"] = 25
sizes["bloodTest"] = 1.5
sizes["mammogram"] = 18
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

st.title("Unit economics")
#risk_patient = st.selectbox("Select Patient Risk Profile",["Low risk", "Medium risk", "High risk"])
with st.expander("Edit risk profile consultation frequencies"):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text("Low risk")
        for i in costs:
            costs[i][3] = st.number_input(f"{i.upper()} visit freq", value = float(costs[i][3]), key= 0, step = 1.0 , min_value = 0.0, format = "%.2f")
    with c2:
        st.text("Medium risk")
        for i in costs:
            costs[i][4] = st.number_input(f"{i.upper()} visit freq", value = float(costs[i][4]), key = 1 , step = 1.0, min_value = 0.0, format = "%.2f")
    with c3:
        st.text("High risk")
        for i in costs:
            costs[i][5] = st.number_input(f"{i.upper()} visit freq", value = float(costs[i][5]), key = 2, step = 1.0, min_value = 0.0 , format = "%.2f")

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
    file_opening_charges = st.slider("Enter file opening charges",0,500,200)
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
    for i in range(1,len(cum_tot_revenue)):
        cum_tot_revenue[i] += file_opening_charges
    #st.write((cum_tot_revenue))

    cum_tot_profits = []
    for i in range(years_of_usage+1):
        cum_tot_profits.append(cum_tot_revenue[i]-total_cost[i])

    margin_for_year = [0]
    for i in range(1,years_of_usage+1):
        if (cum_tot_revenue[i]-cum_tot_revenue[i-1]) == 0:
            margin_for_year.append(0)
        else:
            margin_for_year.append( (cum_tot_profits[i] - cum_tot_profits[i-1])/(cum_tot_revenue[i]-cum_tot_revenue[i-1])*100 )
    
    cum_margin = []
    for i in range(years_of_usage+1):
        if (cum_tot_revenue[i]) == 0:
            cum_margin.append(0)
        else:
            cum_margin.append(cum_tot_profits[i]*100/cum_tot_revenue[i])


    if(cum_tot_profits[-1] > 0):
        st.success("PROFITABLE SCENARIO")
    else:
        st.error("LOSS MAKING SCENARIO")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Revenue")
        f = plot_line([i for i in range(len(cum_tot_revenue))], cum_tot_revenue, None, "Cumulative revenue", "Total revenue till year", None, None)
        st.plotly_chart(f, use_container_width=True)
    with col2:
        st.subheader("Expenses")
        f = plot_line([i for i in range(len(total_cost))], total_cost, None, "Cumulative expenses", "Total Costs till year", None, None)
        st.plotly_chart(f, use_container_width=True)
    with col3:
        st.subheader("Profits")
        f = plot_line([i for i in range(len(cum_tot_profits))], cum_tot_profits, None, "Cumulative profits", "Total Profit till year", None, None)
        st.plotly_chart(f, use_container_width=True)

    
    new_title = f'<p style="font-family:sans-serif; color:Green; font-size: 42px;">{str(round(cum_margin[-1],2)) + "%"}</p>'
    new_title_red = f'<p style="font-family:sans-serif; color:Red; font-size: 42px;">{str(round(cum_margin[-1],2)) + "%"}</p>'
    st.subheader("Gross margin for entire usage")
    if cum_margin[-1] > 0:
        st.markdown(new_title, unsafe_allow_html=True)
    else:
        st.markdown(new_title_red, unsafe_allow_html=True)

    #st.metric("",str(round(cum_margin[-1],2)) + "%")

    col1_, col2_ = st.columns(2)
    with col1_:
        st.subheader("Gross margin for years of usage")
        f = plot_line([i for i in range(len(cum_margin))], cum_margin, None, "Average Margin ", "Total Margin in % till year", None, None)
        st.plotly_chart(f, use_container_width=True)
        
    with col2_:
        st.subheader("Margin for year")
        f = plot_line([i for i in range(len(margin_for_year))], margin_for_year, None, "Margin for year ", "Margin in % per year", None, None)
        st.plotly_chart(f, use_container_width=True)

    st.title("Financial Forecasting")
    error = False
    no_of_users = st.number_input("Number of users",value = 400000, min_value=0)
    cagr = st.slider("CAGR %", 0.0,20.0,10.0)
    cols = st.columns(5)
    years_str = ["1st", "3rd", "5th", "7th", "10th"]
    lowrisk_percent = [0]*5
    mediumrisk_percent = [0]*5
    highrisk_percent = [0]*5
    inactive_percent  = [0]*5
    for i in range(5):
        with cols[i]:
            st.subheader(f"till {years_str[i]} year")
            lowrisk_percent[i] = st.number_input("Low risk %", value = 0, min_value=0, max_value = 100, key = f"l{i}")
            mediumrisk_percent[i] = st.number_input("Medium risk %", value =0, min_value=0, max_value = 100 - lowrisk_percent[i], key = f"m{i}")
            highrisk_percent[i] = st.number_input("High risk %", value = 0, min_value=0, max_value = 100 - mediumrisk_percent[i] - lowrisk_percent[i], key = f"h{i}") 
            inactive_percent[i] = 100 - lowrisk_percent[i] - mediumrisk_percent[i] - highrisk_percent[i]
            st.metric("Inactive %", str(inactive_percent[i]) + " %")
    
    total_revenue = [0]
    total_size = [0]
    total_objects = [0]
    total_size_till_now = sizes["base_records"]*no_of_users
    cost_maintenance = [0]
    cost_storage = [0]
    cost_ddb = [0]
    cost_cmpt = [0]
    cost_rw = [0]
    cost_employee = [0]

    tot_revenue_till_now = file_opening_charges*no_of_users
    def getindex(i):
        if i < 1:
            return 0
        if i < 3:
            return 1
        if i < 5:
            return 2
        if i < 7:
            return 3
        if i < 10:
            return 4

    for i in range(10):
        no_of_low_risk = no_of_users*lowrisk_percent[getindex(i)]/100
        no_of_med_risk = no_of_users*mediumrisk_percent[getindex(i)]/100
        no_of_high_risk = no_of_users*highrisk_percent[getindex(i)]/100
        no_of_inactive = no_of_users*inactive_percent[getindex(i)]/100
        
        tot_revenue_till_now += lmh_revenue_py[0]*no_of_low_risk + lmh_revenue_py[1]*no_of_med_risk + lmh_revenue_py[2]*no_of_high_risk
        total_revenue.append(tot_revenue_till_now*((1+cagr/100)**i))

        total_size_till_now += lmh_risk_size[0]*no_of_low_risk + lmh_risk_size[1]*no_of_med_risk + lmh_risk_size[2]*no_of_high_risk
        total_size.append(total_size_till_now)

        total_objects.append(total_size_till_now/16)
        cost_maintenance.append(total_size_till_now*object_maintenance_cost_pm*12/16)

        inactive_size = total_size_till_now*inactive_percent[getindex(i)]/100
        active_size = total_size_till_now - inactive_size
        cost_storage.append(inactive_size*gb_glacier_cost_pm*12/1024  +  active_size*gb_storage_cost_pm*12/1024)
        
        cost_rw.append(s3_rw_cost_pm*12*(no_of_low_risk + no_of_high_risk + no_of_med_risk))
        cost_ddb.append(dynamodb_cost_pm*12*no_of_users)
        cost_cmpt.append(ec2_cost_pm*12*no_of_users)
        cost_employee.append(85000000*((1+0.10)**i))
    
    cum_maintenance = np.cumsum(cost_maintenance)
    cum_storage = np.cumsum(cost_storage)
    cum_rw = np.cumsum(cost_rw)
    cum_ddb = np.cumsum(cost_ddb)
    cum_cmpt = np.cumsum(cost_cmpt)
    cum_emply = np.cumsum(cost_employee)

    total_expenses = []
    for i in range(len(cum_maintenance)):
        total_expenses.append(cum_maintenance[i]+cum_storage[i]+cum_rw[i]+cum_ddb[i]+cum_cmpt[i]+cum_emply[i])
    # st.write(total_revenue)
    # st.write(total_expenses)

    total_profits = np.subtract(total_revenue,total_expenses)

    margin_for_year = [0]
    for i in range(1,10+1):
        if (total_revenue[i]-total_revenue[i-1]) == 0:
            margin_for_year.append(0)
        else:
            margin_for_year.append( (total_profits[i] - total_profits[i-1])/(total_revenue[i]-total_revenue[i-1])*100 )
    
    cum_margin = [0]
    for i in range(1,10+1):
        if (total_revenue[i]) == 0:
            cum_margin.append(0)
        else:
            cum_margin.append(total_profits[i]*100/total_revenue[i])



    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Revenue")
        f = plot_line([i for i in range(len(total_revenue))], total_revenue, None, "Cumulative revenue", "Total revenue till year", None, None)
        st.plotly_chart(f, use_container_width=True)
    with col2:
        st.subheader("Expenses (Cloud costs + Employee costs)")
        f = plot_line([i for i in range(len(total_expenses))], total_expenses, None, "Cumulative expenses", "Total Costs till year", None, None)
        st.plotly_chart(f, use_container_width=True)
    with col3:
        st.subheader("Profits")
        f = plot_line([i for i in range(len(total_profits))], total_profits, None, "Cumulative profits", "Total Profit till year", None, None)
        st.plotly_chart(f, use_container_width=True)

    
    new_title = f'<p style="font-family:sans-serif; color:Green; font-size: 42px;">{str(round(cum_margin[-1],2)) + "%"}</p>'
    new_title_red = f'<p style="font-family:sans-serif; color:Red; font-size: 42px;">{str(round(cum_margin[-1],2)) + "%"}</p>'
    st.subheader("Gross margin for entire usage")
    if cum_margin[-1] > 0:
        st.markdown(new_title, unsafe_allow_html=True)
    else:
        st.markdown(new_title_red, unsafe_allow_html=True)

    #st.metric("",str(round(cum_margin[-1],2)) + "%")

    col1_, col2_ = st.columns(2)
    with col1_:
        st.subheader("Gross margin for years of usage")
        f = plot_line([i for i in range(len(cum_margin))], cum_margin, None, "Average Margin ", "Total Margin in % till year", None, None)
        st.plotly_chart(f, use_container_width=True)
        
    with col2_:
        st.subheader("Margin for year")
        f = plot_line([i for i in range(len(margin_for_year))], margin_for_year, None, "Margin for year ", "Margin in % per year", None, None)
        st.plotly_chart(f, use_container_width=True)
