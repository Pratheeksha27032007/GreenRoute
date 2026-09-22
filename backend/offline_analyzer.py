from gemini_analyzer import TaskRequirements


def analyze_task_offline(task):
    """
    Local fallback analyzer used when Gemini is unavailable.
    Uses deterministic rules so GreenRoute can continue
    operating without an active Gemini connection.
    """

    text = task.lower()

    # -------------------------
    # Task type
    # -------------------------
    if any(word in text for word in ["financial", "finance", "fraud", "transaction"]):
        task_type = "Financial Analysis"
    elif any(word in text for word in ["medical", "health", "diagnosis", "patient"]):
        task_type = "Healthcare Analysis"
    elif any(word in text for word in ["code", "coding", "program", "debug", "software"]):
        task_type = "Code Analysis"
    elif any(word in text for word in ["research", "researching", "investigate"]):
        task_type = "Research"
    elif any(word in text for word in ["summarize", "summary", "summarise"]):
        task_type = "Summarization"
    elif any(word in text for word in ["classify", "classification", "categorize"]):
        task_type = "Classification"
    elif any(word in text for word in ["translate", "translation"]):
        task_type = "Translation"
    elif any(word in text for word in ["generate", "write", "draft", "create"]):
        task_type = "Content Generation"
    else:
        task_type = "General AI Task"

    # -------------------------
    # Complexity
    # -------------------------
    if any(word in text for word in [
        "financial", "finance", "fraud", "medical",
        "research", "technical", "complex", "detailed",
        "diagnosis", "legal", "deep analysis"
    ]):
        complexity = "high"

    elif any(word in text for word in [
        "summarize", "summary", "classify",
        "classification", "translate", "extract",
        "simple"
    ]):
        complexity = "low"

    else:
        complexity = "medium"

    # -------------------------
    # Urgency
    # -------------------------
    if any(word in text for word in [
        "urgent", "immediately", "asap",
        "real-time", "realtime", "right now",
        "critical"
    ]):
        urgency = "high"

    elif any(word in text for word in [
        "later", "weekly", "batch",
        "overnight", "non-urgent", "non urgent"
    ]):
        urgency = "low"

    else:
        urgency = "normal"

    # -------------------------
    # Can task be delayed?
    # -------------------------
    can_be_delayed = urgency != "high"

    # -------------------------
    # Required accuracy
    # -------------------------
    if any(word in text for word in [
        "highly accurate",
        "very accurate",
        "high accuracy",
        "critical accuracy",
        "precise",
        "precision"
    ]):
        recommended_accuracy = 96

    elif complexity == "high":
        recommended_accuracy = 94

    elif complexity == "medium":
        recommended_accuracy = 90

    else:
        recommended_accuracy = 88

    return TaskRequirements(
        task_type=task_type,
        complexity=complexity,
        recommended_accuracy=recommended_accuracy,
        urgency=urgency,
        can_be_delayed=can_be_delayed
    )