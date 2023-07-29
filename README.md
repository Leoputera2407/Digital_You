To run the program

You need to run both the front-end and back-end

### Back-end
* We need to first setup your environment. We need python at least Python 3.11
```
brew install pyenv pipx
pyenv install 3.11.4
pyenv global 3.11.4
# Check that Python version is now 3.11.4
python --version

pipx install poetry
# Should print some version of poetry
poetry --version
```
* Now install the deps and run-m '
```
cd backend
make virtualenv 
source .venv/bin/activate 
uvicorn digital_twin.main:app --host 0.0.0.0 --port 8080
# Will run on http://localhost:8080
```

* Set to use Slack
First, download ngrok (https://ngrok.com/download).
Get your AUTH_TOKEN in ngrok
```
./ngrok authtoken YOUR_AUTH_TOKEN
./ngrok http 8080
```
Go to slack and change the Slash Command and Redirect URI to:
[Slash Command](https://api.slack.com/apps/A05A440PDLZ/slash-commands?): `{NGROK_URL}/slack/events`
[RedirecURI](https://api.slack.com/apps/A05A440PDLZ/oauth?): `{NGROK_URL}/slack/oauth_redirect`


### Front-end 
Access it on the browser! `localhost:3000`
```
cd frontend
npm install 
npm run dev
```
