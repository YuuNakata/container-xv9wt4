import os
import traceback

from sqlalchemy import Column, Integer, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

#####***IMPORTANTE***#######-
# --Copyrights--
# - Este bot fue creado para uso personal , si se lo han vendido o ve que es usado por alguien mas por favor contactar a su creador:
# Link de Telegram: https://t.me/NakataYuu
# Numero de telefono: +5355791136


Base = declarative_base()


class General(Base):
    __tablename__ = "generales"
    id_sms = Column(Integer, primary_key=True)


class User(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    zips = Column(Integer, default=1999)
    thumb_list = Column(Text, default="")
    default_thumb = Column(Text, default="")


class DBHelper:
    def __init__(self, dbname: str):
        if dbname.startswith("sqlite"):
            self.engine = create_engine(dbname, connect_args={"check_same_thread": False})
        elif dbname.startswith("postgres://"):
            dbname = dbname.replace("postgres://", "postgresql://", 1)
            self.engine = create_engine(dbname)
        else:
            self.engine = create_engine(dbname)
        Base.metadata.bind = self.engine
        Base.metadata.create_all(checkfirst=True)

    def get_u(self, id: int):
        session: Session = sessionmaker(self.engine)()
        try:
            db_item = session.query(User).filter_by(id=id).first()
            session.close()
            if db_item:
                return True
            else:
                return False
        except Exception as e:
            session.close()
            print(f"An error occurred retrieving items. Item was\n{id}")
            raise e

    def get_u_all(self):
        session: Session = sessionmaker(self.engine)()
        try:
            items = session.query(User).all()
            session.close()
            if items:
                return [[item.id, []] for item in items]
            else:
                return False
        except Exception as e:
            session.close()
            print(f"An error occurred retrieving items. Item was\n{id}")
            raise e

    def new_u(self, id: int):
        session: Session = sessionmaker(self.engine)()
        try:
            new_item = User(id=id)
            session.add(new_item)
            session.commit()
            session.close()
        except Exception as e:
            session.close()
            traceback.print_exc()
            print(e)
            return False

    def set_zips(self, id: int, zips: int):
        session: Session = sessionmaker(self.engine)()
        try:
            db_item = session.query(User).filter_by(id=id).first()
            if db_item:
                db_item.zips = zips
                session.commit()
                session.close()
        except:
            session.close()
            print(f"An error occurred updating. The item to update was\n{id}")

    def set_thumb_list(self, id: int, thumb: str):
        session: Session = sessionmaker(self.engine)()
        try:
            db_item = session.query(User).filter_by(id=id).first()
            if db_item:
                old_item = self.get_thumb_list(id)
                db_item.thumb_list = (old_item + thumb + os.linesep) if old_item else (thumb + os.linesep)
                session.commit()
                session.close()
        except:
            session.close()
            traceback.print_exc()
            return False
        return True

    def set_thumb_default(self, id: int, thumb: str, delete: bool = False):
        session: Session = sessionmaker(self.engine)()
        try:
            db_item = session.query(User).filter_by(id=id).first()
            if db_item:
                db_item.default_thumb = thumb if not delete else ""
                session.commit()
                session.close()
        except:
            session.close()
            traceback.print_exc()
            return False
        return True

    def delete_thumb_list(self, id: int, thumb: str):
        session: Session = sessionmaker(self.engine)()
        try:
            db_item = session.query(User).filter_by(id=id).first()
            if db_item:
                new_thumb = ""
                for temp in self.get_thumb_list(id).split(os.linesep):
                    if not thumb in temp and not "User.thumb_list" in temp:
                        new_thumb += temp + os.linesep
                db_item.thumb_list = new_thumb
                session.commit()
                session.close()
        except:
            session.close()
            traceback.print_exc()
            return False
        return True

    def get_zips(self, id: int):
        session: Session = sessionmaker(self.engine)()
        try:
            db_item = session.query(User).filter_by(id=id).first()
            session.close()
            if db_item:
                return db_item.zips
        except Exception as e:
            session.close()
            print(f"An error occurred retrieving items. Item was\n{id}")
            raise e

    def get_thumb_list(self, id: int):
        session: Session = sessionmaker(self.engine)()
        try:
            db_item = session.query(User).filter_by(id=id).first()
            session.close()
            if db_item:
                return db_item.thumb_list
        except Exception as e:
            session.close()
            traceback.format_exc()
        return False

    def get_thumb_default(self, id: int):
        session: Session = sessionmaker(self.engine)()
        try:
            db_item = session.query(User).filter_by(id=id).first()
            session.close()
            if db_item:
                return db_item.default_thumb
        except Exception as e:
            session.close()
            traceback.format_exc()
            raise e
