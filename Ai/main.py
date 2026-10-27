import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from scraper import scrape_google_maps

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_index():
    return FileResponse("index.html")

@app.get("/fetch-leads")
def fetch_leads(location: str, business_type: str):
    query = f"{business_type} in {location}"
    print(f"Starting search for: '{query}'")
    
    try:
        leads = scrape_google_maps(query)
        return {
            "status": "success",
            "total_found_without_website": len(leads),
            "leads": leads
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "total_found_without_website": 0,
            "leads": []
        }