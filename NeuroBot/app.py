import os
import random
import sqlite3
import threading
import time
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, g
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("OPENAI_ASSISTANT_ID")

# bloc 2 ---------  global definitions ------------------------------

app = Flask(__name__)

chatID = int(0)
visitID = int(0)
client = None
my_assistant = None
assisant_thread = None



# bloc 3 -------------database connection-------------------------------------

# Function to get the database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect("check.db")
    return db


# Function to close the database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Create tables if they don't exist
def init_db():
    with app.app_context():
        db = get_db()
        try:
            db.execute("""
             CREATE TABLE IF NOT EXISTS message (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                visit_id INTEGER,
                timestamp INTEGER,
                message TEXT
             );
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS visit (
                    visit_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    enter_timestamp INTEGER,  
                    timezone VARCHAR(30),
                    landing_page VARCHAR(100),
                    IP_address VARCHAR(100),
                    browser VARCHAR(100),
                    os VARCHAR(100)
                 );
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS chat (
                    chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT,
                    requiredAction TEXT,
                    createdbyvisitID INTEGER,
                    firstMessageID INTEGER,
                    lastMessageID INTEGER,
                    NoMessages INTEGER
                );
            """)
            db.commit()
            cursor = db.cursor()
            # Set the initial auto-increment value for visitID to 999
            cursor.execute(
                ("SELECT visit_id FROM visit WHERE visit_id >= 999 LIMIT 1"))
            result = cursor.fetchone()

            if not result:
                db.execute(
                    "INSERT INTO visit (visit_id, enter_timestamp, timezone, landing_page, IP_address, browser, os) "
                    "VALUES (999, 0,'tz','l','http','b','o')"
                )
                db.execute("DELETE FROM visit WHERE visit_id = 999")
                print(" visit_id 1000.")
                db.commit()
        except Exception as e:
            print("Error occurred during database initialization:", e)


def store_message_element_in_db(senderID, message):
    db = get_db()
    cursor = db.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(timestamp)
    # Convert current time to Unix timestamp
    print(message)
    print(chatID)
    print(senderID)

    if chatID == 0:
        # If chat_id is 0 or None, create a new chat
        store_chat_in_db()  # Assuming this function returns the new chat_id

    cursor.execute("""
        INSERT INTO message(chat_id, visit_id, timestamp, message)
        VALUES(?, ?, ?, ?)
        """, (chatID, senderID, timestamp, message))
    db.commit()
    print("")
    return


def store_visit_in_db(enter_timestamp, timezone, landing_page, ip_address, browser, os):
    # Store visitor information in the database
    global visitID

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO visit(enter_timestamp, timezone, landing_page, IP_address, browser, os)
        VALUES(?, ?, ?, ?, ?, ?)
    """, (enter_timestamp, timezone, landing_page, ip_address, browser, os))

    db.commit()
    visitID = cursor.lastrowid

    return


@app.route('/new_visit', methods=['POST'])
def new_visit():
    init_db()
    print("visitID from new_visit", visitID)

    if visitID == 0:
        # Extract parameters from the request
        enter_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        timezone = request.json.get('timezone')
        landing_page = request.json.get('landing_page')
        ip_address = request.json.get('ip_address')
        browser = request.json.get('browser')
        os = request.json.get('os')

        # Call store_visit_in_db to create a new visit
        store_visit_in_db(enter_timestamp, timezone, landing_page, ip_address, browser, os)

    return "New visit created successfully"


def store_chat_in_db():
    global chatID
    global visitID
    global assistant_thread
    try:
        db = get_db()
        cursor = db.cursor()
        status = "active"
        required_action = "none"
        first_message_id = 1  # Example message ID, replace with actual value
        last_message_id = 1  # Example message ID, replace with actual value
        num_messages = 1

        cursor.execute("""
            INSERT INTO chat(status, requiredAction, createdbyvisitID, firstMessageID, lastMessageID, NoMessages)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (status, required_action, visitID, first_message_id, last_message_id, num_messages))

        db.commit()
        chatID = cursor.lastrowid
        cursor.close()

    except Exception as e:
        print("Error occurred:", e)
    assistant_thread = client.beta.threads.create()
    return



import smtplib
from email.message import EmailMessage


def send_email(subject, message, to_email):
    from_email = "neurobot@ymetry.com"
    msg = EmailMessage()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(message)

    try:
        # Connect to SMTP server
        server = smtplib.SMTP('mail.ymetry.com', 587)  # Use port 587 for TLS
        # server.starttls()  # Not needed if using port 587

        # Login to your email account
        server.login(from_email, 'BotBotBot:2024')  # Make sure this password is correct

        # Send email
        server.send_message(msg)
        print("Email sent successfully.")

        # Close connection
        server.quit()
    except smtplib.SMTPException as e:
        print("An error occurred while sending the email:", e)


