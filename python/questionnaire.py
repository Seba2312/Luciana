from flask import Blueprint, render_template, request, session, jsonify
from python.auth import login_required
from python.db import store_questionnaire, store_user_evaluation

questionnaire_bp = Blueprint("questionnaire_bp", __name__, template_folder="templates")

@questionnaire_bp.route('/questionnaire', methods=['GET', 'POST'])
@login_required
def questionnaire_page():
    """Handle displaying and submitting the questionnaire."""
    if request.method == 'POST':
        data = request.get_json(force=True)
        store_questionnaire(session['uid'], data)
        store_user_evaluation(session['uid'], data)
        return jsonify(success=True)
    return render_template('questionnaire.html', variant=session.get('variant', 'A'))

