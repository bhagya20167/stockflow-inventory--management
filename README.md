StockFlow – Inventory Management System

## 🚀 Live Demo

**Live Website:** [StockFlow Inventory Management](https://stockflow-inventory-management-nu7y.onrender.com)

StockFlow is a web-based inventory management application that helps users manage products, monitor stock levels, and identify low-stock items.

## ✨ Key Features

- User registration and login
- Add, view, edit, and delete products
- Inventory quantity tracking
- Low-stock alerts
- Organization-based data separation
- MySQL database integration

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Database:** MySQL
- **Deployment:** Render
- **Database Hosting:** Aiven
- **Version Control:** Git and GitHub


StockFlow is a web-based inventory management application designed to help organizations manage products, track stock quantities, and identify products that need restocking.



Features



User Authentication: Sign up and log in securely.



Organization Management: Associate users with their organization.



Product Management: Add and view inventory products.



Product Editing: Update existing product information.



Product Deletion: Remove products from inventory.



Inventory Tracking: Store product quantities, SKU, descriptions, cost prices, and selling prices.



Low-Stock Thresholds: Set a threshold for identifying products with low inventory.



Organization Data Isolation: Restrict product operations to the logged-in user's organization.



Database Integration: Store application data in MySQL.



Technology Stack



Frontend: HTML, CSS, JavaScript



Backend: Python, Flask



Database: MySQL



Database Connector: MySQL Connector/Python



Authentication: Werkzeug password hashing



Security: Flask-WTF CSRF protection



Version Control: Git and GitHub



Project Structure



stockflow/

├── app.py

├── db.py

├── .env

├── .gitignore

├── README.md

└── templates/

&#x20;   ├── login.html

&#x20;   ├── signup.html

&#x20;   ├── dashboard.html

&#x20;   ├── products.html

&#x20;   └── edit\_product.html



Prerequisites



Install the following before running the project:



Python 3



MySQL Server



Git



Installation and Setup



1\. Clone the repository



git clone YOUR\_GITHUB\_REPOSITORY\_URL

cd stockflow



Replace YOUR\_GITHUB\_REPOSITORY\_URL with your repository's actual URL.



2\. Create and activate a virtual environment



On Windows:



python -m venv venv

venv\\Scripts\\activate



3\. Install dependencies



python -m pip install flask mysql-connector-python python-dotenv flask-wtf



4\. Configure the MySQL database



Open MySQL Workbench and create the database and tables required by the application.



The application expects a database named stockflow\_db and the following tables:



organizations



users



products



Create the tables using the SQL schema maintained for this project.



5\. Configure environment variables



Create a .env file in the project root and add your local configuration:



DB\_HOST=127.0.0.1

DB\_PORT=3306

DB\_USER=your\_mysql\_username

DB\_PASSWORD=your\_mysql\_password

DB\_NAME=stockflow\_db

FLASK\_SECRET\_KEY=your\_generated\_secret\_key



Replace the example values with your own configuration. Generate a strong secret key for your local environment.



Security: Never commit .env or publish database passwords, secret keys, or other credentials to GitHub.



6\. Run the application



python app.py



Open the application in your browser:



http://127.0.0.1:5000



How to Use



Create an account with your organization name.



Log in to StockFlow.



Open the product management page.



Add products with their SKU, quantity, prices, and stock threshold.



View, edit, or delete products.



Track inventory and identify items that need restocking.



Security Considerations



Passwords are stored as hashes rather than plain text.



Database queries use parameterized SQL.



CSRF protection is enabled for form submissions.



Product queries are scoped to the authenticated user's organization.



Application secrets are configured through environment variables.



Future Improvements



Dashboard statistics for total products and total quantity.



A dashboard section listing low-stock products.



Search, filtering, and pagination.



Improved responsive user interface.



Deployment to a cloud hosting platform.



Author



Bhagya Pasupuleti



License



This project is currently provided for educational and demonstration purposes. A formal license can be added if the project is distributed publicly.

