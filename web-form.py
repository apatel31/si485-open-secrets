import streamlit as st
import datetime as datetime
import json

st.title("OpenSecrets Graph Analyzer Tool")
st.subheader("Select what you want to look for")
st.text('Description of how to use the tool here')

with st.form("graphForm", clear_on_submit=False):
    dateRange = st.date_input("Time Range", value=[datetime.date(2019, 7, 6), datetime.date(2020, 7, 6)])
    industryOrTopic = st.text_input("Enter Keywords Here")
    dollarThreshold = st.slider("$ Threshold for Relevance", 0, 1000000, 10000)
    commonBills = st.number_input('Number of bills in common', value=1)
    submit = st.form_submit_button("Submit")

jsonObj = st.json({
            'dateRange': dateRange,
            'industryOrTopic': industryOrTopic,
            'dollarThreshold': int(dollarThreshold),
            'commonBills': int(commonBills),
        })
st.write("" + json.dumps(jsonObj))