
import streamlit as st 
import mysql.connector
import hashlib
import smtplib
from email.mime.text import MIMEText
import time
from email.message import EmailMessage
import json
import pandas as pd
import numpy as np
import requests
from requests.auth import HTTPBasicAuth
import uuid
import altair as alt 
from datetime import datetime, timedelta  
import joblib
from sklearn.preprocessing import LabelEncoder
import random
import string

# Set up page configuration only once
st.set_page_config(page_title="Techbid Marketplace")

# Cache the database connection to prevent re-connecting every time
@st.cache_resource
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="your-host",
            user="your-username",
            password="your-password",
            database="your-database"
        )
        return connection
    except mysql.connector.Error as e:
        st.error(f"Error connecting to database: {e}")
        return None

# Function to generate a unique referral code (used frequently)
@st.cache_data
def generate_referral_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# Prediction function (expensive computation, cached)
@st.cache_data
def predict_win_probability(input_data):
    input_df = pd.DataFrame([input_data])
    # Simulate a machine learning model prediction process
    # Assume 'model.joblib' exists as a trained model file
    model = joblib.load("model.joblib")
    prediction = model.predict(input_df)
    return prediction

# Async email sending function for non-blocking execution
async def send_email_async(receiver_email, message):
    smtp_server = smtplib.SMTP("smtp.server.com", 587)
    smtp_server.starttls()
    smtp_server.login("your-email", "your-password")
    smtp_server.sendmail("your-email", receiver_email, message)
    smtp_server.quit()

# Cache data loading function
@st.cache_data
def load_data():
    return pd.read_csv("your_data.csv")

# Cached bid fetch function
@st.cache_data
def get_highest_bid(product_code):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT MAX(bid_amount) FROM bids WHERE product_code = %s", (product_code,))
        highest_bid = cursor.fetchone()
        return highest_bid[0] if highest_bid else 0
    return 0

# Display gadgets (optimized for performance)
def display_gadgets(gadgets):
    for gadget in gadgets:
        product_code = gadget['product code']
        product_name = gadget["name"]
        price = gadget['price']
        
        st.image(gadget["image"], use_column_width=True)
        st.subheader(gadget["name"])
        st.write(f"**Price**: KSh {gadget['price']}")
        st.write(f"**Description**: {gadget['description']}")

        # Get and display the highest bid
        highest_bid = get_highest_bid(product_code)
        st.write(f"**Highest Bid**: KSh {highest_bid}")

        # Bid form for the gadget
        bid_button_key = f"bid-button-{product_code}"

        if st.button(f"Bid for {gadget['name']}", key=bid_button_key):
            st.session_state.selected_gadget = product_code

        if st.session_state.get('selected_gadget') == product_code:
            with st.form(key=f"bid-form-{product_code}"):
                Fname = st.text_input("First Name")
                Lname = st.text_input("Last Name")
                email = st.text_input("Email Address")
                phone = st.text_input("Phone Number (+254...)")
                bid_amount = st.number_input(f"Enter your bid for {gadget['name']}", min_value=price, value=price, step=1)
                
                submit_button = st.form_submit_button("Confirm Bid")
                if submit_button and Fname and Lname and phone and email:
                    # Call your payment logic here
                    st.success(f"Bid of KSh {bid_amount} submitted!")
                else:
                    st.error("Please fill out all fields.")
