#!/usr/bin/env python3
"""
Generate a 12-Slide Academic Defense Presentation for SOU Pichchomrong
Degree of Bachelor in Applied Mathematics and Statistics (I4 AMS), ITC
Defense Date: October 31, 2026
Format: 16:9 Widescreen PowerPoint (.pptx)
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

# -------------------------------------------------------------
# Color Palette Constants (Academic Royal Navy & Slate Theme)
# -------------------------------------------------------------
NAVY_PRIMARY    = RGBColor(11, 37, 69)      # #0B2545 - Deep Royal Navy
NAVY_SECONDARY  = RGBColor(19, 64, 116)     # #134074 - Slate Navy
COBALT_ACCENT   = RGBColor(0, 80, 157)      # #00509D - Vibrant Academic Blue
BG_LIGHT        = RGBColor(248, 249, 250)   # #F8F9FA - Ultra-light Slate
CARD_BG_WHITE   = RGBColor(255, 255, 255)   # #FFFFFF - Crisp Card White
CARD_BG_TINT    = RGBColor(240, 244, 248)   # #F0F4F8 - Soft Blue Card Tint
CARD_BORDER     = RGBColor(218, 224, 233)   # #DAE0E9 - Border Grey
TEXT_DARK       = RGBColor(33, 37, 41)      # #212529 - Charcoal Text
TEXT_MUTED      = RGBColor(108, 117, 125)   # #6C757D - Muted Grey
GOLD_ACCENT     = RGBColor(202, 138, 4)     # #CA8A04 - Amber Gold for Highlights
SUCCESS_GREEN   = RGBColor(22, 101, 52)     # #166534 - Forest Green for Wins
HEADER_BAR_BLUE = RGBColor(14, 43, 82)      # Top banner color

FONT_TITLE = "Calibri"
FONT_BODY  = "Calibri"

def set_slide_background(slide, color=BG_LIGHT):
    """Fills the slide background with a solid color."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_header(slide, title_text, category_text, slide_num, total_slides=12):
    """Creates a consistent, executive academic header with category and slide numbering."""
    # Top thin accent line
    accent = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.1)
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = COBALT_ACCENT
    accent.line.fill.background()

    # Header container
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.25), Inches(10.0), Inches(1.05))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    # Category breadcrumb
    p_cat = tf.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.name = FONT_TITLE
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COBALT_ACCENT
    p_cat.space_after = Pt(2)

    # Main slide title
    p_title = tf.add_paragraph()
    p_title.text = title_text
    p_title.font.name = FONT_TITLE
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = NAVY_PRIMARY

    # Slide number badge (top right)
    badge = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(11.2), Inches(0.35), Inches(1.35), Inches(0.42)
    )
    badge.fill.solid()
    badge.fill.fore_color.rgb = CARD_BG_TINT
    badge.line.color.rgb = CARD_BORDER
    badge.line.width = Pt(1)
    btf = badge.text_frame
    btf.margin_left = btf.margin_right = btf.margin_top = btf.margin_bottom = 0
    bp = btf.paragraphs[0]
    bp.alignment = PP_ALIGN.CENTER
    bp.text = f"{slide_num:02d} / {total_slides:02d}"
    bp.font.name = FONT_BODY
    bp.font.size = Pt(11)
    bp.font.bold = True
    bp.font.color.rgb = NAVY_SECONDARY

