from flask import Flask,request,redirect,url_for,render_template,flash
from mysql.connector import connect,Error

app = Flask(__name__)
app.config["SECRET_KEY"]="hhjsdwedfwerfwee#$#%$@E##!DAEDSSDFSD@#@%@#$R%@RW"

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

# Let's define register router
@app.route('/register',methods=['POST','GET'])
def register():

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
            if db_email:
                flash("Email already exist! Please use login...!",'warning')
                cursor.close()
                conn.close()
                return redirect(url_for('register'))
            else:
                cursor.execute("INSERT INTO users(name,email,password) VALUES (%s,%s,%s)",(name,email,password))
                conn.commit()

                flash("User registration Successful...!",'success')
                return render_template('login.html')

        except Error as err:
            flash(f"Database Error:{err}",'error')
            return redirect(url_for('register'))
        
    return render_template("register.html")


if __name__=="__main__":
    app.run(debug=True)
