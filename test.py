import streamlit as st 
from streamlit_lottie import st_lottie
import mysql.connector
from mysql.connector import Error
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
from mysql.connector import Error
import altair as alt
from datetime import datetime, timedelta  # Import directly
import joblib
from sklearn.preprocessing import LabelEncoder
from  pymongo import MongoClient
import pymongo
import gridfs
import io
import random
import pathlib


# Set up page configuration only once
st.set_page_config(page_title="Techbid Marketplace", layout="wide")


# Load the preprocessor and model
preprocessor_filename = r"C:\Users\A\Documents\preprocessor.pkl"
model_filename =r"C:\Users\A\Documents\rf_pipeline.pkl" 


preprocessor = joblib.load(preprocessor_filename)
model = joblib.load(model_filename)


 #Prediction function
def predict_win_probability(input_data):
    # Convert input data to a DataFrame
    input_df = pd.DataFrame([input_data])

    # Apply the preprocessor to handle categorical features
    input_df_transformed = preprocessor.transform(input_df)

    # Make a prediction
    prediction = model.predict(input_df_transformed)
    return prediction

# Function to generate custom product IDs based on the ranges provided
def generate_product_id():
    prefixes = {
        'p': range(1, 21),     # p001 to p020
        't': range(1, 11),     # t001 to t010
        's': range(1, 21),   # soo1 to soo20
        'a': range(1, 25),     # a001 to a024
        'c': range(1, 26)      # c001 to c025
    }
    
    # Choose a random prefix
    prefix = random.choice(list(prefixes.keys()))
    
    # Choose a random number from the corresponding range
    number = random.choice(prefixes[prefix])
    
    # Format the product ID accordingly
    if prefix == 'soo':  # special case for 'soo'
        return f'{prefix}{number:02}'
    else:
        return f'{prefix}{number:03}'
# Set up session state for page navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Home'

# Local CSS
def local_css(file):
    with open(file) as f:
        st.html(f"<style>{f.read()}</style>")

Css=pathlib.Path(r"C:\Users\A\Downloads\styles (8).css")
local_css(Css)  # Path to CSS file


# Load assets
image1 = r"C:\Users\A\Downloads\Untitled design.png"



# Initialize PesaPal class for authentication and order submission



# Function to send confirmation email using Gmail SMTP
def send_confirmation_email(email, name):
    try:
        # Set up the email server
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        sender_email = 'techbidmarketplace@gmail.com'  # Replace with your Gmail address
        sender_password = 'vnot dyyh plrw syag'  # Replace with your app password

        # Create the email content
        subject = 'Welcome to TechBid!'
        body = f'Hi {name},\n\nThank you for signing up for TechBid! We are excited to have you on board.\n\nBest regards,\nThe TechBid Team'
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = email

        # Connect to the email server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
            st.success("Confirmation email sent!")
             
    except Exception as e:
        st.error("Could not send email.Please check your internet connection.")
        # Optionally log the error message without showing it to the user
      # Define log_error() function to handle logging securely.
        return None



# Function to send email
def send_email(to_email, from_email, subject, message):
    try:
        # Set up your SMTP server
        smtp_server = 'smtp.gmail.com'  # For Gmail
        smtp_port = 587
        smtp_username = 'techbidmarketplace@gmail.com'  # Your email
        smtp_password = 'vnot dyyh plrw syag'  # Your email password (Consider using app-specific password for Gmail)

        # Create an email message object
        email = EmailMessage()
        email['From'] = from_email
        email['To'] = to_email
        email['Subject'] = subject
        email.set_content(message)

        # Connect to the server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(smtp_username, smtp_password)
            server.send_message(email)
        return True
    except Exception as e:
        st.error("Could not send confirmation email,check your internet connection and try again")
        return None

# Function to display the customer support form
def customer_support_page():
    st.title("Customer Support")

    st.write("If you have any questions or need assistance, please fill out the form below and we'll get back to you.")

    # Custom CSS for styling the form

    with st.form("support_form"):
        user_name = st.text_input("Your Name")
        user_email = st.text_input("Your Email")
        message = st.text_area("Your Message")
        
        # Submit button
        submit_button = st.form_submit_button("Submit")
        
        # Handle form submission
        if submit_button:
            if user_name and user_email and message:
                # Compose the email
                subject = f"Customer Support Request from {user_name}"
                body = f"Name: {user_name}\nEmail: {user_email}\n\nMessage:\n{message}"

                # Send the email to your support email
                email_sent = send_email(
                    to_email="your_support_email@domain.com",  # Your support email
                    from_email=user_email,  # User's email
                    subject=subject,
                    message=body
                )

                if email_sent:
                    st.success("Thank you for reaching out! Your message has been successfully received. We shall get back to you soon.")
                else:
                    st.error("Failed to send your message. Please try again later.")
            else:
                st.error("Please fill out all fields before submitting the form.")




# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to save new user data into the MySQL database
def save_user_data(name, email, password, phone, address):
    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(
            charset="utf8mb4",
            connection_timeout=10,
            database="defaultdb",
            host="mysql-f3601b9-jonesjorney-bd4e.f.aivencloud.com",
            password="AVNS_ERXe8j5gIX5yis97hnw",
            port=21038,
            user="avnadmin"
        )
        cursor = connection.cursor()

        # Hash the password before storing
        hashed_password = hash_password(password)

        # Insert the user data into the database
        cursor.execute("INSERT INTO users (name, email, password, phone, address) VALUES (%s, %s, %s, %s, %s)",
                       (name, email, hashed_password, phone, address))
        connection.commit()

         # Send email confirmation
        send_confirmation_email(email, name)

        # Close cursor and connection
        cursor.close()
        connection.close()

        st.success("User registered successfully! You can now Bid.")
    except mysql.connector.Error:
        st.error("Email already registered. Please use another email address.")
    except Exception as e:
        st.error("An error occurred. Please check your internet connection and try again.")


def verify_user(email, password):
    try:
        connection = mysql.connector.connect(
                charset="utf8mb4",
                connection_timeout=10,
                database="defaultdb",
                host="mysql-f3601b9-jonesjorney-bd4e.f.aivencloud.com",
                password="AVNS_ERXe8j5gIX5yis97hnw",
                port=21038,
                user="avnadmin"

        )
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM users WHERE email = %s AND password = %s",
                    (email, hash_password(password)))  # Use the hashing function here
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        # If user is found, return it as a dictionary; otherwise return None
        return {"name": user[0]} if user else None
    
    except mysql.connector.Error:
        st.error("Error checking email. Please try again later.")
        return False






# Login page
def login_page():
    st.title("Log In")
    email = st.text_input("Email Address")
    password = st.text_input("Password", type='password')

    if st.button("Log In", key= "Login_key"):
        user = verify_user(email, password)
        if user:
            st.session_state.user = user
            st.success(f"Login successful! Welcome back {user['name']}!")
            st.session_state.current_page = "Bids and Gadgets"  # Redirect to a new page after successful login
        else:
            st.error("Invalid email or password.")

# Add CSS to style the "Sign Up" button
st.markdown(
    """
    <style>
    /* Styling for the Sign Up button */
    .stButton > button {
        background-color: #4CAF50; /* Green background color */
        color: white; /* White text color */
        border: none; /* Remove default border */
        border-radius: 10px; /* Rounded corners */
        padding: 12px 24px; /* Space inside the button */
        font-size: 18px; /* Text size */
        cursor: pointer; /* Pointer cursor on hover */
        transition: background-color 0.3s; /* Smooth background color transition */
    }

    /* Hover effect for the button */
    .stButton > button:hover {
        background-color: #45a049; /* Darker green on hover */

    }
    .stButton > button:focus p {
    color: #FFD700;
    }
    .stButton > button:focus {
    background-color: #45a049; /* Keep the same as hover */
    border: none;
    }
    .stButton > button:focus p {
    color: #FFD700;
    }

    /* Active effect for the button */
    .stButton > button:active {
        background-color: #388e3c; /* Even darker green on click */
    }
    </style>
    """,
    unsafe_allow_html=True
)



