from datetime import datetime
from app import db

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=True)
    transcript = db.Column(db.Text, nullable=False)

    extracted_json = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Meeting {self.id}>"
