from skill_fleet.core.dspy.utils.question_options import generate_smart_options

try:
    res = generate_smart_options("test question", "test context")
    print(f"Result: {res}")
    a, b = res
    print("Unpacked successfully")
except Exception as e:
    print(f"Error: {e}")