def signup_page():
    st.title("Sign Up for TechBid")

    # Create a form for user signup
    with st.form("signup_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        password = st.text_input("Password", type='password')

        # Additional fields with unique keys
        st.markdown("### Additional Information")
        phone = st.text_input("Phone Number", key="styledinput_phone")
        address = st.text_input("Address", key="styledinput_address")

        # Submit button
        submitted = st.form_submit_button("Sign Up")

        if submitted:
            # Check if all fields are filled
            if not name or not email or not password or not phone or not address:
                st.error("Please fill out all fields before submitting.")
            else:
                # Call the function to save user data to MySQL
                save_user_data(name, email, password, phone, address)




# Function to display the home page
def home_page():
    st.write("")

def bid_history():
    st.title("Bid History")

    # Sample data with specific values for bids
    data2 = pd.DataFrame({
        'Time': pd.date_range('2024-09-25', periods=10),
        'Bids': [10, 25, 35, 15, 50, 45, 30, 20, 55, 40]  # Insert your specific values here
    })

    # Create an Altair chart using raw Vega-Lite specifications to disable the actions
    chart = alt.Chart(data2).mark_line().encode(
        x='Time:T',
        y='Bids:Q'
    ).properties(
        width=600,
        height=300
    ).to_dict()

    # Embed the Vega-Lite spec without the action buttons
    st.vega_lite_chart(chart, use_container_width=True)


    data = pd.DataFrame({
    'Time': pd.date_range('2024-09-25', periods=10),
    'Bids': [10, 18, 9, 12, 50, 45, 32, 20, 65, 41],
    'Winners': [6, 11, 3, 5, 21, 33, 17, 8, 33, 13]
})

# Melt the DataFrame to long format
    data_melted = data.melt('Time', var_name='Category', value_name='Count')

    # Altair line chart
    chart = alt.Chart(data_melted).mark_line().encode(
        x='Time:T',
        y='Count:Q',
        color='Category:N'
    ).properties(
        title="Bids and Winners Over Time"
    )

    st.altair_chart(chart, use_container_width=True)
    if st.checkbox("View Raw Data"):
        st.write(data)



# Function to display Bids and Gadgets page
# Initialize session state for each gadget to track if the form should be displayed
if "show_payment_form" not in st.session_state:
    st.session_state.show_payment_form = {}
   
    

   
# Pesapal class from your code
class PesaPal:
    def __init__(self):
        self.auth_url = "https://pay.pesapal.com/v3/api/Auth/RequestToken"
        self.ipn_base_url = "https://pay.pesapal.com/v3/api/"
        self.consumer_key = "tHHdZzfUleF7xUe7NIKmhFndky2LzE0v"
        self.consumer_secret = "OuVah65aa8nlL4r8JwpHdoSRgcU="
        self.cached_ipn_id = None

    def authentication(self):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        payload = json.dumps({
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret
        })

        response = requests.post(self.auth_url, headers=headers, data=payload)

        if response.status_code == 200:
            return response.json().get('token')
        else:
            return None

    def initiate_payment(self, token, phone_number, amount, order_id, Fname, Lname):
        endpoint = "Transactions/SubmitOrderRequest"
        ipn_id = self.register_ipn()

        payload = {
            "id": order_id,
            "currency": "KES",
            "amount": amount,
            "description": "Payment For Product",
            "callback_url": "https://callbak-1.onrender.com",  # Replace with your actual callback URL
            "notification_id": ipn_id,
            "billing_address": {
                "phone_number": phone_number,
                "First_name": Fname,
                "Last_name": Lname,
                "country_code": "KE",
                "line_1": "Your Address",
                "city": "Nairobi",
                "postal_code": "00100"
            },
            
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {token}"
        }

        response = requests.post(self.ipn_base_url + endpoint, headers=headers, json=payload)
        return response.json()

    def register_ipn(self):
        if self.cached_ipn_id:
            return self.cached_ipn_id
        ipn_endpoint = "URLSetup/RegisterIPN"
        payload = {
            "url": "https://ipn-06ai.onrender.com",
            "ipn_notification_type": "GET"
        }

        token = self.authentication()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {token}"
        }

        response = requests.post(self.ipn_base_url + ipn_endpoint, headers=headers, json=payload)
        if response.status_code == 200:
            ipn_response = response.json()
            self.cached_ipn_id = ipn_response.get("ipn_id")
            return self.cached_ipn_id
        return None



