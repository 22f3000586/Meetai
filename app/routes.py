import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from app.utils.llm_extractor import extract_meeting_data
import os
from app.utils.export_utils import export_minutes_pdf, export_tasks_csv
from werkzeug.utils import secure_filename
from app.utils.whisper_transcriber import transcribe_audio
from app.utils.text_cleaner import clean_transcript



from app import db
from app.models import Meeting

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")

@main_bp.route("/export/pdf/<int:meeting_id>")
def export_pdf(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    data = json.loads(meeting.extracted_json)

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    export_dir = os.path.join(project_root, "exports")
    os.makedirs(export_dir, exist_ok=True)

    filename = f"meeting_{meeting_id}.pdf"
    filepath = os.path.join(export_dir, filename)

    export_minutes_pdf(data, filepath)
    return send_file(filepath, as_attachment=True)



@main_bp.route("/export/csv/<int:meeting_id>")
def export_csv(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    data = json.loads(meeting.extracted_json)

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    export_dir = os.path.join(project_root, "exports")
    os.makedirs(export_dir, exist_ok=True)

    filename = f"tasks_{meeting_id}.csv"
    filepath = os.path.join(export_dir, filename)

    export_tasks_csv(data.get("action_items", []), filepath)
    return send_file(filepath, as_attachment=True)


@main_bp.route("/process", methods=["POST"])
def process():
    title = request.form.get("title", "").strip()
    transcript = request.form.get("transcript", "").strip()
    audio = request.files.get("audio")

    final_transcript = ""

    # ✅ CASE 1: audio upload
    if audio and audio.filename:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        upload_dir = os.path.join(project_root, "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        filename = secure_filename(audio.filename)
        audio_path = os.path.join(upload_dir, filename)
        audio.save(audio_path)

        try:
            final_transcript = transcribe_audio(audio_path)
        except Exception as e:
            flash(f"Whisper transcription failed: {str(e)}")
            return redirect(url_for("main.index"))

    # ✅ CASE 2: transcript pasted
    elif transcript:
        final_transcript = transcript

    else:
        flash("Please upload audio or paste transcript.")
        return redirect(url_for("main.index"))

    # clean transcript
    final_transcript = clean_transcript(final_transcript)

    try:
        data = extract_meeting_data(final_transcript)
    except Exception as e:
        flash(f"Extraction failed: {str(e)}")
        return redirect(url_for("main.index"))

    if title:
        data["meeting_title"] = title

    meeting = Meeting(
        title=title if title else None,
        transcript=final_transcript,
        extracted_json=json.dumps(data, ensure_ascii=False),
    )
    db.session.add(meeting)
    db.session.commit()

    return redirect(url_for("main.result", meeting_id=meeting.id))


@main_bp.route("/result/<int:meeting_id>")
def result(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    data = json.loads(meeting.extracted_json)
    return render_template("result.html", data=data, transcript=meeting.transcript, meeting=meeting)



@main_bp.route("/history")
def history():
    meetings = Meeting.query.order_by(Meeting.created_at.desc()).all()
    return render_template("history.html", meetings=meetings)

@main_bp.route("/update/<int:meeting_id>", methods=["POST"])
def update_meeting(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)

    data = json.loads(meeting.extracted_json)

    # Update meeting title from form (optional)
    new_title = request.form.get("meeting_title", "").strip()

    if new_title:
        data["meeting_title"] = new_title
        meeting.title = new_title
    else:
        data["meeting_title"] = None
        meeting.title = None




    # Update action items
    updated_items = []
    action_items = data.get("action_items", [])

    for i in range(len(action_items)):
        task = request.form.get(f"task_{i}", "").strip()
        owner = request.form.get(f"owner_{i}", "").strip()
        due_date = request.form.get(f"due_date_{i}", "").strip()
        priority = request.form.get(f"priority_{i}", "").strip()
        status = request.form.get(f"status_{i}", "").strip()


        # keep safe defaults
        if not task:
            task = action_items[i].get("task", "")

        updated_items.append({
            **action_items[i],
            "task": task,
            "owner": owner if owner else None,
            "due_date": due_date if due_date else None,
            "priority": priority if priority else action_items[i].get("priority", "Medium"),
            "status": status if status else action_items[i].get("status", "To Do"),

        })

    data["action_items"] = updated_items

    # Save back to DB
    meeting.extracted_json = json.dumps(data, ensure_ascii=False)
    db.session.commit()

    flash("✅ Changes saved successfully!")
    return redirect(url_for("main.result", meeting_id=meeting.id))


@main_bp.route("/api/task/status/<int:meeting_id>/<int:task_index>", methods=["POST"])
def api_update_task_status(meeting_id, task_index):
    meeting = Meeting.query.get_or_404(meeting_id)
    data = json.loads(meeting.extracted_json)

    payload = request.get_json(silent=True) or {}
    new_status = payload.get("status")

    allowed = ["Backlog", "To Do", "In Progress", "Done"]
    if new_status not in allowed:
        return {"ok": False, "error": "Invalid status"}, 400

    action_items = data.get("action_items", [])
    if task_index < 0 or task_index >= len(action_items):
        return {"ok": False, "error": "Invalid task index"}, 400

    action_items[task_index]["status"] = new_status
    data["action_items"] = action_items

    meeting.extracted_json = json.dumps(data, ensure_ascii=False)
    db.session.commit()

    return {"ok": True}

@main_bp.route("/api/task/add/<int:meeting_id>", methods=["POST"])
def api_add_task(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    data = json.loads(meeting.extracted_json)

    payload = request.get_json(silent=True) or {}

    task = (payload.get("task") or "").strip()
    owner = (payload.get("owner") or "").strip()
    due_date = (payload.get("due_date") or "").strip()
    priority = (payload.get("priority") or "Medium").strip()
    status = (payload.get("status") or "To Do").strip()

    if not task:
        return {"ok": False, "error": "Task is required"}, 400

    allowed_priority = ["Low", "Medium", "High"]
    allowed_status = ["Backlog", "To Do", "In Progress", "Done"]

    if priority not in allowed_priority:
        priority = "Medium"
    if status not in allowed_status:
        status = "To Do"

    new_item = {
        "task": task,
        "owner": owner if owner else None,
        "due_date_text": None,
        "due_date": due_date if due_date else None,
        "priority": priority,
        "confidence": 0.9,   # user-added task, confidence high
        "status": status
    }

    if "action_items" not in data or not isinstance(data["action_items"], list):
        data["action_items"] = []

    data["action_items"].append(new_item)

    meeting.extracted_json = json.dumps(data, ensure_ascii=False)
    db.session.commit()

    return {"ok": True}
