from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# データベースの初期化
def init_db():
    conn = sqlite3.connect('point_test.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            points INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# ポイント追加用のカラムを追加
def add_points_column():
    pass
    conn = sqlite3.connect('point_test.db')
    cursor = conn.cursor()
    cursor.execute('''
        ALTER TABLE customers ADD COLUMN points INTEGER DEFAULT 0
    ''')
    conn.commit()
    conn.close()

# 顧客登録ページの表示
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        # パスワードのハッシュ化
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # データベースに登録
        try:
            conn = sqlite3.connect('point_test.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO customers (name, password) VALUES (?, ?)', (name, hashed_password))
            conn.commit()
            conn.close()
            flash('Customer registered successfully!', 'success')
            return redirect(url_for('register'))
        except sqlite3.Error as e:
            flash(f'An error occurred: {e}', 'error')

    return render_template('register.html')

# ポイントを加算するページ
@app.route('/add_points', methods=['GET', 'POST'])
def add_points():
    if request.method == 'POST':
        name = request.form['name']
        purchase_amount = int(request.form['purchase_amount'])

        # 購入金額に基づいてポイントを計算（2000円ごとに1ポイント）
        points_to_add = purchase_amount // 2000

        # データベースから顧客を検索
        conn = sqlite3.connect('point_test.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, points FROM customers WHERE name = ?', (name,))
        customer = cursor.fetchone()

        if customer:
            customer_id, current_points = customer
            new_points = current_points + points_to_add

            # 顧客のポイントを更新
            cursor.execute('UPDATE customers SET points = ? WHERE id = ?', (new_points, customer_id))
            conn.commit()
            conn.close()

            flash(f'{name} に {points_to_add} ポイントが追加されました！ 現在のポイント: {new_points}', 'success')
        else:
            flash('顧客が見つかりませんでした。', 'error')

        return redirect(url_for('add_points'))

    return render_template('add_points.html')

# データベースに接続して顧客情報を取得する関数
def get_customer_by_name(name):
    conn = sqlite3.connect('point_test.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM customers WHERE name = ?', (name,))
    customer = cursor.fetchone()
    conn.close()
    return customer

# 顧客ログインページの表示
@app.route('/customer_login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        # 顧客情報をデータベースから取得
        customer = get_customer_by_name(name)

        if customer and check_password_hash(customer[2], password):
            # ログイン成功、セッションに顧客情報を保存
            session['customer_name'] = customer[1]
            return redirect(url_for('view_points'))  # ログイン後にポイント確認ページにリダイレクト
        else:
            return 'ログインに失敗しました。名前またはパスワードが正しくありません。'
    
    return render_template('customer_login.html')

@app.route('/view_points')
def view_points():
    if 'customer_name' in session:
        name = session['customer_name']
        customer = get_customer_by_name(name)
        if customer:
            current_points = customer[3]
            discount_points = 50  # 割引に必要なポイント
            points_needed = discount_points - current_points if current_points < discount_points else 0  # 必要なポイント計算

            # テンプレートに渡すデータを更新
            return render_template('view_points.html', customer_name=customer[1], customer_points=current_points, points_needed=points_needed)
    return redirect(url_for('customer_login'))


# ポイントを使用するページ
@app.route('/use_points', methods=['GET', 'POST'])
def use_points():
    if request.method == 'POST':
        name = request.form['name']
        points_to_use = int(request.form['points_to_use'])  # 使用したいポイント数

        # データベースから顧客を検索
        conn = sqlite3.connect('point_test.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, points FROM customers WHERE name = ?', (name,))
        customer = cursor.fetchone()

        if customer:
            customer_id, current_points = customer

            # ポイントが50以上あるか確認
            if current_points >= points_to_use:
                new_points = current_points - points_to_use

                # 顧客のポイントを更新
                cursor.execute('UPDATE customers SET points = ? WHERE id = ?', (new_points, customer_id))
                conn.commit()
                conn.close()

                flash(f'{name} さんが {points_to_use} ポイントを使用しました！ 現在のポイント: {new_points}', 'success')
            else:
                flash(f'{name} さんは十分なポイントを持っていません。現在のポイント: {current_points}', 'error')
        else:
            flash('顧客が見つかりませんでした。', 'error')

        return redirect(url_for('use_points'))

    return render_template('use_points.html')



if __name__ == '__main__':
    init_db()
    app.run(debug=False)
