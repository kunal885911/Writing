#!/usr/bin/env python3
"""
Professional PDF Generator for THE IDEAL MAN
Generates a publication-ready 6x9 trade paperback PDF
with elegant typography and professional book design
"""

import re
import os
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    Paragraph, Spacer, PageBreak, Flowable, 
    BaseDocTemplate, Frame, PageTemplate, KeepTogether
)
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black
from reportlab.pdfgen import canvas

# ============================================================================
# PAGE DIMENSIONS - 6" x 9" Trade Paperback
# ============================================================================
PAGE_WIDTH = 6 * inch
PAGE_HEIGHT = 9 * inch

# Margins
MARGIN_TOP = 0.8 * inch
MARGIN_BOTTOM = 0.8 * inch
MARGIN_INSIDE = 0.8 * inch  # Binding side
MARGIN_OUTSIDE = 0.6 * inch
GUTTER = 0.2 * inch

# Content area
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_INSIDE - MARGIN_OUTSIDE - GUTTER
CONTENT_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

# ============================================================================
# FONT SETUP - Use EB Garamond if available, else Times
# ============================================================================
def setup_fonts():
    """Try to register Garamond fonts, fall back to Times"""
    try:
        # Try system fonts (Linux/Ubuntu)
        garamond_paths = [
            '/usr/share/fonts/truetype/ebgaramond/EBGaramond-Regular.ttf',
            '/usr/share/fonts/truetype/ebgaramond/EBGaramond-Italic.ttf',
            '/usr/share/fonts/truetype/ebgaramond/EBGaramond-Bold.ttf',
        ]
        if os.path.exists(garamond_paths[0]):
            pdfmetrics.registerFont(TTFont('Garamond', garamond_paths[0]))
            pdfmetrics.registerFont(TTFont('Garamond-Italic', garamond_paths[1]))
            pdfmetrics.registerFont(TTFont('Garamond-Bold', garamond_paths[2]))
            return 'Garamond'
    except:
        pass
    
    # Fall back to Times (built-in)
    return 'Times'

FONT_FAMILY = setup_fonts()
FONT_ROMAN = f'{FONT_FAMILY}-Roman' if FONT_FAMILY == 'Times' else FONT_FAMILY
FONT_ITALIC = f'{FONT_FAMILY}-Italic'
FONT_BOLD = f'{FONT_FAMILY}-Bold' if FONT_FAMILY == 'Times' else FONT_FAMILY

# For Times built-in fonts
if FONT_FAMILY == 'Times':
    FONT_ROMAN = 'Times-Roman'
    FONT_ITALIC = 'Times-Italic'
    FONT_BOLD = 'Times-Bold'

print(f"Using font family: {FONT_FAMILY}")

# ============================================================================
# CUSTOM FLOWABLES
# ============================================================================

class DropCapParagraph(Flowable):
    """A paragraph with an elegant drop cap"""
    def __init__(self, text, style, drop_lines=3, width=CONTENT_WIDTH):
        Flowable.__init__(self)
        self.text = text
        self.style = style
        self.drop_lines = drop_lines
        self.width = width
        self.drop_size = style.fontSize * drop_lines * 0.85
        
    def wrap(self, availWidth, availHeight):
        # Calculate height needed
        self.availWidth = availWidth
        # Simple estimate - actual rendering will adjust
        lines_estimate = len(self.text) / 60
        self.height = max(self.drop_size, (lines_estimate + 1) * self.style.leading)
        return (availWidth, self.height)
        
    def draw(self):
        if not self.text:
            return
            
        c = self.canv
        first_letter = self.text[0].upper()
        rest_text = self.text[1:]
        
        # Draw drop cap
        c.setFont(FONT_BOLD, self.drop_size)
        c.drawString(0, -self.drop_size + self.style.fontSize * 0.4, first_letter)
        
        # Calculate drop cap width
        drop_width = c.stringWidth(first_letter, FONT_BOLD, self.drop_size) + 0.08 * inch
        
        # Draw rest of text wrapping around drop cap
        # For first few lines, indent past the drop cap
        c.setFont(FONT_ROMAN, self.style.fontSize)
        
        words = rest_text.split()
        x = drop_width
        y = 0
        line_height = self.style.leading
        lines_with_indent = self.drop_lines
        current_line = 0
        
        for word in words:
            word_width = c.stringWidth(word + ' ', FONT_ROMAN, self.style.fontSize)
            max_x = self.availWidth
            
            if current_line < lines_with_indent:
                indent = drop_width
            else:
                indent = 0
                
            if x + word_width > max_x:
                # New line
                current_line += 1
                if current_line < lines_with_indent:
                    x = drop_width
                else:
                    x = 0
                y -= line_height
                
            c.drawString(x, y, word)
            x += word_width