def add_card(slide, left, top, width, height, bg_color=CARD_BG_WHITE, border_color=CARD_BORDER):
    """Draws a clean modern rounded card container."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
    else:
        card.line.fill.background()
    return card

def add_bullet_point(tf, title, body="", level=0, bold_title=True, font_size=13, space_after=8):
    """Adds a structured bullet point with optional bold lead-in."""
    p = tf.add_paragraph() if len(tf.paragraphs[0].text) > 0 else tf.paragraphs[0]
    p.level = level
    p.space_after = Pt(space_after)

    run_title = p.add_run()
    run_title.text = title
    run_title.font.name = FONT_BODY
    run_title.font.size = Pt(font_size)
    run_title.font.bold = bold_title
    run_title.font.color.rgb = TEXT_DARK

    if body:
        run_body = p.add_run()
        run_body.text = f" {body}"
        run_body.font.name = FONT_BODY
        run_body.font.size = Pt(font_size)
        run_body.font.bold = False
        run_body.font.color.rgb = TEXT_DARK

# -------------------------------------------------------------
# Main Slide Generation Function
# -------------------------------------------------------------
def build_presentation(output_path="docs/presentation/I4_Internship_Defense_Presentation.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    base_img_path = "docs/i4_thesis_report/LaTeX_Thesis_Template/images"
    itc_logo = os.path.join(base_img_path, "schools/itc.png")
    ams_logo = os.path.join(base_img_path, "schools/ams.png")

    # =========================================================
    # SLIDE 1: Title Slide (Cover)
    # =========================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, BG_LIGHT)

    # Top dark navy banner
    banner = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.3))
    banner.fill.solid()
    banner.fill.fore_color.rgb = HEADER_BAR_BLUE
    banner.line.fill.background()

    # Logos on banner
    if os.path.exists(itc_logo):
        s1.shapes.add_picture(itc_logo, Inches(0.8), Inches(0.18), height=Inches(0.95))
    if os.path.exists(ams_logo):
        s1.shapes.add_picture(ams_logo, Inches(11.5), Inches(0.18), height=Inches(0.95))

    # Banner institutional text
    tb_inst = s1.shapes.add_textbox(Inches(2.0), Inches(0.25), Inches(9.3), Inches(0.85))
    tf_inst = tb_inst.text_frame
    tf_inst.word_wrap = True
    p_inst1 = tf_inst.paragraphs[0]
    p_inst1.alignment = PP_ALIGN.CENTER
    p_inst1.text = "INSTITUTE OF TECHNOLOGY OF CAMBODIA"
    p_inst1.font.name = FONT_TITLE
    p_inst1.font.size = Pt(14)
    p_inst1.font.bold = True
    p_inst1.font.color.rgb = RGBColor(255, 255, 255)

    p_inst2 = tf_inst.add_paragraph()
    p_inst2.alignment = PP_ALIGN.CENTER
    p_inst2.text = "FACULTY OF APPLIED SCIENCE • DEPARTMENT OF APPLIED MATHEMATICS AND STATISTICS"
    p_inst2.font.name = FONT_BODY
    p_inst2.font.size = Pt(11)
    p_inst2.font.color.rgb = RGBColor(218, 224, 233)

    # Main Title Card
    add_card(s1, Inches(0.8), Inches(1.6), Inches(11.733), Inches(3.2), CARD_BG_WHITE, CARD_BORDER)

    tb_title = s1.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(11.1), Inches(2.7))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True

    p_badge = tf_title.paragraphs[0]
    p_badge.alignment = PP_ALIGN.CENTER
    p_badge.text = "ENGINEERING INTERNSHIP DEFENSE (I4 AMS)"
    p_badge.font.name = FONT_TITLE
    p_badge.font.size = Pt(12)
    p_badge.font.bold = True
    p_badge.font.color.rgb = COBALT_ACCENT
    p_badge.space_after = Pt(8)

    p_main = tf_title.add_paragraph()
    p_main.alignment = PP_ALIGN.CENTER
    p_main.text = "End-to-End Data Engineering & Time-Series Forecasting\nof International Trade Logistics"
    p_main.font.name = FONT_TITLE
    p_main.font.size = Pt(28)
    p_main.font.bold = True
    p_main.font.color.rgb = NAVY_PRIMARY
    p_main.space_after = Pt(10)

    p_sub = tf_title.add_paragraph()
    p_sub.alignment = PP_ALIGN.CENTER
    p_sub.text = "A 2-Tier Star Schema Data Warehouse, Automated Airflow ETL, Outlier-Treated Holt-Winters Forecasting & Interactive Streamlit Telemetry"
    p_sub.font.name = FONT_BODY
    p_sub.font.size = Pt(13)
    p_sub.font.italic = True
    p_sub.font.color.rgb = TEXT_MUTED

    # Bottom Metadata Cards (Presenter, Advisor, Supervisor, Date)
    col_w = Inches(3.75)
    gap = Inches(0.24)
    y_card = Inches(5.0)
    h_card = Inches(2.05)

    # Card 1: Candidate
    add_card(s1, Inches(0.8), y_card, col_w, h_card, CARD_BG_WHITE, CARD_BORDER)
    tb_c1 = s1.shapes.add_textbox(Inches(1.0), y_card + Inches(0.15), col_w - Inches(0.4), h_card - Inches(0.3))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    p = tf_c1.paragraphs[0]
    p.text = "CANDIDATE / PRESENTER"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COBALT_ACCENT
    p.space_after = Pt(4)
    p2 = tf_c1.add_paragraph()
    p2.text = "SOU Pichchomrong"
    p2.font.size = Pt(15)
    p2.font.bold = True
    p2.font.color.rgb = NAVY_PRIMARY
    p3 = tf_c1.add_paragraph()
    p3.text = "Degree of Bachelor in Applied Mathematics and Statistics (AMS)"
    p3.font.size = Pt(11)
    p3.font.color.rgb = TEXT_MUTED

    # Card 2: Committee & Advisors
    add_card(s1, Inches(0.8) + col_w + gap, y_card, col_w, h_card, CARD_BG_WHITE, CARD_BORDER)
    tb_c2 = s1.shapes.add_textbox(Inches(1.0) + col_w + gap, y_card + Inches(0.15), col_w - Inches(0.4), h_card - Inches(0.3))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    p = tf_c2.paragraphs[0]
    p.text = "ACADEMIC & INDUSTRIAL GUIDANCE"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COBALT_ACCENT
    p.space_after = Pt(4)
    p2 = tf_c2.add_paragraph()
    p2.text = "Academic Advisor: Dr. CHHEANG Vinha"
    p2.font.size = Pt(12)
    p2.font.bold = True
    p2.font.color.rgb = NAVY_PRIMARY
    p3 = tf_c2.add_paragraph()
    p3.text = "Industrial Supervisor: Mr. YON Kimkosal"
    p3.font.size = Pt(12)
    p3.font.bold = True
    p3.font.color.rgb = NAVY_PRIMARY
    p4 = tf_c2.add_paragraph()
    p4.text = "Department of Applied Mathematics and Statistics, ITC"
    p4.font.size = Pt(10)
    p4.font.color.rgb = TEXT_MUTED

    # Card 3: Defense Session Info
    add_card(s1, Inches(0.8) + (col_w + gap)*2, y_card, col_w, h_card, CARD_BG_WHITE, CARD_BORDER)
    tb_c3 = s1.shapes.add_textbox(Inches(1.0) + (col_w + gap)*2, y_card + Inches(0.15), col_w - Inches(0.4), h_card - Inches(0.3))
    tf_c3 = tb_c3.text_frame
    tf_c3.word_wrap = True
    p = tf_c3.paragraphs[0]
    p.text = "DEFENSE PROTOCOL"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COBALT_ACCENT
    p.space_after = Pt(4)
    p2 = tf_c3.add_paragraph()
    p2.text = "Saturday, October 31, 2026"
    p2.font.size = Pt(14)
    p2.font.bold = True
    p2.font.color.rgb = NAVY_PRIMARY
    p3 = tf_c3.add_paragraph()
    p3.text = "Allocated Time: 15 Minutes Total\n(10 min Presentation + 5 min Q&A)"
    p3.font.size = Pt(11)
    p3.font.bold = True
    p3.font.color.rgb = GOLD_ACCENT

    # =========================================================
    # SLIDE 2: Context & Problem Statement
    # =========================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Macroeconomic Significance & Operational Bottlenecks", "Context & Problem Statement", 2)

    # Left Column: Macroeconomic Context
    add_card(s2, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.4), CARD_BG_WHITE, CARD_BORDER)
    tb = s2.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(5.1), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Cambodia's Trade Logistics Landscape"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(12)

    add_bullet_point(tf, "Economic Trade Dependency:", "Merchandise trade exceeds 120% of Cambodia's national GDP, acting as the primary engine for industrial growth and employment.")
    add_bullet_point(tf, "Multi-Modal Freight Traffic:", "Cargo throughput expands across deep-sea maritime ports (PAS in Sihanoukville), river terminals (PPAP in Phnom Penh), and cross-border land corridors.")
    add_bullet_point(tf, "Asymmetric Trade Flows:", "Cambodia imports heavy raw textiles and intermediate inputs while exporting finished garments, travel goods, and footwear to Western markets.")
    add_bullet_point(tf, "High Vulnerability to Shocks:", "Acute sensitivity to external shocks (COVID-19 border closures, supply chain chokepoints, declaration batching delays) demands continuous monitoring.")

    # Right Column: Existing Gaps & Problem Statement
    add_card(s2, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), CARD_BG_WHITE, CARD_BORDER)
    tb2 = s2.shapes.add_textbox(Inches(7.1), Inches(1.7), Inches(5.1), Inches(5.0))
    tf2 = tb2.text_frame
    tf2.word_wrap = True

    p = tf2.paragraphs[0]
    p.text = "Operational & Data Challenges"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(12)

    add_bullet_point(tf2, "1. Severe Data Fragmentation:", "Customs and logistics records are scattered across public web portals in nested, unstandardized JSON formats with inconsistent nomenclature.")
    add_bullet_point(tf2, "2. High Reporting Latency:", "Analysts rely on ad-hoc manual Excel extraction, introducing weeks of data lag and high risk of human data entry errors.")
    add_bullet_point(tf2, "3. Complete Lack of Predictive Modeling:", "No automated forecasting infrastructure exists to project trade deficits, freight tonnage surges, or port capacity requirements.")
    add_bullet_point(tf2, "4. The Core Internship Mandate:", "To design an automated, production-grade data engineering pipeline and deploy mathematically validated econometric models to enable predictive trade planning.")

    # =========================================================
    # SLIDE 3: Objectives & Solution Scope
    # =========================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Four Foundational Pillars of the Internship Project", "Project Objectives & Scope", 3)

    pillars = [
        ("Pillar 1: Automated Data Ingestion", "Engineered resilient Python scrapers with automated retries and exponential backoff. Ingested 128 continuous months (Jan 2016 – Aug 2026) with zero missing intervals."),
        ("Pillar 2: 2-Tier Data Warehouse", "Designed a PostgreSQL Star Schema. Raw JSONB staging ensures complete auditability; Kimball fact/dimension tables accelerate analytical aggregations by over 10x."),
        ("Pillar 3: Applied Statistical Forecasting", "Conducted ADF unit-root testing, STL decomposition, outlier rolling median smoothing, and a 12-month holdout tournament establishing Holt-Winters as champion (13.77% MAPE)."),
        ("Pillar 4: Interactive BI & Operations", "Deployed an interactive Streamlit BI platform featuring 3D Plotly trade corridors, dynamic forecast horizon selectors, and live database telemetry for real-time monitoring.")
    ]

    card_w = Inches(5.7)
    card_h = Inches(2.55)
    positions = [
        (Inches(0.8), Inches(1.5)),
        (Inches(6.8), Inches(1.5)),
        (Inches(0.8), Inches(4.35)),
        (Inches(6.8), Inches(4.35))
    ]

    for idx, (title, desc) in enumerate(pillars):
        x, y = positions[idx]
        add_card(s3, x, y, card_w, card_h, CARD_BG_WHITE, CARD_BORDER)
        
        # Color accent pill on top of card
        pill = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, card_w, Inches(0.08))
        pill.fill.solid()
        pill.fill.fore_color.rgb = COBALT_ACCENT
        pill.line.fill.background()

        tb = s3.shapes.add_textbox(x + Inches(0.3), y + Inches(0.2), card_w - Inches(0.6), card_h - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = NAVY_PRIMARY
        p.space_after = Pt(8)

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(12)
        p2.font.color.rgb = TEXT_DARK

    # =========================================================
    # SLIDE 4: End-to-End Pipeline Architecture
    # =========================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "4-Stage Production Architecture: Scraper to Decision Support", "Data Engineering & Pipeline", 4)

    # Left: Architecture Diagram
    add_card(s4, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4), CARD_BG_WHITE, CARD_BORDER)
    arch_img = os.path.join(base_img_path, "figures/architecture_pipeline.png")
    if os.path.exists(arch_img):
        s4.shapes.add_picture(arch_img, Inches(0.95), Inches(1.7), width=Inches(6.5))

    # Right: Technical Specifications
    add_card(s4, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4), CARD_BG_WHITE, CARD_BORDER)
    tb = s4.shapes.add_textbox(Inches(8.0), Inches(1.7), Inches(4.3), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Pipeline Execution Specs"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(12)

    add_bullet_point(tf, "1. Extraction Layer:", "Custom Python scrapers harvest 128 monthly trade snapshots. Session persistence and exponential backoff prevent rate-limit throttling.")
    add_bullet_point(tf, "2. Transformation Engine:", "Pandas data cleansing maps currencies (USD & KHR), converts raw kilograms into Metric Tons, and standardizes Month-Start dates.")
    add_bullet_point(tf, "3. Loading & Idempotency:", "Dual-tier PostgreSQL loading with ON CONFLICT DO UPDATE upserts guarantees idempotent backfilling without record duplication.")
    add_bullet_point(tf, "4. Airflow Orchestration:", "Monthly automated DAG with SLA failure alerts, containerized under Docker Compose for zero environment drift.")

    # =========================================================
    # SLIDE 5: Dimensional Modeling & Star Schema
    # =========================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "PostgreSQL Star Schema Optimized for Analytical Querying", "Data Warehouse Modeling", 5)

    # Left: Schema Image (Properly scaled to fit inside container)
    add_card(s5, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4), CARD_BG_WHITE, CARD_BORDER)
    dw_img = os.path.join(base_img_path, "figures/warehouse_schema.png")
    if os.path.exists(dw_img):
        s5.shapes.add_picture(dw_img, Inches(1.15), Inches(1.7), height=Inches(4.9))

    # Right: Schema Components
    add_card(s5, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4), CARD_BG_WHITE, CARD_BORDER)
    tb = s5.shapes.add_textbox(Inches(8.0), Inches(1.7), Inches(4.3), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Core Fact & Dimension Design"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(10)

    add_bullet_point(tf, "Central Fact Table:", "fact_trade_customs stores granular transactions: quantity_kg, gross_weight_kg, value_usd, and value_khr.")
    add_bullet_point(tf, "Dimension: dim_country:", "Standardized ISO Alpha-2/3 codes, country names, and regional economic trading blocs.")
    add_bullet_point(tf, "Dimension: dim_commodity:", "Hierarchical Harmonized System classifications (HS2 Chapter and HS4 Heading).")
    add_bullet_point(tf, "Dimension: dim_transport_mode:", "Captures Sea (PAS), River (PPAP), Land road freight, and Air cargo.")
    add_bullet_point(tf, "Dimension: dim_date:", "Surrogate integer key (date_key = YYYYMMDD) enabling sub-millisecond date partitioning.")

    # =========================================================
    # SLIDE 6: Temporal Regularity & Date Architecture (Fixed Heights)
    # =========================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "Temporal Regularity & Date Architecture for Econometrics", "Data Quality & Regularity", 6)

    # 3 Horizontal Cards with adjusted heights to avoid banner collision
    card_w = Inches(11.733)
    card_h = Inches(1.25)
    y_start = Inches(1.45)
    gap_y = Inches(0.18)

    specs = [
        ("1. Month-Start Resampling Standard (MS Frequency)",
         "Time-series econometric models require equidistant, strictly monotonic intervals. Raw declaration dates are standardized to ISO-8601 Month-Start (YYYY-MM-01) at frequency f = MS, preventing uneven monthly interval distortions."),
        ("2. 128 Continuous Gapless Months (Jan 2016 – Aug 2026)",
         "A complete longitudinal window of 128 continuous months was verified with 100% temporal completeness. Null-imputation audits confirmed zero missing monthly intervals across the entire 10.6-year analytical history."),
        ("3. Surrogate Date Key Architecture (date_key = YYYYMMDD)",
         "The star schema utilizes an integer surrogate key linking facts to dim_date. This decouples analytical grouping (by fiscal year, quarter, or semester) from computational datetime parsing overhead, accelerating OLAP query response times.")
    ]

    for idx, (title, desc) in enumerate(specs):
        y = y_start + idx * (card_h + gap_y)
        add_card(s6, Inches(0.8), y, card_w, card_h, CARD_BG_WHITE, CARD_BORDER)

        pill = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), y, Inches(0.12), card_h)
        pill.fill.solid()
        pill.fill.fore_color.rgb = COBALT_ACCENT
        pill.line.fill.background()

        tb = s6.shapes.add_textbox(Inches(1.2), y + Inches(0.12), card_w - Inches(0.6), card_h - Inches(0.24))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = NAVY_PRIMARY
        p.space_after = Pt(3)

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11.5)
        p2.font.color.rgb = TEXT_DARK

    # Bottom Stat Banner
    banner_y = Inches(5.8)
    banner_h = Inches(0.95)
    add_card(s6, Inches(0.8), banner_y, card_w, banner_h, CARD_BG_TINT, COBALT_ACCENT)
    tb_b = s6.shapes.add_textbox(Inches(1.0), banner_y + Inches(0.15), card_w - Inches(0.4), banner_h - Inches(0.3))
    tf_b = tb_b.text_frame
    tf_b.word_wrap = True
    p = tf_b.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "Data Integrity Milestone: 128 / 128 Verified Months (100.0%) • 0 Date Collisions • 0 Missing Partitions"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY

    # =========================================================
    # SLIDE 7: Exploratory Data Analysis & Outlier Diagnostics (~30% Math Starts)
    # =========================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "Stationarity Analysis & Robust Anomaly Filtering", "Applied Statistical Analysis", 7)

    # Left: STL Decomposition Image
    add_card(s7, Inches(0.8), Inches(1.5), Inches(6.0), Inches(5.4), CARD_BG_WHITE, CARD_BORDER)
    stl_img = os.path.join(base_img_path, "figures/stl_decomposition.png")
    if os.path.exists(stl_img):
        s7.shapes.add_picture(stl_img, Inches(0.95), Inches(1.65), width=Inches(5.7))

    # Right Top: ADF Table
    add_card(s7, Inches(7.0), Inches(1.5), Inches(5.5), Inches(2.5), CARD_BG_WHITE, CARD_BORDER)
    tb = s7.shapes.add_textbox(Inches(7.2), Inches(1.6), Inches(5.1), Inches(0.4))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = "Augmented Dickey-Fuller (ADF) Unit-Root Test"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY

    # ADF Table
    rows, cols = 5, 4
    table_shape = s7.shapes.add_table(rows, cols, Inches(7.2), Inches(2.05), Inches(5.1), Inches(1.7))
    tbl = table_shape.table
    tbl.columns[0].width = Inches(2.1)
    tbl.columns[1].width = Inches(1.0)
    tbl.columns[2].width = Inches(1.0)
    tbl.columns[3].width = Inches(1.0)

    headers = ["Series", "ADF Stat", "p-Value", "Inference"]
    data = [
        ["Raw Imports (It)", "-0.354", "0.905", "Non-Stationary"],
        ["Raw Exports (Et)", "+0.312", "0.998", "Non-Stationary"],
        ["Diff Imports (ΔIt)", "-9.412", "< 0.0001", "Stationary d=1"],
        ["Diff Exports (ΔEt)", "-11.831", "< 0.0001", "Stationary d=1"]
    ]

    for c, h in enumerate(headers):
        cell = tbl.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)

    for r, row in enumerate(data):
        for c, val in enumerate(row):
            cell = tbl.cell(r+1, c)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG_WHITE if r % 2 == 0 else CARD_BG_TINT
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            p.font.size = Pt(9.5)
            p.font.color.rgb = TEXT_DARK
            if "Stationary" in val and c == 3:
                p.font.bold = True
                p.font.color.rgb = SUCCESS_GREEN

    # Right Bottom: Outlier Diagnostics & Smoothing
    add_card(s7, Inches(7.0), Inches(4.2), Inches(5.5), Inches(2.7), CARD_BG_WHITE, CARD_BORDER)
    tb_out = s7.shapes.add_textbox(Inches(7.2), Inches(4.35), Inches(5.1), Inches(2.4))
    tf_out = tb_out.text_frame
    tf_out.word_wrap = True

    p = tf_out.paragraphs[0]
    p.text = "Pre-Fitting Outlier Screening & Median Smoothing"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(6)

    add_bullet_point(tf_out, "Anomaly Screening:", "Flagged observations with standardized scores |zt| > 2.5 and STL residuals |Rt| > 2.5σR.", font_size=11, space_after=4)
    add_bullet_point(tf_out, "Robust 5-Month Rolling Median:", "Extreme shocks treated via R~t = median(Rt-2, ..., Rt+2) yielding cleaned series Yt* = Tt + St + R~t.", font_size=11, space_after=4)
    add_bullet_point(tf_out, "Critical Rationale:", "Protects exponential smoothing against acute shock distortions without discarding genuine seasonal dynamics.", font_size=11, space_after=4)

    # =========================================================
    # SLIDE 8: Forecasting Methodology & Holdout Tournament
    # =========================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "Leakage-Free Chronological Holdout Evaluation Tournament", "Predictive Modeling Methodology", 8)

    # Top: Holdout Strategy Card
    add_card(s8, Inches(0.8), Inches(1.5), Inches(11.733), Inches(1.5), CARD_BG_WHITE, CARD_BORDER)
    tb = s8.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(11.333), Inches(1.2))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Data Leakage Prevention & Holdout Partitioning"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(4)

    add_bullet_point(tf, "Why Random K-Fold is Prohibited:", "Random cross-validation shuffles future data into the past, causing catastrophic lookahead bias.", font_size=11.5, space_after=3)
    add_bullet_point(tf, "Chronological Split:", "Training Set = 116 Months (Jan 2016 – Aug 2025) | Out-of-Sample Holdout = 12 Months (Sep 2025 – Aug 2026).", font_size=11.5, space_after=3)
    add_bullet_point(tf, "Annual Cycle Horizon (h = 12):", "Tests model robustness across the entire annual macroeconomic cycle (Q4 holiday surge + Q1 post-holiday trough).", font_size=11.5, space_after=3)

    # Bottom: Leaderboard Table Card
    add_card(s8, Inches(0.8), Inches(3.2), Inches(11.733), Inches(3.7), CARD_BG_WHITE, CARD_BORDER)
    tb_t = s8.shapes.add_textbox(Inches(1.0), Inches(3.35), Inches(11.333), Inches(0.4))
    tf_t = tb_t.text_frame
    p = tf_t.paragraphs[0]
    p.text = "Holdout Accuracy Leaderboard: National Trade Flows (2025 – 2026)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY

    # Leaderboard Table
    rows, cols = 7, 5
    table_shape = s8.shapes.add_table(rows, cols, Inches(1.0), Inches(3.8), Inches(11.333), Inches(2.8))
    tbl = table_shape.table
    tbl.columns[0].width = Inches(2.6)
    tbl.columns[1].width = Inches(3.3)
    tbl.columns[2].width = Inches(1.8)
    tbl.columns[3].width = Inches(1.8)
    tbl.columns[4].width = Inches(1.8)

    headers = ["Trade Flow Series", "Candidate Model", "MAE ($ USD)", "RMSE ($ USD)", "MAPE (%)"]
    t_data = [
        ["National Imports (Cleaned)", "Holt-Winters (Champion)", "$455.0M", "$556.5M", "13.77%"],
        ["National Imports (Cleaned)", "Box-Jenkins SARIMAX", "$467.5M", "$563.7M", "14.17%"],
        ["National Imports (Cleaned)", "Seasonal Naive Baseline", "$690.7M", "$779.2M", "21.46%"],
        ["National Exports (Cleaned)", "Box-Jenkins SARIMAX", "$317.7M", "$392.5M", "10.71%"],
        ["National Exports (Cleaned)", "Holt-Winters (Competitive)", "$338.3M", "$424.3M", "11.28%"],
        ["National Exports (Cleaned)", "Seasonal Naive Baseline", "$593.7M", "$687.7M", "20.36%"]
    ]

    for c, h in enumerate(headers):
        cell = tbl.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)

    for r, row in enumerate(t_data):
        for c, val in enumerate(row):
            cell = tbl.cell(r+1, c)
            cell.text = val
            cell.fill.solid()
            # Highlight Champion row
            if "Champion" in row[1]:
                cell.fill.fore_color.rgb = RGBColor(230, 244, 234)
            elif r % 2 == 0:
                cell.fill.fore_color.rgb = CARD_BG_WHITE
            else:
                cell.fill.fore_color.rgb = CARD_BG_TINT

            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c in [0, 1] else PP_ALIGN.CENTER
            p.font.size = Pt(10.5)
            p.font.color.rgb = TEXT_DARK
            if "Champion" in row[1]:
                p.font.bold = True
                if c == 4:
                    p.font.color.rgb = SUCCESS_GREEN

    # =========================================================
    # SLIDE 9: Production Champion & Forward Projections
    # =========================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "Holt-Winters Production Champion & Forward Horizon Outlook", "Econometric Forecasting Results", 9)

    # Left: Champion Justification Card
    add_card(s9, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4), CARD_BG_WHITE, CARD_BORDER)
    tb = s9.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.0), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Why Holt-Winters Won Production"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(12)

    add_bullet_point(tf, "1. Leading Accuracy on Inbound Flows:", "Achieved 13.77% MAPE on National Imports, outperforming SARIMAX (14.17%) and the baseline (21.46%).")
    add_bullet_point(tf, "2. Sub-Second Latency (~0.02s):", "Executes parameter estimation in approximately 0.02 seconds, making it 100x faster than SARIMAX numerical grid searches.")
    add_bullet_point(tf, "3. Elimination of Hessian Singularities:", "SARIMAX frequently encounters non-invertible covariance matrix crashes during interactive dashboard queries; Holt-Winters guarantees 100% parameter stability.")
    add_bullet_point(tf, "4. Production Parsimony:", "Smoothly separates trend and seasonal level equations without requiring non-stationary Differencing inversion.")

    # Right: Forward Projections Table & Analysis
    add_card(s9, Inches(6.5), Inches(1.5), Inches(6.033), Inches(5.4), CARD_BG_WHITE, CARD_BORDER)
    tb2 = s9.shapes.add_textbox(Inches(6.7), Inches(1.7), Inches(5.6), Inches(0.4))
    tf2 = tb2.text_frame
    p = tf2.paragraphs[0]
    p.text = "Forward Projections: Sep 2026 – Dec 2026 (95% CI)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY

    # Forward Projections Table
    rows, cols = 5, 4
    table_shape2 = s9.shapes.add_table(rows, cols, Inches(6.7), Inches(2.2), Inches(5.6), Inches(2.1))
    tbl2 = table_shape2.table
    tbl2.columns[0].width = Inches(1.1)
    tbl2.columns[1].width = Inches(1.5)
    tbl2.columns[2].width = Inches(1.5)
    tbl2.columns[3].width = Inches(1.5)

    headers2 = ["Period", "Exports ($)", "Imports ($)", "Balance ($)"]
    p_data = [
        ["Sep 2026", "$2,632.6M", "$2,903.1M", "-$270.5M"],
        ["Oct 2026", "$2,488.7M", "$3,007.4M", "-$518.7M"],
        ["Nov 2026", "$2,620.6M", "$3,047.4M", "-$426.9M"],
        ["Dec 2026", "$2,775.5M", "$3,125.8M", "-$350.3M"]
    ]

    for c, h in enumerate(headers2):
        cell = tbl2.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)

    for r, row in enumerate(p_data):
        for c, val in enumerate(row):
            cell = tbl2.cell(r+1, c)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG_WHITE if r % 2 == 0 else CARD_BG_TINT
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            p.font.size = Pt(10)
            p.font.color.rgb = TEXT_DARK
            if c == 3:
                p.font.bold = True
                p.font.color.rgb = RGBColor(185, 28, 28)

    # Narrative under table
    tb_narr = s9.shapes.add_textbox(Inches(6.7), Inches(4.5), Inches(5.6), Inches(2.2))
    tf_narr = tb_narr.text_frame
    tf_narr.word_wrap = True
    p = tf_narr.paragraphs[0]
    p.text = "Macroeconomic Policy Insights:"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(4)

    add_bullet_point(tf_narr, "Fourth-Quarter Export Surge:", "Projections capture year-end manufacturing surges reaching $2.78B in Dec 2026.", font_size=10.5, space_after=3)
    add_bullet_point(tf_narr, "Structural Trade Deficit:", "Inbound inputs expand to $3.13B, maintaining a manageable structural deficit (-$117M to -$539M/mo) typical of expanding export economies.", font_size=10.5, space_after=3)

    # =========================================================
    # SLIDE 10: Interactive Streamlit BI & Operations Platform
    # =========================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "Interactive Streamlit BI Platform & Operational Telemetry", "Decision Support Platform", 10)

    # Left: Platform UI Screenshot
    add_card(s10, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4), CARD_BG_WHITE, CARD_BORDER)
    dash_img = os.path.join(base_img_path, "figures/dashboard_overview.png")
    if os.path.exists(dash_img):
        s10.shapes.add_picture(dash_img, Inches(0.95), Inches(1.7), width=Inches(6.5))

    # Right: 4 Operational Modules
    add_card(s10, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4), CARD_BG_WHITE, CARD_BORDER)
    tb = s10.shapes.add_textbox(Inches(8.0), Inches(1.7), Inches(4.3), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Four Core Platform Views"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(10)

    add_bullet_point(tf, "1. Global Trade Corridor View:", "Orthographic 3D Plotly globe visualizing international shipping routes to the US, EU, China, and ASEAN.")
    add_bullet_point(tf, "2. Freight Modality Analysis:", "Interactive breakdown of cargo tonnage across Sea (PAS), River (PPAP), Land trucking, and Air freight.")
    add_bullet_point(tf, "3. Dynamic Forecasting View:", "Allows users to adjust forecast horizons (3 to 24 months), toggle 80%/95% confidence ribbons, and evaluate deficits.")
    add_bullet_point(tf, "4. DW Telemetry & Health:", "Exposes live PostgreSQL database health, ingestion run durations, and pipeline status logs.")

    # =========================================================
    # SLIDE 11: Real-World Impact & Engineering Contributions (Enriched Cards)
    # =========================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_header(s11, "Applied Value for National Planning & Technical Contributions", "Business & Operational Impact", 11)

    cards_impact = [
        ("Macroeconomic & Fiscal Policy",
         GOLD_ACCENT,
         [
             ("FX Liquidity Early-Warning:", "Anticipates foreign currency demand for $3.1B/month raw industrial input imports, supporting central bank reserve planning."),
             ("Structural Deficit Monitoring:", "Differentiates healthy input-driven trade deficits (-$117M to -$539M/mo) from acute external currency shocks."),
             ("Fiscal Revenue Planning:", "Enables the Ministry of Economy & Finance (MEF) to forecast customs tariff yields across bilateral partner corridors.")
         ]),
        ("Port Logistics & Infrastructure",
         COBALT_ACCENT,
         [
             ("Seaport Capacity (PAS):", "Alerts Sihanoukville Autonomous Port of Q4 export volume rushes (+18.7% over baseline) to prevent berth congestion."),
             ("River Port Logistics (PPAP):", "Forecasts Phnom Penh container barge demand along the Mekong River to optimize feeder vessel scheduling."),
             ("Equipment & Yard Planning:", "Provides forward freight tonnage projections to schedule gantry crane maintenance and container yard staging.")
         ]),
        ("Production Engineering Standard",
         SUCCESS_GREEN,
         [
             ("Zero Data-Loss Idempotency:", "PostgreSQL ON CONFLICT DO UPDATE upserts eliminate duplicate transaction collisions during backfills."),
             ("Automated Orchestration:", "Apache Airflow DAGs replace 10+ hours of manual ad-hoc scraping with automated, scheduled monthly pipelines."),
             ("Sub-Second Query Latency:", "Kimball Star Schema and indexed surrogate keys accelerate complex multi-year OLAP queries to under 100ms.")
         ])
    ]

    card_w = Inches(3.75)
    gap = Inches(0.24)
    h_impact = Inches(5.4)

    for idx, (title, accent_c, bullets) in enumerate(cards_impact):
        x = Inches(0.8) + idx * (card_w + gap)
        add_card(s11, x, Inches(1.5), card_w, h_impact, CARD_BG_WHITE, CARD_BORDER)

        pill = s11.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(1.5), card_w, Inches(0.1))
        pill.fill.solid()
        pill.fill.fore_color.rgb = accent_c
        pill.line.fill.background()

        tb = s11.shapes.add_textbox(x + Inches(0.22), Inches(1.75), card_w - Inches(0.44), h_impact - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = NAVY_PRIMARY
        p.space_after = Pt(12)

        for b_title, b_desc in bullets:
            add_bullet_point(tf, b_title, b_desc, font_size=11, space_after=8)

    # =========================================================
    # SLIDE 12: Conclusion, Future Roadmap & Acknowledgments
    # =========================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12)
    add_header(s12, "Summary of Achievements, Future Extensions & Acknowledgments", "Conclusion & Defense Wrap-up", 12)

    # Left Card: Summary & Future Work
    add_card(s12, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.4), CARD_BG_WHITE, CARD_BORDER)
    tb = s12.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(5.1), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Key Achievements & Future Roadmap"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(10)

    add_bullet_point(tf, "Completed Deliverables:", "Engineered 128-month continuous ETL pipeline, 2-tier Star Schema DW, Holt-Winters champion forecasting, and interactive Streamlit BI platform.")
    add_bullet_point(tf, "Strict Methodological Rigor:", "Prevented data leakage via chronological holdout tournament; filtered acute shocks using robust 5-month rolling median smoothing.")
    add_bullet_point(tf, "Future Extension 1:", "Real-time streaming ingestion with Apache Kafka to capture live customs gate clearance events.")
    add_bullet_point(tf, "Future Extension 2:", "Deep learning sequence forecasting (NHITS, PatchTST) as multi-decade longitudinal data accumulates.")

    # Right Card: Acknowledgments & Q&A
    add_card(s12, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), CARD_BG_WHITE, CARD_BORDER)
    tb2 = s12.shapes.add_textbox(Inches(7.1), Inches(1.7), Inches(5.1), Inches(5.0))
    tf2 = tb2.text_frame
    tf2.word_wrap = True

    p = tf2.paragraphs[0]
    p.text = "Acknowledgments & Committee Defense"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(10)

    add_bullet_point(tf2, "Academic Advisor:", "Dr. CHHEANG Vinha (Department of Applied Mathematics and Statistics, ITC) for invaluable academic guidance and mathematical rigor.")
    add_bullet_point(tf2, "Industrial Supervisor:", "Mr. YON Kimkosal for industry domain expertise, operational insights, and project supervision.")
    add_bullet_point(tf2, "Faculty & Jury:", "Professors and jury members of the Faculty of Applied Science, ITC.")

    # Big Q&A Box
    qa_card = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.1), Inches(4.5), Inches(5.1), Inches(2.1))
    qa_card.fill.solid()
    qa_card.fill.fore_color.rgb = CARD_BG_TINT
    qa_card.line.color.rgb = COBALT_ACCENT
    qa_card.line.width = Pt(1.5)
    tb_qa = qa_card.text_frame
    tb_qa.margin_left = tb_qa.margin_right = tb_qa.margin_top = tb_qa.margin_bottom = Inches(0.15)
    tb_qa.word_wrap = True

    p_qa1 = tb_qa.paragraphs[0]
    p_qa1.alignment = PP_ALIGN.CENTER
    p_qa1.text = "Thank You for Your Attention!"
    p_qa1.font.name = FONT_TITLE
    p_qa1.font.size = Pt(18)
    p_qa1.font.bold = True
    p_qa1.font.color.rgb = NAVY_PRIMARY
    p_qa1.space_after = Pt(4)

    p_qa2 = tb_qa.add_paragraph()
    p_qa2.alignment = PP_ALIGN.CENTER
    p_qa2.text = "I am ready for your questions and feedback.\n(Interactive Streamlit BI Demonstration Standby)"
    p_qa2.font.name = FONT_BODY
    p_qa2.font.size = Pt(12)
    p_qa2.font.bold = True
    p_qa2.font.color.rgb = COBALT_ACCENT

    # Save presentation
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    build_presentation()
