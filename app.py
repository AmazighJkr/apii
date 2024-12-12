from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration
app.config["MYSQL_HOST"] = "sql7.freesqldatabase.com"
app.config["MYSQL_USER"] = "sql7751314"
app.config["MYSQL_PASSWORD"] = "U9isixmKa5"
app.config["MYSQL_DB"] = "sql7751314"
app.config["MYSQL_PORT"] = 3306

mysql = MySQL(app)

# API Endpoints
@app.route("/sell", methods=["POST"])
def sell_product():
    """Process a sale"""
    data = request.json  # JSON input
    vending_machine_code = data["vendingMachineCode"]
    uid = data["uid"]
    password = data["password"]
    product_code = data["productCode"]
    product_price = data["productPrice"]
    
    try:
        cursor = mysql.connection.cursor()

        # Verify vending machine
        cursor.execute("SELECT vendingMachineId FROM vendingmachines WHERE vendingMachineCode = %s", (vending_machine_code,))
        vending_machine = cursor.fetchone()
        if not vending_machine:
            return jsonify({"error": "Invalid vending machine code"}), 400
        vending_machine_id = vending_machine[0]

        # Verify user
        cursor.execute("SELECT userId, balance FROM users WHERE uid = %s AND password = %s", (uid, password))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "Invalid user credentials"}), 400
        user_id, balance = user

        # Check if balance is sufficient
        if balance < product_price:
            return jsonify({"error": "Insufficient balance"}), 400

        # Update user's balance
        new_balance = balance - product_price
        cursor.execute("UPDATE users SET balance = %s WHERE userId = %s", (new_balance, user_id))

        # Record the sale
        sale_table = f"sales{vending_machine_id}"
        cursor.execute(
            f"INSERT INTO {sale_table} (productName, SalePrice, saleTime) VALUES (%s, %s, NOW())",
            (product_code, product_price)
        )

        # Record the purchase
        purchase_table = f"purchases{user_id}"
        cursor.execute(
            f"INSERT INTO {purchase_table} (price, date) VALUES (%s, NOW())",
            (product_price,)
        )

        # Commit the changes
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Sale successful"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/update_price", methods=["POST"])
def update_price():
    """Update product prices"""
    data = request.json  # JSON input
    vending_machine_id = data["vendingMachineId"]
    product_code = data["productCode"]
    new_price = data["newPrice"]

    try:
        cursor = mysql.connection.cursor()

        # Update the product price
        query = """
            UPDATE products 
            SET productPrice = %s 
            WHERE vendingMachineId = %s AND productCode = %s
        """
        cursor.execute(query, (new_price, vending_machine_id, product_code))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Product price updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
