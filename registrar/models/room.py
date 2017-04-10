from peewee import *

from .base import BaseModel

class Room(BaseModel):
    guid = CharField(unique=True)
    name = CharField()
