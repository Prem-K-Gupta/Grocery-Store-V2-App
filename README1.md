### Fisrt You will have to create the virtul environment
#### for windows/linux/mac run the command
- python -m venv .env

### then activate the environment
#### for windows run the command
- .env\scripts\activate
#### for linux/mac run the command
- . .env/bin/activate
### Now install all the required modules/library from requirements.txt
#### for windows/linux/mac run the command
- pip install -r requirements.txt

#### That's all now you can run the project
#### by running the app.py python file
- python app.py



#### To start redis server(Terminal 1)

- sudo service redis-server start

#### Terminal 2
- source local_run.sh

#### To start MailHog Application
- ~/go/bin/MailHog

#### Terminal 4
- source local_workers.sh
