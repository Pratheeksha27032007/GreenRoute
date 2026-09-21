from flask import Flask, request, jsonify
from flask_cors import CORS


from scheduler import schedule_task, schedule_workflow
from gemini_analyzer import analyze_task

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return {
        "message": "GreenRoute Scheduler API is running"
    }


@app.route("/api/analyze-and-schedule", methods=["POST"])
def analyze_and_schedule():

    data = request.get_json()

    task = data.get("task")

    if not task:
        return jsonify({
            "status": "error",
            "message": "Task is required"
        }), 400

    # Step 1: Gemini understands the task
    requirements = analyze_task(task)

    # Step 2: Local scheduler optimizes execution
    result = schedule_task(
        required_accuracy=requirements.recommended_accuracy,
        max_latency=20,
        priority=requirements.urgency,
        carbon_weight=5 if requirements.can_be_delayed else 2,
        cost_weight=2,
        energy_weight=2
    )
    workflow = schedule_workflow(
        urgency=requirements.urgency,
        can_be_delayed=requirements.can_be_delayed
    )
   
    return jsonify({
        "task": task,
        "requirements": requirements.model_dump(),
        "schedule": result,
        "workflow": workflow
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)