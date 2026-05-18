from sqlalchemy import create_engine

DATABASE_URL = "sqlite:///backend/data/live_data.db"

engine = create_engine(DATABASE_URL)