from datetime import datetime
from HandwrittenDigitRecognizer.extensions import db


class Prediction(db.Model):
    __tablename__ = 'Predictions'
    __table_args__ = {'extend_existing': True}

    ID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('Users.ID'), nullable=False)
    ImagePath = db.Column(db.String(255), nullable=False)
    Prediction = db.Column(db.Integer, nullable=False)
    Confidence = db.Column(db.Float, nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('predictions', lazy=True))

    def __repr__(self):
        return f'<Prediction UserID={self.UserID} Digit={self.PredictedDigit} Confidence={self.Confidence:.2f}>'