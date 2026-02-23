#!/usr/bin/env python3
"""
PDF Generator for THE IDEAL MAN
Generates a publication-ready 6x9 trade paperback PDF
"""

import re
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
    KeepTogether, Flowable, NextPageTemplate, PageTemplate,
    BaseDocTemplate, Frame
)
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black
import os

# Page dimensions (6" x 9" trade paperback)
PAGE_WIDTH = 6 * inch
PAGE_HEIGHT = 9 * inch

# Margins
MARGIN_TOP = 0.8 * inch
MARGIN_BOTTOM = 0.8 * inch
MARGIN_INSIDE = 0.8 * inch
MARGIN_OUTSIDE = 0.6 * inch
GUTTER = 0.2 * inch

class NumberedCanvas:
    """Canvas that handles page numbering with roman/arabic numerals"""
    def __init__(self, canvas, doc):
        self.canvas = canvas
        self.doc = doc
        
class BookDocTemplate(BaseDocTemplate):
    """Custom document template for book formatting"""
    def __init__(self, filename, **kwargs):
        BaseDocTemplate.__init__(self, filename, **kwargs)
        self.page_counts = {'front': 0, 'body': 0}
        self.current_section = 'front'
        self.chapter_first_pages = set()
        
    def afterPage(self):
        """Called after each page is rendered"""
        if self.current_section == 'front':
            self.page_counts['front'] += 1
        else:
            self.page_counts['body'] += 1

def int_to_roman(num):
    """Convert integer to lowercase roman numerals"""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ['m', 'cm', 'd', 'cd', 'c', 'xc', 'l', 'xl', 'x', 'ix', 'v', 'iv', 'i']
    roman_num = ''
    for i in range(len(val)):
        count = int(num / val[i])
        if count:
            roman_num += syms[i] * count
            num -= val[i] * count
    return roman_num

class ChapterTitle(Flowable):
    """Custom flowable for chapter titles"""
    def __init__(self, text, width):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        
    def wrap(self, availWidth, availHeight):
        return (self.width, 0.5 * inch)
        
    def draw(self):
        self.canv.setFont("Times-Bold", 16)
        self.canv.drawCentredString(self.width / 2, 0, self.text.upper())

class PartTitle(Flowable):
    """Custom flowable for part titles"""
    def __init__(self, text, width):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        
    def wrap(self, availWidth, availHeight):
        return (self.width, 0.3 * inch)
        
    def draw(self):
        self.canv.setFont("Times-Italic", 12)
        self.canv.drawCentredString(self.width / 2, 0, self.text)

class SceneBreak(Flowable):
    """Scene break with asterisks"""
    def __init__(self, width):
        Flowable.__init__(self)
        self.width = width
        
    def wrap(self, availWidth, availHeight):
        return (self.width, 0.4 * inch)
        
    def draw(self):
        self.canv.setFont("Times-Roman", 11)
        self.canv.drawCentredString(self.width / 2, 0.15 * inch, "*   *   *")

