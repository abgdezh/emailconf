from web_app.database import db
from web_app import app

with app.test_request_context():
     db.init_app(app)

     db.create_all()
