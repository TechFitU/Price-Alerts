# Prices Alerts 
Receive alerts for changes on the prices of online products. 
Built with Flask, Flask-RESTful, Flask-Login, Flask-WTF, Flask-Bootstrap4 and Flask-SQLAlchemy.

## Installation
To get started:

When you've created the project folder and downloaded the project from GitHub, you'll also need to create a correct runtime configuration in PyCharm.
1. Clone the project source code from the repository:
    
    `git clone https://github.com/TechFitU/Price-Alerts.git`
    
    `cd Price-Alerts` 

2. Create a virtualenv for this project and activate it:

    `$ python3 -m venv venv`
       
    `$ . venv/bin/activate`
    
    Or on Windows cmd:

    `> py -3 -m venv venv`
    
    `> venv\Scripts\activate.bat`
3. Install requirements using `pip install -r requirements.txt`

    If you need to keep requirements.txt updated then run:

    `$ pip freeze > requirements/base.txt`
    
    `$ echo "-r base.txt" > requirements/development.txt`
    
## Test
Create a sample unittest configuration in PyCharm (for example), and choose:

- `Path` as as target, with your project's `/tests` folder.

- Run the tests
## Run


    $ export FLASK_APP=pricealerts
    $ export FLASK_ENV=development
    $ flask init-db
    
    $ flask run
    or 
    $ python -m flask run

Or on Windows cmd::

    > set FLASK_APP=pricealerts
    > set FLASK_ENV=development
    > flask init-db
    > flask run

Open http://127.0.0.1:5000 in a browser.

## Deployment
    