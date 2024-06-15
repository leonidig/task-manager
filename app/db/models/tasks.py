from .. import Base

from sqlalchemy.orm import Mapped

from datetime import datetime 


class Task(Base):
    __tablename__ = "tasks"

    title: Mapped[str]
    content: Mapped[str]
    deadline: Mapped[datetime]