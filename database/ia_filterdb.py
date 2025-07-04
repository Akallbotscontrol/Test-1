import pymongo
from info import DATABASE_NAME, DATABASE_URI

client = pymongo.MongoClient(DATABASE_URI)
db = client[DATABASE_NAME]
col = db["files"]

async def get_file_details(query):
    return col.find(query)