class FleuronBreak(Flowable):
    """Ornamental section break with fleuron"""
    def __init__(self, width=CONTENT_WIDTH):
        Flowable.__init__(self)
        self.width = width
        
    def wrap(self, availWidth, availHeight):
        return (availWidth, 0.5 * inch)
        
    def draw(self):
        c = self.canv
        # Draw ornamental break - use a nice typographic ornament
        c.setFont('ZapfDingbats', 12)
        # ❧ equivalent in ZapfDingbats is character 118 (leaf)
        c.drawCentredString(self.width / 2, 0.2 * inch, '❖')


class ChapterOpening(Flowable):
    """Professional chapter opening with number and title"""
    def __init__(self, number, title, width=CONTENT_WIDTH):
        Flowable.__init__(self)
        self.number = number
        self.title = title
        self.width = width
        
    def wrap(self, availWidth, availHeight):
        return (availWidth, 2.8 * inch)
        
    def draw(self):
        c = self.canv
        # Chapter number - elegant small caps style
        c.setFont(FONT_BOLD, 11)
        chapter_num_text = f"CHAPTER {self.number}"
        c.drawCentredString(self.width / 2, 1.8 * inch, chapter_num_text)
        
        # Thin decorative line
        line_width = 1 * inch
        c.setLineWidth(0.5)
        c.line(self.width/2 - line_width/2, 1.65 * inch, 
               self.width/2 + line_width/2, 1.65 * inch)
        
        # Chapter title - larger, elegant
        c.setFont(FONT_BOLD, 18)
        c.drawCentredString(self.width / 2, 1.2 * inch, self.title.upper())


class PartHeading(Flowable):
    """Elegant part heading within chapter"""
    def __init__(self, title, width=CONTENT_WIDTH):
        Flowable.__init__(self)
        self.title = title
        self.width = width
        
    def wrap(self, availWidth, availHeight):
        return (availWidth, 0.7 * inch)
        
    def draw(self):
        c = self.canv
        c.setFont(FONT_ITALIC, 13)
        c.drawCentredString(self.width / 2, 0.25 * inch, self.title)


# ============================================================================
# PAGE TEMPLATES WITH MIRRORED MARGINS
# ============================================================================

class BookPageTemplate:
    """Handles page numbering and running headers"""
    def __init__(self):
        self.page_number = 0
        self.section = 'front'  # 'front' or 'body'
        self.chapter_title = ''
        self.chapter_start_pages = set()
        self.front_pages = 0
        
    def on_page(self, canvas, doc):
        """Called for each page - add page numbers and running headers"""
        self.page_number += 1
        canvas.saveState()
        
        # Determine if odd (right) or even (left) page
        is_odd = (self.page_number % 2) == 1
        
        # Skip page number on chapter start pages
        if self.page_number in self.chapter_start_pages:
            canvas.restoreState()
            return
            
        # Page number position
        if self.section == 'front':
            # Roman numerals for front matter
            page_text = self._int_to_roman(self.page_number)
        else:
            # Arabic numerals for body (subtract front pages)
            body_page = self.page_number - self.front_pages
            page_text = str(body_page)
        
        # Draw page number at bottom center
        canvas.setFont(FONT_ROMAN, 10)
        canvas.drawCentredString(PAGE_WIDTH / 2, 0.4 * inch, page_text)
        
        # Running headers (only in body section, not on chapter starts)
        if self.section == 'body' and self.page_number not in self.chapter_start_pages:
            canvas.setFont(FONT_ITALIC, 9)
            if is_odd:
                # Right page - show book title on outside (right)
                canvas.drawRightString(PAGE_WIDTH - MARGIN_OUTSIDE, 
                                       PAGE_HEIGHT - 0.5 * inch, 
                                       "THE IDEAL MAN")
            else:
                # Left page - show chapter title on outside (left)
                canvas.drawString(MARGIN_INSIDE + GUTTER, 
                                 PAGE_HEIGHT - 0.5 * inch, 
                                 self.chapter_title)
        
        canvas.restoreState()
    
    def _int_to_roman(self, num):
        """Convert to lowercase roman numerals"""
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ['m', 'cm', 'd', 'cd', 'c', 'xc', 'l', 'xl', 'x', 'ix', 'v', 'iv', 'i']
        result = ''
        for i, v in enumerate(val):
            while num >= v:
                result += syms[i]
                num -= v
        return result


