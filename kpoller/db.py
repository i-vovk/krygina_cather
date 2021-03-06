# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey,\
    create_engine
from sqlalchemy.orm import relationship, backref, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import or_, and_
from sqlalchemy.pool import SingletonThreadPool, StaticPool

from web import KrBoxItem, KrBox

Base = declarative_base()


class Subscriber(Base):
    __tablename__ = 'subscribers'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    active = Column(Boolean)
    last_box_id = Column(Integer, ForeignKey('boxes.id'))
    last_box = relationship('DbBox')

    def __repr__(self):
        return u"<Subscriber(id=%s, email=%s, active=%s, "\
                "last_box_id=%s)>" % (self.id, self.email,
                                   self.active, self.last_box_id)


class DbBoxItem(Base):
    __tablename__ = 'box_items'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    price = Column(String)
    box_id = Column(Integer, ForeignKey('boxes.id'))

    def __repr__(self):
        return u"<DbBoxItem(id=%s, name=%s, description=%s, "\
                "price=%s, box_id=%s)>" % (self.id, self.name, self.description,
                                           self.price, self.box_id)

    @classmethod
    def from_kr_box_item(cls, kr_box_item):
        return cls(name=kr_box_item.name,
                   description=kr_box_item.description,
                   price=kr_box_item.price)


class DbBox(Base):
    __tablename__ = 'boxes'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    month = Column(String)
    description = Column(String)
    price = Column(String)
    items = relationship('DbBoxItem', order_by=DbBoxItem.id,
                         backref=backref("box_items",
                                         cascade="delete, all"))
    # subscribers = relationship('Subscriber', order_by=Subscriber.id,
    #                            back_populates="last_box")

    def __repr__(self):
        return u"<DbBox(id=%s, name=%s, month=%s, description=%s, "\
                "price=%s, %d items)>" % (self.id,
                                self.name,
                                self.month,
                                self.description,
                                self.price,
                                len(self.items))

    @classmethod
    def from_kr_box(cls, kr_box):
        db_box_items = [DbBoxItem.from_kr_box_item(b_item)
                        for b_item in kr_box.box_items]
        return cls(name=kr_box.name,
                   month=kr_box.month,
                   description=kr_box.description,
                   price=kr_box.price,
                   items=db_box_items)


class DbEngine(object):
    """docstring for DbEngine"""
    def __init__(self, url):
        super(DbEngine, self).__init__()
        self.url = url
        self.engine = create_engine(url, echo=False)
        Base.metadata.create_all(self.engine)
        self.session_factory = scoped_session(sessionmaker(bind=self.engine,
                                                           autoflush=True,
                                                           autocommit=False))

    def get_session(self):
        return self.session_factory()


class DbSession(object):
    """docstring for DbSession"""
    def __init__(self, db_engine):
        super(DbSession, self).__init__()
        self.session = db_engine.get_session()

    def add(self, db_obj):
        self.session.add(db_obj)
        self.session.commit()

    def get_active_subs(self):
        return self.session.query(Subscriber).filter_by(active=True).all()

    def get_subscriber_bymail(self, mail):
        return self.session.query(Subscriber).filter_by(email=mail).one()

    def get_not_notified_subs(self, db_box):
        return self.session.query(Subscriber).filter(
            Subscriber.last_box != db_box).all()

    def update_sub_notification(self, db_sub, db_box):
        db_sub.last_box = db_box
        self.session.commit()

    def is_new_box(self, db_box):
        return not bool(
            self.session.query(DbBox).filter(
                and_(DbBox.name == db_box.name,
                     DbBox.month == db_box.month)
            ).all()
        )

    def get_box(self, kr_box):
        return self.session.query(DbBox).filter_by(
            name=kr_box.name,
            month=kr_box.month).one()

    def get_box_byid(self, box_id):
        return self.session.query(DbBox).get(box_id)

    def get_all_boxes(self):
        return self.session.query(DbBox).all()



# db = DbSession('sqlite:////etc/kpoller/kp.db')

# subscriber = Subscriber(email="litvinenko_v@inbox.ru", active=True)
# db.add(subscriber)
# subscriber = Subscriber(email="adikue@gmail.com", active=True)
# db.add(subscriber)

# b_item = DbBoxItem(name="first item", description="first item description",
#                  price="1000")

# box = DbBox(name="first box", month="january",
#           description="first box description", price="1100", items=[b_item])
# db.add(box)
# print box

# sbs = db.session.query(Subscriber).filter_by(email="adikue@gmail.com").one()
# sbs = db.get_active_subs()
# print sbs[0].last_box

# b = db.session.query(DbBox).filter_by(month="january").one()
# print b

# for sub in db.get_not_notified_subs(box):
#     print sub
#     db.update_sub_notification(sub, box)

# print db.get_not_notified_subs(box)

# print db.is_new_box(box)

