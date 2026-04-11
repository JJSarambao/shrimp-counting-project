import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
import pandas as pd
import numpy as np  
from datetime import datetime, timedelta
import datetime as dt
import time
import streamlit.components.v1 as components
from bs4 import BeautifulSoup
import random
from st_mui_table import st_mui_table
import requests
import json

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pymongo

st.set_page_config(layout="wide")


class ManilaTZ(dt.tzinfo):
    def utcoffset(self, when):
        return dt.timedelta(hours=8)
    def dst(self, when):
        return dt.timedelta(0)
    def tzname(self, when):
        return "Manila/Philippines"
    def __repr__(self):
        return f"{self.__class__.__name__}()"


column_change_dictionary = {
    "start_date" : "Start Date",
    "end_date" : "End Date",
    "isc" : "Initial Shrimp Count",
    "fsc" : "Final Shrimp Count",
    "metrics" : "Metrics",
    "EC" : "Electric Conductivity",
    "temperature" : "Temperature",
    "DO" : "Dissolved Oxygen",
    "pH" : "pH"
}


if "authentication_success" not in st.session_state:
    st.session_state["authentication_success"] = False

if "last_refresh_time" not in st.session_state:
    st.session_state["last_refresh_time"] = datetime.now(tz=ManilaTZ())

@st.dialog("Authentication Required", dismissible=False)
def login():
    st.write("Password Required")
    password = st.text_input("Password", type="password")
    if password == 'shrimpproj25':
        st.session_state.authentication_success = True
        st.session_state.login = True
    else:
        st.toast(
        ":red[WARNING: Incorrect Password.]"
    )
    if st.session_state.authentication_success == True:
        st.rerun()

if st.session_state.authentication_success == False:
    login()