# ============================================================================
# STYLES
# ============================================================================

def create_styles():
    """Create all paragraph styles for the book"""
    styles = {}
    
    # Body text - first paragraph (no indent)
    styles['body_first'] = ParagraphStyle(
        'body_first',
        fontName=FONT_ROMAN,
        fontSize=11,
        leading=14.5,
        alignment=TA_LEFT,
        firstLineIndent=0,
        spaceBefore=0,
        spaceAfter=0,
    )
    
    # Body text - subsequent paragraphs (indented)
    styles['body'] = ParagraphStyle(
        'body',
        fontName=FONT_ROMAN,
        fontSize=11,
        leading=14.5,
        alignment=TA_LEFT,
        firstLineIndent=0.3 * inch,
        spaceBefore=0,
        spaceAfter=0,
    )
    
    # Italicized text (thoughts, flashbacks)
    styles['italic'] = ParagraphStyle(
        'italic',
        fontName=FONT_ITALIC,
        fontSize=11,
        leading=14.5,
        alignment=TA_LEFT,
        firstLineIndent=0.3 * inch,
        spaceBefore=0,
        spaceAfter=0,
    )
    
    # Italic first paragraph
    styles['italic_first'] = ParagraphStyle(
        'italic_first',
        fontName=FONT_ITALIC,
        fontSize=11,
        leading=14.5,
        alignment=TA_LEFT,
        firstLineIndent=0,
        spaceBefore=0,
        spaceAfter=0,
    )
    
    # Letter/journal block - indented from both sides
    styles['letter'] = ParagraphStyle(
        'letter',
        fontName=FONT_ITALIC,
        fontSize=10.5,
        leading=13.5,
        alignment=TA_LEFT,
        leftIndent=0.5 * inch,
        rightIndent=0.5 * inch,
        firstLineIndent=0,
        spaceBefore=6,
        spaceAfter=6,
    )
    
    # Letter signature
    styles['letter_signature'] = ParagraphStyle(
        'letter_signature',
        fontName=FONT_ITALIC,
        fontSize=10.5,
        leading=13.5,
        alignment=TA_RIGHT,
        rightIndent=0.5 * inch,
        spaceBefore=6,
        spaceAfter=12,
    )
    
    # Chapter title (for TOC)
    styles['chapter_title'] = ParagraphStyle(
        'chapter_title',
        fontName=FONT_BOLD,
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceBefore=0,
        spaceAfter=0.5 * inch,
    )
    
    # Part title within chapter
    styles['part_title'] = ParagraphStyle(
        'part_title',
        fontName=FONT_ITALIC,
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        spaceBefore=0.3 * inch,
        spaceAfter=0.3 * inch,
    )
    
    # ---- FRONT MATTER STYLES ----
    
    # Half title / Title
    styles['book_title'] = ParagraphStyle(
        'book_title',
        fontName=FONT_BOLD,
        fontSize=28,
        leading=34,
        alignment=TA_CENTER,
    )
    
    # Half title (smaller)
    styles['half_title'] = ParagraphStyle(
        'half_title',
        fontName=FONT_BOLD,
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
    )
    
    # Subtitle
    styles['book_subtitle'] = ParagraphStyle(
        'book_subtitle',
        fontName=FONT_ITALIC,
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
    )
    
    # Author byline
    styles['author_by'] = ParagraphStyle(
        'author_by',
        fontName=FONT_ROMAN,
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
    )
    
    # Author name
    styles['author'] = ParagraphStyle(
        'author',
        fontName=FONT_ROMAN,
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
    )
    
    # Copyright page
    styles['copyright'] = ParagraphStyle(
        'copyright',
        fontName=FONT_ROMAN,
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
        spaceBefore=4,
        spaceAfter=4,
    )
    
    # Dedication
    styles['dedication'] = ParagraphStyle(
        'dedication',
        fontName=FONT_ITALIC,
        fontSize=14,
        leading=20,
        alignment=TA_CENTER,
    )
    
    # TOC title
    styles['toc_title'] = ParagraphStyle(
        'toc_title',
        fontName=FONT_BOLD,
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceBefore=0,
        spaceAfter=0.4 * inch,
    )
    
    # TOC chapter entry
    styles['toc_chapter'] = ParagraphStyle(
        'toc_chapter',
        fontName=FONT_BOLD,
        fontSize=11,
        leading=18,
        alignment=TA_LEFT,
        spaceBefore=8,
        spaceAfter=0,
    )
    
    # TOC part entry (indented)
    styles['toc_part'] = ParagraphStyle(
        'toc_part',
        fontName=FONT_ROMAN,
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        leftIndent=0.3 * inch,
        spaceBefore=0,
        spaceAfter=0,
    )
    
    # Section headers (Acknowledgments, etc.)
    styles['section_header'] = ParagraphStyle(
        'section_header',
        fontName=FONT_BOLD,
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceBefore=1.5 * inch,
        spaceAfter=0.5 * inch,
    )
    
    return styles


