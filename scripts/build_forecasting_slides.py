#!/usr/bin/env python3
"""
Generate a dedicated Applied Time-Series Forecasting Presentation (.pptx)
for SOU Pichchomrong (I4 AMS Defense).
Widescreen 16:9 layout with executive cards, tables, and visuals.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

NAVY_PRIMARY    = RGBColor(11, 37, 69)      # #0B2545 - Deep Royal Navy
NAVY_SECONDARY  = RGBColor(19, 64, 116)     # #134074 - Slate Navy
COBALT_ACCENT   = RGBColor(0, 80, 157)      # #00509D - Vibrant Academic Blue
BG_LIGHT        = RGBColor(248, 249, 250)   # #F8F9FA - Ultra-light Slate
CARD_BG_WHITE   = RGBColor(255, 255, 255)   # #FFFFFF - Crisp Card White
CARD_BG_TINT    = RGBColor(240, 244, 248)   # #F0F4F8 - Soft Blue Card Tint
CARD_BORDER     = RGBColor(218, 224, 233)   # #DAE0E9 - Border Grey
TEXT_DARK       = RGBColor(33, 37, 41)      # #212529 - Charcoal Text
TEXT_MUTED      = RGBColor(108, 117, 125)   # #6C757D - Muted Grey
GOLD_ACCENT     = RGBColor(202, 138, 4)     # #CA8A04 - Amber Gold
SUCCESS_GREEN   = RGBColor(22, 101, 52)     # #166534 - Forest Green for Wins
HEADER_BAR_BLUE = RGBColor(14, 43, 82)

FONT_FAMILY = "Calibri"

def set_slide_background(slide, color=BG_LIGHT):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_header(slide, title_text, category_text, slide_num, total_slides):
    accent = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.1)
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = COBALT_ACCENT
    accent.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.25), Inches(10.0), Inches(1.05))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_cat = tf.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.name = FONT_FAMILY
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COBALT_ACCENT
    p_cat.space_after = Pt(2)

    p_title = tf.add_paragraph()
    p_title.text = title_text
    p_title.font.name = FONT_FAMILY
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = NAVY_PRIMARY

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
    bp.font.name = FONT_FAMILY
    bp.font.size = Pt(11)
    bp.font.bold = True
    bp.font.color.rgb = NAVY_SECONDARY

def add_card(slide, left, top, width, height, bg_color=CARD_BG_WHITE, border_color=CARD_BORDER):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
    else:
        card.line.fill.background()
    return card

def add_bullet_point(tf, title, body="", level=0, bold_title=True, font_size=12, space_after=6):
    p = tf.add_paragraph() if len(tf.paragraphs[0].text) > 0 else tf.paragraphs[0]
    p.level = level
    p.space_after = Pt(space_after)

    run_title = p.add_run()
    run_title.text = title
    run_title.font.name = FONT_FAMILY
    run_title.font.size = Pt(font_size)
    run_title.font.bold = bold_title
    run_title.font.color.rgb = TEXT_DARK

    if body:
        run_body = p.add_run()
        run_body.text = f" {body}"
        run_body.font.name = FONT_FAMILY
        run_body.font.size = Pt(font_size)
        run_body.font.bold = False
        run_body.font.color.rgb = TEXT_DARK

def build_forecasting_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    base_img_path = "docs/i4_thesis_report/LaTeX_Thesis_Template/images/figures"

    # =========================================================================
    # OPTION 1: THE ALL-IN-ONE MASTER FORECASTING SLIDE (Single Comprehensive Slide)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)
    add_header(s1, "Applied Time-Series Forecasting: Objective, Workflow & Results", "Applied Mathematical Modeling", 1, 3)

    # 3-Column Layout: Left (Objective & Workflow), Center (Tournament Leaderboard), Right (Champion & Outlook)
    col_w = Inches(3.75)
    col_h = Inches(5.6)
    y_pos = Inches(1.4)

    # Column 1: Objective & Methodology Workflow
    c1 = add_card(s1, Inches(0.8), y_pos, col_w, col_h, CARD_BG_WHITE, CARD_BORDER)
    pill1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), y_pos, col_w, Inches(0.08))
    pill1.fill.solid()
    pill1.fill.fore_color.rgb = COBALT_ACCENT
    pill1.line.fill.background()

    tb1 = s1.shapes.add_textbox(Inches(1.0), y_pos + Inches(0.2), col_w - Inches(0.4), col_h - Inches(0.4))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "1. Objectives & 5-Step Workflow"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(10)

    add_bullet_point(tf1, "Core Objective:", "Forecast national monthly trade flows (Imports & Exports) across an annual horizon (h = 12 months) for FX and port planning.")
    add_bullet_point(tf1, "Step 1 (Date Regularity):", "Resampled warehouse facts to Month-Start (MS) frequency. 128 continuous months (2016–2026) with 0 gaps.")
    add_bullet_point(tf1, "Step 2 (ADF & STL Diagnostics):", "ADF unit-root proved I(1) non-stationarity (p < 0.0001). STL isolated upward trend and +18% Q4 seasonality.")
    add_bullet_point(tf1, "Step 3 (Outlier Smoothing):", "Flagged extreme shocks (|Rt| > 2.5σ) and smoothed via centered 5-month rolling median on STL residuals.")
    add_bullet_point(tf1, "Step 4 (Zero Data Leakage):", "Enforced chronological split: 116 months training (Jan 2016 – Aug 2025) vs. 12 months holdout (Sep 2025 – Aug 2026).")

    # Column 2: Tournament Leaderboard Table & Verification
    c2 = add_card(s1, Inches(4.783), y_pos, col_w, col_h, CARD_BG_WHITE, CARD_BORDER)
    pill2 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.783), y_pos, col_w, Inches(0.08))
    pill2.fill.solid()
    pill2.fill.fore_color.rgb = GOLD_ACCENT
    pill2.line.fill.background()

    tb2 = s1.shapes.add_textbox(Inches(4.983), y_pos + Inches(0.2), col_w - Inches(0.4), Inches(1.2))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = "2. Holdout Tournament Leaderboard"
    p2.font.size = Pt(15)
    p2.font.bold = True
    p2.font.color.rgb = NAVY_PRIMARY
    p2.space_after = Pt(6)

    p_sub = tf2.add_paragraph()
    p_sub.text = "12-Month Out-of-Sample Holdout (Sep 2025 – Aug 2026):"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = TEXT_MUTED

    # Insert Table inside Column 2
    table_shape = s1.shapes.add_table(4, 3, Inches(4.95), y_pos + Inches(1.15), col_w - Inches(0.35), Inches(1.75))
    table = table_shape.table
    table.columns[0].width = Inches(1.6)
    table.columns[1].width = Inches(0.9)
    table.columns[2].width = Inches(0.9)

    headers = ["Model Name", "RMSE ($)", "MAPE (%)"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = CARD_BG_WHITE

    rows = [
        ("🏆 Holt-Winters", "$556.5M", "13.77%"),
        ("🥈 SARIMAX", "$563.7M", "14.17%"),
        ("📊 Seasonal Naive", "$779.2M", "21.46%")
    ]
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            if i == 0:
                cell.fill.fore_color.rgb = CARD_BG_TINT
            else:
                cell.fill.fore_color.rgb = CARD_BG_WHITE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT
            p.font.size = Pt(10)
            p.font.bold = (i == 0)
            if i == 0 and j == 2:
                p.font.color.rgb = SUCCESS_GREEN
            else:
                p.font.color.rgb = TEXT_DARK

    # Summary notes below table
    tb2_b = s1.shapes.add_textbox(Inches(4.983), y_pos + Inches(3.05), col_w - Inches(0.4), Inches(2.3))
    tf2_b = tb2_b.text_frame
    tf2_b.word_wrap = True
    add_bullet_point(tf2_b, "Accuracy Winner:", "Holt-Winters achieved 13.77% MAPE on Imports, beating SARIMAX (14.17%) and beating Naive baseline by 7.7%.")
    add_bullet_point(tf2_b, "Exports Performance:", "SARIMAX (10.71%) and Holt-Winters (11.28%) demonstrated high precision across Western export cycles.")
    add_bullet_point(tf2_b, "Validation Source:", "Verified in verify_import_export_forecasting.ipynb with zero data leakage.")

    # Column 3: Champion Rationale & Forward Outlook
    c3 = add_card(s1, Inches(8.766), y_pos, col_w, col_h, CARD_BG_WHITE, CARD_BORDER)
    pill3 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.766), y_pos, col_w, Inches(0.08))
    pill3.fill.solid()
    pill3.fill.fore_color.rgb = SUCCESS_GREEN
    pill3.line.fill.background()

    tb3 = s1.shapes.add_textbox(Inches(8.966), y_pos + Inches(0.2), col_w - Inches(0.4), col_h - Inches(0.4))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    p3 = tf3.paragraphs[0]
    p3.text = "3. Champion & Forward Outlook"
    p3.font.size = Pt(15)
    p3.font.bold = True
    p3.font.color.rgb = NAVY_PRIMARY
    p3.space_after = Pt(10)

    add_bullet_point(tf3, "Why Holt-Winters Won:", "1. Top Accuracy (13.77% MAPE).\n2. Sub-second runtime (~0.02s vs SARIMAX numerical optimization).\n3. 100% Parameter Stability (zero Hessian singularity crashes during live queries).")
    add_bullet_point(tf3, "Full 128M Retraining:", "Fitted champion model across the complete 128 months to produce forward 12-month projections.")
    add_bullet_point(tf3, "Late 2026 Export Peak:", "National exports expand to $2.62B in Nov and $2.78B in Dec 2026, capturing year-end holiday manufacturing.")
    add_bullet_point(tf3, "Structural Trade Deficit:", "Inbound inputs expand to $3.13B, forecasting a healthy structural deficit (-$117M to -$539M/mo) with 95% CI.")

    # =========================================================================
    # SLIDE 2: DEEP DIVE: METHODOLOGY WORKFLOW & DIAGNOSTICS (Detailed View)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Time-Series Methodology: Diagnostics, Outlier Smoothing & Tournament", "Forecasting Methodology", 2, 3)

    # Left: STL Chart Image
    add_card(s2, Inches(0.8), Inches(1.4), Inches(6.0), Inches(5.6), CARD_BG_WHITE, CARD_BORDER)
    stl_img = os.path.join(base_img_path, "stl_decomposition.png")
    if os.path.exists(stl_img):
        s2.shapes.add_picture(stl_img, Inches(0.95), Inches(1.55), width=Inches(5.7))

    # Right: Methodology Steps
    add_card(s2, Inches(7.0), Inches(1.4), Inches(5.533), Inches(5.6), CARD_BG_WHITE, CARD_BORDER)
    tb_m = s2.shapes.add_textbox(Inches(7.2), Inches(1.6), Inches(5.133), Inches(5.2))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True

    p = tf_m.paragraphs[0]
    p.text = "Mathematical Rigor & Workflow Steps"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(10)

    add_bullet_point(tf_m, "1. ADF Stationarity Test:", "Raw trade series are non-stationary (p = 0.90, 0.99). First differences ΔYt achieve p < 0.0001, proving series are integrated of order 1, I(1).")
    add_bullet_point(tf_m, "2. STL 12-Month Decomposition:", "Uncovered long-term upward trend and strong annual seasonality (Q4 export surge +18%, February post-holiday trough).")
    add_bullet_point(tf_m, "3. Outlier Residual Smoothing:", "Flagged extreme external shocks where standardized residual |Rt| > 2.5σ (COVID border closures). Smoothed using centered 5-month rolling median on residuals without losing genuine seasonality.")
    add_bullet_point(tf_m, "4. Leakage-Free Holdout Partition:", "Random K-fold is prohibited in time series (causes future lookahead leakage). Enforced chronological split: 116 months training (2016–2025) vs 12 months out-of-sample holdout (2025–2026).")
    add_bullet_point(tf_m, "5. Candidate Benchmarking:", "Compared Seasonal Naive (baseline), SARIMAX(1,1,1)x(1,1,1)12, and Holt-Winters Triple Exponential Smoothing.")

    # =========================================================================
    # SLIDE 3: DEEP DIVE: RESULTS, CHAMPION SELECTION & FORWARD PROJECTIONS
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Forecasting Results: Holt-Winters Champion & Forward Outlook", "Empirical Findings & Outlook", 3, 3)

    # Left: Projections Image
    add_card(s3, Inches(0.8), Inches(1.4), Inches(6.0), Inches(5.6), CARD_BG_WHITE, CARD_BORDER)
    proj_img = os.path.join(base_img_path, "forecast_projections.png")
    if os.path.exists(proj_img):
        s3.shapes.add_picture(proj_img, Inches(0.95), Inches(1.55), width=Inches(5.7))

    # Right: Leaderboard & Economic Policy Takeaways
    add_card(s3, Inches(7.0), Inches(1.4), Inches(5.533), Inches(5.6), CARD_BG_WHITE, CARD_BORDER)
    tb_r = s3.shapes.add_textbox(Inches(7.2), Inches(1.6), Inches(5.133), Inches(5.2))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p = tf_r.paragraphs[0]
    p.text = "Empirical Results & Production Selection"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_after = Pt(8)

    # Table on Slide 3
    t3_shape = s3.shapes.add_table(4, 3, Inches(7.2), Inches(2.1), Inches(5.1), Inches(1.6))
    t3 = t3_shape.table
    t3.columns[0].width = Inches(2.3)
    t3.columns[1].width = Inches(1.4)
    t3.columns[2].width = Inches(1.4)

    for j, h in enumerate(["Model", "RMSE (USD)", "MAPE (%)"]):
        cell = t3.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = CARD_BG_WHITE

    for i, row in enumerate([("🏆 Holt-Winters", "$556.5M", "13.77%"), ("🥈 SARIMAX", "$563.7M", "14.17%"), ("📊 Seasonal Naive", "$779.2M", "21.46%")]):
        for j, val in enumerate(row):
            cell = t3.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG_TINT if i == 0 else CARD_BG_WHITE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT
            p.font.size = Pt(10)
            p.font.bold = (i == 0)
            if i == 0 and j == 2:
                p.font.color.rgb = SUCCESS_GREEN

    # Bullets below table
    tb_r2 = s3.shapes.add_textbox(Inches(7.2), Inches(3.9), Inches(5.133), Inches(3.0))
    tf_r2 = tb_r2.text_frame
    tf_r2.word_wrap = True

    add_bullet_point(tf_r2, "Why Holt-Winters Won Production:", "Lowest error on imports (13.77% MAPE), ultra-fast 0.02s execution (100x faster than SARIMAX), and zero Hessian singularity crashes in Streamlit.")
    add_bullet_point(tf_r2, "Q4 Holiday Surge Forecast:", "Exports peak at $2.62B in Nov and $2.78B in Dec 2026, alerting Sihanoukville Port (PAS) of container volume surges.")
    add_bullet_point(tf_r2, "Structural Deficit Monitoring:", "Imports expand to $3.13B, forecasting a manageable monthly trade deficit (-$117M to -$539M) to guide central bank FX liquidity planning.")

    output_path = "docs/presentation/Applied_Time_Series_Forecasting_Deck.pptx"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    print(f"✅ Successfully created: {output_path}")

if __name__ == "__main__":
    build_forecasting_presentation()
