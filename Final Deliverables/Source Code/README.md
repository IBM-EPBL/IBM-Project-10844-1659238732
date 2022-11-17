# Personal Expense Tracker

# Setting up environment
1. Create ```.env``` file
  ```shell
  touch .env
  ```
2. Copy all data from ```.env.example``` file and paste it in ```.env```
3. Create ```IBM DB2``` credential and Add it to ```Database Credential ibm DB2``` section in .env.
4. Create ```Random Key``` for ```Secret Key``` section.
5. Create ```SendGrid API key``` and Add it to ```SEND GRID``` section also Add ```Default Sender Email```.

# Starting the project
1. Go to app directory
  ```shell
  cd app
  ```
2. Initiate virtual environment
  ```shell
  python3 -m venv venv
  ```
3. Activate Virtual environment
  ```shell
  source venv/bin/activate
  ```
4. Install Required Python packages
  ```shell
  pip install -r requirements.txt
  ``` 
4. Start the appliction
  ```shell
  python3 app.py
  ``` 

# Starting the project using docker
1. Build the image using given Dockerfile
2. Run the application using docker image and export the PORT provided at FLASK_HTTP_PORT(located at .env)