from flask import Flask, render_template, request,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import google.generativeai as genai
import textwrap
import sqlite3



genai.configure(api_key="your api key")

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Use a strong, random key
db = SQLAlchemy(app)

# Create the User model
class User(db.Model):
    __tablename__ = 'user'  # Explicitly specify the table name
    userid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(200))
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"

# Create the Chat model and reference the 'user' table for the foreign key
class Chat(db.Model):
    __tablename__ = 'chat'  # Optional, SQLAlchemy will infer the name
    chatid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)  # ForeignKey refers to 'user'
    chat = db.Column(db.String(1000), nullable=False)
    chat_time = db.Column(db.DateTime, default=datetime.utcnow)
    sender_type = db.Column(db.String(50), nullable=False)
# Route for signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        # Check if username already exists
        flag = User.query.filter_by(username=username).first()

        if flag:
            return render_template("signup.html", value="color:white;font-size:10px;")
        else:
            user = User(username=username, password=password, email=email)
            db.session.add(user)
            db.session.commit()
            return render_template("login.html")
    
    return render_template("signup.html", value="display:none;")

# Route for login
@app.route("/login", methods=["GET", "POST"])
def login():
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Check if the username exists and passwords match
        
        flag = User.query.filter_by(username=username).first()
        if flag and flag.password == password:
            session['userid'] = flag.userid 
            return render_template("Home.html")

    return render_template("login.html")
@app.route("/", methods=["GET", "POST"])
def Main():
    return render_template("index.html")

# Route to handle chat input
@app.route("/chat", methods=["GET", "POST"])
def chat():
    user_input = ""
    userid = session.get('userid')
    if request.method == "POST":
        user_input = request.form.get("query")
        busi=request.form.get("busi")
        print(busi)
        if user_input:
            if busi=="yes":
            # Start a chat session and get a response
            # Function to get a database connection
                def get_db():
                    DATABASE = 'business_insights.db'
                    conn = sqlite3.connect(DATABASE)
                    return conn

                def run_query(query):
                    try:
                        conn = get_db()
                        cursor = conn.cursor()
                        cursor.execute(query)
                        result = cursor.fetchall()
                        conn.close()

                        if len(result) == 0:
                            return "No results found."
                        else:
                            return result
                    except Exception as e:
                        return str(e)

                chat_session = model.start_chat(history=[])
                response = chat_session.send_message(
    f"{user_input}\n:You are a professional data analyst. For the given natural language query, generate only the SQLite query as a string. Do not include the word 'sql' or any SQL block formatting. Provide the query in plain text as if I'm asking you to write it directly. Use the following schema:\n"
    "customers (customer_id, first_name, last_name, email, phone, address)\n"
    "sales (sale_id, sale_date, customer_id, product_id, quantity_sold, total_amount)\n"
    "products (product_id, product_name, category, price, description)\n"
    "product_availability (product_id, stock_quantity, last_updated)"
)

                
                quey = response.text
                result = run_query(quey)
                print("Result:",result)
                if isinstance(result, str):
                    print(result)
                else:
                    for row in result:
                        print(row)
                # Save user chat in the database
                user_chat = Chat(userid=userid, chat=user_input, sender_type="user")  # Placeholder userid for now
                db.session.add(user_chat)
                db.session.commit()
                
                # Save AI response in the database
                stri=""
                for i in str(result):
                    if i in "/[]}{*(),":
                        continue
                    else:
                        stri+=i
                ai_response = stri
                ai_chat = Chat(userid=userid, chat=ai_response, sender_type="bot")  # Placeholder userid for now
                db.session.add(ai_chat)
                db.session.commit()
                
                # Retrieve chat history
                temp= Chat.query.filter_by(userid=userid).all()
                history=[]
                for i in temp:
                    history.append(textwrap.fill(i.chat, width=80))
                # print(history)
                # print(response.text)
            else:
                chat_session = model.start_chat(history=[])
                response = chat_session.send_message(
    user_input + ":  this is   a message from the customer to  this Respond as if you are a representative of C5i, if they greet you also greet this em nothig else  using a professional and friendly tone. Ensure your response reflects C5i's commitment to client engagement, expertise, and company values. Answer the question based on C5i's mission and values. here is some information about c5i:In today’s volatile business environment, C5i stands out by helping clients navigate complexity through transformative decision-making. We combine advanced AI, data science, and analytical methodologies with a human touch to deliver tailored solutions. Our approach integrates cutting-edge technology with top talent, ensuring actionable insights and swift business impact. With our AI Labs and a robust suite of products and accelerators, we address diverse industry challenges effectively. Committed to innovation and client-centricity, we also focus on empowering employees and making a positive community impact. Our mission is to drive significant business and societal change through AI and analytics."
)



                    
                # Save user chat in the database
                user_chat = Chat(userid=userid, chat=user_input, sender_type="user")  # Placeholder userid for now
                db.session.add(user_chat)
                db.session.commit()
                
                # Save AI response in the database
                ai_response = response.text
                ai_chat = Chat(userid=userid, chat=ai_response, sender_type="bot")  # Placeholder userid for now
                db.session.add(ai_chat)
                db.session.commit()
                
                # Retrieve chat history
                temp= Chat.query.filter_by(userid=userid).all()
                history=[]
                for i in temp:
                    history.append(textwrap.fill(i.chat, width=80))
            
            return render_template("Home.html", user_input=user_input, ai_response=ai_response, history=history,i=0)
    
    return render_template("Home.html")
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  
    app.run(debug=True)
