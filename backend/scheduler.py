CONFIGURATIONS = [
    {
        "id": "flash-edge-now",
        "model": "Gemini Flash Lite",
        "location": "Edge",
        "timing": "Now",
        "latency": 2.1,
        "accuracy": 91,
        "cost": 0.30,
        "energy": 0.6,
        "carbon": 2.4
    },
    {
        "id": "flash-cloud-now",
        "model": "Gemini Flash Lite",
        "location": "Cloud",
        "timing": "Now",
        "latency": 3.5,
        "accuracy": 91,
        "cost": 0.25,
        "energy": 0.5,
        "carbon": 3.0
    },
    {
        "id": "flash-cloud-later",
        "model": "Gemini Flash Lite",
        "location": "Cloud",
        "timing": "Later",
        "latency": 15.0,
        "accuracy": 91,
        "cost": 0.15,
        "energy": 0.4,
        "carbon": 1.5
    },
    {
        "id": "advanced-cloud-now",
        "model": "Gemini Flash",
        "location": "Cloud",
        "timing": "Now",
        "latency": 4.8,
        "accuracy": 96,
        "cost": 1.20,
        "energy": 2.5,
        "carbon": 8.0
    },
    {
        "id": "advanced-cloud-later",
        "model": "Gemini Flash",
        "location": "Cloud",
        "timing": "Later",
        "latency": 17.0,
        "accuracy": 96,
        "cost": 0.80,
        "energy": 1.8,
        "carbon": 5.0
    }
]


def schedule_task(
    required_accuracy,
    max_latency,
    priority,
    carbon_weight,
    cost_weight,
    energy_weight
):
    # Step 1: Find configurations that satisfy hard constraints
    feasible = []

    for config in CONFIGURATIONS:
        if config["accuracy"] < required_accuracy:
            continue

        if config["latency"] > max_latency:
            continue

        feasible.append(config)

    # No valid configuration
    if not feasible:
        return {
            "status": "no_feasible_configuration",
            "message": "No available configuration satisfies the requirements."
        }

    # Step 2: Give latency different importance based on priority
    if priority == "high":
        latency_weight = 5
    elif priority == "medium":
        latency_weight = 2
    else:
        latency_weight = 0.25

    # Step 3: Calculate score
    def score(config):
        return (
            latency_weight * config["latency"]
            + cost_weight * config["cost"]
            + energy_weight * config["energy"]
            + carbon_weight * config["carbon"]
            - 0.1 * config["accuracy"]
        )

    # Step 4: Select lowest-scoring feasible configuration
    selected = min(feasible, key=score)

    # Step 5: Keep alternatives for the UI
    alternatives = sorted(feasible, key=score)

    reason_parts = []

    if priority == "high":
        reason_parts.append("high urgency made latency important")
    elif priority == "low":
        reason_parts.append("low urgency allowed additional latency")

    if carbon_weight >= 5:
        reason_parts.append("carbon reduction was strongly prioritized")

    if cost_weight >= 5:
        reason_parts.append("cost reduction was strongly prioritized")

    if energy_weight >= 5:
        reason_parts.append("energy reduction was strongly prioritized")

    reason = "Selected because " + " and ".join(reason_parts) + "."

    return {
        "status": "success",
        "selected": selected,
        "alternatives": alternatives,
        "reason": reason
    }
def schedule_workflow(urgency="normal", can_be_delayed=True):
    """
    Schedule each workflow step independently while respecting
    the overall task urgency.
    """

    # High urgency means the workflow should not intentionally
    # delay its final output.
    if urgency == "high":
        generate_priority = "high"
        generate_carbon_weight = 2
    elif urgency == "low" and can_be_delayed:
        generate_priority = "low"
        generate_carbon_weight = 5
    else:
        generate_priority = "normal"
        generate_carbon_weight = 3

    steps = [
        {
            "name": "Classify",
            "description": "Understand and classify the incoming task",
            "accuracy": 88,
            "max_latency": 5,
            "priority": "high",
            "carbon_weight": 2,
            "cost_weight": 2,
            "energy_weight": 2,
            "reason_hint": "A lightweight configuration is sufficient for classification while keeping latency and resource usage low."
        },
        {
            "name": "Retrieve",
            "description": "Retrieve relevant information or context",
            "accuracy": 90,
            "max_latency": 6,
            "priority": "high",
            "carbon_weight": 2,
            "cost_weight": 2,
            "energy_weight": 2,
            "reason_hint": "Fast execution is preferred because retrieval is latency-sensitive and does not require the highest-capability configuration."
        },
        {
            "name": "Analyze",
            "description": "Perform deeper reasoning and analysis",
            "accuracy": 94,
            "max_latency": 12,
            "priority": urgency,
            "carbon_weight": 3 if urgency != "low" else 5,
            "cost_weight": 2,
            "energy_weight": 2,
            "reason_hint": "Higher-capability execution is justified because this step requires deeper reasoning and higher accuracy."
        },
        {
            "name": "Generate",
            "description": "Generate the final response",
            "accuracy": 90,
            "max_latency": 20,
            "priority": generate_priority,
            "carbon_weight": generate_carbon_weight,
            "cost_weight": 2,
            "energy_weight": 2,
            "reason_hint": "The selected configuration meets the generation requirements without using more resources than necessary."
        }
    ]

    workflow = []

    for step in steps:
        result = schedule_task(
            required_accuracy=step["accuracy"],
            max_latency=step["max_latency"],
            priority=step["priority"],
            carbon_weight=step["carbon_weight"],
            cost_weight=step["cost_weight"],
            energy_weight=step["energy_weight"]
        )

        workflow.append({
            "name": step["name"],
            "description": step["description"],
            "reason": step["reason_hint"],
            "schedule": result
        })

    return workflow