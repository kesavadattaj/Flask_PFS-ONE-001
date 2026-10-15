from flask import Flask,request,redirect,url_for,render_template,flash,session
from mysql.connector import connect,Error
import bcrypt
from datetime import datetime,timedelta
from email.message import EmailMessage
import smtplib
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.config["SECRET_KEY"]="hhjsdwedfwerfwee#$#%$@E##!DAEDSSDFSD@#@%@#$R%@RW"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=1)

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
salt = 'F#$WE#RFCERF#%$^#%RGWERTGERF'

DB_CONFIG = {
    "host":"127.0.0.1", # localhost ip = 127.0.0.1
    "port":3306,
    "user":"root",
    "password":"0818",
    "database":"snm_db"
}

EMAIL_CONFIG = {
    'smtp_server' : 'smtp.gmail.com',
    'smtp_port' : 587,
    'email' : 'kesavadatta@codegnan.com',
    'password' : 'lmkn twaa szrr ypka'
}

# We'll define Helper methods
def get_db_connection():
    # In this we'll create and get the db connection
    return connect(**DB_CONFIG)


def send_email(to_email,subject,body,html=False):
    try:
        msg = EmailMessage()
        msg['subject'] = subject
        msg['From'] = EMAIL_CONFIG['email']
        msg['To'] = to_email

        if html:
            msg.add_alternative(body,subtype='html')
        else:
            msg.set_content(body)

        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'],EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['email'],EMAIL_CONFIG['password'])
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Email error:{e}")
        return False

def generate_reset_token(email):
    return serializer.dumps(email,salt=salt)

def verify_reset_token(token,expiration=600):
    try:
        email = serializer.loads(token,salt=salt,max_age=expiration)
        return email
    except Exception as e:
        print(f"Token verification failed :{e}")
        return None


@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    return render_template('home.html')

# Let's define register router
@app.route('/register',methods=['POST','GET'])
def register():

    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method=='POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not name or not email or not password or not confirm_password:
            flash("All fields required!")
            return redirect(url_for('register'))

        if len(password)<6:
            flash("Password length must be greater 6-Characters...!")
            return redirect(url_for('register'))

        if password!=confirm_password:
            flash("Password and Confirm Password Do not match.")
            return redirect(url_for('register'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT email from users where email=%s",(email,))
            db_email = cursor.fetchone()

            # Check if email exists
            if db_email:
                flash("Email already exist! Please use login...!",'warning')
                cursor.close()
                conn.close()
                return redirect(url_for('register'))
            else:
                # Hash password with bcrypt
                hashed_pw = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

                # Insert user
                cursor.execute("INSERT INTO users(name,email,password) VALUES (%s,%s,%s)",(name,email,hashed_pw))
                conn.commit()

                cursor.close()
                conn.close()
                flash("User registration Successful...!",'success')
                return render_template('login.html')

        except Error as err:
            flash(f"Database Error:{err}",'error')
            return redirect(url_for('register'))
        
    return render_template("register.html")

# Login router
@app.route('/login',methods=['POST','GET'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method=='POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Email and Password are required fields...!","warning")
            return redirect(url_for('login'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * from users where email=%s",(email,))
            user = cursor.fetchone()

            cursor.close()
            conn.close()

            if user:

                validate_pw = bcrypt.checkpw(password.encode('utf-8'),user['password'].encode('utf-8'))
        
                if validate_pw:
                    session.permanent = True
                    session['user_id'] = user['id']
                    session['user_name'] = user['name']
                    session['email'] = user['email']

                    flash('Login Successful...!','success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid password...! Please try again...!','warning')
                    return redirect(url_for('login'))
            else:
                flash('Invalid user...! Please register...!','warning')
                return redirect(url_for('register'))
        
        except Error as err:
            flash(f"Database Error:{err}",'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        session.pop('user_id',None)
        session.pop('user_name',None)
        session.pop('email',None)
        flash('logout successful...!','success')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('home'))


@app.route('/forgot-password',methods=['GET','POST'])
def forgot_password():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method=='POST':
        email = request.form.get('email')

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT email from users where email=%s",(email,))
            user = cursor.fetchone()

            cursor.close()
            conn.close()

            if user:
                token = generate_reset_token(email)
                reset_link = url_for('reset_password', token=token, _external=True)

                email_body = f"""
                            <h2>Password Reset Request</h2>
                <p>Click the link below to reset your password:</p>
                <a href="{reset_link}" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
                            """
                subject = "SNM - Password Reset"
                send_email(email,subject,email_body,html=True)
                flash('Password Reset is sent to mail....!','success')
                return redirect(url_for('login'))
            else:
                flash("User not registered with us...! Please register...!",'warning')
                return redirect(url_for('register'))
            
        except Error as err:
            flash(f"Database Error:{err}",'error')
            return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>',methods=['GET','POST'])
def reset_password(token):
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    check_token_email = verify_reset_token(token=token,expiration=300)
    if not check_token_email:
        flash('Reset link not Valid...! Please request again...!')
        return redirect(url_for('forgot_password'))
    
    if request.method=="POST":
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if  not password or not confirm_password:
            flash("All fields required!")
            return redirect(url_for('reset_password',token=token))
        
        if len(password)<6:
            flash("Password length must be greater 6-Characters...!")
            return redirect(url_for('reset_password',token=token))

        if password!=confirm_password:
            flash("Password and Confirm Password Do not match.")
            return redirect(url_for('reset_password',token=token))

        try :
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Hash password with bcrypt
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

            cursor.execute("UPDATE users SET password=%s WHERE email=%s",(hashed_pw.decode('utf-8'),check_token_email))

            conn.commit()

            cursor.close()
            conn.close()
            flash('Password Reset Successful...! Login Again...!','success')
            return redirect(url_for('login'))
        except Error as err:
            flash(f"Database Error:{err}",'error')
            return redirect(url_for('reset_password',token=token))
        
    return render_template('reset_password.html',token=token)

        


@app.route('/dashboard')
def dashboard():
    if not 'user_id' in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


if __name__=="__main__":
    app.run(debug=True)
