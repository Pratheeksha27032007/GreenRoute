from flask import Flask, request, jsonify
from flask_cors import CORS


from scheduler import schedule_task, schedule_workflow
from gemini_analyzer import analyze_task
from offline_analyzer import analyze_task_offline
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
    optimization_mode = data.get("optimization_mode", "balanced")
    if not task:
        return jsonify({
            "status": "error",
            "message": "Task is required"
        }), 400
    MODES = {
        "balanced": {
            "carbon": 3,
            "cost": 3,
            "energy": 3
        },
        "carbon": {
            "carbon": 8,
            "cost": 2,
            "energy": 5
        },
        "latency": {
            "carbon": 1,
            "cost": 1,
            "energy": 1
        },
        "cost": {
            "carbon": 2,
            "cost": 8,
            "energy": 3
        },
        "energy": {
            "carbon": 5,
            "cost": 2,
            "energy": 8
        }
    }

    weights = MODES.get(
        optimization_mode,
        MODES["balanced"]
    )
    # Step 1: Gemini understands the task
    try:
        requirements = analyze_task(task)
        analysis_source = "Gemini"
        offline = False

    except Exception as e:
        print(f"Gemini unavailable. Using offline fallback: {e}")

        requirements = analyze_task_offline(task)
        analysis_source = "Local Offline Fallback"
        offline = True

    # Step 2: Local scheduler optimizes execution
    required_accuracy = min(requirements.recommended_accuracy, 96)

    result = schedule_task(
        required_accuracy=required_accuracy,
        max_latency=20,
        priority=requirements.urgency,
        carbon_weight=weights["carbon"],
        cost_weight=weights["cost"],
        energy_weight=weights["energy"]
    )
    # Compare selected configuration with the highest-resource
    # feasible configuration.
    impact = None

    if result.get("status") == "success":
        selected = result["selected"]
        alternatives = result["alternatives"]

        baseline = max(
            alternatives,
            key=lambda x: (
                x["carbon"],
                x["energy"],
                x["cost"]
            )
        )

        impact = {
            "baseline": baseline,
            "carbon_reduction": round(
                max(
                    0,
                    (baseline["carbon"] - selected["carbon"])
                    / baseline["carbon"] * 100
                ),
                1
            ),
            "cost_reduction": round(
                max(
                    0,
                    (baseline["cost"] - selected["cost"])
                    / baseline["cost"] * 100
                ),
                1
            ),
            "energy_reduction": round(
                max(
                    0,
                    (baseline["energy"] - selected["energy"])
                    / baseline["energy"] * 100
                ),
                1
            )
        }
    workflow = schedule_workflow(
        urgency=requirements.urgency,
        can_be_delayed=requirements.can_be_delayed
    )
   
    return jsonify({
        "task": task,
        "requirements": requirements.model_dump(),
        "schedule": result,
        "impact": impact,
        "workflow": workflow,
        "analysis_source": analysis_source,
        "offline": offline
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)