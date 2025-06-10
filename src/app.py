import time
import uvicorn
from typing import Dict
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse,FileResponse

# Local imports
from modules.algo import BloomFilter, Environ, EncryptHash
from modules.model import URL
from modules.db import MongoEngine

# Initializing the fast api class
app = FastAPI()
env = Environ()
env.load_from_dotenv()
mongoEngine: MongoEngine = MongoEngine(Environ()) # type: ignore
filter_obj = BloomFilter(size=10, hash_size=10)
connection = mongoEngine.connect()

# Set the directory for templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Static file handler
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")

@app.get("/css/style.css")
async def getting_style_css():
    return FileResponse("static/css/style.css")

# Rendering homepage
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):

    return templates.TemplateResponse(
        "index.html",
        context={
            'request': request
        }
    )


# Server Section
@app.post("/g", response_class=HTMLResponse)
async def generate_shorturl(request: Request, org_url: str = Form(...)):

    if request.method == "POST":
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
                    return templates.TemplateResponse(
                            "short-url.html",
                            context={
                                'request': request,
                                'original_url' : "",
                                'short_url' : short_id
                            }
                        )

                    
                else:
                    # URL already exists in the database, return the existing short URL
                    return templates.TemplateResponse(
                            "short-url.html",
                            context={
                                'request': request,
                                'original_url' : "",
                                'short_url' : result.get('short_url')
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

    else:
        return RedirectResponse(url="/", status_code=303)


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

    if short_url == "g":
        return RedirectResponse(url="/", status_code=303)
    
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
        return RedirectResponse(url="/", status_code=303)

    # If database is not connected
    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000)