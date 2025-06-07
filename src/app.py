import time
from typing import Dict
from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse

# Local imports
from algo import BloomFilter, Environ, EncryptHash
from model import URL
from db import MongoEngine

# Initializing the fast api class
app = FastAPI()
env = Environ()
env.load_from_dotenv()
mongoEngine: MongoEngine = MongoEngine(Environ()) # type: ignore
filter_obj = BloomFilter(size=10, hash_size=10)
connection = mongoEngine.connect()



# Server Section
@app.post("/generate")
async def generate_shorturl(org_url: str):
    # Extract and wrap the original URL
    url: str = org_url
    url_obj = URL(str(url))

    # Check if URL is not empty
    if url != "":
        # Attempt to connect to MongoDB
        if connection == True:  # type: ignore
            # Check if the original URL is already in the database
            result = await mongoEngine.is_url_present( # type: ignore
                url_obj.url, 
                mongoEngine.get_collection("real_and_short_url_collection")  # type: ignore
            )

            # If the URL does not already exist, create a new short URL
            if not result['exist']:
                # Initialize hash generator with desired length
                hashed_url = EncryptHash(6)

                # Generate a short ID from the original URL
                short_id = hashed_url.generate_short_id(url_obj.url)

                # Ensure the short ID is not already in the Bloom filter (basic collision handling)
                while filter_obj.check(value=short_id):
                    short_id = hashed_url.generate_short_id(url_obj.url)
                    filter_obj.add(short_id)

                # Prepare the document to insert into the database
                post_data: Dict[str, str] = {
                    "original_url": url_obj.url,
                    "short_url": short_id,
                    "timestamp": str(time.ctime())
                }

                # Insert the data into MongoDB
                await mongoEngine.insert_into_collection( # type: ignore
                    data=post_data,
                    collection_obj=mongoEngine.get_collection("real_and_short_url_collection")  # type: ignore
                )

                # Return success response with new short URL
                return JSONResponse(
                    content={
                        'status': 'created',
                        'message': 'New short url generated',
                        'short_url': short_id,
                        'timestamp': str(time.ctime())
                    },
                    status_code=200
                )
            else:
                # URL already exists in the database, return the existing short URL
                return JSONResponse(
                    content={
                        'status': 'exist',
                        'message': 'URL already present',
                        'short_url': result.get('short_url')
                    }
                )
        else:
            # No active connection to mongodb
            return JSONResponse(
                content={
                    'status': 'failed',
                    'message': 'Connection to Database failed'
                },
                status_code=200
            )
    else:
        # URL input was empty
        return JSONResponse(
            content={
                'status': 'rejected',
                'message': 'URL is mandatory'
            },
            status_code=200
        )


@app.get("/{short_url}")
async def get_original_url_and_redirect(short_url: str):
    """
    Endpoint to redirect a user from a short URL to the original full URL.
    
    Parameters:
        short_url (str): The short ID used to lookup the original URL in the database.

    Returns:
        RedirectResponse: Redirects to the original URL if found.
        JSONResponse: Error message if the short URL is invalid or DB is not connected.
    """
    
    if connection:  # Ensure the DB connection is established
        result = await mongoEngine.get_original_url_from_short_url( # type: ignore
            short_url, 
            mongoEngine.get_collection("real_and_short_url_collection")  # type: ignore
        )
        
        # If the short URL exists in the DB, redirect the user
        if result.get('exist'):

            # Optional safety: Ensure the URL has a valid scheme
            url_to_redirect = result['original_url']
            if not url_to_redirect.startswith(("http://", "https://")):
                url_to_redirect = "https://" + url_to_redirect
            
            return RedirectResponse(url=url_to_redirect, status_code=301)

        # If not found, return a failure response
        return JSONResponse(
            content={'status': 'failed', 'message': 'Invalid short URL'},
            status_code=404
        )

    # If database is not connected
    return JSONResponse(
        content={'status': 'rejected', 'message': 'No active DB connection'},
        status_code=503
    )