def chat_resume(chat_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM message WHERE chat_id=?", (chat_id,))
    messages = cursor.fetchall()

    conversation = ""
    for message in messages:
        conversation += f"{message[3]} - "
        if message[1] == visitID and message[2] != visitID:
            conversation += "visitID: "
        elif message[2] == visitID:
            conversation += f"Visitid: {visitID}:"
        else:
            conversation += "Neurobotid: 1: "
        conversation += f"{message[4]}\n"

    recipient_email = "neurobot@ymetry.com"
    subject = f"Chat Resume - Chat ID: {chat_id}"
    send_email(subject, conversation, recipient_email)


# bloc4 -------------------------formating openai response-------------------------------------------------------
import re


def format_openai_response(chat_response):
    # Apply bold formatting to numeric points and their following text
    formatted_response = re.sub(
        r'(^|\n)(\d+\.\s*)(.*?)(?=$|\n)',
        lambda match: f'{match.group(1)}<strong>{match.group(2)}</strong> {match.group(3)}',
        chat_response
    )

    # Apply bold formatting before '-' symbol
    formatted_response = re.sub(
        r'(\w+)\s*-\s*',
        r'<strong>\1</strong> - ',
        formatted_response
    )

    # Add <br> tags after each formatted line
    formatted_response = re.sub(
        r'\n',
        r'<br>',
        formatted_response
    )

    return formatted_response


# bloc 5 ----------------------------html --------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/admin')
def admin():
    db = get_db()
    x = db.execute("SELECT * FROM message").fetchall()  # Fetching data from the 'message' table
    return render_template('admin.html', x=x)


@app.route('/viewchat')
def viewchats():
    db = get_db()
    x = db.execute("SELECT * FROM visit").fetchall()
    return render_template('viewchat.html', x=x)


@app.route('/check', methods=['POST'])
def check():
    user = request.form["email"]
    password = request.form["password"]
    if user == os.getenv("EMAIL") and password == os.getenv("PASSWORD"):
        return redirect("/admin")
    else:
        return redirect("/")


# bloc6----------------------search function---------------------------------------------------------------------------

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '')  # Get the query from the form data
    print(request.form)

    topicslist = ["neuroscience", "neuroscience related company", "biology"]
    notintopicsanswerslist = ["please ask only neuroscience related questions",
                              "I prefer to answer only neuroscience related questions"]
    topics_related_question = "please answer in only one word TRUE or FALSE whether the following question is related to the following topics : "

    # Creating composite string to ask GPT whether it is related to the topics in topicsList
    topics_string = ", ".join(topicslist)
    is_in_topics_request = topics_related_question + topics_string + " : " + query
    NeuroBotID = 1

    store_message_element_in_db(visitID, query)

    if query.startswith('###'):
        # If developer question, proceed directly with Get OpenAI response
        result = get_Neurobot_response(query)
    else:

        result = get_Neurobot_response(is_in_topics_request)
        if "TRUE" in result:
            result = get_Neurobot_response(query)
        else:
            result = random.choice(notintopicsanswerslist)

    store_message_element_in_db(NeuroBotID, result)
    # Sending email
    recipient_email = "neurobot@ymetry.com"  # Update with recipient's email

    # Generating chat resume
    chat_resume(chatID)

    return format_openai_response(result)


# bloc7 --------------------------

def get_openai_response(query):
    from openai import OpenAI
    import os
    import json
    # Replace 'YOUR_API_KEY' with your actual OpenAI API key
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY",
                                           ''))

    MODEL = "gpt-4-turbo-preview"  # Use an available model
    prompt = query

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": query},
        ],
        temperature=0,
    )
    return json.loads(response.model_dump_json())["choices"][0]["message"]['content']


# bloc8 --------------------------
# Set your OpenAI API key and assistant ID directly in the script
api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("OPENAI_ASSISTANT_ID")




#load the openai client assistant
def load_openai_client_and_assistant():
    global client, my_assistant, assistant_thread
    try:
        client = OpenAI(api_key=api_key)
        my_assistant = client.beta.assistants.retrieve(assistant_id)
        assistant_thread = client.beta.threads.create()
    except Exception as e:
        print(f"Error loading OpenAI client and assistant: {e}")

load_openai_client_and_assistant()
def create_assistant_thread():
    try:
        return client.beta.threads.create()
    except Exception as e:
        print(f"Error creating assistant thread: {e}")
        return None
# Check in loop if assistant ai parses our request
def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

# Initiate assistant ai response
def get_Neurobot_response(user_input=""):
    try:
        message = client.beta.threads.messages.create(
            thread_id=assistant_thread.id,
            role="user",
            content=user_input,
        )
#create a
        run = client.beta.threads.runs.create(
            thread_id=assistant_thread.id,
            assistant_id=assistant_id,
        )

        run = wait_on_run(run, assistant_thread)


        messages = client.beta.threads.messages.list(
            thread_id=assistant_thread.id, order="asc", after=message.id
        )

        return messages.data[0].content[0].text.value

    except Exception as e:
        return f"An error occurred: {e}"




# bloc9 ------------------------main----------------------------------------------------
if __name__ == '__main__':

    app.run(debug=True)