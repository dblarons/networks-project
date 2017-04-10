from peewee import *

from .base import BaseModel
from .room import Room

class Client(BaseModel):
    internal_name = CharField(unique=True)
    name = CharField()
    room = ForeignKeyField(Room, related_name='clients')