# ============================================================================
# TEXT PROCESSING
# ============================================================================

def process_text(text):
    """Process text for ReportLab, handling inline formatting"""
    # Escape XML special characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # Convert markdown bold **text** to <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    
    # Convert markdown italic *text* to <i>text</i>
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
    
    return text


def normalize_chapter_number(chapter_text):
    """Convert chapter text to standardized number word"""
    # Handle "CHAPTER ONE", "Chapter 7:", etc.
    number_words = ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 
                    'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN']
    
    # Check for word numbers
    for word in number_words:
        if word in chapter_text.upper():
            return word
    
    # Check for numeric
    match = re.search(r'(\d+)', chapter_text)
    if match:
        num = int(match.group(1))
        if 1 <= num <= 10:
            return number_words[num - 1]
    
    return 'ONE'


def extract_chapter_title(chapter_line, subtitle_line=None):
    """Extract the title from chapter heading"""
    # "# CHAPTER ONE" -> "The Man in the Mirror" (from subtitle)
    # "# Chapter 7: The Return" -> "The Return"
    
    if ':' in chapter_line:
        return chapter_line.split(':', 1)[1].strip()
    elif subtitle_line and subtitle_line.startswith('##'):
        return subtitle_line.lstrip('#').strip()
    return ''


# ============================================================================
# DOCUMENT PARSING
# ============================================================================

