def build_analysis_prompt(raw_text: str, language: str) -> str:
    return f"""
You are a math tutor. The following text is extracted from an image of a student's math problem and their working.

Return STRICT JSON ONLY. No markdown. Format:
{{
  "title": "...",
  "steps": [
    {{"status": "correct|error|info", "text": "Step explanation in {language}"}},
    ...
  ],
  "correction": "Overall correction advice in {language}",
  "extracted_text": "Original extracted text"
}}

Rules:
- Identify each meaningful step they attempted.
- Mark mistakes as status=error with clear reason.
- Correct steps status=correct.
- Neutral context steps status=info.
- Provide culturally and linguistically natural wording in {language}.
- If final answer wrong, highlight under correction.
Student Work:
{raw_text}
"""
def build_chat_prompt(question: str, prior_steps: list, language: str) -> str:
    flattened = "\n".join(
        f"- ({s.get('status')}) {s.get('text')}" for s in prior_steps[:25]
    )
    return f"""
You are a math tutor responding in {language}.
Context (previous analysis steps):
{flattened or 'No prior steps.'}

Student question:
{question}

Give a concise, clear answer in {language}. If they ask for more detail, provide step-by-step reasoning. Avoid changing previously confirmed correct steps unless necessary.
"""