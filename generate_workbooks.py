import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

WORKBOOK_DIR = os.path.join(os.path.dirname(__file__), "products", "workbooks")
os.makedirs(WORKBOOK_DIR, exist_ok=True)

# Color Palette
PRIMARY = colors.HexColor("#16202C")     # Deep Charcoal Navy
ACCENT = colors.HexColor("#A87432")      # Polished Bronze / Amber
SECONDARY = colors.HexColor("#2B3D4F")   # Medium Slate Navy
MUTED_BG = colors.HexColor("#F7F5F0")    # Warm Sand / Ivory Cream
BORDER_COLOR = colors.HexColor("#D8CEBF")# Elegant Border Cream
TEXT_MAIN = colors.HexColor("#1A1A1A")   # Ink Dark
TEXT_MUTED = colors.HexColor("#555555")  # Charcoal Subdued
WHITE = colors.HexColor("#FFFFFF")
HIGHLIGHT_BOX = colors.HexColor("#ECE7DD")# Card Background

class NumberedCanvas(canvas.Canvas):
    """Adds professional running headers and footers with page numbers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#777777"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "THE INSTINCTIVE TRUST SKILL — 5-DAY ACTION PLAN")
            self.drawRightString(612 - 54, 750, "SAI SHIVARAJUU M")
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)

        # Footer
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)
        self.drawString(54, 32, "Confidential Action Plan · For Personal Implementation")
        page_str = f"Day Action Plan · Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 32, page_str)
        self.restoreState()


def get_custom_styles():
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=21,
        textColor=PRIMARY,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=ACCENT,
        spaceAfter=8
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=6,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'MainBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=TEXT_MAIN,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=TEXT_MAIN,
        leftIndent=10,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=SECONDARY,
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=WHITE
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=TEXT_MAIN
    )

    return {
        'title': title_style,
        'subtitle': subtitle_style,
        'h1': h1_style,
        'body': body_style,
        'bullet': bullet_style,
        'callout': callout_style,
        'th': table_header_style,
        'td': table_cell_style
    }


def make_callout(text, styles, width=518):
    p = Paragraph(f"<b>CORE LAW:</b> {text}", styles['callout'])
    t = Table([[p]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HIGHLIGHT_BOX),
        ('BOX', (0, 0), (-1, -1), 1, ACCENT),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def make_action_box(title, exercises, styles, width=518):
    flowables = []
    flowables.append(Paragraph(f"<b>{title}</b>", styles['h1']))
    for ex in exercises:
        box_check = "<b>[ &nbsp; ]</b> &nbsp; "
        flowables.append(Paragraph(f"{box_check}<b>{ex['name']}</b>: {ex['desc']}", styles['bullet']))
    
    t = Table([[flowables]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), MUTED_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, BORDER_COLOR),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def make_reflection_table(rows, styles, width=518):
    data = [[
        Paragraph("<b>Reflection Field / Checkpoint</b>", styles['th']),
        Paragraph("<b>My Field Observations & Honest Notes</b>", styles['th'])
    ]]
    for label, prompt in rows:
        cell_l = Paragraph(f"<b>{label}</b><br/><font color='#666666'>{prompt}</font>", styles['td'])
        cell_r = Paragraph("<br/><br/>", styles['td'])
        data.append([cell_l, cell_r])
    
    t = Table(data, colWidths=[190, 328])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0, 1), (0, -1), MUTED_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
    ]))
    return t


DAYS_DATA = [
    {
        "day": 1,
        "title": "DAY 1: Anchoring Your Baseline & Radical Predictability",
        "subtitle": "Companion Action Plan to The Instinctive Trust Skill · Chapter 1, 2 & Step 1",
        "core_law": "Confidence is not a loud performance; it is radical predictability. When your physical baseline is calm and devoid of erratic micro-movements, other nervous systems instantly register you as safe and capable.",
        "why_it_matters": "When people meet you, their primal threat-detection system scans you in milliseconds. Sudden head tilts, jerky pacing, and darting eyes signal unpredictability. Today, your sole objective is to strip away involuntary erratic noise so your presence becomes clear, calm, and grounded.",
        "exercises": [
            {
                "name": "The 3-Second Threshold Pause",
                "desc": "Before crossing any doorway (office, meeting room, client lobby, or home), stop completely for 3 seconds. Take one steady breath, relax your shoulders down, and step in with measured pacing."
            },
            {
                "name": "Eliminate the Erratic Eyeline",
                "desc": "When speaking or listening, resist the impulse to dart your eyes to the floor or phone when searching for words. Hold a calm triangle focus (between the eyes and forehead), or look gently away at horizontal level."
            },
            {
                "name": "Pacing Decelerator Drill",
                "desc": "Consciously slow your walking speed by 15% during transit between tasks. Move with intent. Observe how an unhurried tempo changes the way people part and acknowledge you."
            },
            {
                "name": "Stillness in Inaction",
                "desc": "When waiting in an elevator, line, or sitting in a meeting lobby, do NOT pull out your phone immediately. Stand or sit with quiet, balanced stillness for 2 uninterrupted minutes."
            }
        ],
        "reflections": [
            ("Doorway Transitions", "Did I pause before entering high-stakes or common rooms? What internal urge did I feel?"),
            ("Physical Stillness vs. Urgency", "Where did I catch myself moving too quickly or fidgeting? How did pausing change my internal state?"),
            ("Others' Reaction", "Did people seem more relaxed or attentive when I maintained a steady, predictable baseline?")
        ]
    },
    {
        "day": 2,
        "title": "DAY 2: Open Demeanor & Territory Expansion",
        "subtitle": "Companion Action Plan to The Instinctive Trust Skill · Step 2 & Step 3",
        "core_law": "Insecurity compresses; instinctive trust expands. When you retract your elbows, clutch objects against your chest, or shrink your posture, you communicate defensive fear. Claiming your territory without aggression projects natural authority.",
        "why_it_matters": "Trust is earned when you show that you do not fear your environment. Defensive barriers (crossing arms over your vital organs, hunching over laptops, holding coffees like body armor) tell everyone in the room that you feel vulnerable. Today, you open your frame.",
        "exercises": [
            {
                "name": "Torso Shield Audit",
                "desc": "Catch yourself holding notebooks, phones, or beverages directly against your heart and chest. Move them down to hip level or set them on the table. Keep your chest and throat plane completely unobstructed."
            },
            {
                "name": "The 15% Territory Expansion",
                "desc": "When seated at a conference table, desk, or cafe, place your forearms gently on the table with elbows spaced at comfortable shoulder width. Do not pull your limbs inward toward your centerline."
            },
            {
                "name": "Shoulder-Blade Anchor",
                "desc": "Three times today (morning, midday, afternoon), roll your shoulders up, back, and gently lock them down into their natural pockets. Lengthen the back of your neck by tucking your chin half an inch."
            },
            {
                "name": "Uncrossing the Baseline",
                "desc": "During listening periods in meetings or casual dialogue, plant both feet flat on the floor with ankles uncrossed. Feel the physical floor anchoring your weight."
            }
        ],
        "reflections": [
            ("Shielding Tendencies", "What objects was I unconsciously using as shields (coffee cup, phone, folder)? When did this occur?"),
            ("Seated Comfort & Space", "How did it feel to occupy a relaxed, expanded footprint at the table? Did it change my vocal projection?"),
            ("Perceived Authority", "Did people interrupt less or yield more conversational room when my posture remained open?")
        ]
    },
    {
        "day": 3,
        "title": "DAY 3: Gesture Mastery & Calming Stress Tells",
        "subtitle": "Companion Action Plan to The Instinctive Trust Skill · Step 5 & Step 7",
        "core_law": "Your hands are the truth-tellers of your nervous system. Fidgeting, neck-touching, and clasping betray tension, while deliberate, palm-visible gestures inside your power zone command immediate credibility.",
        "why_it_matters": "Evolutionary psychology reveals that human brains must see the hands to assess trustworthiness. Hiding your hands in pockets, clasping them behind your back, or engaging in pacifying behaviors (rubbing the nape of your neck, twisting rings) quietly torpedoes your message.",
        "exercises": [
            {
                "name": "The Navel-to-Sternum Power Zone",
                "desc": "Confine all speaking hand gestures to the box between your navel and sternum. Avoid erratic flailing above shoulder height or dropping hands lifelessly to your sides."
            },
            {
                "name": "Open Palm Delivery",
                "desc": "When presenting an idea, making a proposal, or explaining a problem, show open palms at 45-degree angles. This physiological signal denotes transparency and non-threat."
            },
            {
                "name": "Pacifying Behavior Ban",
                "desc": "Identify your primary nervous tic: collar adjustment, ring twisting, beard/hair stroking, leg bouncing. The instant you catch yourself, freeze the hand and place it calmly flat on your thigh or the desk."
            },
            {
                "name": "The 5-Minute Still Hands Challenge",
                "desc": "In one conversation or meeting today, keep your hands entirely resting in a relaxed clasp or flat on the table while listening. Do not touch a pen, hair, or phone for 5 full minutes."
            }
        ],
        "reflections": [
            ("My Primary Stress Tell", "What was the exact physical pacifying movement I caught myself doing when under pressure?"),
            ("Gesture Precision", "Did anchoring my gestures in the navel-to-sternum zone make my speech clearer and more deliberate?"),
            ("Internal Calmness", "How quickly did the urge to fidget disappear once I physically stilled my hands?")
        ]
    },
    {
        "day": 4,
        "title": "DAY 4: Reading Others & Disarming Confrontation",
        "subtitle": "Companion Action Plan to The Instinctive Trust Skill · Step 6, 8 & Step 9",
        "core_law": "When tension rises, amateurs match heat with heat; masters de-escalate with rhythm. By spotting baseline deviations in others and decelerating your response time, you control the emotional temperature of any room.",
        "why_it_matters": "Trust is tested in disagreement. If a colleague, client, or partner becomes tense, matching their elevated pitch or accelerated tempo sparks confrontation. Today you practice stepping into their emotional river without getting swept away.",
        "exercises": [
            {
                "name": "Baseline-Deviation Spotting",
                "desc": "Observe a colleague or partner for their normal rhythm (speech speed, blink rate, posture). Notice the exact moment a sensitive topic causes a micro-deviation: sudden throat-clearing, foot-shifting, or vocal pitch rise."
            },
            {
                "name": "The 2-Second Decelerator",
                "desc": "When asked a difficult question, interrupted, or met with friction, wait 2 full seconds before uttering a single word. Look the speaker in the eye with calm curiosity. Never rush to defend."
            },
            {
                "name": "Volume & Pitch Downshift",
                "desc": "If someone raises their voice, speaks rapidly, or bristles with frustration, deliberately lower your vocal pitch by half an octave and reduce your volume by 10%. They will subconsciously regulate down to match you."
            },
            {
                "name": "Validate Before Steering",
                "desc": "Before offering a counterpoint, repeat back the core emotion: 'It sounds like this timeline is putting massive pressure on the team. Let's look at what we can protect.' Align before you redirect."
            }
        ],
        "reflections": [
            ("Observed Deviations", "What physical cue did I notice in someone else that indicated tension before they even spoke?"),
            ("The 2-Second Pause Effect", "How did the other person react when I didn't snap back with an immediate answer?"),
            ("De-escalation Outcome", "Did lowering my pitch and volume help take the heat out of a potential disagreement?")
        ]
    },
    {
        "day": 5,
        "title": "DAY 5: Somatic Rehearsal & The 30-Day Integration",
        "subtitle": "Companion Action Plan to The Instinctive Trust Skill · Step 10 & Part V",
        "core_law": "You do not rise to the occasion under pressure; you sink to the level of your somatic preparation. Rehearsing your physical posture and emotional stillness before entering the arena locks the skill into your nervous system.",
        "why_it_matters": "A skill unpracticed under simulated friction quickly evaporates. To make Instinctive Trust your permanent default, you must combine mental emulation with a sustainable daily ritual that carries forward over the next 30 days.",
        "exercises": [
            {
                "name": "The 3-Minute Pre-Performance Rehearsal",
                "desc": "Before an important call, interview, or social interaction, close your eyes and mentally walk through the scenario in real time. Visualize your calm posture, the doorway pause, your steady voice, and your unhurried response to surprises."
            },
            {
                "name": "Emulate Your Exemplar",
                "desc": "Choose a historical or real-world leader known for unflappable gravitas. Identify 2 specific micro-behaviors they embody (e.g., slow head turns, steady deep breathing). Adopt those 2 cues today."
            },
            {
                "name": "Weekly Audit Commitment",
                "desc": "Schedule a recurring 15-minute appointment with yourself every Sunday to review your stress tells, territory expansion, and conversational pacing."
            },
            {
                "name": "The Instinctive Trust Pledge",
                "desc": "Sign and date your personal declaration to practice these behavioral standards consistently, choosing calm clarity over reactive impulse."
            }
        ],
        "reflections": [
            ("Rehearsal Impact", "Did mentally visualizing my calm baseline improve my real-time composure when things got busy?"),
            ("My Chosen Exemplar", "Who did I model today, and what specific physical habit did I adopt?"),
            ("Next 30-Day Milestone", "What is the single most critical trust behavior I will practice every single day this month?")
        ]
    }
]


def generate_single_day_pdf(day_data, filename):
    filepath = os.path.join(WORKBOOK_DIR, filename)
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = get_custom_styles()
    story = []
    
    # Title & Subtitle
    story.append(Paragraph(day_data["title"], styles['title']))
    story.append(Paragraph(day_data["subtitle"], styles['subtitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=1, spaceAfter=8))
    
    # Core Law
    story.append(make_callout(day_data["core_law"], styles, width=522))
    story.append(Spacer(1, 8))
    
    # Why It Matters
    story.append(Paragraph("<b>THE PRINCIPLE IN PRACTICE</b>", styles['h1']))
    story.append(Paragraph(day_data["why_it_matters"], styles['body']))
    story.append(Spacer(1, 6))
    
    # Action Exercises Box
    story.append(make_action_box("DAILY ACTION PROTOCOLS (CHECK OFF AS COMPLETED)", day_data["exercises"], styles, width=522))
    story.append(Spacer(1, 8))
    
    # Reflection Table
    story.append(Paragraph("<b>FIELD DEBRIEF & INTROSPECTION WORKSHEET</b>", styles['h1']))
    story.append(Paragraph("Complete these questions at the end of Day " + str(day_data["day"]) + " to solidify behavioral gains:", styles['body']))
    story.append(Spacer(1, 4))
    story.append(make_reflection_table(day_data["reflections"], styles, width=522))
    
    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated: {filepath} ({os.path.getsize(filepath)} bytes)")
    return filepath


def generate_master_workbook():
    filepath = os.path.join(WORKBOOK_DIR, "5_Day_Master_Workbook_Action_Plan.pdf")
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = get_custom_styles()
    story = []
    
    # Cover / Master Title Page
    story.append(Spacer(1, 30))
    master_title = ParagraphStyle(
        'MasterTitle',
        parent=styles['title'],
        fontSize=26,
        leading=32,
        textColor=PRIMARY,
        alignment=1 # Center
    )
    master_sub = ParagraphStyle(
        'MasterSub',
        parent=styles['subtitle'],
        fontSize=13,
        leading=18,
        textColor=ACCENT,
        alignment=1
    )
    story.append(Paragraph("THE INSTINCTIVE TRUST SKILL", master_title))
    story.append(Spacer(1, 8))
    story.append(Paragraph("5-DAY ACCELERATED ACTION PLAN & WORKBOOK", master_sub))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Sai Shivarajuu M</b> · Author Edition", styles['callout']))
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="80%", thickness=2, color=ACCENT, spaceBefore=10, spaceAfter=20))
    
    overview_text = (
        "This 5-Day Action Plan is the direct execution companion to <i>The Instinctive Trust Skill</i>. "
        "Knowledge without somatic drill is merely philosophy. Each day targets one physiological domain "
        "of high-trust presence: stillness, space, gesture control, behavioral calibration, and mental rehearsal. "
        "Use this master edition to track your complete journey from baseline to effortless instinct."
    )
    story.append(Paragraph(overview_text, styles['body']))
    story.append(Spacer(1, 25))
    
    overview_box = [
        [Paragraph("<b>Day</b>", styles['th']), Paragraph("<b>Core Theme</b>", styles['th']), Paragraph("<b>Primary Skill Outcome</b>", styles['th'])],
        [Paragraph("<b>Day 1</b>", styles['td']), Paragraph("Anchoring Your Baseline", styles['td']), Paragraph("Eliminate nervous eye-darting and erratic doorway transitions", styles['td'])],
        [Paragraph("<b>Day 2</b>", styles['td']), Paragraph("Open Demeanor & Territory", styles['td']), Paragraph("Drop defensive torso shielding; expand seated presence by 15%", styles['td'])],
        [Paragraph("<b>Day 3</b>", styles['td']), Paragraph("Gesture Mastery & Tells", styles['td']), Paragraph("Confine gestures to power box; arrest subconscious pacifiers", styles['td'])],
        [Paragraph("<b>Day 4</b>", styles['td']), Paragraph("Reading Others & Disarming", styles['td']), Paragraph("Spot baseline shifts; de-escalate tension via 2-second pause", styles['td'])],
        [Paragraph("<b>Day 5</b>", styles['td']), Paragraph("Rehearsal & Integration", styles['td']), Paragraph("Somatic visualization protocol; lock in the 30-day ritual", styles['td'])],
    ]
    t = Table(overview_box, colWidths=[60, 160, 284])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(PageBreak())
    
    # Append Each Day
    for idx, day_data in enumerate(DAYS_DATA):
        story.append(Paragraph(day_data["title"], styles['title']))
        story.append(Paragraph(day_data["subtitle"], styles['subtitle']))
        story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=2, spaceAfter=14))
        
        story.append(make_callout(day_data["core_law"], styles))
        story.append(Spacer(1, 14))
        
        story.append(Paragraph("<b>THE PRINCIPLE IN PRACTICE</b>", styles['h1']))
        story.append(Paragraph(day_data["why_it_matters"], styles['body']))
        story.append(Spacer(1, 12))
        
        story.append(make_action_box("DAILY ACTION PROTOCOLS (CHECK OFF AS COMPLETED)", day_data["exercises"], styles))
        story.append(Spacer(1, 14))
        
        story.append(Paragraph("<b>FIELD DEBRIEF & INTROSPECTION WORKSHEET</b>", styles['h1']))
        story.append(Paragraph("Complete these questions at the end of Day " + str(day_data["day"]) + " to solidify behavioral gains:", styles['body']))
        story.append(Spacer(1, 6))
        story.append(make_reflection_table(day_data["reflections"], styles))
        
        if idx < len(DAYS_DATA) - 1:
            story.append(PageBreak())

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated Master Workbook: {filepath} ({os.path.getsize(filepath)} bytes)")
    return filepath


def main():
    print("=== Generating 5-Day Action Plan PDFs ===")
    for day in DAYS_DATA:
        filename = f"Day_{day['day']}_Workbook_Action_Plan.pdf"
        generate_single_day_pdf(day, filename)
    
    print("\n=== Generating Master 5-Day Workbook PDF ===")
    generate_master_workbook()
    print("\nAll workbooks generated successfully!")

if __name__ == "__main__":
    main()