def create_styles():
    """Create paragraph styles for the book"""
    styles = {}
    
    # Body text - first paragraph (no indent)
    styles['body_first'] = ParagraphStyle(
        'body_first',
        fontName='Times-Roman',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        firstLineIndent=0,
        spaceBefore=0,
        spaceAfter=0,
    )
    
    # Body text - subsequent paragraphs (indented)
    styles['body'] = ParagraphStyle(
        'body',
        fontName='Times-Roman',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        firstLineIndent=0.3 * inch,
        spaceBefore=0,
        spaceAfter=0,
    )
    
    # Italicized text (thoughts, letters)
    styles['italic'] = ParagraphStyle(
        'italic',
        fontName='Times-Italic',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        firstLineIndent=0.3 * inch,
        spaceBefore=0,
        spaceAfter=0,
    )
    
    # Italic first paragraph
    styles['italic_first'] = ParagraphStyle(
        'italic_first',
        fontName='Times-Italic',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        firstLineIndent=0,
        spaceBefore=0,
        spaceAfter=0,
    )
    
    # Journal/letter entries (centered, narrower)
    styles['journal'] = ParagraphStyle(
        'journal',
        fontName='Times-Italic',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        leftIndent=0.75 * inch,
        rightIndent=0.75 * inch,
        firstLineIndent=0,
        spaceBefore=6,
        spaceAfter=6,
    )
    
    # Chapter title
    styles['chapter_title'] = ParagraphStyle(
        'chapter_title',
        fontName='Times-Bold',
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceBefore=2 * inch,
        spaceAfter=0.5 * inch,
    )
    
    # Chapter subtitle
    styles['chapter_subtitle'] = ParagraphStyle(
        'chapter_subtitle',
        fontName='Times-Italic',
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        spaceBefore=0,
        spaceAfter=0.5 * inch,
    )
    
    # Part title
    styles['part_title'] = ParagraphStyle(
        'part_title',
        fontName='Times-Italic',
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        spaceBefore=0.3 * inch,
        spaceAfter=0.3 * inch,
    )
    
    # Title page styles
    styles['book_title'] = ParagraphStyle(
        'book_title',
        fontName='Times-Bold',
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
    )
    
    styles['book_subtitle'] = ParagraphStyle(
        'book_subtitle',
        fontName='Times-Italic',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
    )
    
    styles['author'] = ParagraphStyle(
        'author',
        fontName='Times-Roman',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
    )
    
    # Copyright page
    styles['copyright'] = ParagraphStyle(
        'copyright',
        fontName='Times-Roman',
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
        spaceBefore=6,
        spaceAfter=6,
    )
    
    # Dedication
    styles['dedication'] = ParagraphStyle(
        'dedication',
        fontName='Times-Italic',
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
    )
    
    # TOC styles
    styles['toc_title'] = ParagraphStyle(
        'toc_title',
        fontName='Times-Bold',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceBefore=0,
        spaceAfter=0.5 * inch,
    )
    
    styles['toc_chapter'] = ParagraphStyle(
        'toc_chapter',
        fontName='Times-Bold',
        fontSize=11,
        leading=16,
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=0,
    )
    
    styles['toc_part'] = ParagraphStyle(
        'toc_part',
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        leftIndent=0.3 * inch,
        spaceBefore=0,
        spaceAfter=0,
    )
    
    # Section headers (Acknowledgments, About)
    styles['section_header'] = ParagraphStyle(
        'section_header',
        fontName='Times-Bold',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceBefore=1.5 * inch,
        spaceAfter=0.4 * inch,
    )
    
    return styles

