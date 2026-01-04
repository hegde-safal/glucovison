import random
import json
import os

try:
    from groq import Groq
except ImportError:
    Groq = None

class RAGEngine:
    def __init__(self):
        # Clinical guidelines to inject into context, not to return directly
        self.clinical_context = """
        Clinical Guidelines for High Glycemic Management:
        1. Activity: Suggest post-meal light walking (10-15 mins) to improve insulin sensitivity.
        2. Hydration: Encourage water intake (250-500ml) to aid glucose excretion.
        3. Food Sequencing: Recommend eating fiber/protein *before* starches/sugar.
        4. Dietary Swaps: Swap high-GI foods (white rice, white bread, sugary drinks) for low-GI alternatives (quinoa, legumes, whole fruit).
        5. Portion Control: Suggest reducing simple carb portion sizes by 50% in the next meal.
        """

    def _get_api_key(self):
        return os.environ.get("GROQ_API_KEY")

    def generate_suggestions(self, totals, risk_level):
        """
        Generate grounded next-day suggestions regarding glycemic control.
        Uses Groq API for dynamic, context-aware advice.
        """
        api_key = self._get_api_key()
        
        if api_key and Groq:
            try:
                client = Groq(api_key=api_key)
                
                prompt = f"""
                You are a senior clinical nutritionist specializing in diabetes and glycemic control.
                
                Patient Data:
                - Sugar: {totals.get('total_sugar', 0)}g
                - Carbs: {totals.get('total_carbs', 0)}g
                - Fiber: {totals.get('total_fiber', 0)}g
                - Protein: {totals.get('total_protein', 0)}g
                - Fat: {totals.get('total_fat', 0)}g
                - Calculated Risk Level: {risk_level}

                {self.clinical_context}

                Your Goal:
                1. Analyze the patient's intake relative to their risk level.
                2. Provide 5 personalized, specific, and actionable suggestions based strictly on the Clinical Guidelines provided above.
                3. Provide 3-4 clear, scientific reasons explaining the current risk level.

                Output Guidelines:
                - Do NOT simply list the guidelines; apply them to the patient's specific data (e.g., "Since your sugar was 50g, try...").
                - Be empathetic but professional.
                - Return ONLY valid JSON.

                JSON Format:
                {{
                    "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3", "suggestion 4", "suggestion 5"],
                    "analysis": ["reason 1", "reason 2", "reason 3", "reason 4"]
                }}
                """
                
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a helpful nutrition assistant which outputs only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama-3.3-70b-versatile",
                    response_format={"type": "json_object"},
                    temperature=0.7
                )
                
                response_content = chat_completion.choices[0].message.content
                data = json.loads(response_content)
                
                if "suggestions" in data and "analysis" in data:
                    return data
                
                return {
                    "suggestions": data.get("suggestions", ["Guidance currently unavailable. Please focus on whole foods."]),
                    "analysis": data.get("analysis", ["Analysis currently unavailable."])
                }

            except Exception as e:
                print(f"RAG Error: {e}")
                return self._error_fallback()
        
        return self._error_fallback()

    def _error_fallback(self):
        """
        Fallback when AI service is unavailable. 
        Avoids hardcoded 'fake' advice, returns safe, generic system messages.
        """
        return {
            "suggestions": [
                "AI service is currently unavailable.",
                "Please focus on staying hydrated.",
                "Prioritize whole, unprocessed foods.",
                "Monitor your portions at the next meal.",
                "Consult a healthcare provider for specific advice."
            ],
            "analysis": [
                "Automated analysis unavailable.",
                "Please check your internet connection or API configuration.",
                "Metrics are still being tracked."
            ]
        }

    def generate_weekly_context(self, history):
        if not history:
            return "No data available for weekly analysis."
        
        sugar_high_days = 0
        fiber_low_days = 0
        total_days = len(history)

        for entry in history:
            totals = json.loads(entry['total_nutrition_json'])
            sugar = totals.get('total_sugar', 0)
            fiber = totals.get('total_fiber', 0)
            
            # Using 40g as the "safe" limit
            if sugar > 40:
                sugar_high_days += 1
            if fiber < 25:
                fiber_low_days += 1
        
        messages = []
        if sugar_high_days > 0:
            messages.append(f"Sugar intake exceeded the safe limit on {sugar_high_days} of the last {total_days} days.")
        
        if fiber_low_days >= (total_days / 2):
            messages.append("Fiber intake was consistently lower than optimal.")
            
        if not messages:
            messages.append("Your weekly trends indicate a stable glycemic load.")

        return " ".join(messages)
