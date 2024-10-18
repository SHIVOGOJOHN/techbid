import streamlit as st 
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
preprocessor_filename = "preprocessor.pkl"
model_filename ="rf_pipeline.pkl" 


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
        't': range(1, 21),     # t001 to t020
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




# Initialize PesaPal class for authentication and order submission



# Function to send confirmation email using Gmail SMTP
def send_confirmation_email(email, name):
    try:
        # Set up the email server
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        sender_email = 'techbidmarketplace@gmail.com'  # Replace with your Gmail address
        sender_password = st.secrets["general"]["sender_password"]  # Replace with your app password

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
        smtp_password = st.secrets["general"]["sender_password"]   # Your email password (Consider using app-specific password for Gmail)

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
            password=st.secrets["general"]["password"],
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
                password=st.secrets["general"]["password"],
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

    # Ensure the form key is generated only once and stored in session state
    if 'signup_form_key' not in st.session_state:
        st.session_state.signup_form_key = f"signup_form_{uuid.uuid4()}"

    # Ensure signup status tracking
    if 'signup_submitted' not in st.session_state:
        st.session_state.signup_submitted = False

    # Create the form using the unique key stored in session state
    if not st.session_state.signup_submitted:
        with st.form(key=st.session_state.signup_form_key):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            password = st.text_input("Password", type='password')

            # Additional fields with unique keys
            st.markdown("### Additional Information")
            phone = st.text_input("Phone Number")
            address = st.text_input("Address")

            # Submit button
            submitted = st.form_submit_button("Sign Up")

            if submitted:
                # Check if all fields are filled
                if not name or not email or not password or not phone or not address:
                    st.error("Please fill out all fields before submitting.")
                else:
                    # Call the function to save user data to MySQL (replace with actual save logic)
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
        self.consumer_secret =  "OuVah65aa8nlL4r8JwpHdoSRgcU="
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
            token = response.json().get('token')
            if token:                     
                return token
            else:
                raise ValueError("Token not found in authentication response.")
        else:
            raise ValueError(f"Authentication failed with status code {response.status_code}.")

    def initiate_payment(self, token, phone_number, amount, order_id, Fname, Lname):
        endpoint = "Transactions/SubmitOrderRequest"
        ipn_id = self.register_ipn()
        if not ipn_id:
            raise ValueError("Failed to register IPN.")
        payload = {
            "id": order_id,
            "currency": "KES",
            "amount": amount,
            "description": "Payment For Product",
            "callback_url": "https://callbak-1.onrender.com/pesapal/callback",  # Replace with your actual callback URL
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
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Payment initiation failed with status code {response.status_code}: {response.text}")
         
    def register_ipn(self):
        if self.cached_ipn_id:
            return self.cached_ipn_id
         
        
        ipn_endpoint = "URLSetup/RegisterIPN"
        payload = {
            "url": "https://ipn-06ai.onrender.com/pesapal/ipn",
            "ipn_notification_type": "GET"
        }

        token = self.authentication()
        if not token:
            raise ValueError("Failed to retrieve token for IPN registration.") 
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {token}"
        }

        response = requests.post(self.ipn_base_url + ipn_endpoint, headers=headers, json=payload)
        if response.status_code == 200:
            ipn_response = response.json()
            self.cached_ipn_id = ipn_response.get("ipn_id")
            return self.cached_ipn_id
        else:
            raise ValueError(f"IPN registration failed with status code {response.status_code}.")



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
            password=st.secrets["general"]["password"],
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

            st.success("Bid saved successfully! loading...")

    except mysql.connector.Error:
        st.error("Error saving bid. Check your connection and try again")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
        

            