def parse_markdown(filepath):
    """Parse the markdown file and extract content"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into lines
    lines = content.split('\n')
    
    elements = []
    current_chapter = None
    current_part = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines at start
        if not line:
            i += 1
            continue
            
        # Book title (# THE IDEAL MAN)
        if line.startswith('# THE IDEAL MAN') or line == '# THE IDEAL MAN':
            elements.append({'type': 'book_title', 'text': 'THE IDEAL MAN'})
            i += 1
            continue
            
        # Subtitle (## *A Story...)
        if line.startswith('## *') and 'Story of the One Who Believed' in line:
            elements.append({'type': 'book_subtitle', 'text': 'A Story of the One Who Believed'})
            i += 1
            continue
            
        # Chapter title (# CHAPTER ONE or # Chapter 7:)
        chapter_match = re.match(r'^#\s*(CHAPTER\s+\w+|Chapter\s+\d+)', line, re.IGNORECASE)
        if chapter_match:
            current_chapter = line.lstrip('#').strip()
            i += 1
            # Check for subtitle on next line
            if i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith('## '):
                    subtitle = next_line.lstrip('#').strip()
                    elements.append({'type': 'chapter', 'title': current_chapter, 'subtitle': subtitle})
                    i += 1
                else:
                    elements.append({'type': 'chapter', 'title': current_chapter, 'subtitle': ''})
            continue
            
        # Part title (### Part I:)
        if line.startswith('### Part'):
            current_part = line.lstrip('#').strip()
            elements.append({'type': 'part', 'title': current_part})
            i += 1
            continue
            
        # Scene break (---)
        if line == '---' or line == '***' or line == '* * *':
            elements.append({'type': 'scene_break'})
            i += 1
            continue
            
        # Regular paragraph
        if line:
            # Check if it's italicized (starts with *)
            if line.startswith('*') and line.endswith('*') and not line.startswith('**'):
                # Full italic paragraph
                text = line.strip('*').strip()
                elements.append({'type': 'paragraph', 'text': text, 'italic': True})
            else:
                # Process inline formatting
                elements.append({'type': 'paragraph', 'text': line, 'italic': False})
        
        i += 1
    
    return elements

def process_text(text):
    """Process text for ReportLab, handling inline formatting"""
    # Escape XML special characters first
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # Convert markdown bold **text** to <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    
    # Convert markdown italic *text* to <i>text</i>
    text = re.sub(r'\*([^*]+?)\*', r'<i>\1</i>', text)
    
    # Convert em dashes
    text = text.replace('---', '—')
    text = text.replace('--', '—')
    
    return text

def create_front_matter(styles):
    """Create front matter pages"""
    story = []
    frame_width = PAGE_WIDTH - MARGIN_INSIDE - MARGIN_OUTSIDE - GUTTER
    
    # Page 1: Half title
    story.append(Spacer(1, 3.5 * inch))
    story.append(Paragraph("THE IDEAL MAN", styles['book_title']))
    story.append(PageBreak())
    
    # Page 2: Blank
    story.append(Spacer(1, 0.1 * inch))
    story.append(PageBreak())
    
    # Page 3: Full title page
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("THE IDEAL MAN", styles['book_title']))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("A Story of the One Who Believed", styles['book_subtitle']))
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("by", styles['author']))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Kunal Meena", styles['author']))
    story.append(PageBreak())
    
    # Page 4: Copyright
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Copyright © 2024 by Kunal Meena", styles['copyright']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        "All rights reserved. No part of this book may be reproduced or used in any manner "
        "without written permission of the copyright owner except for the use of quotations "
        "in book reviews.",
        styles['copyright']
    ))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        "This is a work of fiction. Names, characters, places, and incidents are products "
        "of the author's imagination or are used fictitiously. Any resemblance to actual "
        "persons, living or dead, events, or locales is entirely coincidental.",
        styles['copyright']
    ))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("First Edition: 2024", styles['copyright']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Published by Kunal Meena", styles['copyright']))
    story.append(Paragraph("[Self-Published]", styles['copyright']))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("For permissions or inquiries:", styles['copyright']))
    story.append(Paragraph("Email: kunalmeena1311@gmail.com", styles['copyright']))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Cover design by [To be added]", styles['copyright']))
    story.append(Paragraph("Interior design by Kunal Meena", styles['copyright']))
    story.append(PageBreak())
    
    # Page 5: Dedication
    story.append(Spacer(1, 2.5 * inch))
    story.append(Paragraph("For my grandfather,", styles['dedication']))
    story.append(Paragraph("who wrote for the man in the mirror", styles['dedication']))
    story.append(PageBreak())
    
    # Page 6: Blank
    story.append(Spacer(1, 0.1 * inch))
    story.append(PageBreak())
    
    # Page 7: Table of Contents
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("CONTENTS", styles['toc_title']))
    
    # TOC entries
    toc_entries = [
        ("Chapter One: The Man in the Mirror", 1),
        ("Chapter Two: The Other Four", 32),
        ("Chapter Three: The Game Behind the Game", 63),
        ("Chapter Four: The Ceremony", 107),
        ("Chapter Five: Coming Home", 147),
        ("Chapter Six: The Fellowship", 179),
        ("Chapter Seven: The Return", 213),
        ("Chapter Eight: The Publication", 240),
        ("Chapter Nine: The Man in the Mirror", 256),
    ]
    
    for title, page in toc_entries:
        # Create dot leader
        story.append(Paragraph(f"{title}", styles['toc_chapter']))
    
    story.append(PageBreak())
    
    # Page 8: Blank (so Chapter 1 starts on right-hand page)
    story.append(Spacer(1, 0.1 * inch))
    story.append(PageBreak())
    
    return story

def create_back_matter(styles):
    """Create acknowledgments and about the author"""
    story = []
    
    # Start on new page
    story.append(PageBreak())
    
    # Acknowledgments
    story.append(Paragraph("ACKNOWLEDGMENTS", styles['section_header']))
    story.append(Paragraph(
        "The author would like to thank Meera, without whom this book would not exist; "
        "Virginia Ashworth, who opened doors; and every reader who has ever believed "
        "that truth is worth telling, even when it hurts.",
        styles['body_first']
    ))
    story.append(PageBreak())
    
    # About the Author
    story.append(Paragraph("ABOUT THE AUTHOR", styles['section_header']))
    story.append(Paragraph(
        "Kunal Meena is a writer from India. THE IDEAL MAN is his first novel. "
        "He writes about architecture, silence, and the courage it takes to tell the truth. "
        "He can be reached at kunalmeena1311@gmail.com.",
        styles['body_first']
    ))
    
    return story

def build_pdf(md_filepath, output_filepath):
    """Build the complete PDF"""
    styles = create_styles()
    
    # Parse the markdown
    print("Parsing markdown...")
    elements = parse_markdown(md_filepath)
    
    # Create document
    frame_width = PAGE_WIDTH - MARGIN_INSIDE - MARGIN_OUTSIDE - GUTTER
    frame_height = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    
    # Simple frame for all pages
    frame = Frame(
        MARGIN_INSIDE + GUTTER,  # x
        MARGIN_BOTTOM,           # y
        frame_width,             # width
        frame_height,            # height
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    
    # Create the document
    doc = SimpleDocTemplate(
        output_filepath,
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
        leftMargin=MARGIN_INSIDE + GUTTER,
        rightMargin=MARGIN_OUTSIDE,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )
    
    story = []
    
    # Add front matter
    print("Creating front matter...")
    story.extend(create_front_matter(styles))
    
    # Process body content
    print("Processing body content...")
    is_first_para_in_section = True
    in_chapter = False
    
    for elem in elements:
        if elem['type'] == 'book_title' or elem['type'] == 'book_subtitle':
            # Skip these, handled in front matter
            continue
            
        elif elem['type'] == 'chapter':
            # Chapter starts on new page
            story.append(PageBreak())
            story.append(Spacer(1, 1.5 * inch))
            
            # Format chapter title
            title = elem['title'].upper()
            story.append(Paragraph(title, styles['chapter_title']))
            
            if elem['subtitle']:
                story.append(Paragraph(elem['subtitle'], styles['chapter_subtitle']))
            
            story.append(Spacer(1, 0.5 * inch))
            is_first_para_in_section = True
            in_chapter = True
            
        elif elem['type'] == 'part':
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph(elem['title'], styles['part_title']))
            story.append(Spacer(1, 0.1 * inch))
            is_first_para_in_section = True
            
        elif elem['type'] == 'scene_break':
            story.append(Spacer(1, 0.15 * inch))
            story.append(Paragraph("*&nbsp;&nbsp;&nbsp;*&nbsp;&nbsp;&nbsp;*", 
                                   ParagraphStyle('break', alignment=TA_CENTER, 
                                                  fontName='Times-Roman', fontSize=11)))
            story.append(Spacer(1, 0.15 * inch))
            is_first_para_in_section = True
            
        elif elem['type'] == 'paragraph':
            text = process_text(elem['text'])
            
            # Determine style
            if elem.get('italic', False):
                style = styles['italic_first'] if is_first_para_in_section else styles['italic']
            else:
                style = styles['body_first'] if is_first_para_in_section else styles['body']
            
            story.append(Paragraph(text, style))
            is_first_para_in_section = False
    
    # Add back matter
    print("Creating back matter...")
    story.extend(create_back_matter(styles))
    
    # Build the PDF
    print(f"Building PDF: {output_filepath}")
    doc.build(story)
    print("PDF created successfully!")
    
    return output_filepath

if __name__ == "__main__":
    import sys
    
    md_file = "/workspaces/Writing/THE_IDEAL_MAN.md"
    output_file = "/workspaces/Writing/THE_IDEAL_MAN.pdf"
    
    if len(sys.argv) > 1:
        md_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    build_pdf(md_file, output_file)
