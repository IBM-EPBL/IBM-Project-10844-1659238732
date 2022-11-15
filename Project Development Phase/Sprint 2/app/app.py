from flask import Flask, render_template, request, flash, redirect, url_for, session
from wtforms import Form, StringField, PasswordField, IntegerField, validators
from wtforms.validators import DataRequired
from passlib.hash import sha256_crypt
from functools import wraps
import timeago
import datetime
from wtforms.fields.html5 import EmailField
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_mail import Mail, Message
import plotly.graph_objects as go
import db
from mail import send_mail

app = Flask(__name__, static_url_path='/static')
app.config.from_pyfile('config.py')


@app.route('/')
def index():
    return render_template('index.html')


class SignUpForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=100)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=100)])
    email = EmailField('Email address', [validators.DataRequired(), validators.Email()])
    username = StringField('Username', [validators.Length(min=4, max=100)])
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')
    monthly_limit = IntegerField('Monthly Limit', validators=[DataRequired()])


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'logged_in' in session and session['logged_in'] == True:
        flash('You are already logged in', 'info')
        return redirect(url_for('addTransactions'))
    form = SignUpForm(request.form)
    if request.method == 'POST' and form.validate():
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.hash(str(form.password.data))
        monthly_limit = int(form.monthly_limit.data) if form.monthly_limit.data else 2000
        result = db.select('SELECT * FROM "users" WHERE "email"=? or "username" = ', [email, username])
        if (result) and (len(result) > 0):
            flash('The entered email/username address has already been taken. Please try using or creating another one.', 'info')
            return redirect(url_for('signup'))
        else:
            db.insert('INSERT INTO "users"("first_name", "last_name", "email", "username", "password", "monthly_limit") VALUES(?, ?, ?, ?, ?, ?)',
                (first_name, last_name, email, username, password, monthly_limit)
            )
            flash('You are now registered and can log in', 'success')
            return redirect(url_for('login'))
    return render_template('signUp.html', form=form)


class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=100)])
    password = PasswordField('Password', [
        validators.DataRequired(),
    ])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session and session['logged_in'] == True:
        flash('You are already logged in', 'info')
        return redirect(url_for('addTransactions'))
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password_input = form.password.data
        result = db.select('SELECT * FROM "users" WHERE "username" = ?', [username])
        if (result) and (len(result) > 0):
            data = result[0]
            userID = data['id']
            password = data['password']
            role = data['role']
            email = data['email']
            monthly_limit = data['monthly_limit'] if data['monthly_limit'] else 2000
            if sha256_crypt.verify(password_input, password):
                session['logged_in'] = True
                session['username'] = username
                session['email'] = email
                session['role'] = role
                session['userID'] = userID
                session['monthly_limit'] = monthly_limit
                flash('You are now logged in', 'success')
                return redirect(url_for('transactionHistory'))
            else:
                error = 'Invalid Password'
                return render_template('login.html', form=form, error=error)
        else:
            error = 'Username not found'
            return render_template('login.html', form=form, error=error)
    return render_template('login.html', form=form)


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Please login', 'info')
            return redirect(url_for('login'))
    return wrap


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Add Transactions
@app.route('/addTransactions', methods=['GET', 'POST'])
@is_logged_in
def addTransactions():
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = MONTH(CURRENT DATE) AND YEAR("date") = YEAR(CURRENT DATE) AND "user_id" = ?', [session['userID']])
    data = result[0]
    totalExpenses = int(data['AMOUNT_SUM']) if data['AMOUNT_SUM'] else 0
    if request.method == 'POST':
        amount = request.form['amount']
        description = request.form['description']
        category = request.form['category']
        db.insert('INSERT INTO "transactions"("user_id", "amount", "description","category") VALUES(?, ?, ?, ?)', (session['userID'], amount, description, category))
        monthly_limit = int(session['monthly_limit']) if session['monthly_limit'] else 2000
        if totalExpenses > monthly_limit:
            user_email = session['email']
            msg_title = "Monthly Expense limit excedded"
            msg_content = f"Hi,<br>Your expense for this month has excedded {monthly_limit}"
            send_mail(user_email, msg_title, msg_content)
        flash('Transaction Successfully Recorded', 'success')
        return redirect(url_for('addTransactions'))
    else:
        # get the month's transactions made by a particular user
        result = db.select('SELECT * FROM "transactions" WHERE MONTH("date") = MONTH(CURRENT DATE) AND YEAR("date") = YEAR(CURRENT DATE) AND "user_id" = ? ORDER BY "date" DESC', [session['userID']])
        if (result) and (len(result) > 0):
            transactions = result
            for transaction in transactions:
                if datetime.datetime.now() - transaction['date'] < datetime.timedelta(days=0.5):
                    transaction['date'] = timeago.format(transaction['date'], datetime.datetime.now())
                else:
                    transaction['date'] = transaction['date'].strftime('%d %B, %Y')

            return render_template('addTransactions.html', totalExpenses=totalExpenses, transactions=transactions)
        else:

            return render_template('addTransactions.html', result=result)


