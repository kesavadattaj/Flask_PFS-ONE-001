from flask import Flask,request,redirect,url_for,render_template,flash,session
from mysql.connector import connect,Error
import bcrypt
from datetime import datetime,timedelta

app = Flask(__name__)
app.config["SECRET_KEY"]="hhjsdwedfwerfwee#$#%$@E##!DAEDSSDFSD@#@%@#$R%@RW"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=1)

DB_CONFIG = {
    "host":"127.0.0.1", # localhost ip = 127.0.0.1
    "port":3306,
    "user":"root",
    "password":"0818",
    "database":"snm_db"
}

# We'll define Helper methods
def get_db_connection():
    # In this we'll create and get the db connection
    return connect(**DB_CONFIG)


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
            return "All fields required!"

        if len(password)<6:
            return "Password length must be greater 6-Characters...!"

        if password!=confirm_password:
            return "Password and Confirm Password Do not match."

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

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


if __name__=="__main__":
    app.run(debug=True)