if st.session_state.authentication_success == True:
    st.title("Innovative Tiger Shrimp Farming with Analytics and Environment Monitoring System")

    time_placeholder = st.empty()

    # st_autorefresh(interval=5000, key="data_refresh")
    def dictionary_nester(nested_dict):
        reformed_dict = {}
        for outerKey, innerDict in nested_dict.items():
            outerKey = column_change_dictionary[outerKey]
            if (type(innerDict) == list) and (type(innerDict[0]) != dict):
                if type(innerDict[0]) == pd.Timestamp:
                    reformed_dict[f"<b>{outerKey}</b>"] = [i.strftime("%Y-%m-%d %H:%M:%S") for i in innerDict]
                else:
                    reformed_dict[f"<b>{outerKey}</b>"] = innerDict
                continue
            if (type(innerDict) == list) and (type(innerDict[0]) == dict):
                for item in innerDict:
                    for innerKey, values in item.items():
                        innerKey = column_change_dictionary[innerKey]
                        try:
                            reformed_dict[f"<b>{innerKey}</b>"].append(values)
                        except KeyError as e:
                            reformed_dict[f"<b>{innerKey}</b>"] = [values]
                        
        return reformed_dict
    def ChangeButtonColour(widget_label, font_color, background_color='transparent'):
        htmlstr = f"""
            <script>
                var elements = window.parent.document.querySelectorAll('button');
                for (var i = 0; i < elements.length; ++i) {{ 
                    if (elements[i].innerText == '{widget_label}') {{ 
                        elements[i].style.color ='{font_color}';
                        elements[i].style.background = '{background_color}'
                    }}
                }}
            </script>
            """
        components.html(f"{htmlstr}", height=0, width=0)

    @st.cache_data(ttl=dt.timedelta(seconds=300), show_spinner=False)
    def get_sensor_data():
        uri = st.secrets["database_connection_url"]
        # Create a new client and connect to the server
        client = MongoClient(uri, server_api=ServerApi('1'))
        db = client["sensors_db"]
        collection = db["sensors"]
        shrimp_collection = db["shrimp_count"]
        reports = db["reports"]
        data_df = pd.DataFrame(reversed(list(collection.find().sort([('timestamp', pymongo.DESCENDING )]).limit(100))))
        return data_df

    @st.cache_data(ttl=dt.timedelta(seconds=300), show_spinner=False)
    def get_shrimp_count_data():
        uri = st.secrets["database_connection_url"]
        # Create a new client and connect to the server
        client = MongoClient(uri, server_api=ServerApi('1'))
        db = client["sensors_db"]
        collection = db["sensors"]
        shrimp_collection = db["shrimp_count"]
        reports = db["reports"]
        shrimp_data_df = pd.DataFrame(reversed(list(shrimp_collection.find().sort([('timestamp', pymongo.DESCENDING )]).limit(100))))
        return shrimp_data_df
    
    @st.cache_data(ttl=dt.timedelta(seconds=300), show_spinner=False)
    def get_reports_data():
        uri = st.secrets["database_connection_url"]
        # Create a new client and connect to the server
        client = MongoClient(uri, server_api=ServerApi('1'))
        db = client["sensors_db"]
        collection = db["sensors"]
        shrimp_collection = db["shrimp_count"]
        reports = db["reports"]
        reports_df = pd.DataFrame(reversed(list(reports.find())))
        return reports_df

    @st.cache_data(ttl=dt.timedelta(seconds=10), show_spinner=False)
    def get_current_time():
        current_time = datetime.now(tz=ManilaTZ())
        formatted_time = current_time.strftime("Today is %A, %B %d, %Y | %I:%M:%S %p")
        return formatted_time

    @st.cache_data(ttl=dt.timedelta(seconds=60), show_spinner=False)
    def get_cycle():
        uri = st.secrets["database_connection_url"]
        # Create a new client and connect to the server
        client = MongoClient(uri, server_api=ServerApi('1'))
        db = client["sensors_db"]
        cycles = db["reports"]
        reports_df = list(cycles.find())
        return reports_df

    @st.cache_data(ttl=dt.timedelta(hours=1), show_spinner=False)
    def get_images():
        lambda_function_url = 'https://eebpusdfjqacpqfy7i6qz72cbe0boyxb.lambda-url.ap-southeast-1.on.aws/'
        list_action = 'action=list'
        image_list_response = requests.get(lambda_function_url+'?'+list_action).content
        image_list = json.loads(image_list_response)["image_list"]
        return image_list
    
    @st.cache_data(ttl=dt.timedelta(hours=1), show_spinner=False)
    def get_image_presigned_url(report_id, image_key):
        lambda_function_url = 'https://eebpusdfjqacpqfy7i6qz72cbe0boyxb.lambda-url.ap-southeast-1.on.aws/'
        list_action = 'action=get'
        root_folder = "daily_images/"
        parent_folder = f"{report_id}/"
        image_key = root_folder+parent_folder+image_key
        filename = f'image_name={image_key}'
        request_url = lambda_function_url+'?'+list_action+'&'+filename
        response_object = requests.get(request_url)
        image_url = json.loads(response_object.content)['presigned_url']
        return image_url

    @st.cache_data(ttl=dt.timedelta(hours=1), show_spinner=False)
    def get_daily_image_reports(keyID, num_reps):
        uri = st.secrets["database_connection_url"]
        client = MongoClient(uri, server_api=ServerApi('1'))
        db = client["sensors_db"]
        im_db = db["daily_images"]
        current_cycle = str(get_cycle()[-1]["_id"])
        daily_image_list = list(im_db.find({"_record_id": keyID}))
        new_data = dict()
        iterator = 1
        # Presigned URL generation
        for item in daily_image_list:
            filler = [None]*len(daily_image_list)
            filler[0] = f"<img src={get_image_presigned_url(keyID, item['img_name'])} alt='di_{iterator}' width='400' height='300'>"
            new_data[f"Day {iterator}"] = filler
            second_filler = [None]*len(daily_image_list)
            second_filler[0] = f"<b>{item['count']}"
            new_data[f"Shrimp Count for Day {iterator}"] = second_filler
            iterator += 1
        return new_data


    # @st.cache_data(ttl=dt.timedelta(minutes=1), show_spinner=False)
    def toast_notifs(metric_name, metric_value):
        st.toast(
                        f":red[WARNING: recorded {metric_name} levels are above recommended conditions ({metric_value}).]"
                    )
        pass

    def generate_report_table(report_data):
        report_data_no_id = report_data.drop(columns=["_id"])
        report_data_clean = report_data_no_id.to_dict(orient="list")
        report_data_dict = dictionary_nester(report_data_clean)
        report_data_dataframe = pd.DataFrame(report_data_dict)
        return report_data_dataframe

    def put_cycle():
        uri = st.secrets["database_connection_url"]
        # Create a new client and connect to the server
        client = MongoClient(uri, server_api=ServerApi('1'))
        db = client["sensors_db"]
        cycles = db["reports"]
        new_data = {"start_date": datetime.now(tz=ManilaTZ()).replace(hour=0, minute=0, second=0, microsecond=0), "end_date": "Currently Running", 
                                                                                                     "isc": 50, 
                                                                                                     "fsc": 0, 
                                                                                                     "metrics": {"EC": 0, 
                                                                                                                 "temperature": 0, 
                                                                                                                 "DO": 0, 
                                                                                                                 "pH": 0}}
        cycles.insert_one(new_data)
        return

    def end_cycle():
        uri = st.secrets["database_connection_url"]
        # Create a new client and connect to the server
        client = MongoClient(uri, server_api=ServerApi('1'))
        db = client["sensors_db"]
        cycles = db["reports"]
        metric_data = db["sensors"]
        report_data = db["shrimp_count"]
        latest_metric_data = list(metric_data.find().sort([('_id', -1)]).limit(1))[0]
        latest_report_data = list(report_data.find().sort([('_id', -1)]).limit(1))[0]
        latest_cycle = list(cycles.find().sort([('_id', -1)]).limit(1))[0]
        cycles.update_one({"_id": latest_cycle["_id"]}, {"$set": {"end_date": datetime.now(tz=ManilaTZ()).replace(hour=0, minute=0, second=0, microsecond=0),
                                                                "fsc": latest_report_data["shrimps_counted"],
                                                                "metrics": {"EC": latest_metric_data["EC"],
                                                                            "temperature": latest_metric_data["temperature"],
                                                                            "DO": latest_metric_data["DO"],
                                                                            "pH": latest_metric_data["pH"]}}})
        return


    latest_data_df = get_sensor_data()[-100:]
    latest_shrimp_df = get_shrimp_count_data()[-100:]
    reports_df = get_reports_data()[-100:]

    latest_data = latest_data_df.to_dict(orient='list')
    shrimp_data = latest_shrimp_df.to_dict(orient='list')
    reports_data = reports_df.to_dict(orient='list')


    # latest_data_df, latest_shrimp_df, reports_df = get_data()[-100:]
    
    # .ph 
    # .ec [data-testid="stMetric"] {
    #     background: url("ec-image.jpg") center/cover no-repeat;
    # }
    # .temp [data-testid="stMetric"] {
    #     background: url("temp-image.jpg") center/cover no-repeat;
    # }
    # .do [data-testid="stMetric"] {
    #     background: url("do-image.jpeg") center/cover no-repeat;
    # }
    st.markdown("""
    <style>
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.4);
    }
    table {
        width: 100%;
    }
    tr {
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)               

    monitoring, shrimp_count, reports, harvest_predictions = st.tabs(["Monitoring", "Shrimp Counting", "Reports", "Harvest Predictions"])
    with monitoring:
        # time_placeholder.markdown(f"{get_current_time()}")
        current_cycle = get_cycle()[-1]
        if current_cycle["end_date"] != "Currently Running":
            starter = st.button(label="Start new Cycle", width="stretch", key="starter_button", on_click=put_cycle)
        else:
            st.write(f"A Cycle has started last {current_cycle['start_date'].strftime('%A, %B %d, %Y')}. Currently Monitoring stated cycle.")
            if "end_button" not in st.session_state:
                ender = st.button(type='primary', label="End current Cycle", width="stretch", key=f"end_button", on_click=end_cycle)
        ChangeButtonColour("Start new Cycle", "white", "green")
        # monitoring_frame = st.empty()
        first_metric_row = st.empty()
        second_metric_row = st.empty()
    with shrimp_count:
        shrimp_counting = st.empty()
        # st.metric("Shrimp Count", shrimp_data["shrimps_counted"][-1], border=True)
    with reports:
        reporting_data = generate_report_table(get_reports_data()[-100:])
        latestKey = str(get_reports_data()["_id"][0])
        num_reps = len(list(get_reports_data()))
        daily_data = get_daily_image_reports(latestKey, num_reps)
        # image_list = get_images()
        # sample = image_list[-3:]
        # url_list = [get_image_presigned_url(image) for image in sample]
        # another_sample_code = {"Day 1": [f"<img src={url_list[0]} alt='test_1' width='100' height='100'>", None, None],
        #                        "Day 2": [f"<img src={url_list[1]} alt='test_1' width='100' height='100'>", None, None],
        #                        "Day 3": [f"<img src={url_list[2]} alt='test_1' width='100' height='100'>", None, None]}
        daily_reports = pd.DataFrame(daily_data)
        reporting_data = pd.concat([reporting_data, daily_reports], axis=1)
        tableCSS = """
        .MuiTableCell-root {
                text-align: center;
            }
        .detailHeader {
                text-align: left;
        }
        tr.MuiTableRow-hover:not(:first-of-type) td button.MuiIconButton-root { 
                display: none !important; }
        """
        st_mui_table(reporting_data, 
                     customCss=tableCSS,
                     detailColumns=[k for k, v in daily_data.items()],
                     detailColNum=2,
                     detailsHeader="<div class=detailHeader><b>Daily Image Capture</b></div>")
    with harvest_predictions:
        hp_frame = st.empty()
    while True:
        time_placeholder.markdown(f"{get_current_time()}")
        with monitoring:
            pH, EC = first_metric_row.columns(2)
            Temp, DO = second_metric_row.columns(2)
            if 7.5 < latest_data["pH"][-1] < 8.5:
                pH.metric("pH Level", 
                        round(latest_data["pH"][-1], 2),
                        delta="Within Range",
                        chart_data=latest_data_df["pH"],
                        chart_type="area",
                        border=True)
            else:
                pH.metric("pH Level", 
                    round(latest_data["pH"][-1], 2),
                    delta="ALARMING: Outside safety range",
                    delta_color="inverse",
                    chart_data=latest_data_df["pH"],
                    chart_type="area",
                    border=True)
                toast_notifs("pH", round(latest_data["pH"][-1], 2))
            if 17.022 < latest_data["EC"][-1] < 53.065:
                EC.metric("Electric Conductivity",
                        round(latest_data["EC"][-1], 2),
                        delta="Within Range",
                        chart_data=latest_data_df["EC"],
                        chart_type="area",
                        border=True)
            else:
                EC.metric("Electric Conductivity", 
                        round(latest_data["EC"][-1], 2), 
                        delta="ALARMING: Outside safety range",
                        delta_color="inverse",
                        chart_data=latest_data_df["EC"],
                        chart_type="area",
                        border=True)
                toast_notifs("EC", round(latest_data["EC"][-1], 2))
            if 28 < latest_data["temperature"][-1] < 32:
                Temp.metric("Temperature",
                            round(latest_data["temperature"][-1], 2),
                            delta="Within Range",
                            chart_data=latest_data_df["temperature"],
                            chart_type="area",
                            border=True)
            else:
                Temp.metric("Temperature",
                            round(latest_data["temperature"][-1], 2),
                            delta="ALARMING: Outside safety range",
                            delta_color="inverse",
                            chart_data=latest_data_df["temperature"],
                            chart_type="area",
                            border=True)
                toast_notifs("temperature", round(latest_data["temperature"][-1], 2))
            if latest_data["DO"][-1] > 5:
                DO.metric("Dissolved Oxygen",
                        round(latest_data["DO"][-1], 2),
                        delta="Within Range",
                        chart_data=latest_data_df["DO"],
                        chart_type="area",
                        border=True)
            else:
                DO.metric("Dissolved Oxygen", 
                        round(latest_data["DO"][-1], 2),
                        delta="ALARMING: Outside safety range",
                        delta_color="inverse",
                        chart_data=latest_data_df["DO"],
                        chart_type="area",
                        border=True)
                toast_notifs("DO", round(latest_data["DO"][-1], 2))
        with shrimp_count:
            with shrimp_counting:
                st.metric("Shrimp Count", shrimp_data["shrimps_counted"][-1], border=True)
        with reports:
            reporting_data = generate_report_table(get_reports_data()[-100:])
            latestKey = str(get_reports_data()["_id"][0])
            num_reps = len(list(get_reports_data()))
            daily_data = get_daily_image_reports(latestKey, num_reps)
            # image_list = get_images()
            # sample = image_list[-3:]
            # url_list = [get_image_presigned_url(image) for image in sample]
            # another_sample_code = {"Day 1": [f"<img src={url_list[0]} alt='test_1' width='100' height='100'>", None, None],
            #                        "Day 2": [f"<img src={url_list[1]} alt='test_1' width='100' height='100'>", None, None],
            #                        "Day 3": [f"<img src={url_list[2]} alt='test_1' width='100' height='100'>", None, None]}
            daily_reports = pd.DataFrame(daily_data)
            reporting_data = pd.concat([reporting_data, daily_reports], axis=1)
            # tableCSS = """
            # .MuiTableCell-root {
            #         text-align: center;
            #     }
            # .detailHeader {
            #         text-align: left;
            # }
            # tr.MuiTableRow-hover:not(:first-of-type) td button.MuiIconButton-root { 
            #         display: none !important; }
            # """
            # st_mui_table(reporting_data, 
            #             customCss=tableCSS,
            #             detailColumns=["Day 1", "Day 2", "Day 3"],
            #             detailColNum=1,
            #             detailsHeader="<div class=detailHeader><b>Daily Image Capture</b></div>")
        with harvest_predictions:
            current_cycle = get_cycle()[-1]
            current_sc = shrimp_data["shrimps_counted"][-1]
            with hp_frame:
                if current_cycle["end_date"] != "Currently Running":
                    st.write(f"There are no cycles currently running. No predictions will be presented")
                else:
                    # with harvest_predictions:
                    st.write(f"A Cycle has started last {current_cycle['start_date'].strftime('%A, %B %d, %Y')}. Currently Monitoring stated cycle.")
                    initial, current, nyield = st.columns(3)
                    with initial:
                        st.subheader("Initial Shrimp Count")
                        st.write(f"##### {current_cycle['isc']}")
                    with current:
                        st.subheader("Current Shrimp Count")
                        st.write(f"##### {current_sc}")
                    with nyield:
                        st.subheader("Harvest Rate")
                        st.write(f"##### {(current_sc/current_cycle['isc'])*100:.2f}%")
        time.sleep(30) # Wait for 1 second before updating again

    # while True:
    #     # time_placeholder.markdown(f"{get_current_time()}") # Update the content of the placeholder
    #     # with monitoring:
    #     #     pH, EC = test_column.columns(2)
    #     #     Temp, DO = another_test_column.columns(2)
    #     #     if datetime.now() - st.session_state.last_refresh_time >= timedelta(seconds=5):
    #     #         latest_data_df = get_sensor_data()[-100:]
    #     #         latest_shrimp_df = get_shrimp_count_data()[-100:]
    #     #         latest_data = latest_data_df.to_dict(orient='list')
    #     #         shrimp_data = latest_shrimp_df.to_dict(orient='list')
    #     #         if 7.5 < latest_data["pH"][-1] < 8.5:
    #     #             pH.metric("pH Level", 
    #     #                     round(latest_data["pH"][-1], 2),
    #     #                     delta="Within Range",
    #     #                     chart_data=latest_data_df["pH"],
    #     #                     chart_type="area",
    #     #                     border=True)
    #     #         else:
    #     #             pH.metric("pH Level", 
    #     #                 round(latest_data["pH"][-1], 2),
    #     #                 delta="ALARMING: Outside safety range",
    #     #                 delta_color="inverse",
    #     #                 chart_data=latest_data_df["pH"],
    #     #                 chart_type="area",
    #     #                 border=True)
    #     #             st.toast(
    #     #                 ":red[WARNING: recorded pH levels are above recommended conditions.]"
    #     #             )

    #     #         if 17.022 < latest_data["EC"][-1] < 53.065:
    #     #             EC.metric("Electric Conductivity",
    #     #                     round(latest_data["EC"][-1], 2),
    #     #                     delta="Within Range",
    #     #                     chart_data=latest_data_df["EC"],
    #     #                     chart_type="area",
    #     #                     border=True)
    #     #         else:
    #     #             EC.metric("Electric Conductivity", 
    #     #                     round(latest_data["EC"][-1], 2), 
    #     #                     delta="ALARMING: Outside safety range",
    #     #                     delta_color="inverse",
    #     #                     chart_data=latest_data_df["EC"],
    #     #                     chart_type="area",
    #     #                     border=True)
    #     #             st.toast(
    #     #                 ":red[WARNING: recorded Electric Conductivity levels are above recommended conditions.]"
    #     #             )

    #     #         if 28 < latest_data["temperature"][-1] < 32:
    #     #             Temp.metric("Temperature",
    #     #                         round(latest_data["temperature"][-1], 2),
    #     #                         delta="Within Range",
    #     #                         chart_data=latest_data_df["temperature"],
    #     #                         chart_type="area",
    #     #                         border=True)
    #     #         else:
    #     #             Temp.metric("Temperature",
    #     #                         round(latest_data["temperature"][-1], 2),
    #     #                         delta="ALARMING: Outside safety range",
    #     #                         delta_color="inverse",
    #     #                         chart_data=latest_data_df["temperature"],
    #     #                         chart_type="area",
    #     #                         border=True)
    #     #             st.toast(
    #     #                 ":red[WARNING: recorded temperature levels are above recommended conditions.]"
    #     #             )

    #     #         if latest_data["DO"][-1] > 5:
    #     #             DO.metric("Dissolved Oxygen",
    #     #                     round(latest_data["DO"][-1], 2),
    #     #                     delta="Within Range",
    #     #                     chart_data=latest_data_df["DO"],
    #     #                     chart_type="area",
    #     #                     border=True)
    #     #         else:
    #     #             DO.metric("Dissolved Oxygen", 
    #     #                     round(latest_data["DO"][-1], 2),
    #     #                     delta="ALARMING: Outside safety range",
    #     #                     delta_color="inverse",
    #     #                     chart_data=latest_data_df["DO"],
    #     #                     chart_type="area",
    #     #                     border=True)
    #     #             st.toast(
    #     #                 ":red[WARNING: recorded dissolved oxygen levels are above recommended conditions.]"
    #     #             )
    #     with shrimp_count:
    #         # if datetime.now() - st.session_state.last_refresh_time >= timedelta(seconds=5):
    #         #     shrimp_counting.metric("Shrimp Count",
    #         #         shrimp_data["shrimps_counted"][-1],
    #         #         border=True)
    #         pass
    #     with reports:
    #         pass
    #         # if datetime.now() - st.session_state.last_refresh_time >= timedelta(seconds=5):
    #         #     reports_df = get_reports_data()[-100:]
    #         #     if "mui_table" in st.session_state:
    #         #         print("yes")
    #         #         del st.session_state["mui_table"]
    #         #     reports_data_no_id = reports_df.drop(columns=["_id"])
    #         #     reports_data = reports_data_no_id.to_dict(orient='list')
    #         #     reports_data_dict = dictionary_nester(reports_data)
    #         #     # reports_data_columns = pd.MultiIndex.from_tuples([(i, j) for i, j in reports_data_dict.keys()])
    #         #     # test_data_df = pd.DataFrame(reports_data_dict, columns=reports_data_columns) #.style.set_table_styles([dict(selector='th', props=[('text-align', 'center')])]).hide(axis='index')
    #         #     test_data_df = pd.DataFrame(reports_data_dict)
    #         #     # st.dataframe(test_data_df)
    #         #     with reports_c:
    #         #         st_mui_table(test_data_df)
    #             # test_data_df.columns = ['<div class="col_heading">'+col+'</div>' for data in test_data_df.columns for col in data]
    #             # test_data_df_html = test_data_df.to_html(escape=False)
    #             # soup = BeautifulSoup(test_data_df_html, "html.parser")
    #             # thead = soup.find("thead")
    #             # rows = thead.find_all("tr")
    #             # first_row = rows[0]
    #             # second_row = rows[1]
    #             # ths_first = first_row.find_all("th")
    #             # ths_second = second_row.find_all("th")
    #             # for i in range(4):
    #             #     ths_first[i]["rowspan"] = "2"
    #             # for i in range(4):
    #             #     ths_second[i].decompose()
    #             # final_df = str(soup)
    #             # st.write(final_df, unsafe_allow_html=True)
    #     with harvest_predictions:
    #         pass

    #     if datetime.now() - st.session_state.last_refresh_time >= timedelta(seconds=5):
    #         st.session_state.last_refresh_time = datetime.now()
    #     time.sleep(1) # Wait for 1 second before updating again