@app.route('/transactionHistory', methods=['GET', 'POST'])
@is_logged_in
def transactionHistory():
    if request.method == 'POST':
        month = request.form['month']
        year = request.form['year']
        result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE "user_id" = ?', ([session['userID']]))
        data = result[0]
        totalExpenses = data['AMOUNT_SUM']
        if month == "00":
            result = db.select(f'SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE YEAR("date") = YEAR("{year}-00-00") AND "user_id" = {session["userID"]}')
            data = result[0]
            totalExpenses = data['AMOUNT_SUM']
            result = db.select(f'SELECT * FROM "transactions" WHERE YEAR("date") = YEAR("{year}-00-00") AND "user_id" = {session["userID"]} ORDER BY "date" DESC')
        else:
            result = db.select(f'SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = MONTH("0000-{month}-00") AND YEAR("date") = YEAR("{year}-00-00") AND "user_id" = {session["userID"]}')
            data = result[0]
            totalExpenses = data['AMOUNT_SUM']
            result = db.select(f'SELECT * FROM "transactions" WHERE MONTH("date") = MONTH("0000-{month}-00") AND YEAR("date") = YEAR("{year}-00-00") AND "user_id" = {session["userID"]} ORDER BY "date" DESC')

        if (result) and (len(result) > 0):
            transactions = result
            for transaction in transactions:
                transaction['date'] = transaction['date'].strftime('%d %B, %Y')
            return render_template('transactionHistory.html', totalExpenses=totalExpenses, transactions=transactions)
        else:
            result = db.select(f"SELECT MONTHNAME('0000-{month}-00')")
            data = result[0]
            if month != "00":
                monthName = data[f'MONTHNAME(\'0000-{month}-00\')']
                msg = f"No Transactions Found For {monthName}, {year}"
            else:
                msg = f"No Transactions Found For {year}"
            return render_template('transactionHistory.html', result=result, msg=msg)
        

    else:
        result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE "user_id" = ?', [session['userID']])
        data = result[0]
        totalExpenses = data['AMOUNT_SUM']
        # Get Latest Transactions made by a particular user
        result = db.select('SELECT * FROM "transactions" WHERE "user_id" = ? ORDER BY "date" DESC', [session['userID']])
        if (result) and (len(result) > 0):
            transactions = result
            for transaction in transactions:
                transaction['date'] = transaction['date'].strftime('%d %B, %Y')
            return render_template('transactionHistory.html', totalExpenses=totalExpenses, transactions=transactions)
        else:
            flash('No Transactions Found', 'success')
            return redirect(url_for('addTransactions'))
        


class TransactionForm(Form):
    amount = IntegerField('Amount', validators=[DataRequired()])
    description = StringField('Description', [validators.Length(min=1)])

