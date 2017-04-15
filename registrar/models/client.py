from peewee import *

from .base import BaseModel
from .room import Room

class Client(BaseModel):
    internal_name = CharField(unique=True)
    ip = CharField()
    room = ForeignKeyField(Room, related_name='clients')
    port = IntegerField(default=0)
