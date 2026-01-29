#!/bin/bash
# Continuously poll for HITL clarifying questions

echo "🧪 Testing HITL Clarifying Questions Flow"
echo "=========================================="

# Create job
echo "Creating job..."
RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/skills/ \
  -H "Content-Type: application/json" \
  -d '{"task_description": "help me build something", "user_id": "test"}' \
  -m 90)

JOB_ID=$(echo $RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('job_id',''))")
echo "Job ID: $JOB_ID"

# Poll for questions
echo ""
echo "Polling for clarifying questions..."
for i in {1..30}; do
    sleep 2
    RESULT=$(curl -s http://127.0.0.1:8000/api/v1/hitl/$JOB_ID/prompt)
    STATUS=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))")
    TYPE=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin).get('type',''))")
    QUESTIONS=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin).get('questions',''))")
    
    echo "Poll $i: status=$STATUS, type=$TYPE, questions=$([ \"$QUESTIONS\" != \"None\" ] \&\& [ \"$QUESTIONS\" != \"null\" ] \&\& echo \"PRESENT\" || echo \"EMPTY\")"
    
    if [ "$STATUS" = "pending_user_input" ] || [ "$STATUS" = "pending_hitl" ]; then
        if [ "$QUESTIONS" != "None" ] && [ "$QUESTIONS" != "null" ]; then
            echo ""
            echo "✅ SUCCESS! Clarifying questions found!"
            echo ""
            echo $RESULT | python3 -m json.tool
            exit 0
        fi
    fi
done

echo ""
echo "❌ Timeout - no clarifying questions appeared"
