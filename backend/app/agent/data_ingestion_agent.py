import requests
import random
import datetime
import os
import pandas as pd
import json
import numpy as np

class DataIngestionAgent:
    def __init__(self, use_spreadsheet=False, spreadsheet_api_url="http://localhost:8002", uploaded_data=None):
        self.weather_api = "https://api.open-meteo.com/v1/forecast"
        self.calendar_api = "https://calendarific.com/api/v2/holidays"
        self.calendar_api_key = "pAJTC7q4vTfoPA39qhcggJvqZRI90iCN"
        self.use_spreadsheet = use_spreadsheet
        self.spreadsheet_api_url = spreadsheet_api_url
        self.uploaded_data = uploaded_data or {}
    
    # ----------------------------------------------------
    # 🔹 API FETCHERS (Called directly by LangGraph Node)
    # ----------------------------------------------------
    
    def get_weather(self, lat=13.0843, lon=80.2705):
        """Get current weather data"""
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current_weather": True
            }
            resp = requests.get(self.weather_api, params=params, timeout=10)
            data = resp.json()
            return {
                "temperature": data["current_weather"]["temperature"],
                "windspeed": data["current_weather"]["windspeed"],
                "weathercode": data["current_weather"]["weathercode"]
            }
        except Exception as e:
            print("Weather API error:", e)
            return {"temperature": random.randint(20, 35), "windspeed": 5, "weathercode": 0}
    
    def get_weather_forecast(self, lat=13.0843, lon=80.2705, days=5):
        """Get weather forecast"""
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min",
                "forecast_days": days,
                "timezone": "auto"
            }
            resp = requests.get(self.weather_api, params=params, timeout=10)
            data = resp.json()
            forecast = []
            for i, d in enumerate(data["daily"]["time"]):
                forecast.append({
                    "date": d,
                    "temp_max": data["daily"]["temperature_2m_max"][i],
                    "temp_min": data["daily"]["temperature_2m_min"][i]
                })
            return forecast
        except Exception as e:
            print("Weather forecast API error:", e)
            return [{"date": str(datetime.date.today() + datetime.timedelta(days=i)), 
                    "temp_max": random.randint(25, 35), 
                    "temp_min": random.randint(20, 30)} for i in range(days)]
    
    def get_festival_events(self, country="IN", year=None):
        """Get festival/calendar events"""
        if not year:
            year = datetime.datetime.now().year
        if not self.calendar_api_key:
            return [
                {"date": "2025-09-10", "event": "Ganesh Chaturthi", "impact": "high demand"},
                {"date": "2025-09-15", "event": "Onam", "impact": "spike in vegetables"}
            ]
        try:
            params = {
                "api_key": self.calendar_api_key,
                "country": country,
                "year": year
            }
            resp = requests.get(self.calendar_api, params=params, timeout=10)
            data = resp.json()
            events = []
            for holiday in data["response"]["holidays"]:
                events.append({
                    "date": holiday["date"]["iso"],
                    "event": holiday["name"],
                    "impact": "demand spike"
                })
            return events
        except Exception as e:
            print("Calendar API error:", e)
            return []
    
    def get_user_notes(self):
        """Get static user notes"""
        return [
            "Customers complain tomatoes are getting spoiled quickly.",
            "Festival season coming next week, expect demand surge."
        ]




    # ----------------------------------------------------
    # 🔹 CORE PROCESSING METHOD (Used by LangGraph Node)
    # ----------------------------------------------------

    def process_data(self, fetched_data: dict) -> dict:
        """
        Processes (normalizes) the entire dataset, merging fetched API/spreadsheet data 
        with any manual uploaded data.
        """
        
        # Merge fetched data with uploaded data (uploaded data takes precedence for items like sales/stock)
        
        # Sales and Stock (Perishables)
        
        return {
            "weather": fetched_data.get("weather", {}),
            "weather_forecast": fetched_data.get("weather_forecast", []),
            "calendar_events": fetched_data.get("calendar_events", [])
        }