# Styling the button using custom CSS
# CSS for bounce animation
st.markdown(
    """
    <style>
    .bounce {
        font-size: 36px;
        font-weight: bold;
        color:;
        animation: pulse 0s infinite;
    }

    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-30px);
        }
        60% {
            transform: translateY(-15px);
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    div.stButton > button {
        background-color:#126fe8;  /* Button background color */
        color: #020202;  /* Button text color */
        border-radius: 10px;
        border: 2px solid #126fe8;
        padding: 8px 16px;
        font-size: 16px;
        cursor: pointer;
        animation: bounce 5s infinite;
    }
    div.stButton > button:hover {
        background-color: #d64f6e;  /* No change on hover */
        border-color: #d64f6e;      /* No change on hover */
        color: #020202;             /* No change on hover */
    }
    div.stButton > button:active {
        background-color: #d64f6e;  /* No change on click */
        border-color: #d64f6e;      /* No change on click */
        color: #020202;             /* No change on click */
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
"""
<style>
/* Styling for the text input field */
.stTextInput input {
    background-color: #f0f8ff; /* Light blue background color */
    border: 2px solid #4CAF50; /* Green border color */
    border-radius: 8px; /* Rounded corners */
    padding: 10px; /* Space inside the input */
    font-size: 16px; /* Text size */
    color: #333; /* Text color */
}

/* Placeholder text style */
.stTextInput input::placeholder {
    color: #999; /* Gray placeholder text color */
    font-style: italic; /* Italic style for placeholder */
}

/* Focus state for the text input field */
.stTextInput input:focus {
    border: 2px solid #4a90e2; /* Change border color to blue on focus */
    outline: none; /* Remove default outline */
    background-color: #e6f7ff; /* Slightly darker background on focus */
}
</style>
""", unsafe_allow_html=True)
 

def save_bid(Fname, Lname, email, phone, bid_amount, product_code,product_name):
    try:
            
            connection = mysql.connector.connect(
            charset="utf8mb4",
            connection_timeout=10,
            database="defaultdb",
            host="mysql-f3601b9-jonesjorney-bd4e.f.aivencloud.com",
            password="AVNS_ERXe8j5gIX5yis97hnw",
            port=21038,
            user="avnadmin"    # Your MySQL password
        )
            if connection.is_connected():

                cursor = connection.cursor()

            # SQL query to insert bid details into the database
            query = """INSERT INTO bids (Fname, Lname, email, phone, bid_amount, product_code) 
                        VALUES (%s, %s, %s, %s, %s, %s)"""

            # Values to be inserted
            record = (Fname, Lname, email, phone, bid_amount, product_code)

            # Execute the SQL query
            cursor.execute(query, record)

            # Commit the transaction
            connection.commit()
            send_confirmation(email, Fname, Lname, bid_amount, product_name)

            st.success("Bid saved successfully!")

    except Error as e:
        st.error(f"Error while connecting to MySQL: {e}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
        

            
###########################################################
def send_confirmation(email, Fname, Lname, bid_amount, product_name):
    sender_email = 'techbidmarketplace@gmail.com'
    sender_password = 'vnot dyyh plrw syag'  # Use app-specific password or environment variable for security
    
    # Email body
    body = f"""
Hello {Fname} {Lname},

Your bid of KSh {bid_amount} on {product_name} has been received.
You shall be notified when the auction ends.

Best regards,
The TechBid Team
"""


    # Create the email message
    msg = MIMEText(body)
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = "Bid Confirmation"

    
    # Send email using Gmail SMTP
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Upgrade to secure connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email ,msg.as_string())
        return True
    
    except Exception as e:
        print(f"Error: {e}. Check Internet connection and try again!")
        return False         


    
# Set how many hours or days to extend the countdown by once it reaches zero (for demo purposes)
extension_period = timedelta(hours=72)  

def get_time_left(expiry_time,product_code):
    now = datetime.now()
    time_left = expiry_time - now
    if time_left.total_seconds() > 0:
        return time_left
    else:
        # When the countdown reaches zero, reset to a new expiry
        new_expiry = now + extension_period
        expiry_times[product_code] = new_expiry  # Update expiry time for this product
        return new_expiry - now  # Return new countdown

expiry_times = {
    "p001": datetime(2024, 10, 11, 12, 0, 0),
    "p002": datetime(2024, 10, 11, 15, 30, 0),
    "p003": datetime(2024, 10, 12, 10, 0, 0),
    "p004": datetime(2024, 10, 12, 12, 0, 0),
    "p005": datetime(2024, 10, 11, 15, 30, 0),
    "p006": datetime(2024, 10, 12, 10, 0, 0),
    "p007": datetime(2024, 10, 10, 12, 0, 0),
    "p008": datetime(2024, 10, 11, 15, 30, 0),
    "p009": datetime(2024, 10, 12, 10, 0, 0),
    "p010": datetime(2024, 10, 10, 12, 0, 0),
    "p011": datetime(2024, 10, 11, 15, 30, 0),
    "p012": datetime(2024, 10, 12, 10, 0, 0),
    "p013": datetime(2024, 10, 10, 12, 0, 0),
    "p014": datetime(2024, 10, 12, 10, 0, 0),
    "p015": datetime(2024, 10, 11, 12, 0, 0),
    "p016": datetime(2024, 10, 11, 15, 30, 0),
    "p017": datetime(2024, 10, 12, 10, 0, 0),
    "p018": datetime(2024, 10, 10, 12, 0, 0),
    "p019": datetime(2024, 10, 11, 15, 30, 0),
    "p020": datetime(2024, 10, 12, 10, 0, 0),
    "t001": datetime(2024, 10, 12, 10, 0, 0),
    "t002": datetime(2024, 10, 12, 10, 0, 0),
    "t003": datetime(2024, 10, 12, 10, 0, 0),
    "t004": datetime(2024, 10, 11, 10, 0, 0),
    "t005": datetime(2024, 10, 12, 10, 0, 0),
    "t006": datetime(2024, 10, 12, 10, 0, 0),
    "t007": datetime(2024, 10, 12, 10, 0, 0),
    "t008": datetime(2024, 10, 12, 10, 0, 0),
    "t009": datetime(2024, 10, 12, 10, 0, 0),
    "t010": datetime(2024, 10, 12, 10, 0, 0),
    "s001": datetime(2024, 10, 12, 10, 0, 0),
    "s002": datetime(2024, 10, 12, 10, 0, 0),
    "s003": datetime(2024, 10, 10, 10, 0, 0),
    "s004": datetime(2024, 10, 12, 10, 0, 0),
    "s005": datetime(2024, 10, 12, 10, 0, 0),
    "s006": datetime(2024, 10, 12, 10, 0, 0),
    "s007": datetime(2024, 10, 11, 10, 0, 0),
    "s008": datetime(2024, 10, 12, 10, 0, 0),
    "s009": datetime(2024, 10, 12, 10, 0, 0),
    "s010": datetime(2024, 10, 12, 10, 0, 0),
    "s011": datetime(2024, 10, 12, 10, 0, 0),
    "s012": datetime(2024, 10, 12, 10, 0, 0),
    "s013": datetime(2024, 10, 12, 10, 0, 0),
    "s014": datetime(2024, 10, 12, 10, 0, 0),
    "s015": datetime(2024, 10, 12, 10, 0, 0),
    "s016": datetime(2024, 10, 12, 10, 0, 0),
    "s017": datetime(2024, 10, 12, 10, 0, 0),
    "s018": datetime(2024, 10, 12, 10, 0, 0),
    "s019": datetime(2024, 10, 10, 10, 0, 0),
    "s020": datetime(2024, 10, 12, 10, 0, 0),
    "a001": datetime(2024, 10, 12, 10, 0, 0),
    "a002": datetime(2024, 10, 11, 10, 0, 0),
    "a003": datetime(2024, 10, 12, 10, 0, 0),
    "a004": datetime(2024, 10, 12, 10, 0, 0),
    "a005": datetime(2024, 10, 12, 10, 0, 0),
    "a006": datetime(2024, 10, 11, 10, 0, 0),
    "a007": datetime(2024, 10, 12, 10, 0, 0),
    "a008": datetime(2024, 10, 12, 10, 0, 0),
    "a009": datetime(2024, 10, 12, 10, 0, 0),
    "a010": datetime(2024, 10, 12, 10, 0, 0),
    "a011": datetime(2024, 10, 12, 10, 0, 0),
    "a012": datetime(2024, 10, 12, 10, 0, 0),
    "a013": datetime(2024, 10, 12, 10, 0, 0),
    "a014": datetime(2024, 10, 10, 10, 0, 0),
    "a015": datetime(2024, 10, 12, 10, 0, 0),
    "a016": datetime(2024, 10, 12, 10, 0, 0),
    "a017": datetime(2024, 10, 12, 10, 0, 0),
    "a018": datetime(2024, 10, 11, 10, 0, 0),
    "a019": datetime(2024, 10, 12, 10, 0, 0),
    "a020": datetime(2024, 10, 12, 10, 0, 0),
    "a021": datetime(2024, 10, 12, 10, 0, 0),
    "a022": datetime(2024, 10, 12, 10, 0, 0),
    "a023": datetime(2024, 10, 12, 10, 0, 0),
    "a024": datetime(2024, 10, 12, 10, 0, 0),
    "c001": datetime(2024, 10, 10, 10, 0, 0),
    "c002": datetime(2024, 10, 12, 10, 0, 0),
    "c003": datetime(2024, 10, 12, 10, 0, 0),
    "c004": datetime(2024, 10, 12, 10, 0, 0),
    "c005": datetime(2024, 10, 12, 10, 0, 0),
    "c006": datetime(2024, 10, 11, 10, 0, 0),
    "c007": datetime(2024, 10, 12, 10, 0, 0),
    "c008": datetime(2024, 10, 12, 10, 0, 0),
    "c009": datetime(2024, 10, 12, 10, 0, 0),
    "c010": datetime(2024, 10, 12, 10, 0, 0),
    "c011": datetime(2024, 10, 12, 10, 0, 0),
    "c012": datetime(2024, 10, 11, 10, 0, 0),
    "c013": datetime(2024, 10, 12, 10, 0, 0),
    "c014": datetime(2024, 10, 12, 10, 0, 0),
    "c015": datetime(2024, 10, 10, 10, 0, 0),
    "c016": datetime(2024, 10, 12, 10, 0, 0),
    "c017": datetime(2024, 10, 12, 10, 0, 0),
    "c018": datetime(2024, 10, 10, 10, 0, 0),
    "c019": datetime(2024, 10, 12, 10, 0, 0),
    "c020": datetime(2024, 10, 11, 10, 0, 0),
}
##########################                    
    
   
    
#########################################
def bids_and_gadgets_page():
    

    st.title("Bids and Gadgets")
    st.write("----")
    st.subheader("Hot This Week")
    gadgets = [
        {
            "name": "XIAOMI Redmi A3, 6.71",
            "image": r"C:\Users\A\Downloads\1 (3).jpg",
            "description": "4GB RAM +128GB (Dual SIM), 5000mAh, Midnight Black (Newest Model)",
            "price": 180,
            "product code": "p001",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",  # Replace with your Ko-fi link
            "mpesa_link": "**Pochi La Biashara/Send Money**: +254704234829"
        },
        {
            "name": "Itel Flip 1 Folding Phone",
            "image": r"C:\Users\A\Downloads\1 (4).jpg",
            "description": " 2.4 inches QQVGA (240 x 320 pixels) display, 8MB of RAM 2.4 - 1200mAh (Dual SIM), Wireless FM, Blue (1YR WRTY)",
            "price": 268,
            "product code": "p002",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Itel S24",
            "image": r"C:\Users\A\Downloads\1 (5).jpg",
            "description": "6.6'', 128GB + 4GB (Extended UPTO 8GB) RAM, 5000mAh, Dawn White (1YR WRTY)",
            "price": 185,
            "product code": "p003",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name":"Apple iPhone 15 Pro Max",
            "image":r"C:\Users\A\Downloads\1 (6).jpg",
            "description":"6.7‑inch (diagonal) all‑screen OLED display1, 256GB Storage256GB Storage, Action ButtonAction Button, USB-C Charge Cable capable4,Enabled by TrueDepth camera for facil recognition,",
            "price": 30800,
            "product code": "p004",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Samsung Galaxy S24 Ultra",
            "image": r"C:\Users\A\Downloads\1 (8).jpg",
            "description":"Cell Phone, 512GB AI Smartphone, Unlocked Android, 50MP Zoom Camera, Long Battery Life, S Pen",
            "price": 28000,
            "product code": "p005",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "XIAOMI Redmi 13C",
            "image":r"C:\Users\A\Downloads\1 (9).jpg",
            "description":"6.47'',  256GB + 8GB RAM (Dual SIM) 5000mAh, 4G - Navy Blue",
            "price": 180,
            "product code": "p006",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name":" **Refurbished** Oppo A31",
            "image": r"C:\Users\A\Downloads\2 (1).jpg",
            "description":"6GB RAM+128GB ROM 6.5 Inch Screen HD Camera 12MP Cyan",
            "price":110 ,
            "product code": "p007",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Itel 2176 ",
            "image": r"C:\Users\A\Downloads\3 (1).jpg",
            "description":"Wireless FM, 1.8'', Dual SIM - 1000mAh - Blue",
            "price": 80,
            "product code": "p008",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Denver Smartwatch",
            "image": r"C:\Users\A\Downloads\550x661.jpg",
            "description": "Stay fully informed with the Denver SW182 smartwatch! Connect to the 'Denver Smart Life Plus' app for accurate monitoring of heart rate, blood pressure, blood oxygen, steps, sleep activity and choose from 22 sports modes. Receive notifications directly on the watch. The 1.7'' full touch display and various 'watch faces' let you adjust the watch to your own liking!",
            "price": 70,
            "product code": "t001",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"

        },
        {
            "name": "Smartwatch T900 Pro Max",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/85/8855721/1.jpg?7826",
            "description": "Bluetooth call, Custom Wallpaper, drinking reminder blood oxygen, sports mode (outdoor running, walking, mountaineering, indoor running), Facebook, twitter, WhatsApp, calendar, message reminder ,heart rate, sleep monitoring, Bluetooth music, SMS, call record, SIRI/Voice Assistant, alarm clock, remote photo, step counting, blood pressure, address book, looking for mobile phone, etc.",
            "price": 60,
            "product code": "t002",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        }
    
    ]
    


    # Initialize selected_category if not already set
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = "Home"

    selected_category = st.session_state.selected_category

    # Define the product codes for "Phones and Tablets" category
    phones_and_tablets_product_codes = [f"p{str(i).zfill(3)}" for i in range(1, 21)]
    tablets_product_codes = [f"t{str(i).zfill(3)}" for i in range(1, 11)]
    tv_and_audio_product_codes = [f"s{str(i).zfill(3)}" for i in range(1, 21)]
    appliances_product_codes = [f"a{str(i).zfill(3)}" for i in range(1, 21)]
    computing_product_codes = [f"c{str(i).zfill(3)}" for i in range(1, 21)]

    phones_and_tablets_product_codes += tablets_product_codes
        

    if selected_category == "Phones and Tablets":
        filtered_gadgets = [gadget for gadget in gadgets if gadget["product code"] in phones_and_tablets_product_codes]
    elif selected_category == "TV and Audio":
        filtered_gadgets = [gadget for gadget in gadgets if gadget["product code"] in tv_and_audio_product_codes]
    elif selected_category == "Appliances":
        filtered_gadgets = [gadget for gadget in gadgets if gadget["product code"] in appliances_product_codes]
    elif selected_category == "Computing":
        filtered_gadgets = [gadget for gadget in gadgets if gadget["product code"] in computing_product_codes]
    else:
        filtered_gadgets = gadgets  # Show all gadgets if another category is selected
    

    pesapal = PesaPal()
    # Initialize the selected gadget in session_state
    if 'selected_gadget' not in st.session_state:
        st.session_state.selected_gadget = None
    if 'show_form' not in st.session_state:
        st.session_state.show_form = {}
    
    # Create columns for displaying gadgets
    cols = st.columns(3)  # Create 3 columns

    # Create a list to hold the layout of gadgets
    rows = []

    # Ensure the session state keys are initialized
    if 'selected_gadget' not in st.session_state:
        st.session_state.selected_gadget = None

    if 'show_form' not in st.session_state:
        st.session_state.show_form = {}

    # Initialize highest bids in session_state (persist in a database for a real app)
    if 'highest_bids' not in st.session_state:
        st.session_state.highest_bids = {
            "p001": 180,  
            "p002": 140,
            "p003": 1845,
            "p004": 3400,  
            "p005": 2800,
            "p006": 110,  
            "p007": 110,
            "p008": 80,
            "p009": 120,  
            "p010": 135,
            "p011": 120,
            "p012": 85,  
            "p013": 130,
            "p014": 150,
            "p015": 110,  
            "p015": 95,
            "p016": 190,
            "p017": 210,  
            "p018": 268,
            "p019": 185,
            "t001": 85,
            "t002": 100,
            "t003": 65,
            "t004": 75,
            "t005": 90,
            "t006": 70,
            "t007": 65,
            "t008": 80,
            "t009": 75,
            "t010":95,
            "s001": 90,
            "s002": 70,
            "s003": 85,
            "s001": 90,
            "s002": 120,
            "s003": 95,            
            "s001": 100,
            "s002": 85,
            "s003": 90,           
            "s004": 100,
            "s005": 75,
            "s006": 135,           
            "s007": 60,
            "s008": 80,
            "s009": 95,           
            "s010": 85,
            "s011": 75,
            "s012": 125,            
            "s013": 80,
            "s014": 140,
            "s015":230,           
            "s016": 100,
            "s017": 80,
            "s018": 85,            
            "s019": 80,
            "s020": 105,
            "s021": 100,           
            "s022": 110,
            "s023": 95,
            "s024": 80,
            "a001": 90,
            "a002": 95,
            "a003":105,
            "a004": 175,
            "a005": 85,
            "a006": 112,
            "a007": 145,
            "a008": 89,
            "a009": 131,
            "a010": 98,
            "a011": 134,
            "a012": 105,
            "a013": 149,
            "a014": 87,
            "a015": 140,
            "a016": 91,
            "a017": 122,
            "a018": 147,
            "a019": 80,
            "a020": 110,
            "a021": 142,
            "a022": 96,
            "a023": 120,
            "a024": 136,
            "c001": 93,
            "c002": 138,
            "c003": 108,
            "c004": 132,
            "c005": 86,
            "c006": 101,
            "c007": 150,
            "c008": 123,
            "c009": 115,
            "c010": 97,
            "c011": 129,
            "c012": 90,
            "c013": 148,
            "c014": 99,
            "c015": 118,
            "c017": 125,
            "c018": 82,
            "c019": 144,
            "c020": 106,
            "c021": 83,
            "c022": 116,
            "c023": 130,
            "c024": 103,
            "c025": 84
        }
       

               

    # Function to get the current highest bid for a product
    def get_highest_bid(product_code):
        return st.session_state.highest_bids.get(product_code, 0)

                # Update the highest bid after each successful bid
    def update_highest_bid(product_code, new_bid):
        if new_bid > st.session_state.highest_bids[product_code]:
            st.session_state.highest_bids[product_code] = new_bid 

    # Simulate random bid increase between 1 and 10
    def simulate_random_bids():
        for product_code in st.session_state.highest_bids.keys():
            random_increment = random.randint(1, 10)
            new_highest_bid = st.session_state.highest_bids[product_code] + random_increment
            update_highest_bid(product_code, new_highest_bid)      
    
    simulate_random_bids()

    # Display products in columns and rows
    for idx, gadget in enumerate(filtered_gadgets):
        col_idx = idx % 3  # Get column index
        if col_idx==0:
            rows.append([])#start new row

# Append the gadget info to the current row
        rows[-1].append(gadget)

    for row in rows:
        cols = st.columns(len(row))  # Create as many columns as gadgets in the row
        for idx, gadget in enumerate(row):
            with cols[idx]:    
        
                st.image(gadget["image"], use_column_width=True)
                st.subheader(gadget["name"])
                st.write(f"**Price**: KSh {gadget['price']}")
                st.write(f"**Description**: {gadget['description']}")
                st.write(f"**Product code**: {gadget['product code']}")



                #######
                product_name=gadget["name"]
                product_code = gadget["product code"]
                if product_code in expiry_times:           

                    time_left = get_time_left(expiry_times[product_code], product_code)
                    days = time_left.days
                    hours = time_left.seconds // 3600
                    minutes = (time_left.seconds % 3600) // 60
                    seconds = time_left.seconds % 60

                    # Display countdown timer
                    st.metric("**Time Left**", f"{days}d {hours}h {minutes}m ")

                    # Handle expired bids
                    if time_left.total_seconds() <= 0:
                        st.warning("Bid expired!")

                     # Display highest bids
                highest_bid = get_highest_bid(product_code)
                st.write(f"**Highest Bid** : KSh {highest_bid}")

                bid_button_key = f"bid-button-{gadget['product code']}-{idx}"


                # Toggle form visibility when button is clicked
                if st.button(f"Bid for {gadget['name']}", key=bid_button_key):
                # Your bid logic here

                    # Toggle form visibility for this specific gadget
                    if st.session_state.selected_gadget == product_code:
                        st.session_state.selected_gadget = None
                    else:
                        st.session_state.selected_gadget = product_code
                        st.session_state.show_form[product_code] = True  # Show form for this product

                # Check if the form for the current gadget should be displayed
                if st.session_state.selected_gadget == product_code:
                    # Minimize/Expand button for form
                    if st.button("Minimize/Expand Form", key=f"minimize-{gadget['name']}-{product_code}"):
                        # Toggle the visibility state for the form
                        st.session_state.show_form[product_code] = not st.session_state.show_form.get(product_code, True)

                    # Display the form if it is currently visible
                    if st.session_state.show_form.get(product_code, True):

                        Fname = st.text_input("First Name", key=f"fname-{product_code}")
                        Lname = st.text_input("Last Name", key=f"lname-{product_code}")
                        email = st.text_input("Email Address",key=f"email-{product_code}")
                        phone = st.text_input("Phone Number (+254...)", key=f"phone-{product_code}")
                        bid_amount = st.number_input(
                            f"Enter your bid amount for {gadget['name']}",
                            min_value=gadget['price'],
                            value=gadget['price'],
                            step=1,
                            key=f"bid-{product_code}"
                        )             

                        if st.button("Confirm Bid", key=f"confirm-{gadget['name']}-{idx}"):

                            # Payment initiation with spinner for loading effect
                            if Fname and Lname and phone and email and product_code and bid_amount and product_name :
                                if bid_amount >= gadget["price"]:
                                    save_bid(Lname, Lname, email, phone, bid_amount, product_code,product_name)
                                    send_confirmation(email, Fname, Lname, bid_amount, product_name)

                                    pesapal = PesaPal()
                                    token = pesapal.authentication()

                                    if token:
                                        with st.spinner("Checkout Loading..."):
                                            order_id = str(uuid.uuid4())
                                            result = pesapal.initiate_payment(token, phone, bid_amount, order_id, Fname, Lname)

                                        if result:
                                            redirect_url = result.get("redirect_url")
                                            st.markdown(f"[👉Click here to complete bid .]({redirect_url})", unsafe_allow_html=True)
                                        else:
                                            st.error("Bid failed. Please try again!.")
                                    else:
                                        st.error("Cannot process payment. Try again!")
                                else:
                                    st.error(f"Your bid must be at least KSh {gadget['price']} or higher.")
                            else:
                                st.error("Please fill out all the details to proceed") 

                        st.markdown(f"</div>", unsafe_allow_html=True)






#search Engine
def search_bar():
    gadgets = [
        {
            "name": "XIAOMI Redmi A3, 6.71",
            "image": r"C:\Users\A\Downloads\1 (3).jpg",
            "description": "4GB RAM +128GB (Dual SIM), 5000mAh, Midnight Black (Newest Model)",
            "price": 180,
            "product code": "p001",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",  # Replace with your Ko-fi link
            "mpesa_link": "**Pochi La Biashara/Send Money**: +254704234829"
        },
        {
            "name": "Itel Flip 1 Folding Phone",
            "image": r"C:\Users\A\Downloads\1 (4).jpg",
            "description": " 2.4 inches QQVGA (240 x 320 pixels) display, 8MB of RAM 2.4 - 1200mAh (Dual SIM), Wireless FM, Blue (1YR WRTY)",
            "price": 268,
            "product code": "p002",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Itel S24",
            "image": r"C:\Users\A\Downloads\1 (5).jpg",
            "description": "6.6'', 128GB + 4GB (Extended UPTO 8GB) RAM, 5000mAh, Dawn White (1YR WRTY)",
            "price": 185,
            "product code": "p003",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name":"Apple iPhone 15 Pro Max",
            "image":r"C:\Users\A\Downloads\1 (6).jpg",
            "description":"6.7‑inch (diagonal) all‑screen OLED display1, 256GB Storage256GB Storage, Action ButtonAction Button, USB-C Charge Cable capable4,Enabled by TrueDepth camera for facil recognition,",
            "price": 30800,
            "product code": "p004",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Samsung Galaxy S24 Ultra",
            "image": r"C:\Users\A\Downloads\1 (8).jpg",
            "description":"Cell Phone, 512GB AI Smartphone, Unlocked Android, 50MP Zoom Camera, Long Battery Life, S Pen",
            "price": 28000,
            "product code": "p005",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "XIAOMI Redmi 13C",
            "image":r"C:\Users\A\Downloads\1 (9).jpg",
            "description":"6.47'',  256GB + 8GB RAM (Dual SIM) 5000mAh, 4G - Navy Blue",
            "price": 180,
            "product code": "p006",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name":" **Refurbished** Oppo A31",
            "image": r"C:\Users\A\Downloads\2 (1).jpg",
            "description":"6GB RAM+128GB ROM 6.5 Inch Screen HD Camera 12MP Cyan",
            "price":110 ,
            "product code": "p007",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Itel 2176 ",
            "image": r"C:\Users\A\Downloads\3 (1).jpg",
            "description":"Wireless FM, 1.8'', Dual SIM - 1000mAh - Blue",
            "price": 80,
            "product code": "p008",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Denver Smartwatch",
            "image": r"C:\Users\A\Downloads\550x661.jpg",
            "description": "Stay fully informed with the Denver SW182 smartwatch! Connect to the 'Denver Smart Life Plus' app for accurate monitoring of heart rate, blood pressure, blood oxygen, steps, sleep activity and choose from 22 sports modes. Receive notifications directly on the watch. The 1.7'' full touch display and various 'watch faces' let you adjust the watch to your own liking!",
            "price": 70,
            "product code": "t001",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"

        },
        {
            "name": "Smartwatch T900 Pro Max",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/85/8855721/1.jpg?7826",
            "description": "Bluetooth call, Custom Wallpaper, drinking reminder blood oxygen, sports mode (outdoor running, walking, mountaineering, indoor running), Facebook, twitter, WhatsApp, calendar, message reminder ,heart rate, sleep monitoring, Bluetooth music, SMS, call record, SIRI/Voice Assistant, alarm clock, remote photo, step counting, blood pressure, address book, looking for mobile phone, etc.",
            "price": 60,
            "product code": "t002",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        }
    
    ]

    
    if 'selected_gadget' not in st.session_state:
        st.session_state.selected_gadget = None
    if 'show_form' not in st.session_state:
        st.session_state.show_form = {}

    # Dropdown for category selection
    category = st.selectbox("Select a Category", ["All", "Phones and Tablets", "Tv and Audio", "Appliances", "Computing"])

    # Search bar
    search_query = st.text_input("Search for a gadget by name or description")

    # Search logic based on category and search query
    search_results = []
    for index, gadget in enumerate(gadgets):
        if (category == "All" or gadget.get("category", "") == category) and \
        (search_query.lower() in gadget["name"].lower() or search_query.lower() in gadget["description"].lower()):
            search_results.append(gadget)
    

     # Function to get the current highest bid for a product
    def get_highest_bid(product_code):
        return st.session_state.highest_bids.get(product_code, 0)

                # Update the highest bid after each successful bid
    def update_highest_bid(product_code, new_bid):
        if new_bid > st.session_state.highest_bids[product_code]:
            st.session_state.highest_bids[product_code] = new_bid 

    # Simulate random bid increase between 1 and 10
    def simulate_random_bids():
        for product_code in st.session_state.highest_bids.keys():
            random_increment = random.randint(1, 10)
            new_highest_bid = st.session_state.highest_bids[product_code] + random_increment
            update_highest_bid(product_code, new_highest_bid)      
    
    simulate_random_bids()


    for index, result in enumerate(search_results):
            st.subheader(result["name"])
            st.image(result['image'], width=300)
            st.write(result["description"])
            st.write(f"**Product Code**: {result['product code']}")
            st.write(f"**Price**: KSh {result['price']}")

#####################
            product_name=result["name"]
            product_code = result["product code"]
            if product_code in expiry_times:           

                time_left = get_time_left(expiry_times[product_code], product_code)
                days = time_left.days
                hours = time_left.seconds // 3600
                minutes = (time_left.seconds % 3600) // 60
                seconds = time_left.seconds % 60

                #display timer
                st.metric("**Time Left**", f"{days}d {hours}h {minutes}m ")

                # Handle expired bids
                if time_left.total_seconds() <= 0:
                    st.warning("Bid expired!")

                # Display highest bids
            highest_bid = get_highest_bid(product_code)
            st.write(f"**Highest Bid** : KSh {highest_bid}")

            bid_button_key = f"bid-button-{result['product code']}-{index}"
            st.write(f"**Highest Bid** : KSh {highest_bid}")

            bid_button_key = f"bid-button-{result['product code']}-{index}"
            
            # Toggle form visibility
            if st.button(f"Bid for {result['name']}", key=f"mpesa-{result['name']}-{index}"):
                if st.session_state.selected_gadget == index:
                    st.session_state.selected_gadget = None
                else:
                    st.session_state.selected_gadget = index
                    st.session_state.show_form[index] = True

            # Show form if the selected gadget index matches
            if st.session_state.selected_gadget == index:
                if st.button("Minimize/Expand Form", key=f"minimize-{result['name']}-{index}"):
                    st.session_state.show_form[index] = not st.session_state.show_form.get(index, True)

                if st.session_state.show_form.get(index, True):
                    # Input fields for user details
                    Fname = st.text_input("First Name", key=f"fname-{result['name']}-{index}")
                    Lname = st.text_input("Last Name", key=f"lname-{result['name']}-{index}")
                    email = st.text_input("Email Address",key=f"email-{product_code}")
                    phone = st.text_input("Phone Number (+254...)", key=f"phone-{result['name']}-{index}")
                    bid_amount = st.number_input(f"Enter your bid amount for {result['name']}", min_value=result['price'], value=result['price'], step=1, key=f"bid-{result['name']}-{index}")
                    
                    if st.button("Confirm Bid", key=f"confirm-{result['name']}-{index}"):
                        if Fname and Lname and phone and email and product_code and bid_amount and product_name :
                            if bid_amount >= result["price"]:
                                save_bid(Lname, Lname, email, phone, bid_amount, product_code,product_name)
                                send_confirmation(email, Fname, Lname, bid_amount, product_name)

                                pesapal = PesaPal()  # Ensure PesaPal is defined in your code
                                token = pesapal.authentication()

                                if token:
                                    with st.spinner("Checkout Loading..."):
                                        order_id = str(uuid.uuid4())
                                        payment_result = pesapal.initiate_payment(token, phone, bid_amount, order_id, Fname, Lname)

                                    if payment_result:
                                        redirect_url = payment_result.get("redirect_url")
                                        st.markdown(f"[👉Click here to complete bid.]({redirect_url})", unsafe_allow_html=True)
                                    else:
                                        st.error("Bid failed. Please try again!")
                                else:
                                    st.error("Cannot process bid. Try again!")
                            else:
                                st.error(f"Your bid must be at least KSh {result['price']} or higher.")
                        else:
                            st.error("Please fill out all the details to proceed.")

            st.write("---")
       
    # Display search results
    if search_results:
        st.write(f"Found {len(search_results)} result(s) matching '{search_query}' in '{category}' category:")
    else:
        st.write(f"No results found for '{search_query}' in '{category}' category.")

            

        
 # Countdown logic
def countdown():

    # Set your countdown date (modify this as needed)
    countdown_time = datetime.datetime(2024, 10, 10, 0, 0, 0)

    # Create a placeholder for the countdown
    countdown_placeholder = st.empty()

    while True:
        # Get the current time
        current_time = datetime.datetime.now()

        # Calculate the time difference between now and the countdown time
        time_left = countdown_time - current_time

        # If the countdown has ended, stop the loop
        if time_left.total_seconds() <= 0:
            countdown_placeholder.markdown("### Auction Started!")
            break

        # Format the time left as H:M:S
        time_left_str = str(time_left).split('.')[0]

        # Display the countdown in the placeholder
        countdown_placeholder.markdown(f"### Time Left for the Next Auction: {time_left_str}")

        # Wait for 1 second before updating the countdown again
        time.sleep(1)


def section_off_page():
    st.write("")  # Blank content   

def tv_audio():
    st.write("")

def appliances():
    st.write("")    

def computing():
    st.write("")








# Function for file upload
def file_upload():
    st.write("---")

    


st.markdown(
        """
        <style>
        /* Adjust the padding at the top */
        .main {
            padding-top: 0px !important;  /* Set top padding to 0 */
        }
        </style>
        """,
        unsafe_allow_html=True
    ) 

def generate_random_metrics():
        highest_bid = random.randint(100, 5000)  # Random highest bid between 1 and 100
        total_bids = random.randint(50, 200)  # Random total number of bids between 50 and 200
        return highest_bid, total_bids

# Function to update the user count and delta
def update_user_metrics():
    if "users_count" not in st.session_state:
        st.session_state.users_count = 2103  # Initial users count
        st.session_state.users_delta = 0

    st.session_state.users_count += random.randint(1, 4)  # Increment users randomly
    st.session_state.users_delta = f"+{random.randint(1, 4)}%"  # Update delta randomly

def how_works():

    st.subheader("How To Participate")
    st.write("---")
    st.write("""
    1.Sign Up
             
    2.Review our privacy policy
             
    3.Auction ends after 72 hours
             
    4 Visit our **Privacy Policy** page for more details
             
    **Final Note**: The winner is determined based on the highest price placed on a product or the number of times a bid  was placed on one or different items(frequency) by an individeal.                                               
    """)
    st.write("---")
    st.title("Shipping and Logistics")
    st.write("""At **TechBid Marketplace**, we are committed to ensuring your winning bids are delivered quickly and securely, no matter where you are located. Our shipping and logistics policy is designed to offer convenience, transparency, and timely updates for all our users.

**Free Delivery for Select Bids**
             
Bids placed below Ksh 200 qualify for free delivery within select regions. Our aim is to make winning even more rewarding by covering your delivery costs.
             
**Nationwide Delivery**
             
We offer countrywide deliveries, ensuring that your gadgets and items reach you wherever you are in Kenya. We partner with reliable courier services to make sure your products arrive safely and on time.         
 
**Fast and Secure Shipping**
             
Once you win a bid, your item will be processed for shipment within 24 hours, and you can expect delivery within 2-5 business days, depending on your location.

**Notifications and Tracking**
             
Bidders will be notified via email upon winning a bid and when the item has been dispatched for delivery. You will also receive a tracking number to monitor your shipment in real-time.

**Shipping Fees**
             
For bids exceeding Ksh 200, shipping fees are calculated based on your location and the size/weight of the item. These charges will be clearly communicated during checkout to ensure transparency.

**International Shipping**
             
While we currently focus on domestic shipping, we are working on expanding our services to include international deliveries in the near future. Stay tuned!

**Return Policy**
             
If your item arrives damaged or is not as described, you can initiate a return request within 7 days of receiving the product. 
For any inquiries regarding shipping and logistics, feel free to contact our support team at [techbidmarketplace@gmail.com] .

             
""")

def about_us():
    st.subheader("About Us")
# Css for the about page 
    st.markdown(
    """
    <style>
    .about-header {
        font-size: 40px;
        font-weight: bold;
        color: #4CAF50;
        margin-bottom: 20px;
    }
    .about-section {
        font-size: 18px;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
    # About Page Content
    st.markdown('<div class="about-header">About TechBid</div>', unsafe_allow_html=True)

# Introduction
    st.markdown('<div class="about-section"><strong>Welcome to TechBid!</strong> We are an innovative online bidding platform dedicated to helping you find the best deals on mobile and computer gadgets. Our mission is to create a fun and engaging environment where users can bid on the latest tech products and save money in the process!</div>', unsafe_allow_html=True)

# Mission Statement
    st.markdown('<div class="about-section"><strong>Our Mission:</strong> At TechBid, we aim to revolutionize the way people shop for gadgets. We believe that everyone deserves access to high-quality products at affordable prices, and our platform makes that possible through competitive bidding.</div>', unsafe_allow_html=True)

# Our Values
    st.markdown('<div class="about-section"><strong>Our Values:</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="about-section">1. Transparency: We believe in clear and honest communication.</div>', unsafe_allow_html=True)
    st.markdown('<div class="about-section">2. Integrity: We are committed to fair play in all our transactions.</div>', unsafe_allow_html=True)
    st.markdown('<div class="about-section">3. Innovation: We constantly strive to improve our platform for a better user experience.</div>', unsafe_allow_html=True)

# How It Works
    st.markdown('<div class="about-section"><strong>How It Works:</strong> Bidding on TechBid is simple! Register for an account, browse our selection of gadgets, and place your bids. The highest bidder wins the item, and we handle the rest!</div>', unsafe_allow_html=True)

# Team Introduction
    st.markdown('<div class="about-section"><strong>Team Effort:</strong> Our dedicated team of tech enthusiasts and professionals are here to ensure a seamless bidding experience for you.</div>', unsafe_allow_html=True)

# Join Us
    st.markdown('<div class="about-section"><strong>Join Us:</strong> Ready to find amazing deals? Sign up today and start bidding on the latest gadgets!</div>', unsafe_allow_html=True)
    st.markdown("### What Our Users Say:")
    st.markdown("⭐️⭐️⭐️⭐️⭐️  \"TechBid helped me find my dream gadget at an unbeatable price!\" - John Ndirangu.")
    st.markdown("⭐️⭐️⭐️⭐️⭐️  \"I love the thrill of bidding!\" - Sarah Kioko.")
def privacy_policy():
    st.subheader("Our Privacy Policy")
    st.write("---")
    st.write("At **TechBid Marketplace**, we are committed to protecting your privacy and ensuring that your personal information is handled in a safe and responsible manner. This privacy policy outlines how we collect, use, and protect the personal information you provide to us through our website.")
    st.title("1.Information We Collect")
    st.write("""
We collect the following types of information:

**Personal Information*: When you register an account, we may collect personal information such as your name, email address, phone number, and payment information.

**Bidding Data**: When you participate in an auction, we collect and store information about your bids, including the items you bid on and the amount of your bids.

**Browsing Information**: We collect information on how you interact with the app, including your IP address, device type, browser type, and browsing actions within the app.
""")
    st.title("2.How We Use Your Information")
    st.write("""
We use the information we collect for the following purposes:

-To provide and operate the app and its features (e.g., managing auctions, bids, and payments).
-To communicate with you about your account, auctions, and updates to our services.
-To enhance the user experience by analyzing app usage and trends.
-To process payments and refunds.
-To comply with legal obligations.
""")
    st.title("3.Sharing Your Information")
    st.write("""
We do not sell or rent your personal information to third parties. However, we may share your information with:

**Service Providers**: We may share your information with third-party service providers who help us operate our app, process payments, and provide customer support.
**Legal Requirements**: We may disclose your information if required by law or in response to legal requests.
""")
    st.title("4.Data Security")
    st.write("We implement security measures to protect your personal information, including encryption and secure server technologies. However, no method of transmission over the internet is completely secure, and we cannot guarantee absolute security.")

    st.title("5.Your Rights")
    st.write("""
You have the right to:

-Access, update, or delete your personal information by contacting us at [Your Contact Information].

-Opt out of marketing communications at any time by clicking "unsubscribe" in the emails we send.

""")
    st.title("6.Cookies")
    st.write("We use cookies to enhance your experience on our app, including remembering your login details and tracking site usage. You can manage your cookie preferences through your browser settings.")

    
    st.title("7.Changes to This Privacy Policy")
    st.write("We may update this privacy policy from time to time. Any changes will be posted on this page.")

    st.write("##")
    st.subheader("Our Terms of Service")
    st.write("---")
    st.write("Welcome to **TechBid Marketplace** By using the App, you agree to comply with and be bound by the following terms and conditions. Please read these terms carefully.")
    st.title("1.Acceptance of Terms") 
    st.write("""By accessing and using our app, you agree to be bound by these terms of service and our privacy policy. If you do not agree with any part of these terms, please do not use the app.""")        
    st.title("2.User Accounts") 
    st.write("""
**Registration**: To participate in auctions, you must create an account by providing accurate information. You are responsible for maintaining the confidentiality of your account credentials.

**Eligibility**: You must be at least 18 years old to use the app and participate in auctions.

**Termination**: We reserve the right to suspend or terminate your account at any time if you violate these terms.
""")   
    st.title("3.Bidding and Auctions") 
    st.write("""
**Auction Participation**: By placing a bid, you agree to purchase the item if you win the auction. All bids are final, and there are no refunds unless explicitly stated
                                
**Auction Modifications**: We reserve the right to modify auction details, cancel auctions, or remove items at our discretion.               
                """)  
    
    st.title("4.Payments")
    st.write("All payments must be made through the payment options provided on our website(e.g., M-Pesa, Ko-fi). We do not store payment information on our servers.")
    
    st.title("5.User Conduct")
    st.write("""
You agree not to engage in any behavior that disrupts or interferes with the app's functionality or other users' experiences, including but not limited to:
1.Hacking, tampering with, or otherwise attempting to bypass security features.

2.Posting or transmitting any illegal, harmful, or offensive content.

3.Using automated scripts or software to interact with the app
            
""")
    st.title("6.Intellectual Property")
    st.write("All content, logos, and other intellectual property associated with the app are the property of **TechBid Marketplace**. You are not permitted to reproduce or use any materials from the app without our written consent.")
    
    st.title("7.Limitation of Liability")
    st.write("To the fb9ullest extent permitted by law,**TechBid Marketplace** shall not be liable for any damages, losses, or expenses arising out of or in connection with your use of the app, including any technical issues, loss of bids, or unauthorized access to your account.")
    st.title("Contact Us")
    st.markdown("For inquiries, feel free to [email us](techbidmarketplace.com).")

    

# Main function to manage the sidebar and page navigation
def main():
    
    st.write("---")
 
    with st.container():
        image_column, text_column = st.columns((1, 1))

        with image_column:
            # Replace the image with a video
            video_file = open(r"C:\Users\A\Videos\x\1005(1).mp4", "rb")
            video_bytes = video_file.read()
            st.video(video_bytes)

            with st.expander("**How do I place a bid?**", expanded=True):
                st.markdown(
                    """
                        **From The Sidebar:**

                        1. Sign Up                  
                        2. Review the 'Privacy Policy'
                        3. Start bidding
                    """,
                    
                )

            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.05)
                progress_bar.progress(i+1)


        with text_column:
            st.markdown('<div class="bounce">Bid Now for Amazing Deals!</div>', unsafe_allow_html=True)
            st.write("Welcome to **TechBid Marketplace**, the ultimate destination for scoring the best deals on the latest mobile and computer gadgets! Whether you're hunting for a sleek smartphone or a powerful laptop, you can join the bidding action, compete for top tech, and grab your favorite devices at unbeatable prices. Start bidding now and discover how you can upgrade your tech for less!")
            unique_key = f"join_techbid_button1_{st.session_state.current_page}"
            if st.button("Join TechBid Now!", key="primary"):
                st.success("**Sign Up** from the sidebar")
                st.session_state.current_page = "✔Sign Up"  # Change the current page to "Sign Up"
            st.write("---")


     # Sidebar navigation
    update_user_metrics()
    st.sidebar.metric(label="Users", value=st.session_state.users_count, delta=st.session_state.users_delta)

    # Create two columns in the sidebar for other metrics
    col1, col2 = st.sidebar.columns(2)

    # Generate random values for the metrics
    highest_bid, total_bids = generate_random_metrics()

    col1.metric(label="Highest Bid", value=f"Ksh{highest_bid}", delta=f"+{random.randint(1, 20)}")
    col2.metric(label="Live Bids", value=f"{total_bids}", delta=f"+{random.randint(1, 50)}")
    st.sidebar.write("---")


    # Navigation buttons
    navigation_buttons = [
        ("Home", home_page),
        ("Sign Up", signup_page),
        ("Bid", bids_and_gadgets_page),
        ("Search", search_bar),
        ("About Us", about_us),
        ("Log In", login_page),
        ("Customer Support", customer_support_page),
        ("How It Works", how_works),
        ("Privacy Policy", privacy_policy)
    ]

    # Sidebar navigation for the main pages
    for name, page_func in navigation_buttons:
        if st.sidebar.button(name):
            st.session_state.active_section = "navigation"
            st.session_state.current_page = name

    # Display the selected page
    current_page_func = dict(navigation_buttons).get(st.session_state.current_page, home_page)
    current_page_func()

    if "active_section"not in st.session_state:
        st.session_state.active_section = "navigation"  # Default value

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"   
       
    st.sidebar.write("---")
    categories=["Exit This Section","Phones and Tablets", "TV and Audio", "Appliances", "Computing"]
    items = st.sidebar.selectbox("**● SELECT CATEGORY**", categories)

    if items != "Exit This Section":
        st.session_state.active_section = "categories"

        if items == "Phones and Tablets":
            st.write("### Displaying Phones and Tablets category")
            bids_and_gadgets_page()  # Show products for Phones and Tablets

        elif items == "TV and Audio":
            st.write("### Displaying TV and Audio category")
            bids_and_gadgets_page()  # Show products for TV and Audio

        elif items == "Appliances":
            st.write("### Displaying Appliances category")
            bids_and_gadgets_page()  # Show products for Appliances

        elif items == "Computing":
            st.write("### Displaying Computing category")
            bids_and_gadgets_page()  # Show products for Computing
    else:
        st.write("### Please select a category from the sidebar to view available products.")

    

    st.sidebar.write("---")  



    st.sidebar.title("Try Out Our New  Bid Predictor")

    product_id = st.sidebar.text_input('Product ID (e.g. p001, t010, etc.)', value='p001') 
    bid_amount = st.sidebar.number_input('Your Bid Amount(Ksh.)', min_value=0.0, value=100.0, step=1.0)
    max_bid_so_far = st.sidebar.number_input('Highest Bid On Product(Ksh.)', min_value=0.0, value=100.0, step=1.0)
    user_past_wins = st.sidebar.number_input('Past Wins', min_value=0, value=0, step=1)
    user_past_bids = st.sidebar.number_input('Total Past Bids', min_value=0, value=1, step=1)
    time_left = st.sidebar.number_input('Time Left (hours)', min_value=1, value=120, step=1)
    product_starting_price = st.sidebar.number_input('Product Starting Price', min_value=1.0, value=100.0, step=1.0)
    user_max_bid = st.sidebar.number_input('Max Bid User Placed(Ksh.)', min_value=0.0, value=200.0, step=1.0)
    product_category = st.sidebar.selectbox('Product Category', options=["Phones and Tablets", "Tv and Audio", "Appliances", "Computing"])
    user_account_age = st.sidebar.number_input('User Account Age (Days)', min_value=1, value=30, step=1)
    user_activity = st.sidebar.selectbox('User Activity', options=['daily', 'weekly', 'monthly'])

     # Make predictions when button is clicked
    
    input_data = {
        'product_id': product_id,
        'bid_amount': bid_amount,
        'max_bid_so_far': max_bid_so_far,
        'user_past_wins': user_past_wins,
        'user_past_bids': user_past_bids,
        'time_left': time_left,
        'product_starting_price': product_starting_price,
        'user_max_bid': user_max_bid,
        'product_category': product_category,
        'user_account_age': user_account_age,
        'user_activity': user_activity
    }
    if st.sidebar.button('Predict Probability of Winning'):
        prediction = predict_win_probability(input_data)  # Get prediction
        st.sidebar.write(f"**Prediction**: {'**Win**' if prediction == 0 else '**Lose**'}")  # Display prediction
        st.sidebar.write("*Disclaimer!!* The Predictor is still under development. The results are based on user data collected")  
    
# Run the app
if __name__ == "__main__":
    main()

