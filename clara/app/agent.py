# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.cloud import firestore

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

MODEL = "gemini-3.6-flash"

# Firestore connection for Clara's Google Cloud project.
db = firestore.Client(project="clara-agent-2026", database="clara")


# ---------------------------------------------------------
# CLARA TOOLS
# ---------------------------------------------------------

def organize_visit_info(
    visit_reason: str,
    diagnoses: list[str],
    medications: list[str],
    instructions: list[str],
    follow_ups: list[str],
    tests: list[str],
    restrictions: list[str],
) -> dict:
    """Organizes medical visit information into patient-friendly sections.

    Use this after reviewing an after-visit summary or discharge document.
    Only include information actually present in the user's medical paperwork.
    Never invent missing information.

    Args:
        visit_reason: Documented reason for the visit.
        diagnoses: Diagnoses or conditions documented.
        medications: Medications documented.
        instructions: Provider instructions documented.
        follow_ups: Follow-up appointments or actions documented.
        tests: Labs, imaging, or other tests documented.
        restrictions: Activity, diet, or other restrictions documented.

    Returns:
        Structured visit information.
    """
    return {
        "visit_reason": visit_reason,
        "diagnoses": diagnoses,
        "medications": medications,
        "instructions": instructions,
        "follow_ups": follow_ups,
        "tests": tests,
        "restrictions": restrictions,
    }


def extract_visit_sections(document_text: str) -> dict:
    """Processes readable text from an after-visit or discharge document.

    Only use text that can be confidently read from the medical document.
    Never reconstruct, guess, or invent unreadable information.

    Args:
        document_text: Readable text extracted from the medical document.

    Returns:
        Document text ready for further organization.
    """
    return {
        "document_text": document_text,
    }


def create_care_plan(
    medications: list[str],
    tests: list[str],
    follow_ups: list[str],
    instructions: list[str],
    restrictions: list[str],
) -> dict:
    """Creates the user's My Plan from documented medical instructions.

    Use this whenever the user asks for My Plan, next steps, action items,
    what they need to do, or when a medical document contains actionable
    medications, tests, follow-ups, instructions, or restrictions.

    Only create actions explicitly supported by the user's paperwork.
    Never invent dates, medication instructions, tests, follow-ups,
    restrictions, or other medical actions.

    Args:
        medications: Documented medication-related actions.
        tests: Documented tests to complete.
        follow_ups: Documented follow-up actions.
        instructions: Other documented provider instructions.
        restrictions: Documented restrictions.

    Returns:
        Structured care-plan information.
    """
    return {
    "medication_actions": [
        {"task": item, "status": "pending"} for item in medications
    ],
    "tests": [
        {"task": item, "status": "pending"} for item in tests
    ],
    "follow_ups": [
        {"task": item, "status": "pending"} for item in follow_ups
    ],
    "instructions": [
        {"task": item, "status": "pending"} for item in instructions
    ],
    "restrictions": [
        {"task": item, "status": "pending"} for item in restrictions
    ],
    "status": "active",
    }

def process_visit_into_plan(
    visit_reason: str,
    diagnoses: list[str],
    medications: list[str],
    instructions: list[str],
    follow_ups: list[str],
    tests: list[str],
    restrictions: list[str],
) -> dict:
    """Runs Clara's structured My Plan workflow.

    This combines organized visit information with a deterministic care plan.

    Args:
        visit_reason: Documented reason for the visit.
        diagnoses: Diagnoses or conditions documented.
        medications: Medication-related information documented.
        instructions: Provider instructions documented.
        follow_ups: Follow-up actions documented.
        tests: Tests or orders documented.
        restrictions: Restrictions documented.

    Returns:
        Both the organized visit information and care plan.
    """

    organized = organize_visit_info(
        visit_reason=visit_reason,
        diagnoses=diagnoses,
        medications=medications,
        instructions=instructions,
        follow_ups=follow_ups,
        tests=tests,
        restrictions=restrictions,
    )

    care_plan = create_care_plan(
        medications=medications,
        tests=tests,
        follow_ups=follow_ups,
        instructions=instructions,
        restrictions=restrictions,
    )

    return {
        "visit": organized,
        "care_plan": care_plan,
    }


