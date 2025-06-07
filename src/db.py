import os
import dotenv
import asyncio
import logging
from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

# Configure basic logging
logging.basicConfig(level=logging.INFO)

class Environ:
    """
    A class to manage environment variables from .env file or OS environment.
    """

    def __init__(self) -> None:
        """Initializes the environment object."""
        self.env_loaded: bool = False

    def load_from_dotenv(self, env_path: Optional[str] = None) -> bool:
        """
        Loads environment variables from a .env file.

        Args:
            env_path (str, optional): Path to .env file. Defaults to None.

        Returns:
            bool: True if loading succeeds.
        """
        try:
            dotenv.load_dotenv(dotenv_path=env_path)
            self.env_loaded = True
            logging.info("[ENVIRON] Dotenv file loaded successfully.")
            return True
        except Exception as e:
            logging.error(f"[ENVIRON] Failed to load dotenv: {e}")
            return False

    def get(self, key: str) -> str:
        """
        Retrieves an environment variable by key.

        Args:
            key (str): Environment variable key.

        Returns:
            str: Value of the environment variable or empty string if not found.
        """
        value = os.getenv(key)
        if value:
            return value
        logging.warning(f"[ENVIRON] Environment variable '{key}' not found.")
        return ""


class MongoEngine:
    """
    A class to manage MongoDB operations using Motor (async MongoDB driver).
    """

    def __init__(self, env: Environ) -> None:
        """
        Initializes the MongoEngine with a connection string from environment.

        Args:
            env (Environ): An Environ object to load connection string.
        """
        self.connection_string: str = env.get("MONGODB_CONN_STRING")
        self.client: Optional[AsyncIOMotorClient] = None # type: ignore
        self.database: Optional[AsyncIOMotorDatabase] = None # type: ignore

    def connect(self, db_name: str = "url_shortener_database") -> bool:
        """
        Connects to the MongoDB server.

        Args:
            db_name (str): Name of the MongoDB database. Defaults to "url_shortener_database".

        Returns:
            bool: True if connected successfully, else False.
        """
        if self.connection_string:
            try:
                self.client = AsyncIOMotorClient(self.connection_string)
                self.database = self.client.get_database(db_name) # type: ignore
                logging.info(f"[MONGO] Connected to MongoDB database: {db_name}")
                return True
            except Exception as e:
                logging.error(f"[MONGO] Connection failed: {e}")
                return False
        logging.error("[MONGO] Connection string is empty.")
        return False

    def get_collection(self, collection_name: str) -> Optional[AsyncIOMotorCollection]: # type: ignore
        """
        Retrieves a collection object from the database.

        Args:
            collection_name (str): Name of the MongoDB collection.

        Returns:
            Optional[AsyncIOMotorCollection]: The MongoDB collection object or None.
        """
        if self.database != None: # type: ignore
            return self.database.get_collection(collection_name) # type: ignore
        logging.error("[MONGO] Database is not connected.")
        return None

    async def insert_into_collection(
        self, data: Dict[str, str], collection_obj: AsyncIOMotorCollection # type: ignore
    ) -> bool:
        """
        Inserts a document into the specified MongoDB collection.

        Args:
            data (Dict[str, str]): Document to insert.
            collection_obj (AsyncIOMotorCollection): Collection to insert into.

        Returns:
            bool: True if inserted successfully, else False.
        """
        try:
            result = await collection_obj.insert_one(data) # type: ignore
            logging.info(f"[MONGO] Document inserted with ID: {result.inserted_id}")
            return True
        except Exception as e:
            logging.error(f"[MONGO] Insertion failed: {e}")
            return False



if __name__=="__main__":
    # Testing purpose only
    env = Environ()
    env.load_from_dotenv()
    m = MongoEngine(Environ()) # type: ignore
    print(m.connect())
    asyncio.run(m.insert_into_collection(data = {"data": "sample"}, collection_obj= m.get_collection("real_and_short_url_collection"))) # type: ignore