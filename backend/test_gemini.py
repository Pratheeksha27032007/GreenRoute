import time

from gemini_analyzer import analyze_task


task = "Analyze 5000 customer reviews and summarize the major complaints."

start = time.perf_counter()

result = analyze_task(task)

elapsed = time.perf_counter() - start

print(result.model_dump_json(indent=2))
print(f"\nGemini latency: {elapsed:.2f} seconds")