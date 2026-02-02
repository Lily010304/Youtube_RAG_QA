import os
import datetime
from pymongo import MongoClient # the library pymongo is for connecting to MongoDB databases
from dotenv import load_dotenv # to load environment variables from a .env file

# initialize env variables from .env using load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

MONGO_DB = os.getenv("MONGO_DB", "youtube_rag")

MONGO_COLLECTION = os.getenv("MONGO_QA_COLLECTION", "queries")

def save_query_answer(video_url:str, question:str, answer:str):
    """
    Docstring for save_query_answer
    
    :param video_url: Description
    :type video_url: str
    :param question: Description
    :type question: str
    :param answer: Description
    :type answer: str
    """
    try:
        # This is the most important step for connecting.
        # We create an instance of the MongoClient, passing it the connection URI.
        # The client manages the connection pool to the database.
        client = MongoClient(MONGO_URI)

        # You can test the connection by sending a "ping" command to the server.
        # This will raise an exception if the connection fails (e.g., wrong password, IP not whitelisted).
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")

        # To get a reference to a specific database, you can use dictionary-style access
        # on the client object with the database name.
        db = client[MONGO_DB]

        # Similarly, you get a reference to a collection within that database.
        # If the database or collection don't exist, MongoDB will create them automatically
        # the first time you write data to them.
        collection = db[MONGO_COLLECTION]

        # We create a standard Python dictionary. This dictionary represents the
        # document we want to store in MongoDB. The keys are the field names.
        document = {
            "video_url": video_url,
            "question": question,
            "answer": answer,
            # datetime.datetime.utcnow() gets the current time in Coordinated Universal Time (UTC).
            # Storing timestamps in UTC is a best practice to avoid timezone issues.
            "timestamp": datetime.datetime.utcnow()
        }
        # The insert_one() method on the collection object takes our dictionary
        # and inserts it as a new document into the 'queries' collection.
        result =collection.insert_one(document)
        # The 'result' object contains information about the insert operation,
        # including the unique '_id' that MongoDB automatically assigned to our new document.
        print(f"Saved Q&A to MongoDB with ID: {result.inserted_id}")


    except Exception as e:
        # It's crucial to handle potential errors, such as connection failures
        # or problems during the insert operation.
        print(f"An error occurred while saving to MongoDB: {e}")

    finally:
        # It's good practice to close the connection when you're done with it.
        # The 'client' variable will only exist if the 'try' block started successfully.
        if 'client' in locals():
            client.close()
            print("MongoDB connection closed.")