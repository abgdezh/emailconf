from application.database import db
from application.server import app

with app.test_request_context():
     db.init_app(app)

     db.create_all()
