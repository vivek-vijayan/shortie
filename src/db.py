import logging
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

# Local imports
from algo import Environ

# Configure basic logging
logging.basicConfig(level=logging.INFO)

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

    async def is_url_present(self, original_url: str, collection_obj: AsyncIOMotorCollection) -> Dict[str, Any]:  # type: ignore
        """
        Function: is_url_present
        Description:
            Asynchronously checks if a given original URL already exists in the specified MongoDB collection.
        Parameters:
            original_url (str): The original long URL to be checked.
            collection_obj (AsyncIOMotorCollection): The MongoDB collection object where the URLs are stored.
        Returns:
            dict: custom return value.
        """
        result = await collection_obj.find_one({"original_url": original_url}) # type: ignore

        return {'exist' : result is not None, 'short_url' :  result.get("short_url") if result else ""} # type: ignore

    async def get_original_url_from_short_url(self, short_url: str, collection_obj: AsyncIOMotorCollection) -> Dict[str, Any]:  # type: ignore
        """
        Function: get_original_url_from_short_url
        Description:
            Asynchronously checks if a given original URL already exists in the specified MongoDB collection.
        Parameters:
            original_url (str): The original long URL to be checked.
            collection_obj (AsyncIOMotorCollection): The MongoDB collection object where the URLs are stored.
        Returns:
            dict: custom return value.
        """
        print({"short_url": short_url})
        result = await collection_obj.find_one({"short_url": short_url})  # type: ignore

        print("Lookup result:", result)  # type: ignore # 🔍 Add this to debug

        return {
            'exist': result is not None,
            'original_url': result.get("original_url", "") if result else "" # type: ignore
        }