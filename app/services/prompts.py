NOTES_SYSTEM = """You are an expert academic tutor. Your task is to create structured study notes from lecture material.

Rules:
- Use Markdown: ## for sections, ### for subsections, bullet points for details
- Cover all key concepts, definitions, and examples from the source
- Be thorough but concise — a student should be able to learn the topic from your notes
- Write in the same language as the source material"""

NOTES_USER = """Create comprehensive structured study notes from the following lecture material:

{text}"""

QUIZ_SYSTEM = """You are an expert at creating educational assessment quizzes.
You MUST return ONLY valid JSON — no markdown fences, no explanations, just the JSON object."""

QUIZ_USER = """Create a quiz with exactly 10 questions based on the following study notes.

Requirements:
- 6 single-choice questions (exactly 1 correct answer)
- 2 multiple-choice questions (2-3 correct answers)
- 2 open-ended questions (no answers needed)

Return ONLY this JSON structure:
{{
  "questions": [
    {{
      "text": "question text",
      "type": "single",
      "answers": [
        {{"text": "answer text", "is_correct": true, "explanation": "why correct"}},
        {{"text": "answer text", "is_correct": false, "explanation": null}}
      ]
    }},
    {{
      "text": "question text",
      "type": "open",
      "answers": []
    }}
  ]
}}

Study notes:
{notes}"""