def save_care_plan(
    user_id: str,
    medications: list[str],
    tests: list[str],
    follow_ups: list[str],
    instructions: list[str],
    restrictions: list[str],
) -> dict:
    """Saves the user's active My Plan to Firestore.

    Only use this tool when the user explicitly asks Clara to save or
    remember their care plan.

    Args:
        user_id: Identifier used for the user's stored care episode.
        medications: Documented medication actions.
        tests: Documented tests to complete.
        follow_ups: Documented follow-up actions.
        instructions: Other documented provider instructions.
        restrictions: Documented restrictions.

    Returns:
        Confirmation that the care plan was stored.
    """

    care_plan = create_care_plan(
    medications=medications,
    tests=tests,
    follow_ups=follow_ups,
    instructions=instructions,
    restrictions=restrictions,
)

    doc_ref = db.collection("care_episodes").document(user_id)

    doc_ref.set(
        {
            "care_plan": care_plan,
            "status": "active",
        },
        merge=True,
    )

    return {
        "saved": True,
        "user_id": user_id,
        "status": "active",
    }
def get_care_plan(user_id: str) -> dict:
    """Retrieves the user's saved active care plan from Firestore.

    Use this when the user asks what they still need to do, asks to see
    their saved My Plan, or asks Clara to remember their current care plan.

    Args:
        user_id: Identifier for the user.

    Returns:
        The saved care plan, or a message if no saved plan exists.
    """
    doc_ref = db.collection("care_episodes").document(user_id)
    doc = doc_ref.get()

    if not doc.exists:
        return {
            "found": False,
            "user_id": user_id,
            "message": "No saved care plan was found.",
        }

    data = doc.to_dict()

    return {
        "found": True,
        "user_id": user_id,
        "status": data.get("status", "unknown"),
        "care_plan": data.get("care_plan", {}),
    }
def update_care_plan_task(
    user_id: str,
    category: str,
    task_name: str,
    status: str,
) -> dict:
    """Updates the status of a task in the user's saved care plan.

    Use when the user says they completed or still need to complete
    a task from their saved My Plan.

    Args:
        user_id: Identifier for the user.
        category: One of medication_actions, tests, follow_ups,
            instructions, or restrictions.
        task_name: The care-plan task to update.
        status: New task status, such as pending or completed.

    Returns:
        Confirmation of whether the task was updated.
    """
    allowed_categories = {
        "medication_actions",
        "tests",
        "follow_ups",
        "instructions",
        "restrictions",
    }

    if category not in allowed_categories:
        return {
            "updated": False,
            "message": f"Unknown care-plan category: {category}",
        }

    if status not in {"pending", "completed"}:
        return {
            "updated": False,
            "message": "Status must be pending or completed.",
        }

    doc_ref = db.collection("care_episodes").document(user_id)
    doc = doc_ref.get()

    if not doc.exists:
        return {
            "updated": False,
            "message": "No saved care plan was found.",
        }

    data = doc.to_dict()
    care_plan = data.get("care_plan", {})
    tasks = care_plan.get(category, [])

    matched = False

    for item in tasks:
        if item["task"].lower() == task_name.lower():
            item["status"] = status
            matched = True
            break

    if not matched:
        return {
            "updated": False,
            "message": f"Task not found: {task_name}",
        }

    care_plan[category] = tasks

    doc_ref.set(
        {"care_plan": care_plan},
        merge=True,
    )

    return {
        "updated": True,
        "task": task_name,
        "status": status,
    }
def create_medication_schedule(
    medications: list[str],
) -> dict:
    """Creates a medication schedule only from documented medication instructions.

    Use this when the user asks about medication timing, schedule, or reminders.

    Args:
        medications: Medication instructions taken from the user's paperwork.

    Returns:
        A structured medication schedule.
    """
    schedule = []

    for item in medications:
        schedule.append(
            {
                "medication": item,
                "status": "needs_review",
            }
        )

    return {
        "medications": schedule,
        "instruction": (
            "Use only documented dose, frequency, and timing. "
            "If timing is not documented, mark it as needing provider confirmation."
        ),
    }

# ---------------------------------------------------------
# CLARA ROOT AGENT
# ---------------------------------------------------------

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""
You are Clara, an AI healthcare navigation agent for everyday people.

Your purpose is to help users understand after-visit summaries, discharge
paperwork, medical instructions, terminology, medications, follow-up
requirements, and recovery expectations in clear, plain English.

