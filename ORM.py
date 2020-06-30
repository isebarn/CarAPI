from sqlalchemy import create_engine
from sqlalchemy import func

import os

if os.environ.get('Database') != None:
  connectionString = os.environ.get('Database')
else:
  connectionString = "postgresql://david:blink182@localhost:5432/cars"

engine = create_engine(connectionString, echo=True)

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import Column, Integer, String, Boolean, DateTime

class Car(Base):
  __tablename__ = 'cars'

  Id = Column(Integer, primary_key=True)
  Maker = Column(String)
  Model = Column(String)
  Type = Column(String)
  Year = Column(Integer)
  Driven = Column(Integer)
  Fuel = Column(String)
  Transmission = Column(String)
  Drive = Column(String)
  ExchangeUp = Column(Boolean)
  ExchangeDown = Column(Boolean)
  Seats = Column(Integer)
  Doors = Column(Integer)
  Valves = Column(Integer)
  Inspected = Column(Boolean)
  Color = Column(String)
  Created = Column(DateTime)
  Sold = Column(DateTime, nullable=True)
  User = Column(String)

  def TryGetInteger(self, value):
    result = 0

    if value.isnumeric():
      result = int(value)

    return result

  def __init__(self, data):
      self.Id = int(data["Id"])
      self.Maker = data["Framleiðandi"]
      self.Model = data["Undirtegund"]
      self.Type = data["Tegund"]
      self.Year = self.TryGetInteger(data["Ár"])
      self.Driven = self.TryGetInteger(data["Akstur"].replace(".", ""))
      self.Fuel = data["Eldsneyti"]
      self.Transmission = data["Skipting"]
      self.Drive = data["Hjóladrifin"]
      self.ExchangeUp = data["Skipti"].find("Fyrir dýrari") > 0
      self.ExchangeDown = data["Skipti"].find("Fyrir ódýrari") > 0
      self.Seats = self.TryGetInteger(data["Fjöldi sæta"])
      self.Doors = self.TryGetInteger(data["Fjöldi dyra"])
      self.Valves = self.TryGetInteger(data["Fjöldi strokka"])
      self.Inspected = data["Skoðaður"] == "Já"
      self.Color = data["Litur"]
      self.Created = data["Created"]
      self.User = data["User"]


class Operations:

  def SaveCar(car):
    exists = session.query(Car.Id).filter_by(Id=car.Id).scalar() != None

    if not exists:
      session.add(car)
      session.commit()

  def GetAllIds():
    return [x[0] for x in session.query(Car.Id).all()]

  def GetMakerModelYearCount():
    data = session.query(Car.Maker, Car.Model, Car.Year, func.count()
      ).group_by(Car.Maker, Car.Model, Car.Year
      ).all()

    dicts = [dict(zip(["Maker", "Model", "Year", "Count"], d)) for d in data]

    result = {}

    for item in dicts:

      if item["Maker"] not in result:
        result[item["Maker"]] = {}

      maker = result[item["Maker"]]

      if item["Model"] not in maker:
        maker[item["Model"]] = {}

      model = maker[item["Model"]]

      model[item["Year"]] = item["Count"]

    return result

  def GetMakers():
    makers = session.query(Car.Maker, func.count()).group_by(Car.Maker).all()
    makers_dict = {maker[0]: maker[1] for maker in makers}
    return makers_dict

  def GetModels():
    return session.query(Car.Model, func.count()).group_by(Car.Model).all()

Base.metadata.create_all(engine)



from sqlalchemy.orm import sessionmaker
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()
# print(Operations.GetMakerModelYearCount())

# ed_user = User(name='ed', fullname='Ed Jones', nickname='edsnickname')
# session.add(ed_user)
# 
# session.commit()
# 
# for instance in session.query(User).order_by(User.id):
  # print(instance.name, instance.fullname)