# Edit transaction
@app.route('/editTransaction/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def editTransaction(id):
    result = db.select('SELECT * FROM "transactions" WHERE "id" = ?', [id])
    transaction = result[0]
    form = TransactionForm(request.form)
    form.amount.data = transaction['amount']
    form.description.data = transaction['description']
    if request.method == 'POST' and form.validate():
        amount = request.form['amount']
        description = request.form['description']
        db.update('UPDATE "transactions" SET "amount"=?, "description"=? WHERE "id" = ?', (amount, description, id))
        flash('Transaction Updated', 'success')
        return redirect(url_for('transactionHistory'))
    return render_template('editTransaction.html', form=form)

# Delete transaction
@app.route('/deleteTransaction/<string:id>', methods=['POST'])
@is_logged_in
def deleteTransaction(id):
    db.delete('DELETE FROM "transactions" WHERE "id" = ?', [id])
    flash('Transaction Deleted', 'success')
    return redirect(url_for('transactionHistory'))


@app.route('/editCurrentMonthTransaction/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def editCurrentMonthTransaction(id):
    transaction = db.select('SELECT * FROM "transactions" WHERE "id" = ?', [id])
    form = TransactionForm(request.form)
    form.amount.data = transaction['amount']
    form.description.data = transaction['description']
    if request.method == 'POST' and form.validate():
        amount = request.form['amount']
        description = request.form['description']
        db.update('UPDATE "transactions" SET "amount"=?, "description"=? WHERE "id" = ?',
                  (amount, description, id))

        flash('Transaction Updated', 'success')
        return redirect(url_for('addTransactions'))
    return render_template('editTransaction.html', form=form)

# Delete transaction
@app.route('/deleteCurrentMonthTransaction/<string:id>', methods=['POST'])
@is_logged_in
def deleteCurrentMonthTransaction(id):
    db.delete('DELETE FROM "transactions" WHERE "id" = ?', [id])
    flash('Transaction Deleted', 'success')
    return redirect(url_for('addTransactions'))


class RequestResetForm(Form):
    email = EmailField('Email address', [
                       validators.DataRequired(), validators.Email()])


@app.route("/reset_request", methods=['GET', 'POST'])
def reset_request():
    if 'logged_in' in session and session['logged_in'] == True:
        flash('You are already logged in', 'info')
        return redirect(url_for('index'))
    form = RequestResetForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        result = db.select(
            "SELECT id,username, email FROM users WHERE email = ?", [email])
        if not result or len(result) == 0:
            flash(
                'There is no account with that email. You must register first.', 'warning')
            return redirect(url_for('signup'))
        else:
            data = result[0]
            user_id = data['id']
            user_email = data['email']
            s = Serializer(app.config['SECRET_KEY'], 1800)
            token = s.dumps({'user_id': user_id}).decode('utf-8')
            msg_title = 'Password Reset Request'
            msg_body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make password reset request then simply ignore this email and no changes will be made.
Note:This link is valid only for 30 mins from the time you requested a password change request.
'''
            send_mail(user_email, msg_title, msg_body)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('login'))
    return render_template('reset_request.html', form=form)


class ResetPasswordForm(Form):
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if 'logged_in' in session and session['logged_in'] == True:
        flash('You are already logged in', 'info')
        return redirect(url_for('index'))
    s = Serializer(app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token)['user_id']
    except:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    data = db.select('SELECT "id" FROM "users" WHERE "id" = ?', [user_id])
    data = data[0]
    user_id = data['id']
    form = ResetPasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        password = sha256_crypt.hash(str(form.password.data))
        db.update('UPDATE "users" SET "password" = ? WHERE "id" = ?', (password, user_id))
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

# Category Wise Pie Chart For Current Year As Percentage #
@app.route('/category')
def createBarCharts():
    result = db.select(f'SELECT SUM("amount") as AMOUNT_SUM, "category" FROM "transactions" WHERE YEAR("date") = YEAR(CURRENT DATE) AND "user_id" = {session["userID"]} GROUP BY "category" ORDER BY "category"')
    if (result) and (len(result) > 0):
        transactions = result
        values = []
        labels = []
        for transaction in transactions:
            values.append(transaction['AMOUNT_SUM'])
            labels.append(transaction['category'])
        fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
        fig.update_traces(textinfo='label+value', hoverinfo='percent')
        fig.update_layout(title_text='Category Wise Pie Chart For Current Year')
        fig.show()
    return redirect(url_for('addTransactions'))

# Comparison Between Current and Previous Year #
@app.route('/yearly_bar')
def yearlyBar():
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE)  AND "user_id" = ?', ('01', session['userID']))
    if (result) and (len(result) > 0):
        a1 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE - 1 YEAR)  AND "user_id" = ?', ('01', session['userID']))
    if (result) and (len(result) > 0):
        a2 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE)  AND "user_id" = ?', ('02', session['userID']))
    if (result) and (len(result) > 0):
        b1 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE - 1 YEAR)  AND "user_id" = ?', ('02', session['userID']))
    if (result) and (len(result) > 0):
        b2 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE)  AND "user_id" = ?', ('03', session['userID']))
    if (result) and (len(result) > 0):
        c1 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE - 1 YEAR)  AND "user_id" = ?', ('03', session['userID']))
    if (result) and (len(result) > 0):
        c2 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE)  AND "user_id" = ?', ('04', session['userID']))
    if (result) and (len(result) > 0):
        d1 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE - 1 YEAR)  AND "user_id" = ?', ('04', session['userID']))
    if (result) and (len(result) > 0):
        d2 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE)  AND "user_id" = ?', ('05', session['userID']))
    if (result) and (len(result) > 0):
        e1 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE - 1 YEAR)  AND "user_id" = ?', ('05', session['userID']))
    if (result) and (len(result) > 0):
        e2 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE)  AND "user_id" = ?', ('06', session['userID']))
    if (result) and (len(result) > 0):
        f1 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE - 1 YEAR)  AND "user_id" = ?', ('06', session['userID']))
    if (result) and (len(result) > 0):
        f2 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE)  AND "user_id" = ?', ('07', session['userID']))
    if (result) and (len(result) > 0):
        g1 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE - 1 YEAR)  AND "user_id" = ?', ('07', session['userID']))
    if (result) and (len(result) > 0):
        g2 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE)  AND "user_id" = ?', ('08', session['userID']))
    if (result) and (len(result) > 0):
        h1 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE - 1 YEAR)  AND "user_id" = ?', ('08', session['userID']))
    if (result) and (len(result) > 0):
        h2 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE)  AND "user_id" = ?', ('09', session['userID']))
    if (result) and (len(result) > 0):
        i1 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE - 1 YEAR)  AND "user_id" = ?', ('09', session['userID']))
    if (result) and (len(result) > 0):
        i2 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE)  AND "user_id" = ?', ('10', session['userID']))
    if (result) and (len(result) > 0):
        j1 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE - 1 YEAR)  AND "user_id" = ?', ('10', session['userID']))
    if (result) and (len(result) > 0):
        j2 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE)  AND "user_id" = ?', ('11', session['userID']))
    if (result) and (len(result) > 0):
        k1 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE - 1 YEAR)  AND "user_id" = ?', ('11', session['userID']))
    if (result) and (len(result) > 0):
        k2 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE)  AND "user_id" = ?', ('12', session['userID']))
    if (result) and (len(result) > 0):
        l1 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE MONTH("date") = ?  AND YEAR("date") = YEAR(CURRENT DATE - 1 YEAR)  AND "user_id" = ?', ('12', session['userID']))
    if (result) and (len(result) > 0):
        l2 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE  YEAR("date") = YEAR(CURRENT DATE)  AND "user_id" = ?', ([session['userID']]))
    if (result) and (len(result) > 0):
        m1 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0
    result = db.select('SELECT SUM("amount") as AMOUNT_SUM FROM "transactions" WHERE YEAR("date") = YEAR(CURRENT DATE - 1 YEAR)  AND "user_id" = ?', ([session['userID']]))
    if (result) and (len(result) > 0):
        m2 = result[0]['AMOUNT_SUM'] if result[0]['AMOUNT_SUM'] else 0

    year = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June',
            'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec', 'Total']
    fig = go.Figure(data=[
        go.Bar(name='Last Year', x=year, y=[
               a2, b2, c2, d2, e2, f2, g2, h2, i2, j2, k2, l2, m2]),
        go.Bar(name='This Year', x=year, y=[
               a1, b1, c1, d1, e1, f1, g1, h1, i1, j1, k1, l1, m1])
    ])
    fig.update_layout(
        barmode='group', title_text='Comparison Between This Year and Last Year')
    fig.show()
    return redirect(url_for('addTransactions'))

# Current Year Month Wise #
@app.route('/monthly_bar')
def monthlyBar():
    result = db.select(f'SELECT SUM("amount") as "AMOUNT", MONTH("date") as "MONTH" FROM "transactions" WHERE YEAR("date") = YEAR(CURRENT DATE) AND "user_id" = ? GROUP BY MONTH("date") ORDER BY MONTH("date")', ([session["userID"]]))
    if (result) and (len(result) > 0):
        transactions = result
        year = []
        value = []
        for transaction in transactions:
            year.append(transaction['MONTH'])
            value.append(transaction['AMOUNT'])
        fig = go.Figure([go.Bar(x=year, y=value)])
        fig.update_layout(title_text='Monthly Bar Chart For Current Year')
        fig.show()

    return redirect(url_for('addTransactions'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config.get("FLASK_HTTP_PORT"))