def parse_manuscript(filepath):
    """Parse the markdown manuscript into structured elements"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    elements = []
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip('\n')
        stripped = line.strip()
        
        # Skip empty lines at document start
        if not stripped:
            i += 1
            continue
        
        # Book title
        if stripped == '# THE IDEAL MAN':
            elements.append({'type': 'book_title'})
            i += 1
            continue
        
        # Subtitle
        if stripped.startswith('## *') and 'Story' in stripped:
            elements.append({'type': 'book_subtitle'})
            i += 1
            continue
        
        # Chapter heading
        if stripped.startswith('# CHAPTER') or stripped.startswith('# Chapter'):
            chapter_num = normalize_chapter_number(stripped)
            
            # Check for inline title (Chapter 7: The Return)
            if ':' in stripped:
                title = extract_chapter_title(stripped)
            else:
                # Check next line for subtitle
                title = ''
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('## '):
                        title = next_line.lstrip('#').strip()
                        i += 1
            
            elements.append({
                'type': 'chapter',
                'number': chapter_num,
                'title': title
            })
            i += 1
            continue
        
        # Part heading
        if stripped.startswith('### Part'):
            part_title = stripped.lstrip('#').strip()
            elements.append({'type': 'part', 'title': part_title})
            i += 1
            continue
        
        # Scene break
        if stripped in ['---', '***', '* * *', '—']:
            elements.append({'type': 'scene_break'})
            i += 1
            continue
        
        # Letter content (detect by italic markers and letter-like content)
        if stripped.startswith('*Dear') or stripped.startswith('*I know'):
            # Start of a letter block
            letter_lines = []
            while i < len(lines):
                line_content = lines[i].strip()
                if not line_content:
                    i += 1
                    break
                letter_lines.append(line_content)
                i += 1
            
            for letter_line in letter_lines:
                # Check if it's a signature line
                if letter_line.strip() in ['*V*', '*Virginia Ashworth*', '*Director, WordCraft International*']:
                    text = letter_line.strip('*').strip()
                    elements.append({'type': 'letter_signature', 'text': text})
                else:
                    text = letter_line.strip('*').strip()
                    elements.append({'type': 'letter', 'text': text})
            continue
        
        # Regular paragraph
        if stripped:
            # Check if entire paragraph is italicized
            is_italic = stripped.startswith('*') and stripped.endswith('*') and not stripped.startswith('**')
            text = stripped.strip('*') if is_italic else stripped
            elements.append({
                'type': 'paragraph',
                'text': text,
                'italic': is_italic
            })
        
        i += 1
    
    return elements


# ============================================================================
# FRONT MATTER
# ============================================================================

def create_front_matter(styles):
    """Create elegant front matter pages"""
    story = []
    
    # ===== PAGE 1: Half Title =====
    story.append(Spacer(1, 3 * inch))
    story.append(Paragraph("THE IDEAL MAN", styles['half_title']))
    story.append(PageBreak())
    
    # ===== PAGE 2: Blank =====
    story.append(Spacer(1, 0.1 * inch))
    story.append(PageBreak())
    
    # ===== PAGE 3: Full Title Page =====
    story.append(Spacer(1, 2.5 * inch))
    story.append(Paragraph("THE IDEAL MAN", styles['book_title']))
    story.append(Spacer(1, 0.25 * inch))
    
    # Decorative line
    story.append(Paragraph("—", ParagraphStyle('line', alignment=TA_CENTER, 
                                                fontName=FONT_ROMAN, fontSize=14)))
    story.append(Spacer(1, 0.25 * inch))
    
    story.append(Paragraph("A Story of the One Who Believed", styles['book_subtitle']))
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("by", styles['author_by']))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("KUNAL MEENA", styles['author']))
    story.append(PageBreak())
    
    # ===== PAGE 4: Copyright =====
    story.append(Spacer(1, 0.5 * inch))
    
    copyright_text = [
        "Copyright © 2024 by Kunal Meena",
        "",
        "All rights reserved. No part of this book may be reproduced or used in any manner without written permission of the copyright owner except for the use of quotations in book reviews.",
        "",
        "This is a work of fiction. Names, characters, places, and incidents are products of the author's imagination or are used fictitiously. Any resemblance to actual persons, living or dead, events, or locales is entirely coincidental.",
        "",
        "First Edition: 2024",
        "",
        "Published by Kunal Meena",
        "[Self-Published]",
        "",
        "For permissions or inquiries:",
        "Email: kunalmeena1311@gmail.com",
        "",
        "Cover design by [To be added]",
        "Interior design by Kunal Meena",
    ]
    
    for line in copyright_text:
        if line:
            story.append(Paragraph(line, styles['copyright']))
        else:
            story.append(Spacer(1, 6))
    
    story.append(PageBreak())
    
    # ===== PAGE 5: Dedication =====
    story.append(Spacer(1, 3 * inch))
    story.append(Paragraph("For my grandfather,", styles['dedication']))
    story.append(Paragraph("who wrote for the man in the mirror", styles['dedication']))
    story.append(PageBreak())
    
    # ===== PAGE 6: Blank =====
    story.append(Spacer(1, 0.1 * inch))
    story.append(PageBreak())
    
    # ===== PAGE 7: Table of Contents =====
    story.append(Spacer(1, 1 * inch))
    story.append(Paragraph("CONTENTS", styles['toc_title']))
    
    # Chapter entries
    chapters = [
        ("Chapter One", "The Man in the Mirror"),
        ("Chapter Two", "The Other Four"),
        ("Chapter Three", "The Game Behind the Game"),
        ("Chapter Four", "The Ceremony"),
        ("Chapter Five", "Coming Home"),
        ("Chapter Six", "The Fellowship"),
        ("Chapter Seven", "The Return"),
        ("Chapter Eight", "The Publication"),
        ("Chapter Nine", "The Man in the Mirror"),
    ]
    
    for chapter, title in chapters:
        entry_text = f"{chapter}: {title}"
        story.append(Paragraph(entry_text, styles['toc_chapter']))
    
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Acknowledgments", styles['toc_chapter']))
    story.append(Paragraph("About the Author", styles['toc_chapter']))
    
    story.append(PageBreak())
    
    # ===== PAGE 8: Blank (so Chapter 1 starts on right page) =====
    story.append(Spacer(1, 0.1 * inch))
    story.append(PageBreak())
    
    return story, 8  # Return number of front pages


# ============================================================================
# BACK MATTER
# ============================================================================

def create_back_matter(styles):
    """Create acknowledgments and about author pages"""
    story = []
    
    # Acknowledgments
    story.append(PageBreak())
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("ACKNOWLEDGMENTS", styles['section_header']))
    story.append(Spacer(1, 0.3 * inch))
    
    ack_text = """This book would not exist without the people who believed in it before I did. To Meera, who read the first draft and told me it was "necessary" rather than merely good—you gave me permission to keep going. To Virginia Ashworth, who opened doors I didn't know existed. To every reader who has ever believed that truth is worth telling, even when it hurts—this book is for you.

