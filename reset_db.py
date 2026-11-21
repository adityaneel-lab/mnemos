import os
import shutil

from backend.database import Base, engine

# 1. Clear all SQLite tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("SQLite database cleared.")

# 2. Delete ChromaDB persistent storage
CHROMA_PATH = "./chroma_db"

if os.path.exists(CHROMA_PATH):
    shutil.rmtree(CHROMA_PATH)
    print("ChromaDB cleared.")
else:
    print("ChromaDB directory does not exist.")

print("All databases reset successfully!")