###########################################################
def send_confirmation(email, Fname, Lname, bid_amount, product_name):
    sender_email = 'techbidmarketplace@gmail.com'
    sender_password = st.secrets["general"]["sender_password"]   # Use app-specific password or environment variable for security
    
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
def bids_and_gadgets_page(category_filter=None):
    

    st.title("Bids and Gadgets")
    st.write("----")
    st.subheader("Hot This Week")
    gadgets = [
        {
            "name": "XIAOMI Redmi A3, 6.71",
            "image": "1 (3).jpg",
            "description": "4GB RAM +128GB (Dual SIM), 5000mAh, Midnight Black (Newest Model)",
            "price": 9999,
            "product code": "p001",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",  # Replace with your Ko-fi link
            "mpesa_link": "**Pochi La Biashara/Send Money**: +254704234829"
        },
         {
            "name": "Sony PS4 ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/23/188122/1.jpg?7875",
            "description": "500GB - Black",
            "price": 19800,
            "product code": "a020",
            "category":  "Appliances",
        },
         {
            "name": "Itel S24",
            "image": "1 (5).jpg",
            "description": "6.6'', 128GB + 4GB (Extended UPTO 8GB) RAM, 5000mAh, Dawn White (1YR WRTY)",
            "price": 7999,
            "product code": "p003",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Samsung Smart TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/96/386025/2.jpg?6154",
            "description": "43CU7000, 43” Crystal UHD 4K Smart TV",
            "price": 11999,
            "product code": "s020",
            "category":  "Tv and Audio",
        },
         {
            "name":"Apple iPhone 15 Pro Max",
            "image":"1 (6).jpg",
            "description":"6.7‑inch (diagonal) all‑screen OLED display1, 256GB Storage256GB Storage, Action ButtonAction Button, USB-C Charge Cable capable4,Enabled by TrueDepth camera for facil recognition,",
            "price": 33999,
            "product code": "p004",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Samsung Galaxy S24 Ultra",
            "image": "1 (8).jpg",
            "description":"Cell Phone, 512GB AI Smartphone, Unlocked Android, 50MP Zoom Camera, Long Battery Life, S Pen",
            "price": 17999,
            "product code": "p005",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "XIAOMI Redmi 13C",
            "image":"1 (9).jpg",
            "description":"6.47'',  256GB + 8GB RAM (Dual SIM) 5000mAh, 4G - Navy Blue",
            "price":8999 ,
            "product code": "p006",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name":" **Refurbished** Oppo A31",
            "image": "2 (1).jpg",
            "description":"6GB RAM+128GB ROM 6.5 Inch Screen HD Camera 12MP Cyan",
            "price":5999 ,
            "product code": "p007",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Itel 2176 ",
            "image": "3 (1).jpg",
            "description":"Wireless FM, 1.8'', Dual SIM - 1000mAh - Blue",
            "price": 8599,
            "product code": "p008",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Moodio Tablet",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/31/7032842/1.jpg?1960",
            "description": " 6000mAH RAM 8GB/ ROM 512GB 10inch Android 11 Dual SIM CARD SLOT 5G TABLET PC Front 5PM Rear 13PM Android 12.0",
            "price": 9999,
            "product code": "t001",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"

        },
        {
            "name": "Smartwatch T900 Pro Max",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/85/8855721/1.jpg?7826",
            "description": "Bluetooth call, Custom Wallpaper, drinking reminder blood oxygen, sports mode (outdoor running, walking, mountaineering, indoor running), Facebook, twitter, WhatsApp, calendar, message reminder ,heart rate, sleep monitoring, Bluetooth music, SMS, call record, SIRI/Voice Assistant, alarm clock, remote photo, step counting, blood pressure, address book, looking for mobile phone, etc.",
            "price": 100,
            "product code": "t002",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Samsung Galaxy A15",
            "image":r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/70/5472971/1.jpg?3910",
            "description": "6.5'', 4GB RAM + 128GB ROM, DUAL SIM, 50MP, 5000mAh - Blue",
            "price": 9599,
            "product code": "p009",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Itel A50",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/16/1237632/1.jpg?6718",
            "description": "IPS LCD 6.6 INCHES WITH DYNAMIC BAR,UPTO 6GB RAM & 64GB ROM,5000MAH,TYPE-C,SPLY",
            "price": 9899,
            "product code": "p010",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Itel RS4",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/29/9119432/1.jpg?3778",
            "description": "6.6 inch DISPLAY 8GB RAM +256 GB ROM 5000 MAH DUAL SIM",
            "price": 11799,
            "product code": "p011",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Samsung Galaxy A05s",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/75/2759581/1.jpg?1123",
            "description": " 6.7 inch, 128GB + 4GB (Dual SIM), 5000mAh, Black",
            "price": 9800,
            "product code": "p012",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Tecno Camon 30 Pro",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/81/3681922/1.jpg?5586",
            "description": "5G, 6.78 inch AMOLED Display, 512GB ROM + 12GB RAM (Dual SIM) 5000mAh - Basaltic Dark",
            "price": 13599,
            "product code": "p013",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "XIAOMI Redmi Note 13",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/22/4911452/1.jpg?7615",
            "description": "6.67, 128GB + 8GB RAM (Dual SIM), 5000mAh, Midnight Black",
            "price":13999 ,
            "product code": "p014",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Vivo V40",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/73/5132972/1.jpg?5207",
            "description": "6.78 inch, 12GB + 256GB ROM -(Dual SIM) - 5500 MAh -Silver",
            "price": 10499,
            "product code": "p015",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "XIAOMI Redmi 12",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/55/5612772/1.jpg?7831",
            "description": "6.79 inch, 8GB RAM + 128GB, 50MP, 5000mAh, (Dual SIM), Midnight Black",
            "price": 8999,
            "product code": "p016",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Itel Flip 1 Folding Phone",
            "image": "1 (4).jpg",
            "description": " 2.4 inches QQVGA (240 x 320 pixels) display, 8MB of RAM 2.4 - 1200mAh (Dual SIM), Wireless FM, Blue (1YR WRTY)",
            "price": 7599,
            "product code": "p002",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Samsung Galaxy S20 Plus",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/88/4193602/1.jpg?2600",
            "description": " 128GB 12GB RAM 5G S20+ Single SIM - Black",
            "price": 12999,
            "product code": "p017",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Tecno POP 8",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/40/2562052/1.jpg?1183",
            "description": "6.6 inch, 128GB ROM+ 4GB RAM+ (4GB RAM Extended), 13MP, 4G (Dual SIM) 5000MAh - Gravity Black",
            "price": 9599,
            "product code": "p018",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Tecno Phantom V Flip",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/19/0012661/1.jpg?8581",
            "description": "5G, 256GB + 8GB RAM (Single SIM), 4000mAh, Mystic Dawn",
            "price": 7999,
            "product code": "p019",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Infinix Smart 8",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/54/5758262/1.jpg?8084",
            "description": "6.6 inch HD Display 4GB RAM Expandable Up to 6GB + 64GB ROM Android 13 (Dual sim) 5000mAh - Black",
            "price": 9599,
            "product code": "p020",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Oraimo Watch ER",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/24/7964581/1.jpg?0563",
            "description": "1.43 inch AMOLED, BT Call, IP68 Smart Watch_ Black. **Major Function** : meter step、Bluetooth call、Heartrate、Blood Oxygen",
            "price": 65,
            "product code": "t003",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Powerbank",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/72/7426251/1.jpg?1601",
            "description": "30000mAh Fast Charging Portable",
            "price":275 ,
            "product code": "t004",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Oraimo FreePods3",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/66/4276151/1.jpg?6389",
            "description": "One Pair, Two Different Fits,Massive 13mm Driver,Incredibly Powerful Bass8+28 Hrs Playtime,Environmental Noise Cancellation,IPX5 Water & Sweat Proof",
            "price": 790,
            "product code": "t005",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "C15 Speaker",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/46/462937/1.jpg?3249",
            "description": "Portable,Bluetooth,,Quality,Speaker,USB,SUPERFLY",
            "price": 370,
            "product code": "t006",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Itel TWS BudsAce Earbud",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/39/5977512/1.jpg?3316",
            "description": "Earpods Buds Ace ENC Bass 35 Hours- Black",
            "price": 569,
            "product code": "t007",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Android Tablet",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/85/5497242/2.jpg?2230",
            "description": "10.0 inch Tablet 8GB RAM 128GB ROM 10core 4G Full Netcom 5GWIFI Android",
            "price": 7890,
            "product code": "t008",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Phone Cooling Fan",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/43/152287/1.jpg?3072",
            "description": ".It is suitable for 4-6.7inch mobile phones.1 HourBattery Capacity (Rechargeable Style).",
            "price": 750,
            "product code": "t009",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Samsung Galaxy Note 10",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/10/261456/1.jpg?2495",
            "description": "6.3 inch, 8GB + 256GB Mobile Phones ",
            "price": 14999,
            "product code": "t010",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Headphones",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/55/442353/1.jpg?2646",
            "description": "heavy bass,foldable,high quality sound,10m range,blutooth 5.0",
            "price": 650,
            "product code": "t011",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Huawei Y6 Prime",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/26/883144/1.jpg?4867",
            "description": "3GB+32GB 5.7Inch, 3000mAh (13MP+8MP) - Black",
            "price":8299 ,
            "product code": "t013",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Oraimo BoomPop 2 headphone",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/66/3751961/1.jpg?6344",
            "description": "Deep Bass Wireless Headset",
            "price": 499,
            "product code": "t012",
            "category":  "Phones and Tablets",
        },
         {
            "name": " Lenovo Thinkplus XT80 Wireless BT Sport Earphone Mini",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/89/9125252/1.jpg?8765",
            "description": "Wireless BT5.3 Earphone.Ergonomic Earhook Design. Waterproof ",
            "price": 295,
            "product code": "t015",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Wired Headphones",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/87/1634001/2.jpg?3719",
            "description": "Wired, Extra Bass",
            "price": 675,
            "product code": "t014",
            "category":  "Phones and Tablets",
        },
         {
            "name": "T500 smart watch",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/27/0196061/1.jpg?1488",
            "description": " Supports heart rate detection/blood pressure detection/blood oxygen detection/sleep monitoring, etc.Make and receive calls. step counting, calories, distance monitoring, incoming call reminders.Sleep monitoring. Bluetooth music player.Bluetooth camera",
            "price": 270,
            "product code": "t016",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Realme C67",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/73/7121932/1.jpg?8237",
            "description": " 8GB RAM +256GB, 6.72 inch,5000mAh",
            "price": 9799,
            "product code": "t017",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Nokia C32",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/72/5942951/1.jpg?1794",
            "description": "6.5 inches 64GB ROM + 4GB RAM Expandable To 7GB,",
            "price": 11899,
            "product code": "t018",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Samsung Galaxy S9+ Plus",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/08/4905961/2.jpg?0424",
            "description": "6.2 inches 64GB + 6GB - (Single SIM) - Midnight Black",
            "price": 8599,
            "product code": "t019",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Earbuds Air31",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/94/7900332/1.jpg?2139",
            "description": "Bluetooth 5.3, transparent design, deep bass, built-in microphone and EDR",
            "price": 499,
            "product code": "t020",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Hikers HD TV",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/37/9811031/7.jpg?4934",
            "description": " 32 inches Digital Frameless HD LED TV-Black",
            "price": 13900,
            "product code": "s001",
            "category":  "Tv and Audio",
        },
         {
            "name": "Vitron Multimedia Speaker System",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/21/749223/3.jpg?2121",
            "description": " Plays FM radio, and MP3 from the USB and SD card slots",
            "price":970 ,
            "product code": "s002",
            "category":  "Tv and Audio",
        },
         {
            "name": "Vitron LED TV",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/59/869053/1.jpg?7469",
            "description": "50” Smart Android 4K UHD LED TV ,FRAMELESS DESIGN, Ports: USB(2), HDMI (3)、AV input(1)",
            "price": 9899,
            "product code": "s003",
            "category":  "Tv and Audio",
        },
         {
            "name": "Vitron BASS Sub Woofer System",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/38/2979701/1.jpg?3973",
            "description": "FM-USB,Bluetooth-9000watts",
            "price": 1299,
            "product code": "s004",
            "category":  "TV and Audio",
        },
         {
            "name": "A2 Subwoofer Speaker",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/25/8272451/3.jpg?6104",
            "description": "Computer Bluetooth Speaker High BoomBox Outdoor Bass HIFI TF FM Radio Audio USB Smart Subwoofer Speaker",
            "price": 2750,
            "product code": "s005",
            "category":  "Tv and Audio",
        },
         {
            "name": "Vitron 4388-FS Android TV",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/03/039084/3.jpg?5217",
            "description": "Display: 43″, FRAMELESS, SMART Android FULL HD TV 1080p,USB x2, HDMI x3,Inbuilt Wi-Fi  ",
            "price": 10599,
            "product code": "s006",
            "category":  "Tv and Audio",
        },
         {
            "name": "Bluetooth Speaker",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/12/2833621/1.jpg?8146",
            "description": "Portable Loud Bluetooth/ USB ,  FM, USB, SD",
            "price": 785,
            "product code": "s007",
            "category":  "Tv and Audio",
        },
         {
            "name": "TCL 50C655 Smart TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/27/8072362/2.jpg?9075",
            "description": "50 Inch UHD 4K QLED Gaming In Dolby Vision Smart TV (2024) Model",
            "price": 9799,
            "product code": "s008",
            "category":  "Tv and Audio",
        },
         {
            "name": "Hifinit Projector ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/75/9715981/3.jpg?1061",
            "description": "1080P 6000 Lumens Full HD USB LED WiFi Projector With High Resolution",
            "price": 9699,
            "product code": "s009",
            "category":  "Tv and Audio",
        },
         {
            "name": "Gld Smart TV",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/42/8717091/2.jpg?2265",
            "description": "65 inch Frameless Ultra HD LED Television - Black.",
            "price":15999 ,
            "product code": "s010",
            "category":  "Tv and Audio",
        },
         {
            "name": "Vention HDMI",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/05/1438862/1.jpg?0123",
            "description": "Female to Female Coupler Adapter Black",
            "price": 75,
            "product code": "s011",
            "category":  "Tv and Audio",
        },
         {
            "name": "Vitron HTC3200S Android TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/37/0349162/4.jpg?9092",
            "description": "32 inches Smart Frameless Android LED TV, With Bluetooth",
            "price":8999,
            "product code": "s012",
            "category":  "Tv and Audio ",
        },
         {
            "name": "Skyworth 32E57 Google TV",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/26/1892961/2.jpg?6485",
            "description": "32-inches Full HD Frameless Smart Google, Android 9.0 Pie, Google Assistant ",
            "price": 12599,
            "product code": "s013",
            "category":  "Tv and Audio",
        },
         {
            "name": "Hisense Smart TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/06/6199191/1.jpg?9767",
            "description": " 32″ 32A4KKEN,Smart  Frameless LED Television",
            "price": 9499,
            "product code": "s014",
            "category":  "Tv and Audio",
        },
         {
            "name": "CTC DIGITAL TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/10/966483/1.jpg?1052",
            "description": "Screen size: 22 inch,Type: LED Backlight, USB HDMI  VGA(1)、AV input(1)",
            "price": 7900,
            "product code": "s015",
            "category":  "Tv and Audio",
        },
         {
            "name": "Skyworth Android TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/84/4380801/1.jpg?5912",
            "description": " 55G3B, 55-inches 4K QLED 2022 Frameless Smart Android TV",
            "price": 19999,
            "product code": "s016",
            "category":  "Tv and Audio",
        },
         {
            "name": "Samsung Smart TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/70/216992/1.jpg?2337",
            "description": "UA32T5300AUXKE 32-inches LED TV, Smart TV, HD 720p",
            "price": 10499,
            "product code": "s017",
            "category":  "Tv and Audio",
        },
         {
            "name": "TCL Android TV",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/68/7134312/3.jpg?3522",
            "description": "43 Inch, 4K Ultra HD Smart LED Google/Android TV,Bluetooth-Enabled",
            "price": 14599,
            "product code": "s018",
            "category":  "Tv and Audio",
        },
         {
            "name": "TV Wall Mount Skilltech 15 inch To 43 inch Tilting Wall Mount Bracket",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/31/089534/1.jpg?6737",
            "description": "",
            "price": 280,
            "product code": "s019",
            "category":  "Tv and Audio",
        },
         {
            "name": "LED Music Bulb",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/07/901592/5.jpg?8096",
            "description": "LED Music Bulb With Bluetooth, Music Player",
            "price": 100,
            "product code": "s021",
            "category":  "Tv and Audio",
        },
         {
            "name": " Tripod Stand",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/25/8259781/4.jpg?3325",
            "description": "LASA 132cm Tripod Travel Stand For Phone / Camera",
            "price": 110,
            "product code": "s022",
            "category":  "Tv and Audio",
        },
         {
            "name": "A2 Subwoofer Speaker ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/25/8272451/3.jpg?6104",
            "description": "4D Crystal Stereo, Comfort LED Light,Two Power Supply Ways.",
            "price": 399,
            "product code": "s023",
            "category":  "Tv and Audio",
        },
         {
            "name": "Lapel Microphone",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/03/2935121/2.jpg?1175",
            "description": "For Cameras Phone,150CM Cable,suitable for various devices,Excellent audio recording ",
            "price": 299,
            "product code": "s024",
            "category":  "Tv and Audio",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Apple MacBook Pro",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/49/4513412/1.jpg?4162",
            "description": "13-inches Core I5 2.4GHz 8GB RAM, 500GB HDD (2012) Silver Refurbished",
            "price":11999,
            "product code": "c001",
            "category":  "Computing",
        },
         {
            "name": "HP Refurbished Elitebook 840 G2",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/63/1880001/2.jpg?7040",
            "description": " 5th Gen Touchscreen Core i5, 8GB RAM 500GB HDD -14-inches, Black , CPU: 2.5GHz CPU: 2.5GHz,Graphics Card: Intel HD Graphics 4000 ",
            "price": 10899,
            "product code": "c002",
            "category":  "Computing",
        },

         {
            "name": "Lenovo Refurbished ThinkPad Yoga 11e",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/24/467116/2.jpg?6596",
            "description": "X360 Intel -Touchscreen- 11.6-inches - 4GB RAM - 128GB SSD - Black, Processor: Intel® Celeron®",
            "price": 8799,
            "product code": "c003",
            "category":  "Computing",
        },
         {
            "name": "Infinix InBook X2",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/44/3582562/3.jpg?3833",
            "description": "14.0 inches, Intel Core i5, 8GB RAM, 512GB SSD - Windows 11 Home - Grey, 4-Cores, 1.0GHz~3.6GHz,Memory: 8GB DDR4 , Intel® Core™ i5-1035G1",
            "price": 15899,
            "product code": "c004",
            "category":  "Computing",
        },

         {
            "name": "Lenovo Refurbished Thinkpad X250",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/31/4719121/2.jpg?2817",
            "description": "Intel Core i5 8GB RAM DDR3  256GB SSD 12.5'' Black, Windows 10, Intel Core i5-4300U  Processor, ",
            "price": 9999,
            "product code": "c005",
            "category":  "Computing",
        },
         {
            "name": "Lenovo Refurbshed Thinkpad T470S",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/43/3631462/2.jpg?0340",
            "description": "Core I5 8GB Ram 256GB SSD, 6th Generation 14 inches,Windows 10",
            "price": 10599,
            "product code": "c006",
            "category":  "Computing",
        },

         {
            "name": "Lenovo IdeaPad 1",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/61/9142572/5.jpg?9602",
            "description": "Intel Celeron N4020,New,  8GB SO-DIMM DDR4-2400, 256GB SSD, 14-inches HD Display, Windows 11 Pro,2 cores / 2 threads, 1.1GHz base / 2.8GHz boost,USB C ",
            "price": 17599,
            "product code": "c007",
            "category":  "Computing",
        },
         {
            "name": "HP REVOLVE 810 G3",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/04/4519691/1.jpg?1447",
            "description": " I7 5TH GEN 8GB RAM 256GB SSD TOUCHSCREEN ,4 CPUs, Refurbished",
            "price": 12299,
            "product code": "c008",
            "category":  "Computing",
        },

         {
            "name": "Lenovo ThinkPad X390",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/55/7775452/4.jpg?1489",
            "description": "Core I5-8th Gen-Touchscreen-16GB Ram 256GB SSD Refurbished - 13-inches Screen- Black- Win 11 Pro ",
            "price": 11599,
            "product code": "c009",
            "category":  "Computing",
        },
         {
            "name": "HP REFURBISHED 8440",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/11/471006/2.jpg?6764",
            "description": "Intel® Core™ i5-7500U  4GB 500HDD  DDR4,14-inches,   windows 10 ",
            "price": 11499,
            "product code": "c010",
            "category":  "Computing",
        },
         {
            "name": "DELL Latitude 3190",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/04/9995202/3.jpg?5766",
            "description": "X360 4GB RAM 128GB SSD 11.6 Inches Touchscreen Intel Pentium Silver 1.1GHz Quad Core 2-in-1 Convertible Windows 10 Pro Refurbished ",
            "price": 10999,
            "product code": "c011",
            "category":  "Computing",
        },

         {
            "name": "Lenovo Refurbished X390 Yoga",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/45/8069172/3.jpg?2049",
            "description": " Intel® Core™ i5-8250U processor 8th Gen 16GB +256GB SSD 13.3-inches FHD X360",
            "price": 10899,
            "product code": "c012",
            "category":  "Computing",
        },
         {
            "name": "HP Elitebook 840 G5",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/24/4911021/2.jpg?2692",
            "description": "Intel Core i7-8300U -8th Generation,16GB DDR4,512 GB SSD, 14-inches",
            "price": 10999,
            "product code": "c013",
            "category":  "Computing",
        },

         {
            "name": "DELL REFURBISHED 5480",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/99/2871642/4.jpg?6568",
            "description": "Intel(R)Core(TM) i5 7th gen 16 GB RAM 256 SSD 14-inches Windows 10Pro",
            "price": 11499,
            "product code": "c014",
            "category":  "Computing",
        },
        {
            "name": "Lenovo Refurbished Thinkpad X131e ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/05/917585/4.jpg?2782",
            "description": " 12.5-inch Display,4 GB RAM , 128GB SSD ,  intel core i3",
            "price": 10199,
            "product code": "c015",
            "category":  "Computing",
        },
         
        {
            "name": "Portable Monitor",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/53/0967182/4.jpg?1956",
            "description": "16inch 2K Monitor USBC UltraThin Gaming",
            "price": 14599,
            "product code": "c016",
            "category":  "Computing",
        },

         {
            "name": "Hp M24f Monitor",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/96/6659112/1.jpg?7998",
            "description": "23.8 Inch FHD Monitor, Edge to Edge,VGA, HDMI 1.4 USB",
            "price": 12599,
            "product code": "c017",
            "category":  "Computing",
        },
         {
            "name": "HP P27 G5 Monitor",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/87/9105172/2.jpg?2942",
            "description": "27-inch 1920 X 1080 75Hz IPS Monitor",
            "price": 13499,
            "product code": "c018",
            "category":  "Computing",
        },

         {
            "name": "Portable Monitor",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/08/1865981/1.jpg?4015",
            "description": "14-inches IPS High-definition Perfect Screen 16:9 ",
            "price": 144,
            "product code": "c019",
            "category":  "Computing",
        },

         {
            "name": "DELL P Series",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/01/6620562/1.jpg?7817",
            "description": "24-inches Screen LED-Lit Monitor ",
            "price": 11199,
            "product code": "c020",
            "category":  "Computing",
        },
         {
            "name": "HP S9000",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/48/665466/2.jpg?6753",
            "description": "Wireless mouse",
            "price": 250,
            "product code": "c021",
            "category":  "Computing",
        },

         {
            "name": "Lenovo ThinkCentre",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/62/7122511/1.jpg?0637",
            "description": "core I5,4GB RAM,320GB, Windows 10 Refurbished Tiny Desktop/Mini PC",
            "price": 7999,
            "product code": "c022",
            "category":  "Computing",
        },

         {
            "name": "GK3V Pro ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/41/2097071/1.jpg?1845",
            "description": " Intel Celeron N5105 CPU Mini PC 16GB+512GB, Windows 10",
            "price": 11300,
            "product code": "c023",
            "category":  "Computing",
        },
         {
            "name": "BMAX B1 Pro",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/16/2244742/1.jpg?0739",
            "description": "Windows 10 Intel Celeron N4000 Mini PC B1 Pro 8GB+128GB",
            "price": 10999,
            "product code": "c024",
            "category":  "Computing",
        },
         {
            "name": "Gaming Speaker",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/21/8255771/1.jpg?7985",
            "description": "Gaming Speaker Setting Temperature 4000 MAh For PC Laptop, ",
            "price": 384,
            "product code": "c025",
            "category":  "Computing",
        },
         {
            "name": "AILYONS Iron Box",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/37/591474/5.jpg?3794",
            "description": "AILYONS HD-198A Electric Dry Iron Box",
            "price": 890,
            "product code": "a001",
            "category":  "Appliances",
        },
         {
            "name": "Sokany Coffee Machine",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/51/7100351/1.jpg?1199",
            "description": "Can brew tea, but also can be used to cook coffee, Anti-drip ",
            "price": 9599,
            "product code": "a002",
            "category":  "Appliances",
        },
         {
            "name": "Roch RFR-120S-I ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/65/7297161/3.jpg?9518",
            "description": "Single Door Refrigerator - 90 Litres",
            "price": 8599,
            "product code": "a003",
            "category":  "Appliances",
        },
         {
            "name": "Ramtons RF/335 - 85L",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/21/3614472/2.jpg?5266",
            "description": " Single Door Refrigerator ",
            "price": 10899,
            "product code": "a004",
            "category":  "Appliances",
        },
         {
            "name": "Mika MBLR301/WG - Blender",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/60/533581/2.jpg?1020",
            "description": "1.5L - 400W - White & Grey",
            "price": 8599,
            "product code": "a005",
            "category":  "Appliances",
        },
         {
            "name": "Hisense WTJA802T ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/04/117685/3.jpg?1630",
            "description": "8Kg Top Load Washing Machine, Silver",
            "price": 13899,
            "product code": "a006",
            "category":  "Appliances",
        },

         {
            "name": "Hisense WFQR1214VAJMT ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/59/7872902/2.jpg?4165",
            "description": "12KG Washing Machine",
            "price": 10900,
            "product code": "a007",
            "category":  "Appliances",
        },
         {
            "name": "Ramtons RG/544",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/42/110663/1.jpg?3773",
            "description": " Stainless Steel Table Top 2 Burner Gas Cooker ",
            "price": 3999,
            "product code": "a008",
            "category":  "Appliances",
        },
         {
            "name": "Ramtons RM/582",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/33/505623/1.jpg?3816",
            "description": "Electric Pressure Cooker- Black",
            "price": 7899,
            "product code": "a009",
            "category":  "Appliances",
        },

         {
            "name": "Ramtons RM/429",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/37/566023/1.jpg?7637",
            "description": "Hot & Normal Water Dispenser + Stand",
            "price":9899,
            "product code": "a010",
            "category":  "Appliances",
        },
         {
            "name": "Jamespot Cooker",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/46/4309981/3.jpg?7111",
            "description": "Multi-functional Touch Electric Ceramic Cooker Induction Cooker",
            "price":13499 ,
            "product code": "a011",
            "category":  "Appliances",
        },
         {
            "name": "Boma Sandwich Maker",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/07/6400061/1.jpg?6441",
            "description": "2slot Sandwich Maker",
            "price": 2999,
            "product code": "a012",
            "category":  "Appliances",
        },

         {
            "name": "VON Water Dispenser",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/66/3063251/2.jpg?2351",
            "description": "3 Tap Hot & Cold & Normal Electric Cooling With Cabinet -Black",
            "price": 14999,
            "product code": "a013",
            "category":  "Appliances",
        },
         {
            "name": "Ramtons RM/458",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/36/472432/3.jpg?0918",
            "description": "Digital Glass Microwave, 700W - 20L",
            "price":8799 ,
            "product code": "a014",
            "category":  "Appliances",
        },
         {
            "name": "AILYONS Iron Box ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/10/031916/1.jpg?0150",
            "description": "Quality Dry Iron Box With Titanium Teflon Nonstick Soleplate",
            "price": 1140,
            "product code": "a015",
            "category":  "Appliances",
        },

         {
            "name": "JP Water Kettle",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/94/930065/2.jpg?1425",
            "description": "7.5 L Stainless Steel Automatic Water Kettle",
            "price": 799,
            "product code": "a016",
            "category":  "Appliances",
        },
         {
            "name": "Oraimo Vacuum Cleaner",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/06/3644781/1.jpg?5681",
            "description": "Hand Held Cordless Vacuum Cleaner-Black",
            "price": 7999,
            "product code": "a017",
            "category":  "Appliances",
        },
         {
            "name": "Oraimo Smart Kettle ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/06/5310681/1.jpg?6123",
            "description": "1.7L Full Metal Liner Kettle",
            "price": 799,
            "product code": "a018",
            "category":  "Appliances",
        },

         {
            "name": "AILYONS FY-1731 Blender",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/01/953072/1.jpg?6452",
            "description": "2 In 1 With Grinder Machines 1.5L",
            "price": 8999,
            "product code": "a019",
            "category":  "Appliances",
        },
         {
            "name": "ALYONS ELECTRIC KETTLE",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/78/7016751/1.jpg?8244",
            "description": "2.2 L LITRES ALYONS ELECTRIC KETTLE",
            "price":999,
            "product code": "a021",
            "category":  "Appliances",
        },

         {
            "name": "XBOX Series S",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/85/331235/1.jpg?6775",
            "description": "512GB All-Digital Console",
            "price": 17899,
            "product code": "a022",
            "category":  "Appliances",
        },
         {
            "name": "G5 Mini",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/63/2651052/1.jpg?6239",
            "description": "Game Box Console Retro Games 2.4G WiFi HD Game",
            "price": 12999,
            "product code": "a023",
            "category":  "Appliances",
        },
         {
            "name": "Nintendo Switch Lite",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/93/3547412/1.jpg?8218",
            "description": "5.5″ touch screen, Battery Life: Approximately 3-7 hours, Compatible with Nintendo Switch games",
            "price": 11399,
            "product code": "a024",
            "category":  "Appliances",
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
    cols = st.columns(4)  # Create 3 columns

    # Create a list to hold the layout of gadgets
    rows = []

    # Ensure the session state keys are initialized
    if 'selected_gadget' not in st.session_state:
        st.session_state.selected_gadget = None

    if 'show_form' not in st.session_state:
        st.session_state.show_form = {}

# Filter products based on the selected category
    if category_filter:
        filtered_gadgets = [gadget for gadget in gadgets if category_filter(gadget['product code'])]
    else:
        filtered_gadgets = gadgets

    # Initialize highest bids in session_state (persist in a database for a real app)
    if 'highest_bids' not in st.session_state:
        st.session_state.highest_bids = {
            "p001": 9999,  
            "p002": 7599,
            "p003": 7999,
            "p004": 33999,  
            "p005": 17999,
            "p006": 8999,  
            "p007": 5999,
            "p008": 85999,
            "p009": 9599,  
            "p010": 9899,
            "p011": 11799,
            "p012": 9800,  
            "p013": 13599,
            "p014": 13999,
            "p015": 10499,  
            "p015": 10499,
            "p016": 8999,
            "p017": 12999,  
            "p018": 9599,
            "p019": 7999,
            "p020": 9599,
            "t001": 185,
            "t002": 100,
            "t003": 65,
            "t004": 275,
            "t005": 790,
            "t006": 370,
            "t007": 569,
            "t008": 7890,
            "t009": 750,
            "t010":14999,
            "t011": 650,
            "t012": 499,
            "t013": 8299,
            "t014": 675,
            "t015": 295,
            "t016": 270,
            "t017": 9799,
            "t018": 11899,
            "t019": 8599,
            "t020": 499,
            "s001": 13900,
            "s002": 970,
            "s003": 9899,           
            "s004": 1299,
            "s005": 2750,
            "s006": 10599,           
            "s007": 785,
            "s008": 9799,
            "s009": 9699,           
            "s010": 15999,
            "s011": 75,
            "s012": 8999,            
            "s013": 12599,
            "s014": 9499,
            "s015":7900,           
            "s016": 19999,
            "s017": 10499,
            "s018": 14599,            
            "s019": 280,
            "s020": 11999,
            "s021": 100,           
            "s022": 110,
            "s023": 399,
            "s024": 299,
            "a001": 890,
            "a002": 9599,
            "a003":8599,
            "a004": 10899,
            "a005": 8599,
            "a006": 13999,
            "a007": 10900,
            "a008": 3999,
            "a009": 7899,
            "a010": 9899,
            "a011": 13499,
            "a012": 2999,
            "a013": 14999,
            "a014": 8799,
            "a015": 1140,
            "a016": 799,
            "a017": 7999,
            "a018": 799,
            "a019": 8999,
            "a020": 19800,
            "a021": 999,
            "a022": 17899,
            "a023": 12999,
            "a024": 11399,
            "c001": 11999,
            "c002": 9899,
            "c003": 8799,
            "c004": 15899,
            "c005": 9999,
            "c006": 10599,
            "c007": 17599,
            "c008": 12299,
            "c009": 11599,
            "c010": 11499,
            "c011": 10999,
            "c012": 10899,
            "c013": 10999,
            "c014": 11499,
            "c015": 10199,
            "c016": 14599,
            "c017": 12599,
            "c018": 13499,
            "c019": 144,
            "c020": 11199,
            "c021": 250,
            "c022": 7999,
            "c023": 11300,
            "c024": 10999,
            "c025": 385
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
            random_increment = random.randint(1, 55)
            new_highest_bid = st.session_state.highest_bids[product_code] + random_increment
            update_highest_bid(product_code, new_highest_bid)      
    
    simulate_random_bids()

    # Display products in columns and rows
    for idx, gadget in enumerate(filtered_gadgets):
        col_idx = idx % 4  # Get column index
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

                bid_button_key = f"bid-button-{gadget['product code']}-{idx}-{gadget['name']}"


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
                        with st.form(key=f"bid-form-{product_code}"): 
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
                            submit_button = st.form_submit_button("Confirm Bid")
                        if submit_button:

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
                                         
                                        if result and "OrderTrackingId" in result:
                                            order_tracking_id = result["OrderTrackingId"]
                                            redirect_url = f"https://pay.pesapal.com/iframe/PesapalIframe3/Index?OrderTrackingId={order_tracking_id}"
                                            redirect_url = result.get("redirect_url")                        
                                            st.markdown(f"[👉Click here to complete bid .](https://pay.pesapal.com/iframe/PesapalIframe3/Index?OrderTrackingId=bvbvffggjnmjjfmkll99phn)", unsafe_allow_html=True)                                                                                                                       
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
            "image": "1 (3).jpg",
            "description": "4GB RAM +128GB (Dual SIM), 5000mAh, Midnight Black (Newest Model)",
            "price": 9999,
            "product code": "p001",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",  # Replace with your Ko-fi link
            "mpesa_link": "**Pochi La Biashara/Send Money**: +254704234829"
        },
         {
            "name": "Sony PS4 ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/23/188122/1.jpg?7875",
            "description": "500GB - Black",
            "price": 19800,
            "product code": "a020",
            "category":  "Appliances",
        },
         {
            "name": "Itel S24",
            "image": "1 (5).jpg",
            "description": "6.6'', 128GB + 4GB (Extended UPTO 8GB) RAM, 5000mAh, Dawn White (1YR WRTY)",
            "price": 7999,
            "product code": "p003",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Samsung Smart TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/96/386025/2.jpg?6154",
            "description": "43CU7000, 43” Crystal UHD 4K Smart TV",
            "price": 11999,
            "product code": "s020",
            "category":  "Tv and Audio",
        },
         {
            "name":"Apple iPhone 15 Pro Max",
            "image":"1 (6).jpg",
            "description":"6.7‑inch (diagonal) all‑screen OLED display1, 256GB Storage256GB Storage, Action ButtonAction Button, USB-C Charge Cable capable4,Enabled by TrueDepth camera for facil recognition,",
            "price": 33999,
            "product code": "p004",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Samsung Galaxy S24 Ultra",
            "image": "1 (8).jpg",
            "description":"Cell Phone, 512GB AI Smartphone, Unlocked Android, 50MP Zoom Camera, Long Battery Life, S Pen",
            "price": 17999,
            "product code": "p005",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "XIAOMI Redmi 13C",
            "image":"1 (9).jpg",
            "description":"6.47'',  256GB + 8GB RAM (Dual SIM) 5000mAh, 4G - Navy Blue",
            "price":8999 ,
            "product code": "p006",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name":" **Refurbished** Oppo A31",
            "image": "2 (1).jpg",
            "description":"6GB RAM+128GB ROM 6.5 Inch Screen HD Camera 12MP Cyan",
            "price":5999 ,
            "product code": "p007",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Itel 2176 ",
            "image": "3 (1).jpg",
            "description":"Wireless FM, 1.8'', Dual SIM - 1000mAh - Blue",
            "price": 8599,
            "product code": "p008",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Moodio Tablet",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/31/7032842/1.jpg?1960",
            "description": " 6000mAH RAM 8GB/ ROM 512GB 10inch Android 11 Dual SIM CARD SLOT 5G TABLET PC Front 5PM Rear 13PM Android 12.0",
            "price": 9999,
            "product code": "t001",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"

        },
        {
            "name": "Smartwatch T900 Pro Max",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/85/8855721/1.jpg?7826",
            "description": "Bluetooth call, Custom Wallpaper, drinking reminder blood oxygen, sports mode (outdoor running, walking, mountaineering, indoor running), Facebook, twitter, WhatsApp, calendar, message reminder ,heart rate, sleep monitoring, Bluetooth music, SMS, call record, SIRI/Voice Assistant, alarm clock, remote photo, step counting, blood pressure, address book, looking for mobile phone, etc.",
            "price": 100,
            "product code": "t002",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Samsung Galaxy A15",
            "image":r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/70/5472971/1.jpg?3910",
            "description": "6.5'', 4GB RAM + 128GB ROM, DUAL SIM, 50MP, 5000mAh - Blue",
            "price": 9599,
            "product code": "p009",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Itel A50",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/16/1237632/1.jpg?6718",
            "description": "IPS LCD 6.6 INCHES WITH DYNAMIC BAR,UPTO 6GB RAM & 64GB ROM,5000MAH,TYPE-C,SPLY",
            "price": 9899,
            "product code": "p010",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Itel RS4",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/29/9119432/1.jpg?3778",
            "description": "6.6 inch DISPLAY 8GB RAM +256 GB ROM 5000 MAH DUAL SIM",
            "price": 11799,
            "product code": "p011",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Samsung Galaxy A05s",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/75/2759581/1.jpg?1123",
            "description": " 6.7 inch, 128GB + 4GB (Dual SIM), 5000mAh, Black",
            "price": 9800,
            "product code": "p012",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Tecno Camon 30 Pro",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/81/3681922/1.jpg?5586",
            "description": "5G, 6.78 inch AMOLED Display, 512GB ROM + 12GB RAM (Dual SIM) 5000mAh - Basaltic Dark",
            "price": 13599,
            "product code": "p013",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "XIAOMI Redmi Note 13",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/22/4911452/1.jpg?7615",
            "description": "6.67, 128GB + 8GB RAM (Dual SIM), 5000mAh, Midnight Black",
            "price":13999 ,
            "product code": "p014",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Vivo V40",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/73/5132972/1.jpg?5207",
            "description": "6.78 inch, 12GB + 256GB ROM -(Dual SIM) - 5500 MAh -Silver",
            "price": 10499,
            "product code": "p015",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "XIAOMI Redmi 12",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/55/5612772/1.jpg?7831",
            "description": "6.79 inch, 8GB RAM + 128GB, 50MP, 5000mAh, (Dual SIM), Midnight Black",
            "price": 8999,
            "product code": "p016",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
        {
            "name": "Itel Flip 1 Folding Phone",
            "image": "1 (4).jpg",
            "description": " 2.4 inches QQVGA (240 x 320 pixels) display, 8MB of RAM 2.4 - 1200mAh (Dual SIM), Wireless FM, Blue (1YR WRTY)",
            "price": 7599,
            "product code": "p002",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Samsung Galaxy S20 Plus",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/88/4193602/1.jpg?2600",
            "description": " 128GB 12GB RAM 5G S20+ Single SIM - Black",
            "price": 12999,
            "product code": "p017",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Tecno POP 8",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/40/2562052/1.jpg?1183",
            "description": "6.6 inch, 128GB ROM+ 4GB RAM+ (4GB RAM Extended), 13MP, 4G (Dual SIM) 5000MAh - Gravity Black",
            "price": 9599,
            "product code": "p018",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Tecno Phantom V Flip",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/19/0012661/1.jpg?8581",
            "description": "5G, 256GB + 8GB RAM (Single SIM), 4000mAh, Mystic Dawn",
            "price": 7999,
            "product code": "p019",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Infinix Smart 8",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/54/5758262/1.jpg?8084",
            "description": "6.6 inch HD Display 4GB RAM Expandable Up to 6GB + 64GB ROM Android 13 (Dual sim) 5000mAh - Black",
            "price": 9599,
            "product code": "p020",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Oraimo Watch ER",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/24/7964581/1.jpg?0563",
            "description": "1.43 inch AMOLED, BT Call, IP68 Smart Watch_ Black. **Major Function** : meter step、Bluetooth call、Heartrate、Blood Oxygen",
            "price": 65,
            "product code": "t003",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Powerbank",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/72/7426251/1.jpg?1601",
            "description": "30000mAh Fast Charging Portable",
            "price":275 ,
            "product code": "t004",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Oraimo FreePods3",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/66/4276151/1.jpg?6389",
            "description": "One Pair, Two Different Fits,Massive 13mm Driver,Incredibly Powerful Bass8+28 Hrs Playtime,Environmental Noise Cancellation,IPX5 Water & Sweat Proof",
            "price": 790,
            "product code": "t005",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "C15 Speaker",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/46/462937/1.jpg?3249",
            "description": "Portable,Bluetooth,,Quality,Speaker,USB,SUPERFLY",
            "price": 370,
            "product code": "t006",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Itel TWS BudsAce Earbud",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/39/5977512/1.jpg?3316",
            "description": "Earpods Buds Ace ENC Bass 35 Hours- Black",
            "price": 569,
            "product code": "t007",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Android Tablet",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/85/5497242/2.jpg?2230",
            "description": "10.0 inch Tablet 8GB RAM 128GB ROM 10core 4G Full Netcom 5GWIFI Android",
            "price": 7890,
            "product code": "t008",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Phone Cooling Fan",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/43/152287/1.jpg?3072",
            "description": ".It is suitable for 4-6.7inch mobile phones.1 HourBattery Capacity (Rechargeable Style).",
            "price": 750,
            "product code": "t009",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Samsung Galaxy Note 10",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/10/261456/1.jpg?2495",
            "description": "6.3 inch, 8GB + 256GB Mobile Phones ",
            "price": 14999,
            "product code": "t010",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Headphones",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/55/442353/1.jpg?2646",
            "description": "heavy bass,foldable,high quality sound,10m range,blutooth 5.0",
            "price": 650,
            "product code": "t011",
            "category":  "Phones and Tablets",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Huawei Y6 Prime",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/26/883144/1.jpg?4867",
            "description": "3GB+32GB 5.7Inch, 3000mAh (13MP+8MP) - Black",
            "price":8299 ,
            "product code": "t013",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Oraimo BoomPop 2 headphone",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/66/3751961/1.jpg?6344",
            "description": "Deep Bass Wireless Headset",
            "price": 499,
            "product code": "t012",
            "category":  "Phones and Tablets",
        },
         {
            "name": " Lenovo Thinkplus XT80 Wireless BT Sport Earphone Mini",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/89/9125252/1.jpg?8765",
            "description": "Wireless BT5.3 Earphone.Ergonomic Earhook Design. Waterproof ",
            "price": 295,
            "product code": "t015",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Wired Headphones",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/87/1634001/2.jpg?3719",
            "description": "Wired, Extra Bass",
            "price": 675,
            "product code": "t014",
            "category":  "Phones and Tablets",
        },
         {
            "name": "T500 smart watch",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/27/0196061/1.jpg?1488",
            "description": " Supports heart rate detection/blood pressure detection/blood oxygen detection/sleep monitoring, etc.Make and receive calls. step counting, calories, distance monitoring, incoming call reminders.Sleep monitoring. Bluetooth music player.Bluetooth camera",
            "price": 270,
            "product code": "t016",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Realme C67",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/73/7121932/1.jpg?8237",
            "description": " 8GB RAM +256GB, 6.72 inch,5000mAh",
            "price": 9799,
            "product code": "t017",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Nokia C32",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/72/5942951/1.jpg?1794",
            "description": "6.5 inches 64GB ROM + 4GB RAM Expandable To 7GB,",
            "price": 11899,
            "product code": "t018",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Samsung Galaxy S9+ Plus",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/08/4905961/2.jpg?0424",
            "description": "6.2 inches 64GB + 6GB - (Single SIM) - Midnight Black",
            "price": 8599,
            "product code": "t019",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Earbuds Air31",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/94/7900332/1.jpg?2139",
            "description": "Bluetooth 5.3, transparent design, deep bass, built-in microphone and EDR",
            "price": 499,
            "product code": "t020",
            "category":  "Phones and Tablets",
        },
         {
            "name": "Hikers HD TV",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/37/9811031/7.jpg?4934",
            "description": " 32 inches Digital Frameless HD LED TV-Black",
            "price": 13900,
            "product code": "s001",
            "category":  "Tv and Audio",
        },
         {
            "name": "Vitron Multimedia Speaker System",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/21/749223/3.jpg?2121",
            "description": " Plays FM radio, and MP3 from the USB and SD card slots",
            "price":970 ,
            "product code": "s002",
            "category":  "Tv and Audio",
        },
         {
            "name": "Vitron LED TV",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/59/869053/1.jpg?7469",
            "description": "50” Smart Android 4K UHD LED TV ,FRAMELESS DESIGN, Ports: USB(2), HDMI (3)、AV input(1)",
            "price": 9899,
            "product code": "s003",
            "category":  "Tv and Audio",
        },
         {
            "name": "Vitron BASS Sub Woofer System",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/38/2979701/1.jpg?3973",
            "description": "FM-USB,Bluetooth-9000watts",
            "price": 1299,
            "product code": "s004",
            "category":  "TV and Audio",
        },
         {
            "name": "A2 Subwoofer Speaker",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/25/8272451/3.jpg?6104",
            "description": "Computer Bluetooth Speaker High BoomBox Outdoor Bass HIFI TF FM Radio Audio USB Smart Subwoofer Speaker",
            "price": 2750,
            "product code": "s005",
            "category":  "Tv and Audio",
        },
         {
            "name": "Vitron 4388-FS Android TV",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/03/039084/3.jpg?5217",
            "description": "Display: 43″, FRAMELESS, SMART Android FULL HD TV 1080p,USB x2, HDMI x3,Inbuilt Wi-Fi  ",
            "price": 10599,
            "product code": "s006",
            "category":  "Tv and Audio",
        },
         {
            "name": "Bluetooth Speaker",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/12/2833621/1.jpg?8146",
            "description": "Portable Loud Bluetooth/ USB ,  FM, USB, SD",
            "price": 785,
            "product code": "s007",
            "category":  "Tv and Audio",
        },
         {
            "name": "TCL 50C655 Smart TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/27/8072362/2.jpg?9075",
            "description": "50 Inch UHD 4K QLED Gaming In Dolby Vision Smart TV (2024) Model",
            "price": 9799,
            "product code": "s008",
            "category":  "Tv and Audio",
        },
         {
            "name": "Hifinit Projector ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/75/9715981/3.jpg?1061",
            "description": "1080P 6000 Lumens Full HD USB LED WiFi Projector With High Resolution",
            "price": 9699,
            "product code": "s009",
            "category":  "Tv and Audio",
        },
         {
            "name": "Gld Smart TV",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/42/8717091/2.jpg?2265",
            "description": "65 inch Frameless Ultra HD LED Television - Black.",
            "price":15999 ,
            "product code": "s010",
            "category":  "Tv and Audio",
        },
         {
            "name": "Vention HDMI",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/05/1438862/1.jpg?0123",
            "description": "Female to Female Coupler Adapter Black",
            "price": 75,
            "product code": "s011",
            "category":  "Tv and Audio",
        },
         {
            "name": "Vitron HTC3200S Android TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/37/0349162/4.jpg?9092",
            "description": "32 inches Smart Frameless Android LED TV, With Bluetooth",
            "price":8999,
            "product code": "s012",
            "category":  "Tv and Audio ",
        },
         {
            "name": "Skyworth 32E57 Google TV",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/26/1892961/2.jpg?6485",
            "description": "32-inches Full HD Frameless Smart Google, Android 9.0 Pie, Google Assistant ",
            "price": 12599,
            "product code": "s013",
            "category":  "Tv and Audio",
        },
         {
            "name": "Hisense Smart TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/06/6199191/1.jpg?9767",
            "description": " 32″ 32A4KKEN,Smart  Frameless LED Television",
            "price": 9499,
            "product code": "s014",
            "category":  "Tv and Audio",
        },
         {
            "name": "CTC DIGITAL TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/10/966483/1.jpg?1052",
            "description": "Screen size: 22 inch,Type: LED Backlight, USB HDMI  VGA(1)、AV input(1)",
            "price": 7900,
            "product code": "s015",
            "category":  "Tv and Audio",
        },
         {
            "name": "Skyworth Android TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/84/4380801/1.jpg?5912",
            "description": " 55G3B, 55-inches 4K QLED 2022 Frameless Smart Android TV",
            "price": 19999,
            "product code": "s016",
            "category":  "Tv and Audio",
        },
         {
            "name": "Samsung Smart TV ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/70/216992/1.jpg?2337",
            "description": "UA32T5300AUXKE 32-inches LED TV, Smart TV, HD 720p",
            "price": 10499,
            "product code": "s017",
            "category":  "Tv and Audio",
        },
         {
            "name": "TCL Android TV",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/68/7134312/3.jpg?3522",
            "description": "43 Inch, 4K Ultra HD Smart LED Google/Android TV,Bluetooth-Enabled",
            "price": 14599,
            "product code": "s018",
            "category":  "Tv and Audio",
        },
         {
            "name": "TV Wall Mount Skilltech 15 inch To 43 inch Tilting Wall Mount Bracket",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/31/089534/1.jpg?6737",
            "description": "",
            "price": 280,
            "product code": "s019",
            "category":  "Tv and Audio",
        },
         {
            "name": "LED Music Bulb",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/07/901592/5.jpg?8096",
            "description": "LED Music Bulb With Bluetooth, Music Player",
            "price": 100,
            "product code": "s021",
            "category":  "Tv and Audio",
        },
         {
            "name": " Tripod Stand",
            "image": r"https://ke.jumia.is/unsafe/fit-in/500x500/filters:fill(white)/product/25/8259781/4.jpg?3325",
            "description": "LASA 132cm Tripod Travel Stand For Phone / Camera",
            "price": 110,
            "product code": "s022",
            "category":  "Tv and Audio",
        },
         {
            "name": "A2 Subwoofer Speaker ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/25/8272451/3.jpg?6104",
            "description": "4D Crystal Stereo, Comfort LED Light,Two Power Supply Ways.",
            "price": 399,
            "product code": "s023",
            "category":  "Tv and Audio",
        },
         {
            "name": "Lapel Microphone",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/03/2935121/2.jpg?1175",
            "description": "For Cameras Phone,150CM Cable,suitable for various devices,Excellent audio recording ",
            "price": 299,
            "product code": "s024",
            "category":  "Tv and Audio",
            "ko_fi_link": "https://ko-fi.com/techbidmarket",
            "mpesa_link": "**Pochi La Biashara/Send Money:** 0704234829"
        },
         {
            "name": "Apple MacBook Pro",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/49/4513412/1.jpg?4162",
            "description": "13-inches Core I5 2.4GHz 8GB RAM, 500GB HDD (2012) Silver Refurbished",
            "price":11999,
            "product code": "c001",
            "category":  "Computing",
        },
         {
            "name": "HP Refurbished Elitebook 840 G2",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/63/1880001/2.jpg?7040",
            "description": " 5th Gen Touchscreen Core i5, 8GB RAM 500GB HDD -14-inches, Black , CPU: 2.5GHz CPU: 2.5GHz,Graphics Card: Intel HD Graphics 4000 ",
            "price": 10899,
            "product code": "c002",
            "category":  "Computing",
        },

         {
            "name": "Lenovo Refurbished ThinkPad Yoga 11e",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/24/467116/2.jpg?6596",
            "description": "X360 Intel -Touchscreen- 11.6-inches - 4GB RAM - 128GB SSD - Black, Processor: Intel® Celeron®",
            "price": 8799,
            "product code": "c003",
            "category":  "Computing",
        },
         {
            "name": "Infinix InBook X2",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/44/3582562/3.jpg?3833",
            "description": "14.0 inches, Intel Core i5, 8GB RAM, 512GB SSD - Windows 11 Home - Grey, 4-Cores, 1.0GHz~3.6GHz,Memory: 8GB DDR4 , Intel® Core™ i5-1035G1",
            "price": 15899,
            "product code": "c004",
            "category":  "Computing",
        },

         {
            "name": "Lenovo Refurbished Thinkpad X250",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/31/4719121/2.jpg?2817",
            "description": "Intel Core i5 8GB RAM DDR3  256GB SSD 12.5'' Black, Windows 10, Intel Core i5-4300U  Processor, ",
            "price": 9999,
            "product code": "c005",
            "category":  "Computing",
        },
         {
            "name": "Lenovo Refurbshed Thinkpad T470S",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/43/3631462/2.jpg?0340",
            "description": "Core I5 8GB Ram 256GB SSD, 6th Generation 14 inches,Windows 10",
            "price": 10599,
            "product code": "c006",
            "category":  "Computing",
        },

         {
            "name": "Lenovo IdeaPad 1",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/61/9142572/5.jpg?9602",
            "description": "Intel Celeron N4020,New,  8GB SO-DIMM DDR4-2400, 256GB SSD, 14-inches HD Display, Windows 11 Pro,2 cores / 2 threads, 1.1GHz base / 2.8GHz boost,USB C ",
            "price": 17599,
            "product code": "c007",
            "category":  "Computing",
        },
         {
            "name": "HP REVOLVE 810 G3",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/04/4519691/1.jpg?1447",
            "description": " I7 5TH GEN 8GB RAM 256GB SSD TOUCHSCREEN ,4 CPUs, Refurbished",
            "price": 12299,
            "product code": "c008",
            "category":  "Computing",
        },

         {
            "name": "Lenovo ThinkPad X390",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/55/7775452/4.jpg?1489",
            "description": "Core I5-8th Gen-Touchscreen-16GB Ram 256GB SSD Refurbished - 13-inches Screen- Black- Win 11 Pro ",
            "price": 11599,
            "product code": "c009",
            "category":  "Computing",
        },
         {
            "name": "HP REFURBISHED 8440",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/11/471006/2.jpg?6764",
            "description": "Intel® Core™ i5-7500U  4GB 500HDD  DDR4,14-inches,   windows 10 ",
            "price": 11499,
            "product code": "c010",
            "category":  "Computing",
        },
         {
            "name": "DELL Latitude 3190",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/04/9995202/3.jpg?5766",
            "description": "X360 4GB RAM 128GB SSD 11.6 Inches Touchscreen Intel Pentium Silver 1.1GHz Quad Core 2-in-1 Convertible Windows 10 Pro Refurbished ",
            "price": 10999,
            "product code": "c011",
            "category":  "Computing",
        },

         {
            "name": "Lenovo Refurbished X390 Yoga",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/45/8069172/3.jpg?2049",
            "description": " Intel® Core™ i5-8250U processor 8th Gen 16GB +256GB SSD 13.3-inches FHD X360",
            "price": 10899,
            "product code": "c012",
            "category":  "Computing",
        },
         {
            "name": "HP Elitebook 840 G5",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/24/4911021/2.jpg?2692",
            "description": "Intel Core i7-8300U -8th Generation,16GB DDR4,512 GB SSD, 14-inches",
            "price": 10999,
            "product code": "c013",
            "category":  "Computing",
        },

         {
            "name": "DELL REFURBISHED 5480",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/99/2871642/4.jpg?6568",
            "description": "Intel(R)Core(TM) i5 7th gen 16 GB RAM 256 SSD 14-inches Windows 10Pro",
            "price": 11499,
            "product code": "c014",
            "category":  "Computing",
        },
        {
            "name": "Lenovo Refurbished Thinkpad X131e ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/05/917585/4.jpg?2782",
            "description": " 12.5-inch Display,4 GB RAM , 128GB SSD ,  intel core i3",
            "price": 10199,
            "product code": "c015",
            "category":  "Computing",
        },
         
        {
            "name": "Portable Monitor",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/53/0967182/4.jpg?1956",
            "description": "16inch 2K Monitor USBC UltraThin Gaming",
            "price": 14599,
            "product code": "c016",
            "category":  "Computing",
        },

         {
            "name": "Hp M24f Monitor",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/96/6659112/1.jpg?7998",
            "description": "23.8 Inch FHD Monitor, Edge to Edge,VGA, HDMI 1.4 USB",
            "price": 12599,
            "product code": "c017",
            "category":  "Computing",
        },
         {
            "name": "HP P27 G5 Monitor",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/87/9105172/2.jpg?2942",
            "description": "27-inch 1920 X 1080 75Hz IPS Monitor",
            "price": 13499,
            "product code": "c018",
            "category":  "Computing",
        },

         {
            "name": "Portable Monitor",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/08/1865981/1.jpg?4015",
            "description": "14-inches IPS High-definition Perfect Screen 16:9 ",
            "price": 144,
            "product code": "c019",
            "category":  "Computing",
        },

         {
            "name": "DELL P Series",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/01/6620562/1.jpg?7817",
            "description": "24-inches Screen LED-Lit Monitor ",
            "price": 11199,
            "product code": "c020",
            "category":  "Computing",
        },
         {
            "name": "HP S9000",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/48/665466/2.jpg?6753",
            "description": "Wireless mouse",
            "price": 250,
            "product code": "c021",
            "category":  "Computing",
        },

         {
            "name": "Lenovo ThinkCentre",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/62/7122511/1.jpg?0637",
            "description": "core I5,4GB RAM,320GB, Windows 10 Refurbished Tiny Desktop/Mini PC",
            "price": 7999,
            "product code": "c022",
            "category":  "Computing",
        },

         {
            "name": "GK3V Pro ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/41/2097071/1.jpg?1845",
            "description": " Intel Celeron N5105 CPU Mini PC 16GB+512GB, Windows 10",
            "price": 11300,
            "product code": "c023",
            "category":  "Computing",
        },
         {
            "name": "BMAX B1 Pro",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/16/2244742/1.jpg?0739",
            "description": "Windows 10 Intel Celeron N4000 Mini PC B1 Pro 8GB+128GB",
            "price": 10999,
            "product code": "c024",
            "category":  "Computing",
        },
         {
            "name": "Gaming Speaker",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/21/8255771/1.jpg?7985",
            "description": "Gaming Speaker Setting Temperature 4000 MAh For PC Laptop, ",
            "price": 384,
            "product code": "c025",
            "category":  "Computing",
        },
         {
            "name": "AILYONS Iron Box",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/37/591474/5.jpg?3794",
            "description": "AILYONS HD-198A Electric Dry Iron Box",
            "price": 890,
            "product code": "a001",
            "category":  "Appliances",
        },
         {
            "name": "Sokany Coffee Machine",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/51/7100351/1.jpg?1199",
            "description": "Can brew tea, but also can be used to cook coffee, Anti-drip ",
            "price": 9599,
            "product code": "a002",
            "category":  "Appliances",
        },
         {
            "name": "Roch RFR-120S-I ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/65/7297161/3.jpg?9518",
            "description": "Single Door Refrigerator - 90 Litres",
            "price": 8599,
            "product code": "a003",
            "category":  "Appliances",
        },
         {
            "name": "Ramtons RF/335 - 85L",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/21/3614472/2.jpg?5266",
            "description": " Single Door Refrigerator ",
            "price": 10899,
            "product code": "a004",
            "category":  "Appliances",
        },
         {
            "name": "Mika MBLR301/WG - Blender",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/60/533581/2.jpg?1020",
            "description": "1.5L - 400W - White & Grey",
            "price": 8599,
            "product code": "a005",
            "category":  "Appliances",
        },
         {
            "name": "Hisense WTJA802T ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/04/117685/3.jpg?1630",
            "description": "8Kg Top Load Washing Machine, Silver",
            "price": 13899,
            "product code": "a006",
            "category":  "Appliances",
        },

         {
            "name": "Hisense WFQR1214VAJMT ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/59/7872902/2.jpg?4165",
            "description": "12KG Washing Machine",
            "price": 10900,
            "product code": "a007",
            "category":  "Appliances",
        },
         {
            "name": "Ramtons RG/544",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/42/110663/1.jpg?3773",
            "description": " Stainless Steel Table Top 2 Burner Gas Cooker ",
            "price": 3999,
            "product code": "a008",
            "category":  "Appliances",
        },
         {
            "name": "Ramtons RM/582",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/33/505623/1.jpg?3816",
            "description": "Electric Pressure Cooker- Black",
            "price": 7899,
            "product code": "a009",
            "category":  "Appliances",
        },

         {
            "name": "Ramtons RM/429",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/37/566023/1.jpg?7637",
            "description": "Hot & Normal Water Dispenser + Stand",
            "price":9899,
            "product code": "a010",
            "category":  "Appliances",
        },
         {
            "name": "Jamespot Cooker",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/46/4309981/3.jpg?7111",
            "description": "Multi-functional Touch Electric Ceramic Cooker Induction Cooker",
            "price":13499 ,
            "product code": "a011",
            "category":  "Appliances",
        },
         {
            "name": "Boma Sandwich Maker",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/07/6400061/1.jpg?6441",
            "description": "2slot Sandwich Maker",
            "price": 2999,
            "product code": "a012",
            "category":  "Appliances",
        },

         {
            "name": "VON Water Dispenser",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/66/3063251/2.jpg?2351",
            "description": "3 Tap Hot & Cold & Normal Electric Cooling With Cabinet -Black",
            "price": 14999,
            "product code": "a013",
            "category":  "Appliances",
        },
         {
            "name": "Ramtons RM/458",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/36/472432/3.jpg?0918",
            "description": "Digital Glass Microwave, 700W - 20L",
            "price":8799 ,
            "product code": "a014",
            "category":  "Appliances",
        },
         {
            "name": "AILYONS Iron Box ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/10/031916/1.jpg?0150",
            "description": "Quality Dry Iron Box With Titanium Teflon Nonstick Soleplate",
            "price": 1140,
            "product code": "a015",
            "category":  "Appliances",
        },

         {
            "name": "JP Water Kettle",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/94/930065/2.jpg?1425",
            "description": "7.5 L Stainless Steel Automatic Water Kettle",
            "price": 799,
            "product code": "a016",
            "category":  "Appliances",
        },
         {
            "name": "Oraimo Vacuum Cleaner",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/06/3644781/1.jpg?5681",
            "description": "Hand Held Cordless Vacuum Cleaner-Black",
            "price": 7999,
            "product code": "a017",
            "category":  "Appliances",
        },
         {
            "name": "Oraimo Smart Kettle ",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/06/5310681/1.jpg?6123",
            "description": "1.7L Full Metal Liner Kettle",
            "price": 799,
            "product code": "a018",
            "category":  "Appliances",
        },

         {
            "name": "AILYONS FY-1731 Blender",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/01/953072/1.jpg?6452",
            "description": "2 In 1 With Grinder Machines 1.5L",
            "price": 8999,
            "product code": "a019",
            "category":  "Appliances",
        },
         {
            "name": "ALYONS ELECTRIC KETTLE",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/78/7016751/1.jpg?8244",
            "description": "2.2 L LITRES ALYONS ELECTRIC KETTLE",
            "price":999,
            "product code": "a021",
            "category":  "Appliances",
        },

         {
            "name": "XBOX Series S",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/85/331235/1.jpg?6775",
            "description": "512GB All-Digital Console",
            "price": 17899,
            "product code": "a022",
            "category":  "Appliances",
        },
         {
            "name": "G5 Mini",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/63/2651052/1.jpg?6239",
            "description": "Game Box Console Retro Games 2.4G WiFi HD Game",
            "price": 12999,
            "product code": "a023",
            "category":  "Appliances",
        },
         {
            "name": "Nintendo Switch Lite",
            "image": r"https://ke.jumia.is/unsafe/fit-in/680x680/filters:fill(white)/product/93/3547412/1.jpg?8218",
            "description": "5.5″ touch screen, Battery Life: Approximately 3-7 hours, Compatible with Nintendo Switch games",
            "price": 11399,
            "product code": "a024",
            "category":  "Appliances",
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
            bid_button_key1 = f"bid-button-{result['product code']}-{index}"
            st.write(f"**Highest Bid** : KSh {highest_bid}")

            bid_button_key1 = f"bid-button-{result['product code']}-{index}"
            
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
                    with st.form(key=f"bid-form-{product_code}"): 
                        # Input fields for user details
                        Fname = st.text_input("First Name", key=f"fname-{result['name']}-{index}")
                        Lname = st.text_input("Last Name", key=f"lname-{result['name']}-{index}")
                        email = st.text_input("Email Address",key=f"email-{product_code}")
                        phone = st.text_input("Phone Number (+254...)", key=f"phone-{result['name']}-{index}")
                        bid_amount = st.number_input(f"Enter your bid amount for {result['name']}",min_value=result['price'], value=result['price'], step=1, key=f"bid-{result['name']}-{index}")
                        
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
        highest_bid = random.randint(100, 40000)  # Random highest bid between 1 and 100
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

    st.subheader("How It Works")
    st.write("---")
    st.write("""
    1.Sign Up
             
    2.Review our privacy policy
             
    3.Auction ends after 72 hours
             
    4.Visit our **Privacy Policy** page for more details""")
             
    
    st.write("---")
    st.title("Shipping and Logistics")
    st.write("""At **TechBid Marketplace**, we are committed to ensuring your winning bids are delivered quickly and securely, no matter where you are located. Our shipping and logistics policy is designed to offer convenience, transparency, and timely updates for all our users.

**Free Delivery for Select Bids**
             
Bids placed below Ksh 1000 qualify for free delivery within select regions. Our aim is to make winning even more rewarding by covering your delivery costs.
             
**Nationwide Delivery**
             
We offer countrywide deliveries, ensuring that your gadgets and items reach you wherever you are in Kenya. We partner with reliable courier services to make sure your products arrive safely and on time.         
 
**Fast and Secure Shipping**
             
Once you win a bid, your item will be processed for shipment within 24 hours, and you can expect delivery within 2-5 business days, depending on your location.

**Notifications and Tracking**
             
Bidders will be notified via email upon winning a bid and when the item has been dispatched for delivery. You will also receive a tracking number to monitor your shipment in real-time.

**Shipping Fees**
             
For bids exceeding Ksh 1000, shipping fees are calculated based on your location and the size/weight of the item. These charges will be clearly communicated during checkout to ensure transparency.

**International Shipping**
             
While we currently focus on domestic shipping, we are working on expanding our services to include international deliveries in the near future. Stay tuned!

**Return Policy**
             
If your item arrives damaged or is not as described, you can initiate a return request within 7 days of receiving the product. 
For any inquiries regarding shipping and logistics, feel free to contact our support team at [techbidmarketplace@gmail.com] , or visit our customer support page.

             
""")

def about_us():
    st.title("About Us")
    st.write("---")
 

    # About Page Content
    st.subheader('About TechBid')


    # Introduction
    st.write("Welcome to TechBid! We are an innovative online bidding platform dedicated to helping you find the best deals on mobile and computer gadgets. Our mission is to create a fun and engaging environment where users can bid on the latest tech products and save money in the process!")

    # Mission Statement
    st.subheader('Our Mission')
    st.write("At TechBid, we aim to revolutionize the way people shop for gadgets. We believe that everyone deserves access to high-quality products at affordable prices, and our platform makes that possible through competitive bidding")

    # Our Values
    st.subheader('Our Values')
    st.write("""
    1.**Transparency**: We believe in clear and honest communication.
    
    2.**Integrity**: We are committed to fair play in all our transactions.
                
    3.**Innovation**: We constantly strive to improve our platform for a better user experience.
    """)

    # How It Works
    st.subheader("How It Works")
    st.write("Bidding on TechBid is simple! Register for an account, browse our selection of gadgets, and place your bids. The highest bidder wins the item, and we handle the rest!")

    # Team Introduction
    st.subheader("Team Effort")
    st.write("Our dedicated team of tech enthusiasts and professionals are here to ensure a seamless bidding experience for you.")
    st.write("##")
    
    # Join Us
    st.markdown(
        '<div><strong>Join Us:</strong> Ready to find amazing deals? Sign up today and start bidding on the latest gadgets!</div>', 
        unsafe_allow_html=True
    )
    
    st.write("##")

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

1.To provide and operate the app and its features (e.g., managing auctions, bids, and payments).

2.To communicate with you about your account, auctions, and updates to our services.

3.To enhance the user experience by analyzing app usage and trends.

4.To process payments and refunds.

5.To comply with legal obligations.
""")
    st.title("3.Sharing Your Information")
    st.write("""
We do not sell or rent your personal information to third parties. However, we may share your information with:

1.**Service Providers**: We may share your information with third-party service providers who help us operate our app, process payments, and provide customer support.

2.**Legal Requirements**: We may disclose your information if required by law or in response to legal requests.
""")
    st.title("4.Data Security")
    st.write("We implement security measures to protect your personal information, including encryption and secure server technologies. However, no method of transmission over the internet is completely secure, and we cannot guarantee absolute security.")

    st.title("5.Your Rights")
    st.write("""
You have the right to:

1.Access, update, or delete your personal information by contacting us at [techbidmarketplace@gmail.com].

2.Opt out of marketing communications at any time by clicking "unsubscribe" in the emails we send.

""")
    st.title("6.Cookies")
    st.write("We use cookies to enhance your experience on our app, including remembering your login details and tracking site usage. You can manage your cookie preferences through your browser settings.")

    
    st.title("7.Changes to This Privacy Policy")
    st.write("We may update this privacy policy from time to time. Any changes will be posted on this page.")

    st.write("##")
    st.subheader("Our Terms of Service")
    st.write("---")
    st.write("By using the App, you agree to comply with and be bound by the following terms and conditions. Please read these terms carefully.")
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
    st.write("All payments must be made through the payment options provided on our website. We do not store payment information on our servers.")
    
    st.title("5.User Conduct")
    st.markdown(
        """
        1. **Hacking**: Tampering with, or otherwise attempting to bypass security features is prohibited.
        2. **Fair Usage**: All users must comply with fair usage policies.
        3. **Data Privacy**: We respect your privacy and handle your data responsibly.
        """)
    st.title("6.Intellectual Property")
    st.write("All content, logos, and other intellectual property associated with the app are the property of **TechBid**. You are not permitted to reproduce or use any materials from the app without our written consent.")
    
    st.title("7.Limitation of Liability")
    st.write("To the fullest extent permitted by law,**TechBid Marketplace** shall not be liable for any damages, losses, or expenses arising out of or in connection with your use of the app, including any technical issues, loss of bids, or unauthorized access to your account.")
   

# Categories filters by product code
def category_filter_phones_tablets(code):
    return code.startswith('p') or code.startswith('t')

def category_filter_computing(code):
    return code.startswith('c')

def category_filter_tv_audio(code):
    return code.startswith('s')

def category_filter_appliances(code):
    return code.startswith('a')



# Main function to manage the sidebar and page navigation
def main():
    
    st.write("---")
 
    with st.container():
        image_column, text_column = st.columns((1, 1))

        with image_column:
            # Replace the image with a video
            video_file = open("1012 (1).mp4", "rb")
            video_bytes = video_file.read()
            st.video(video_bytes)
            with st.expander("**How do I place a bid?**", expanded=True):
                       st.write("""
                          **From The Sidebar:**
      
                          1. Sign Up                  
                          2. Review our Privacy Policy
                          3. Start bidding
                      """) 
                       
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.05)
                progress_bar.progress(i+1)


        with text_column:
            st.markdown('<div class="bounce">Bid Now for Amazing Deals!</div>', unsafe_allow_html=True)
            st.write("Welcome to **TechBid Marketplace**, the ultimate destination for scoring the best deals on the latest mobile and computer gadgets! Whether you're hunting for a sleek smartphone or a powerful laptop, you can join the bidding action, compete for top tech, and grab your favorite devices at unbeatable prices. Start bidding now and discover how you can upgrade your tech for less!")
            if st.button("Join TechBid Now!", key="primary"):
                st.success("**Sign Up from the sidebar**")
                st.session_state.current_page = "Home" 
            st.write("---")
    
    
     # Sidebar navigation
    if "active_section" not in st.session_state:
        st.session_state.active_section = "navigation"  # Default value

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"

    update_user_metrics()
    st.sidebar.metric(label="Users", value=st.session_state.users_count, delta=st.session_state.users_delta)

    # Create two columns in the sidebar for other metrics
    col1, col2 = st.sidebar.columns(2)

    # Generate random values for the metrics
    highest_bid, total_bids = generate_random_metrics()

    col1.metric(label="Highest Bid", value=f"Ksh{highest_bid}", delta=f"+{random.randint(1, 20)}")
    col2.metric(label="Live Bids", value=f"{total_bids}", delta=f"+{random.randint(1, 50)}")
    st.sidebar.write("---")

    # Sidebar to toggle between navigation and categories
    toggle_option = st.sidebar.selectbox("Select View", ["Navigation", "Categories"])

    if toggle_option == "Navigation":
        st.session_state.active_section = "navigation"
    else:
        st.session_state.active_section = "categories"

   
    if st.session_state.active_section == "navigation":
        # Navigation buttons
        navigation_buttons = [
            ("Home", home_page),
            ("Sign Up", signup_page),
            ("Bid", bids_and_gadgets_page),
            ("Sell To Us", customer_support_page),
            ("Search", search_bar),
            ("How It Works", how_works),
            ("About Us", about_us),
            ("Log In", login_page),
            ("Customer Support", customer_support_page),
            ("Privacy Policy", privacy_policy)
        ]
        
        # Sidebar navigation for the main pages
        for name, page_func in navigation_buttons:
            if st.sidebar.button(name):
                st.session_state.current_page = name
                st.session_state.active_section = "navigation"  # Ensure only navigation displays
        
        # Display the selected page
        current_page_func = dict(navigation_buttons).get(st.session_state.current_page, home_page)
        current_page_func()

         
    elif st.session_state.active_section == "categories":
       
        categories=["Exit This Section","Phones and Tablets", "TV and Audio", "Appliances", "Computing"]
        items = st.sidebar.selectbox("**● SELECT CATEGORY**", categories)

        if items != "Exit This Section":
            st.session_state.active_section = "categories"
            if items == "Phones and Tablets":
                st.subheader("Phones and Tablets")
                bids_and_gadgets_page(category_filter_phones_tablets)

            elif items == "TV and Audio":
                st.subheader("TV and Audio")
                bids_and_gadgets_page(category_filter_tv_audio)

            elif items == "Appliances":
                st.subheader("Appliances")
                bids_and_gadgets_page(category_filter_appliances)

            elif items == "Computing":
                st.subheader("Computing")
                bids_and_gadgets_page(category_filter_computing)
        else:
            st.write("Please select a category from the sidebar to view available products.")

    
    st.sidebar.write("---")  
################################
   
######################################
  
    
# Run the app
if __name__ == "__main__":
    main()

