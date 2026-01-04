from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
import json
import os

from .nutrition import NutritionEngine
from .nlp import NLPEngine
from .storage import log_daily_entry, get_history, get_user_settings, update_user_settings
from .rag import RAGEngine

main_bp = Blueprint('main', __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "nutrition_master.csv")

nutrition_engine = NutritionEngine(CSV_PATH)
nlp_engine = NLPEngine()
rag_engine = RAGEngine()

@main_bp.route('/')
def index():
    settings = get_user_settings()
    return render_template('index.html', name=settings.get('name', 'User'))

@main_bp.route('/weekly-analysis')
def weekly_analysis():
    return render_template('weekly_analysis.html')

@main_bp.route('/history')
def history():
    entries = get_history()
    return render_template('history.html', entries=entries)

@main_bp.route('/settings')
def settings():
    settings = get_user_settings()
    return render_template('settings.html', settings=settings)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json() or {}
    
    meals = {
        "breakfast": data.get("breakfast", ""),
        "lunch": data.get("lunch", ""),
        "snacks": data.get("snacks", ""),
        "dinner": data.get("dinner", "")
    }
    
    all_text = f"{meals['breakfast']} {meals['lunch']} {meals['snacks']} {meals['dinner']}"
    
    parsed_items = nlp_engine.parse_meals(all_text)
    
    totals, unmatched = nutrition_engine.analyze_meals(parsed_items)
    
    risk_level, risk_reason = nutrition_engine.calculate_risk(totals)
    
    today = datetime.now().strftime("%Y-%m-%d")
    log_daily_entry(today, meals, totals, risk_level, risk_reason)
    
    suggestions = rag_engine.generate_suggestions(totals, risk_level)
    
    return jsonify({
        "totals": totals,
        "risk_level": risk_level,
        "risk_reason": risk_reason,
        "suggestions": suggestions,
        "unmatched": unmatched
    })

@main_bp.route('/api/settings', methods=['POST'])
def update_settings_api():
    data = request.get_json()
    
    update_user_settings(
        data.get('name'), 
        float(data.get('sugar_limit', 25.0)),
        data.get('weekly', False),
        data.get('monthly', False)
    )
    return jsonify({"status": "success"})

@main_bp.route('/api/settings/status')
def settings_status():
    settings = get_user_settings()
    is_setup = settings.get('name') != 'User'
    return jsonify({"setup_complete": is_setup})

@main_bp.route('/api/stats/weekly')
def weekly_stats():
    history = get_history(limit=7)
    
    history_asc = history[::-1]
    
    dates = []
    sugar = []
    carbs = []
    fiber = []
    risk_counts = {"Safe": 0, "Moderate": 0, "High": 0}
    
    for entry in history_asc:
        d = datetime.strptime(entry['date'], "%Y-%m-%d")
        dates.append(d.strftime("%d/%m"))
        
        totals = json.loads(entry['total_nutrition_json'])
        sugar.append(totals.get('total_sugar', 0))
        carbs.append(totals.get('total_carbs', 0))
        fiber.append(totals.get('total_fiber', 0))
        
        r_level = entry['risk_level']
        if r_level in risk_counts:
            risk_counts[r_level] += 1
            
    context = rag_engine.generate_weekly_context(history)
    
    return jsonify({
        "dates": dates,
        "sugar": sugar,
        "carbs": carbs,
        "fiber": fiber,
        "risk_counts": risk_counts,
        "context": context
    })
