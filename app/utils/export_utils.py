import re
import pandas as pd
from fpdf import FPDF


def safe_text(s: str) -> str:
    if s is None:
        return ""

    s = str(s)
    s = s.replace("\n", " ").replace("\r", " ")

    # remove unsupported unicode
    s = s.encode("latin-1", "ignore").decode("latin-1")

    # remove zero-width characters (these cause the crash)
    s = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", s)

    # break long words/urls
    s = re.sub(r"(\S{40})", r"\1 ", s)

    # normalize spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s


def pdf_line(pdf: FPDF, text: str, ln: int = 6):
    """
    Safe line writer (never crashes).
    """
    text = safe_text(text)

    if not text:
        pdf.ln(ln)
        return

    # write safely
    pdf.write(ln, text)
    pdf.ln(ln)


def export_tasks_csv(action_items: list, filepath: str):
    df = pd.DataFrame(action_items)
    cols = ["task", "owner", "due_date", "priority", "confidence"]
    df = df[[c for c in cols if c in df.columns]]
    df.to_csv(filepath, index=False)


def export_minutes_pdf(data: dict, filepath: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(12)
    pdf.set_right_margin(12)

    pdf.set_font("Arial", "B", 14)
    pdf_line(pdf, "Meeting Minutes", ln=8)

    title = data.get("meeting_title") or "Untitled Meeting"
    date = data.get("date") or "N/A"

    pdf.set_font("Arial", size=12)
    pdf_line(pdf, f"Title: {title}")
    pdf_line(pdf, f"Date: {date}")
    pdf.ln(2)

    # Summary
    pdf.set_font("Arial", "B", 12)
    pdf_line(pdf, "Summary:", ln=7)

    pdf.set_font("Arial", size=12)
    pdf_line(pdf, data.get("summary", ""))
    pdf.ln(2)

    # Decisions
    pdf.set_font("Arial", "B", 12)
    pdf_line(pdf, "Decisions:", ln=7)

    pdf.set_font("Arial", size=12)
    decisions = data.get("decisions", [])
    if decisions:
        for d in decisions:
            pdf_line(pdf, f"- {d}")
    else:
        pdf_line(pdf, "- No decisions found.")
    pdf.ln(2)

    # Action Items
    pdf.set_font("Arial", "B", 12)
    pdf_line(pdf, "Action Items:", ln=7)

    pdf.set_font("Arial", size=12)
    action_items = data.get("action_items", [])
    if action_items:
        for a in action_items:
            task = a.get("task", "")
            owner = a.get("owner") or "Unassigned"
            due = a.get("due_date") or "N/A"
            pr = a.get("priority") or "Medium"
            conf = a.get("confidence", "")

            pdf_line(pdf, f"- {task}")
            pdf_line(pdf, f"  Owner: {owner} | Due: {due} | Priority: {pr} | Confidence: {conf}")
            pdf.ln(1)
    else:
        pdf_line(pdf, "- No action items found.")
    pdf.ln(2)

    # Risks
    pdf.set_font("Arial", "B", 12)
    pdf_line(pdf, "Risks / Blockers:", ln=7)

    pdf.set_font("Arial", size=12)
    risks = data.get("risks_or_blockers", [])
    if risks:
        for r in risks:
            pdf_line(pdf, f"- {r}")
    else:
        pdf_line(pdf, "- None")

    pdf.output(filepath)