To my grandfather, who papered his walls with rejection letters and called them trophies: I finally understand. Writing isn't about what the world accepts. It's about what the man in the mirror demands.

To my family: thank you for your patience during the years I spent in that cramped apartment, talking to imaginary people. Your doubt made me stronger. Your love, when it finally came, made it worthwhile.

And to the readers holding this book: thank you for giving these words a home in your mind, even briefly. Stories are just walls until someone walks through the doors."""
    
    for para in ack_text.split('\n\n'):
        story.append(Paragraph(process_text(para.strip()), styles['body_first']))
        story.append(Spacer(1, 0.15 * inch))
    
    # About the Author
    story.append(PageBreak())
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("ABOUT THE AUTHOR", styles['section_header']))
    story.append(Spacer(1, 0.3 * inch))
    
    about_text = """KUNAL MEENA writes about architecture, silence, and the courage it takes to tell the truth. His work explores what it means to be "ideal"—not through perfection, but through the honest reckoning with one's own weaknesses and the stubborn belief in something larger than oneself.

THE IDEAL MAN is his first novel.

He can be reached at kunalmeena1311@gmail.com.

For updates on future work, visit his website or follow him on social media."""
    
    for para in about_text.split('\n\n'):
        story.append(Paragraph(process_text(para.strip()), styles['body_first']))
        story.append(Spacer(1, 0.15 * inch))
    
    # End mark
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("❖", ParagraphStyle('endmark', alignment=TA_CENTER,
                                                fontName='ZapfDingbats', fontSize=12)))
    
    return story


# ============================================================================
# MAIN DOCUMENT BUILDER
# ============================================================================

def build_pdf(md_filepath, output_filepath):
    """Build the complete professional PDF"""
    print("=" * 60)
    print("THE IDEAL MAN - Professional PDF Generator")
    print("=" * 60)
    
    styles = create_styles()
    
    # Parse manuscript
    print("\n[1/5] Parsing manuscript...")
    elements = parse_manuscript(md_filepath)
    print(f"      Found {len(elements)} content elements")
    
    # Create page template handler
    page_handler = BookPageTemplate()
    
    # Build story list
    story = []
    
    # Add front matter
    print("[2/5] Creating front matter...")
    front_matter, front_pages = create_front_matter(styles)
    story.extend(front_matter)
    page_handler.front_pages = front_pages
    
    # Process body content
    print("[3/5] Processing body content...")
    is_first_para = True
    current_chapter_num = 0
    chapter_titles = {
        'ONE': 'The Man in the Mirror',
        'TWO': 'The Other Four',
        'THREE': 'The Game Behind the Game',
        'FOUR': 'The Ceremony',
        'FIVE': 'Coming Home',
        'SIX': 'The Fellowship',
        'SEVEN': 'The Return',
        'EIGHT': 'The Publication',
        'NINE': 'The Man in the Mirror',
    }
    
    for elem in elements:
        if elem['type'] in ['book_title', 'book_subtitle']:
            # Skip, handled in front matter
            continue
            
        elif elem['type'] == 'chapter':
            current_chapter_num += 1
            # Chapter starts on new page
            story.append(PageBreak())
            
            # Get title
            title = elem.get('title') or chapter_titles.get(elem['number'], '')
            page_handler.chapter_title = title
            
            # Mark this as a chapter start page (for page numbering)
            page_handler.chapter_start_pages.add(front_pages + current_chapter_num)
            
            # Chapter opening flowable
            story.append(Spacer(1, 0.8 * inch))
            story.append(ChapterOpening(elem['number'], title))
            story.append(Spacer(1, 0.5 * inch))
            
            is_first_para = True
            
        elif elem['type'] == 'part':
            story.append(Spacer(1, 0.25 * inch))
            story.append(PartHeading(elem['title']))
            story.append(Spacer(1, 0.15 * inch))
            is_first_para = True
            
        elif elem['type'] == 'scene_break':
            story.append(Spacer(1, 0.15 * inch))
            story.append(FleuronBreak())
            story.append(Spacer(1, 0.15 * inch))
            is_first_para = True
            
        elif elem['type'] == 'letter':
            text = process_text(elem['text'])
            story.append(Paragraph(text, styles['letter']))
            is_first_para = False
            
        elif elem['type'] == 'letter_signature':
            text = process_text(elem['text'])
            story.append(Paragraph(text, styles['letter_signature']))
            is_first_para = True
            
        elif elem['type'] == 'paragraph':
            text = process_text(elem['text'])
            
            # Use drop cap for first paragraph of chapter
            if is_first_para and current_chapter_num > 0 and len(elem['text']) > 50:
                # Use drop cap for substantial first paragraphs
                story.append(DropCapParagraph(elem['text'], styles['body'], 
                                              drop_lines=3, width=CONTENT_WIDTH))
                story.append(Spacer(1, 0.1 * inch))
            else:
                # Regular paragraph
                if elem.get('italic', False):
                    style = styles['italic_first'] if is_first_para else styles['italic']
                else:
                    style = styles['body_first'] if is_first_para else styles['body']
                
                story.append(Paragraph(text, style))
            
            is_first_para = False
    
    # Add end mark after final chapter
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("❖", ParagraphStyle('endmark', alignment=TA_CENTER,
                                                fontName='ZapfDingbats', fontSize=12)))
    
    # Add back matter
    print("[4/5] Creating back matter...")
    story.extend(create_back_matter(styles))
    
    # Create document
    print("[5/5] Building PDF...")
    
    # Create frame with proper margins
    def make_frame(is_odd):
        """Create frame with mirrored margins"""
        if is_odd:
            # Right page: inside margin on left
            return Frame(
                MARGIN_INSIDE + GUTTER,
                MARGIN_BOTTOM,
                CONTENT_WIDTH,
                CONTENT_HEIGHT,
                leftPadding=0, rightPadding=0,
                topPadding=0, bottomPadding=0,
            )
        else:
            # Left page: inside margin on right
            return Frame(
                MARGIN_OUTSIDE,
                MARGIN_BOTTOM,
                CONTENT_WIDTH,
                CONTENT_HEIGHT,
                leftPadding=0, rightPadding=0,
                topPadding=0, bottomPadding=0,
            )
    
    # Simple document (ReportLab handles pagination)
    doc = BaseDocTemplate(
        output_filepath,
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
        leftMargin=MARGIN_INSIDE + GUTTER,
        rightMargin=MARGIN_OUTSIDE,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title="THE IDEAL MAN",
        author="Kunal Meena",
    )
    
    # Create page template
    frame = Frame(
        MARGIN_INSIDE + GUTTER,
        MARGIN_BOTTOM,
        CONTENT_WIDTH,
        CONTENT_HEIGHT,
        id='normal'
    )
    
    template = PageTemplate(id='AllPages', frames=frame, onPage=page_handler.on_page)
    doc.addPageTemplates([template])
    
    # Build
    doc.build(story)
    
    print("\n" + "=" * 60)
    print(f"PDF created successfully: {output_filepath}")
    print("=" * 60)
    
    return output_filepath


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    md_file = "/workspaces/Writing/THE_IDEAL_MAN.md"
    output_file = "/workspaces/Writing/THE_IDEAL_MAN.pdf"
    
    if len(sys.argv) > 1:
        md_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    build_pdf(md_file, output_file)
