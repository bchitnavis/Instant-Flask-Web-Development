from datetime import datetime
from sqlalchemy import Column, ForeignKey
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship, synonym
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class User(Base):

    """A user login, with credentials and authentication."""
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.now)
    modified = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    name = Column('name', String(200))
    email = Column(String(100), unique=True, nullable=False)
    active = Column(Boolean, default=True)

    _password = Column('password', String(100))

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        if password:
            password = password.strip()
            self._password = generate_password_hash(password)

    password_descriptor = property(_get_password, _set_password)
    password = synonym('_password', descriptor=password_descriptor)

    def check_password(self, password):
        if self.password is None:
            return False
        password = password.strip()
        if not password:
            return False
        return check_password_hash(self.password, password)

    @classmethod
    def authenticate(cls, query, email, password):
        email = email.strip().lower()
        user = query(cls).filter(cls.email == email).first()
        if user is None:
            return None, False
        if not user.active:
            return user, False
        return user, user.check_password(password)

    def get_id(self):
        return str(self.id)

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def __repr__(self):
        return ('<{self.__class__.__name__}: {self.id}>'.format(self=self))


class Appointment(Base):

    """An appointment on the calendar."""
    __tablename__ = 'appointment'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.now)
    modified = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User, lazy='joined', join_depth=1, viewonly=True)

    title = Column(String(255))
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    allday = Column(Boolean, default=False)
    location = Column(String(255))
    description = Column(Text)

    @property
    def duration(self):
        delta = self.end - self.start
        return delta.days * 24 * 60 * 60 + delta.seconds

    def __repr__(self):
        return ('<{self.__class__.__name__}: {self.id}>'.format(self=self))


if __name__ == '__main__':  # pragma: no cover
    from datetime import timedelta
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine('sqlite://', echo=True)

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    user = User(name='Administrator',
                email='admin@mail.com',
                password='pass')
    session.add(user)
    session.commit()

    user2 = User(name='Maner',
                 email='maner@mail.com',
                 password='password',
                 active=False)
    session.add(user2)
    session.commit()

    user3 = User(name='Felipe',
                 email='felipe@mail.com',
                 password='password')
    session.add(user3)
    session.commit()

    now = datetime.now()

    session.add(Appointment(
        user_id=user.id,
        title='Important Meeting',
        start=now + timedelta(days=3),
        end=now + timedelta(days=3, seconds=3600),
        allday=False,
        location='The Office'))
    session.commit()

    session.add(Appointment(
        user_id=user.id,
        title='Past Meeting',
        start=now - timedelta(days=3),
        end=now - timedelta(days=3, seconds=3600),
        allday=False,
        location='The Office'))
    session.commit()

    session.add(Appointment(
        user_id=user.id,
        title='Follow Up',
        start=now + timedelta(days=4),
        end=now + timedelta(days=4, seconds=3600),
        allday=False,
        location='The Office'))
    session.commit()

    session.add(Appointment(
        user_id=user.id,
        title='Day Off',
        start=now + timedelta(days=5),
        end=now + timedelta(days=5),
        allday=True))
    session.commit()

    # Create. Add a new model instance to the session.
    appt = Appointment(
        user_id=user.id,
        title='My Appointment',
        start=now,
        end=now + timedelta(seconds=1800),
        allday=False)

    session.add(appt)
    session.commit()

    # Update. Update the object in place, then commit.
    appt.title = 'Your Appointment'
    session.commit()

    # Delete. Tell the session to delete the object.
    session.delete(appt)
    session.commit()

    # Get an appointment by ID.
    appt = session.query(Appointment).get(1)

    # Get all appointments.
    appts = session.query(Appointment).all()

    # Get all appointments before right now, after right now.
    appts = session.query(Appointment).filter(
        Appointment.start < datetime.now()).all()
    appts = session.query(Appointment).filter(
        Appointment.start >= datetime.now()).all()

    # Get all appointments before a certain date.
    appts = session.query(Appointment).filter(
        Appointment.start <= datetime(2013, 5, 1)).all()

    # Get the first appointment matching the filter query.
    appt = session.query(Appointment).filter(
        Appointment.start <= datetime(2013, 5, 1)).first()
