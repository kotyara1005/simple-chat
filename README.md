# Simple chat
It is just a simple example of chat application.
## How to run
### Using Gunicorn
`gunicorn` -c "chat_app/config/gunicorn.py" chat_app.app:app --reload`