MEDICAL SAFETY

- Clara is not a doctor.
- Clara does not diagnose medical conditions.
- Clara does not prescribe medications.
- Clara does not change medication doses, frequency, timing, or provider instructions.
- Clara does not replace a physician or other qualified healthcare professional.
- If a question requires diagnosis, personalized treatment, or changing a medical
  plan, direct the user to an appropriate healthcare professional.

DOCUMENT HANDLING

- When the user uploads an image or PDF of medical paperwork, carefully inspect
  the document and use only information you can confidently read.
- Never guess, reconstruct, or invent text that is blurry, hidden, missing,
  covered, or unreadable.
- Tell the user when information cannot be read clearly.
- Preserve medication names, doses, frequencies, dates, test names,
  restrictions, and follow-up instructions exactly as documented before
  simplifying or explaining them.
- For uploaded medical paperwork, process the readable information using
  extract_visit_sections and organize_visit_info.

SOURCE LABELING

Always distinguish among these categories when relevant:

1. From your paperwork
2. General educational information
3. Ask your provider

- Never present general medical knowledge as though it appeared in the user's paperwork.
- Never invent why a test, medication, restriction, or follow-up was ordered.
- If the document does not give a reason, state that the reason is not provided
  in the paperwork.
- When explaining a medication, first state exactly what the paperwork says.
  Any explanation of what the medication is commonly used for must be labeled
  "General educational information."
- When discussing recovery, food, diet, exercise, or expected symptoms, clearly
  separate provider-specific instructions from general educational information.

PLAIN-ENGLISH EXPLANATION

- Explain medical terminology in everyday language.
- Help organize provider instructions into understandable next steps.
- Use calm, straightforward language.
- Avoid unnecessary medical jargon.
- Clearly explain what is documented without overstating certainty.

MY PLAN

- My Plan contains only actions explicitly supported by the user's paperwork.
- Do not turn diagnoses or background medical history into tasks unless the
  paperwork explicitly tells the patient to take an action.
- My Plan may contain documented medication actions, tests, follow-ups,
  provider instructions, and restrictions.
- When the user asks for "My Plan", "what do I need to do", "next steps",
  "action items", or similar, use process_visit_into_plan.
- Do not invent dates, deadlines, medication changes, appointments,
  restrictions, or other actions.

MEMORY

- Never save medical information automatically.
- Only save a care plan when the user explicitly asks Clara to save or remember it.
- When the user explicitly asks to save or remember My Plan, MUST use
  save_care_plan with user_id "demo-user".
- Pass only documented medications, tests, follow-ups, instructions,
  and restrictions into save_care_plan.
- When the user asks to see their saved My Plan, asks "what do I still need to do?", or asks about previously saved care-plan actions, MUST use get_care_plan with user_id "demo-user".
- Do not ask the user to upload the medical document again if a saved care plan is available in Firestore.
- When the user says they completed, finished, or still need to do a saved care-plan task, use update_care_plan_task with user_id "demo-user".
- Only update tasks that already exist in the saved care plan.
- Use status "completed" when the user says a task is done.
- Use status "pending" when the user says the task still needs to be completed.
- When the user asks "What do I still need to do?", "What is left?", "What is pending?", or similar, show only tasks with status "pending".
- Do not include completed tasks unless the user specifically asks to see completed tasks, task history, or everything in their care plan.

MEDICATION SCHEDULES

- When the user asks for a medication schedule, medication timing, or reminders, use create_medication_schedule.
- Never invent medication timing, frequency, or dose.
- If the paperwork says a dose or frequency, preserve it exactly.
- If the paperwork does not specify when to take a medication, clearly say the timing is not documented and should be confirmed with the provider or pharmacy.

If no medical document or medical information has been provided, explain what
Clara can help with and invite the user to provide an after-visit summary,
discharge paperwork, or other medical instructions.
""",
    tools=[
        extract_visit_sections,
        organize_visit_info,
        create_care_plan,
        process_visit_into_plan,
        save_care_plan,
        get_care_plan,
        update_care_plan_task,
        create_medication_schedule,
    ],
)


# ---------------------------------------------------------
# ADK APPLICATION
# ---------------------------------------------------------

app = App(
    root_agent=root_agent,
    name="app",
)