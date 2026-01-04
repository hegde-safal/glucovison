import pandas as pd
from rapidfuzz import fuzz, process
from typing import List, Dict, Tuple, Any
import requests
import os

class NutritionEngine:
    def __init__(self, csv_path):
        self.df = None
        self.food_names = []
        self.food_lookup = {}
        self.load_data(csv_path)


    def load_data(self, csv_path):
        try:
            self.df = pd.read_csv(csv_path)
            # Normalize
            self.df.columns = [c.strip().lower() for c in self.df.columns]
            self.df["food_name"] = self.df["food_name"].astype(str).str.strip().str.lower()
            
            # PATCH: Fix known bad data (Zero sugar/nutrients for common items)
            # Values are approx per 100g based on USDA
            PATCH_DATA = {
                "apple": {"calories": 52, "carbs": 14, "sugar": 10, "fiber": 2.4, "protein": 0.3, "fat": 0.2},
                "banana": {"calories": 89, "carbs": 23, "sugar": 12, "fiber": 2.6, "protein": 1.1, "fat": 0.3},
                "orange": {"calories": 47, "carbs": 12, "sugar": 9, "fiber": 2.4, "protein": 0.9, "fat": 0.1},
                "grapes": {"calories": 69, "carbs": 18, "sugar": 15, "fiber": 0.9, "protein": 0.7, "fat": 0.2},
                "strawberry": {"calories": 32, "carbs": 7.7, "sugar": 4.9, "fiber": 2.0, "protein": 0.7, "fat": 0.3},
                "oatmeal": {"calories": 68, "carbs": 12, "sugar": 0.5, "fiber": 1.7, "protein": 2.4, "fat": 1.4},
                "white bread": {"calories": 265, "carbs": 49, "sugar": 5, "fiber": 2.7, "protein": 9, "fat": 3.2},
                "milk": {"calories": 50, "carbs": 4.8, "sugar": 5, "fiber": 0, "protein": 3.4, "fat": 2},
                "egg": {"calories": 155, "carbs": 1.1, "sugar": 1.1, "fiber": 0, "protein": 13, "fat": 11},
            }

            for food, data in PATCH_DATA.items():
                mask = self.df["food_name"] == food
                if mask.any():
                    # Update existing
                    for col, val in data.items():
                        if col in self.df.columns:
                            self.df.loc[mask, col] = val
                else:
                    # Append new if not exists (simple append)
                    new_row = {"food_name": food, **data}
                    self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)

            self.food_names = self.df["food_name"].tolist()
            self.food_lookup = {
                row["food_name"]: row for _, row in self.df.iterrows()
            }
        except Exception as e:
            print(f"Error loading CSV: {e}")
            # Initialize empty if fail, to prevent crash, but app should handle
            self.df = pd.DataFrame()

    def fuzzy_match(self, query: str, min_score=80) -> Tuple[str, pd.Series, float]:
        if not query:
            return None, None, 0.0
        
        match = process.extractOne(query, self.food_names, scorer=fuzz.WRatio)
        if not match:
            return None, None, 0.0

        matched_name, score, _ = match
        if score < min_score:
            return None, None, float(score)

        return matched_name, self.food_lookup.get(matched_name), float(score)

    def _get_api_credentials(self):
        return os.environ.get("EDAMAM_APP_ID"), os.environ.get("EDAMAM_APP_KEY")

    def fetch_from_api(self, query: str) -> Dict[str, float]:
        app_id, app_key = self._get_api_credentials()
        
        with open("debug_fallback.log", "a") as f:
            f.write(f"API Call for '{query}'. Creds: {app_id}, {app_key}\n")

        if not app_id or not app_key or "YOUR_" in app_key:
            with open("debug_fallback.log", "a") as f:
                f.write("Missing credentials.\n")
            return None
            
        # Edamam Nutrition Analysis API requires a quantity to return data.
        # If user didn't specify one (e.g. "blueberry cheesecake"), prepend "1 " to force a default match.
        if not query[0].isdigit():
             query = "1 " + query

        # SWITCHED TO NUTRITION ANALYSIS API based on user keys
        url = "https://api.edamam.com/api/nutrition-data"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "ingr": query
        }
        
        try:
            with open("debug_fallback.log", "a") as f:
                f.write(f"Sending Request to {url} with params {params}\n")
            
            response = requests.get(url, params=params, timeout=5)
            
            with open("debug_fallback.log", "a") as f:
                f.write(f"Response Status: {response.status_code}\n")
                f.write(f"Response Body: {response.text[:200]}...\n")

            if response.status_code == 200:
                data = response.json()
                
                # Nutrition Analysis API structure:
                # 1. totalNutrients at root (Standard)
                # 2. If missing, check ingredients[0].parsed[0].nutrients (Fallback)
                
                nutrients = None
                if "totalNutrients" in data and data["totalNutrients"]:
                    nutrients = data["totalNutrients"]
                elif "ingredients" in data and data["ingredients"]:
                    # Try to get from first parsed ingredient
                    try:
                        nutrients = data["ingredients"][0]["parsed"][0]["nutrients"]
                    except (KeyError, IndexError):
                        pass

                if nutrients:
                    return {
                        "calories": nutrients.get("ENERC_KCAL", {}).get("quantity", 0),
                        "protein": nutrients.get("PROCNT", {}).get("quantity", 0),
                        "fat": nutrients.get("FAT", {}).get("quantity", 0),
                        "carbs": nutrients.get("CHOCDF", {}).get("quantity", 0),
                        "fiber": nutrients.get("FIBTG", {}).get("quantity", 0),
                        "sugar": nutrients.get("SUGAR", {}).get("quantity", 0)
                    }
                elif "calories" in data and data["calories"] > 0:
                     # Fallback if totalNutrients empty but calories exist
                     return {
                        "calories": data.get("calories", 0),
                        "protein": 0,
                        "fat": 0,
                        "carbs": 0,
                        "fiber": 0,
                        "sugar": 0
                     }
        except Exception as e:
            with open("debug_fallback.log", "a") as f:
                f.write(f"EXCEPTION: {e}\n")
            print(f"API Error: {e}")
            
        return None

    def calculate_risk(self, totals: Dict[str, float]) -> Tuple[str, str]:
        """
        Determine Glycaemic Risk Level based on updated thresholds.
        Returns: (Risk Level, Explanation)
        
        Rules:
        Safe (Green): Sugar <= 40g
        Moderate (Yellow): Sugar 40-65g
        High (Red): Sugar > 65g
        """
        sugar = totals.get("total_sugar", 0)
        # We can keep carb limits or adjust them. The user only specified sugar.
        # But commonly, moderate sugar comes with moderate carbs. 
        # I will keep carb logic but deprioritize it if sugar is the main focus,
        # or just update sugar logic as requested.
        # Let's assume carb thresholds remain similar or scale. 
        # User specified: "Final Sugar Thresholds (Total Sugar, not Added)"
        # I will strictly follow the sugar tiers and keep existing carb checks as secondary or just independent.
        
        carbs = totals.get("total_carbs", 0)

        # Default to Safe
        level = "Safe"
        reason = "Your sugar intake is within the safe limit (≤40g)."

        # Check High first (priority)
        if sugar > 65 or carbs > 250:
            level = "High"
            reasons = []
            if sugar > 65:
                reasons.append(f"Sugar ({sugar}g) exceeds the 65g high-risk threshold.")
            if carbs > 250:
                reasons.append(f"Carbs ({carbs}g) exceed the 250g upper limit.")
            reason = " ".join(reasons)
        
        # Check Moderate
        elif (40 < sugar <= 65) or (150 < carbs <= 250):
            level = "Moderate"
            reasons = []
            if 40 < sugar <= 65:
                reasons.append(f"Sugar ({sugar}g) is in the moderate risk zone (40-65g).")
            if 150 < carbs <= 250:
                reasons.append(f"Carbs ({carbs}g) are in the moderate range (150-250g).")
            reason = " ".join(reasons) + " Needs moderation."

        return level, reason

    def analyze_meals(self, parsed_items: List[Tuple[str, float]]) -> Dict[str, Any]:
        totals = {
            "total_calories": 0.0,
            "total_carbs": 0.0,
            "total_sugar": 0.0,
            "total_protein": 0.0,
            "total_fat": 0.0,
            "total_fiber": 0.0,
        }
        unmatched = []

        for phrase, qty in parsed_items:
            matched_name, row, score = self.fuzzy_match(phrase)
            if row is None:
                # Fallback to API
                api_data = self.fetch_from_api(phrase)
                if api_data:
                    self._add_to_totals(totals, api_data, qty)
                    continue
                else:
                    unmatched.append(phrase)
                    continue
            
            # Smart Fallback: If local data has 0 sugar but item doesn't claim to be sugar-free, check API
            # This fixes issues where CSV has missing sugar values (common in provided dataset)
            local_sugar = float(row.get("sugar", 0) or 0)
            
            with open("debug_fallback.log", "a") as f:
                f.write(f"Analyzed '{phrase}'. Matched '{matched_name}'. Sugar: {local_sugar}\n")
            
            if local_sugar == 0 and "sugar free" not in matched_name and "zero sugar" not in matched_name:
                with open("debug_fallback.log", "a") as f:
                    f.write(f"Triggering API for '{phrase}'...\n")
                
                api_data = self.fetch_from_api(phrase)
                
                if api_data:
                    with open("debug_fallback.log", "a") as f:
                        f.write(f"API Result: {api_data}\n")
                
                if api_data and api_data.get("sugar", 0) > 0:
                     self._add_to_totals(totals, api_data, qty)
                     continue

            totals["total_calories"] += float(row.get("calories", 0) or 0) * qty
            totals["total_carbs"] += float(row.get("carbs", 0) or 0) * qty
            totals["total_sugar"] += float(row.get("sugar", 0) or 0) * qty
            totals["total_protein"] += float(row.get("protein", 0) or 0) * qty
            totals["total_fat"] += float(row.get("fat", 0) or 0) * qty
            totals["total_fiber"] += float(row.get("fiber", 0) or 0) * qty

        # Round
        rounded_totals = {k: round(v, 2) for k, v in totals.items()}
        
        return rounded_totals, unmatched
    
    def _add_to_totals(self, totals, data, qty):
        totals["total_calories"] += float(data.get("calories", 0) or 0) * qty
        totals["total_carbs"] += float(data.get("carbs", 0) or 0) * qty
        totals["total_sugar"] += float(data.get("sugar", 0) or 0) * qty
        totals["total_protein"] += float(data.get("protein", 0) or 0) * qty
        totals["total_fat"] += float(data.get("fat", 0) or 0) * qty
        totals["total_fiber"] += float(data.get("fiber", 0) or 0) * qty
