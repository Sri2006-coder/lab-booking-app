import os
from fpdf import FPDF

class TimetablePDF(FPDF):
    def draw_seal(self, x, y):
        # Draw a professional vector circular seal representing the college logo
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.3)
        self.circle(x, y, 10, style='D')
        self.circle(x + 1.5, y + 1.5, 7, style='D')
        self.set_font("Helvetica", "B", 5)
        # Inner gear lines or text placeholder
        self.text(x + 3.5, y + 8, "JSEC")
        self.text(x + 3.8, y + 12, "CSE")

    def page_header(self, class_name, sem, hall, advisor):
        self.set_fill_color(255, 255, 255)
        # Margins: Left=10, Right=10, Top=10
        self.set_xy(10, 10)
        
        # Logo on left
        self.draw_seal(15, 12)
        
        # Header text centered
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 5, "JAI SHRIRAM ENGINEERING COLLEGE", ln=True, align="C")
        
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 4, "(An Autonomous Institution)", ln=True, align="C")
        
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 4, "TIRUPPUR - 638 660", ln=True, align="C")
        
        self.set_font("Helvetica", "", 8.5)
        self.cell(0, 4, "Approved by AICTE, New Delhi & Affiliated to Anna University, Chennai", ln=True, align="C")
        self.cell(0, 4, "Recognized by UGC & Accredited by NAAC and NBA (CSE and ECE)", ln=True, align="C")
        
        self.line(10, 33, 287, 33) # Divider line
        
        self.ln(2)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 4.5, "DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING", ln=True, align="C")
        self.set_font("Helvetica", "", 9.5)
        self.cell(0, 4, "Academic Year 2026-2027(Odd Semester)", ln=True, align="C")
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 4.5, "Class Time Table", ln=True, align="C")
        
        self.ln(1)
        
        # Metadata block
        self.set_font("Helvetica", "B", 9)
        # Row 1
        x_start = 10
        y_curr = self.get_y()
        self.text(x_start, y_curr + 3, f"Year/Semester : {class_name} / {sem}")
        self.text(x_start + 180, y_curr + 3, f"Hall No:{hall}")
        
        # Row 2
        y_curr += 4
        self.text(x_start, y_curr + 3, f"Class Advisor : {advisor}")
        self.text(x_start + 180, y_curr + 3, "w.e.f.: 02.07.2026")
        
        self.ln(7)

def generate_clean_timetable():
    pdf = TimetablePDF(orientation="landscape", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    
    # Grid Data for the classes
    classes_data = [
        {
            "class": "II-A",
            "sem": "III",
            "hall": "106",
            "advisor": "Mr.P.T.Prithivirajan, AP/CSE",
            "schedule": {
                "Monday":    ["FODS", "OOPS", "DM", "OS", "DS LAB [LAB-1]", "DS LAB [LAB-1]", "DS LAB [LAB-1]", "DS LAB [LAB-1]"],
                "Tuesday":   ["DM", "DS", "OS", "FODS", "OOPS LAB [LAB-2]", "OOPS LAB [LAB-2]", "OOPS LAB [LAB-2]", "OOPS LAB [LAB-2]"],
                "Wednesday": ["DS", "OS", "FSD LAB [LAB-7]", "FSD LAB [LAB-7]", "OOPS", "DM", "SKILL LAB [LAB-3]", "SKILL LAB [LAB-3]"],
                "Thursday":  ["OOPS", "FODS", "DM", "DS", "OS LAB [LAB-5]", "OS LAB [LAB-5]", "OS LAB [LAB-5]", "OS LAB [LAB-5]"],
                "Friday":    ["PT", "PT", "OOPS", "DS", "OS", "FODS", "ST", "TT"],
                "Saturday":  ["OS", "DM", "FODS", "OOPS", "PET", "PET", "MEN", "LIB"]
            },
            "courses": [
                ("1", "24UMA302", "Discrete Mathematics", "Ms.N.Premalatha,AP/S&H", "5"),
                ("2", "24UCS301", "Data Structures", "Ms.M.Malarvizhi,AP/CSE", "5"),
                ("3", "24UCS302", "Object Oriented Programming", "Ms.T.Kiruthiga,AP/CSE", "5"),
                ("4", "24UCS303", "Operating Systems", "Ms.P.Vijaya,AP/CSE", "5"),
                ("5", "24UCSI301", "Foundation of Data Science", "Mr.P.T.Prithivirajan,AP/CSE / Ms.B.Jeeva,AP/CSE(S)", "5+2"),
                ("6", "24UCS311", "Data Structures Laboratory", "Ms.B.Jeeva,AP/CSE / Ms.M.Malarvizhi,AP/CSE(S)", "4"),
                ("7", "24UCS312", "Object Oriented Programming Lab", "Ms.T.Kiruthiga,AP/CSE / Ms.A.Punithavathi,AP/CSE(S)", "4"),
                ("8", "24UCS313", "Operating Systems Laboratory", "Ms.S.Sathiya,AP/CSE / Ms.P.Vijaya,AP/CSE(S)", "4"),
                ("9", "24UCS314", "Skill Development Laboratory-I", "Mr.S.Gowtham,AP/CSE / Ms.A.Punithavathi,AP/CSE(S)", "2"),
                ("10", "LIB", "Library", "Dr.S.E.Rajarajan,Librarian", "1"),
                ("11", "PET", "Physical Education Training (PET)", "Mr.S.Tamilselvan", "1"),
                ("12", "TT", "Technical Training (TT)", "Ms.J.Uma,AP/CSE", "1"),
                ("13", "PT", "Placement Training (PT)", "Placement Team", "2")
            ]
        },
        {
            "class": "II-B",
            "sem": "III",
            "hall": "107",
            "advisor": "Ms.M.Malarvizhi, AP/CSE",
            "schedule": {
                "Monday":    ["DM", "DS", "FSD LAB [LAB-7]", "FSD LAB [LAB-7]", "OOPS", "OS", "SKILL LAB [LAB-3]", "SKILL LAB [LAB-3]"],
                "Tuesday":   ["OOPS", "FODS", "DM", "DS", "OS LAB [LAB-5]", "OS LAB [LAB-5]", "OS LAB [LAB-5]", "OS LAB [LAB-5]"],
                "Wednesday": ["FODS", "DM", "OS", "OOPS", "DS LAB [LAB-1]", "DS LAB [LAB-1]", "DS LAB [LAB-1]", "DS LAB [LAB-1]"],
                "Thursday":  ["OS", "DS", "DM", "FODS", "OOPS LAB [LAB-2]", "OOPS LAB [LAB-2]", "OOPS LAB [LAB-2]", "OOPS LAB [LAB-2]"],
                "Friday":    ["DS", "OOPS", "OS", "FODS", "SR", "SR", "TT", "PT"],
                "Saturday":  ["DM", "DS", "OS", "PET", "PET", "PET", "MEN", "LIB"]
            },
            "courses": [
                ("1", "24UMA302", "Discrete Mathematics", "Ms.R.Rathna,AP/S&H", "5"),
                ("2", "24UCS301", "Data Structures", "Ms.M.Malarvizhi,AP/CSE", "5"),
                ("3", "24UCS302", "Object Oriented Programming", "Ms.K.Abinaya,AP/CSE", "5"),
                ("4", "24UCS303", "Operating Systems", "Ms.P.Vijaya,AP/CSE", "5"),
                ("5", "24UCSI301", "Foundation of Data Science", "Mr.P.T.Prithivirajan,AP/CSE / Ms.S.Sathiya,AP/CSE(S)", "5+2"),
                ("6", "24UCS311", "Data Structures Laboratory", "Ms.M.Malarvizhi,AP/CSE / Ms.B.Jeeva,AP/CSE(S)", "4"),
                ("7", "24UCS312", "Object Oriented Programming Lab", "Ms.K.Abinaya,AP/CSE / Ms.R.Illakkiyavani,AP/CSE(S)", "4"),
                ("8", "24UCS313", "Operating Systems Laboratory", "Ms.P.Vijaya,AP/CSE / Mr.V.Ragumuniraja,AP/CSE(S)", "4"),
                ("9", "24UCS314", "Skill Development Laboratory-I", "Ms.A.Punithavathi,AP/CSE / Mr.S.Gowtham,AP/CSE(S)", "2"),
                ("10", "LIB", "Library", "Dr.S.E.Rajarajan,Librarian", "1"),
                ("11", "PET", "Physical Education Training (PET)", "Mr.S.Tamilselvan", "1"),
                ("12", "TT", "Technical Training (TT)", "Ms.B.Jeeva,AP/CSE", "1"),
                ("13", "PT", "Placement Training (PT)", "Placement Team", "2")
            ]
        },
        {
            "class": "III-A",
            "sem": "V",
            "hall": "118",
            "advisor": "Mr.V.Ragumuniraja, AP/CSE",
            "schedule": {
                "Monday":    ["CD", "CN", "AI LAB [LAB-8]", "AI LAB [LAB-8]", "FSD", "SKILL LAB [LAB-3]", "SKILL LAB [LAB-3]", "PET"],
                "Tuesday":   ["FSD", "CD", "PT", "PT", "CN LAB [LAB-6]", "CN LAB [LAB-6]", "CN LAB [LAB-6]", "CN LAB [LAB-6]"],
                "Wednesday": ["HVE", "FSD", "BOT", "CD", "CN LAB [LAB-6]", "CN LAB [LAB-6]", "CN LAB [LAB-6]", "CN LAB [LAB-6]"],
                "Thursday":  ["CN", "CD", "PT", "PT", "FSD LAB [LAB-7]", "FSD LAB [LAB-7]", "FSD LAB [LAB-7]", "FSD LAB [LAB-7]"],
                "Friday":    ["BOT", "CN", "VS", "VS", "FSD LAB [LAB-7]", "FSD LAB [LAB-7]", "FSD LAB [LAB-7]", "FSD LAB [LAB-7]"],
                "Saturday":  ["HVE", "FSD", "BOT", "CN", "CD", "MEN/HVE", "LIB", "MC-I/BOT"]
            },
            "courses": [
                ("1", "24UCS501", "Computer Networks", "Ms.J.Jenifer,AP/CSE", "5"),
                ("2", "24UCS502", "Full Stack Development", "Ms.R.Madhumitha,Lecturer/CSE", "5"),
                ("3", "24UCS301", "Compiler Design", "Ms.J.Uma,AP/CSE", "5"),
                ("4", "24UCSP502", "Virtualization", "Dr.A.M.Ravishankkar,Prof/CSE / Ms.R.Madhumitha,Lecturer/CSE(S)", "5+2"),
                ("5", "24UGE501", "Human Values and Ethics", "Ms.B.Jeeva,AP/CSE", "4"),
                ("6", "24UECO03", "Basics of IOT", "Mr.V.Ragumuniraja,AP/CSE", "4"),
                ("7", "24UMC804", "Disaster Risk Reduction", "Mr.V.Ragumuniraja,AP/CSE", "1"),
                ("8", "24UCS511", "Computer Networks Laboratory", "Ms.J.Jenifer,AP/CSE / Ms.K.Abinaya,AP/CSE(S)", "4"),
                ("9", "24UCS512", "Full Stack Development Lab", "Ms.R.Madhumitha,Lecturer/CSE / Mr.S.Gowtham,AP/CSE(S)", "4"),
                ("10", "24UCS513", "Skill Development Laboratory-II", "Ms.S.Ragadharsini,AP/CSE / Ms.M.Dharani,Lecturer/CSE(S)", "2"),
                ("11", "LIB", "Library", "Dr.S.E.Rajarajan,Librarian", "1"),
                ("12", "PET", "Physical Education Training (PET)", "Mr.S.Tamilselvan", "1"),
                ("13", "PT", "Placement Training (PT)", "Placement Team", "4")
            ]
        },
        {
            "class": "III-B",
            "sem": "V",
            "hall": "108",
            "advisor": "Ms.K.ABINAYA, AP/CSE",
            "schedule": {
                "Monday":    ["BOT", "STA", "CD", "FSD", "CN LAB [LAB-6]", "CN LAB [LAB-6]", "CN LAB [LAB-6]", "CN LAB [LAB-6]"],
                "Tuesday":   ["CN", "FSD", "AI LAB [LAB-8]", "AI LAB [LAB-8]", "HVE", "BOT", "STA", "HVE"],
                "Wednesday": ["CD", "CN", "PT", "PT", "FSD LAB [LAB-7]", "FSD LAB [LAB-7]", "FSD LAB [LAB-7]", "FSD LAB [LAB-7]"],
                "Thursday":  ["FSD", "BOT", "CN", "CD", "STA", "PET", "SKILL LAB [LAB-3]", "SKILL LAB [LAB-3]"],
                "Friday":    ["STA", "CD", "PT", "PT", "CN LAB [LAB-6]", "CN LAB [LAB-6]", "CN LAB [LAB-6]", "CN LAB [LAB-6]"],
                "Saturday":  ["HVE", "CN", "CD", "LIB", "MC-I/BOT", "MEN/HVE", "FSD", "STA"]
            },
            "courses": [
                ("1", "24UCS501", "Computer Networks", "Ms.J.Jenifer,AP/CSE", "5"),
                ("2", "24UCS502", "Full Stack Development", "Ms.R.Madhumitha,Lecturer/CSE", "5"),
                ("3", "24UCS301", "Compiler Design", "Ms.J.Uma,AP/CSE", "5"),
                ("4", "24UCSP501", "Software Testing and Automation", "Ms.R.Anieshma,AP/CSE / Ms.J.Uma,AP/CSE(S)", "5+2"),
                ("5", "24UGE501", "Human Values and Ethics", "Dr.J.Vinodhini,AP/S&H", "4"),
                ("6", "24UECO03", "Basics of IOT", "Ms.K.Abinaya,AP/CSE", "4"),
                ("7", "24UMC804", "Disaster Risk Reduction", "Ms.K.Abinaya,AP/CSE", "1"),
                ("8", "24UCS511", "Computer Networks Laboratory", "Ms.M.Dharani,Lecturer/CSE / Ms.J.Jenifer,AP/CSE(S)", "4"),
                ("9", "24UCS512", "Full Stack Development Lab", "Ms.R.Illakkiyavani,AP/CSE / Ms.R.Madhumitha,Lecturer/CSE(S)", "4"),
                ("10", "24UCS513", "Skill Development Laboratory-II", "Ms.R.Anieshma,AP/CSE / Ms.S.Ragadharsini,AP/CSE(S)", "2"),
                ("11", "LIB", "Library", "Dr.S.E.Rajarajan,Librarian", "1"),
                ("12", "PET", "Physical Education Training (PET)", "Mr.S.Tamilselvan", "1"),
                ("13", "PT", "Placement Training (PT)", "Placement Team", "4")
            ]
        },
        {
            "class": "IV-A",
            "sem": "VII",
            "hall": "207",
            "advisor": "Ms.R.ANIESHMA, AP/CSE",
            "schedule": {
                "Monday":    ["MDA", "HVE", "POM", "ITA", "AI LAB [LAB-8]", "AI LAB [LAB-8]", "AI LAB [LAB-8]", "AI LAB [LAB-8]"],
                "Tuesday":   ["TIF", "ITA", "POM", "MDA", "SKILL LAB [LAB-3]", "SKILL LAB [LAB-3]", "SKILL LAB [LAB-3]", "SKILL LAB [LAB-3]"],
                "Wednesday": ["ITA", "HVE", "MDA", "TIF", "PT", "PT", "PT", "PT"],
                "Thursday":  ["POM", "MDA", "TIF", "ITA", "AI LAB [LAB-8]", "AI LAB [LAB-8]", "AI LAB [LAB-8]", "AI LAB [LAB-8]"],
                "Friday":    ["HVE", "ITA", "TIF", "POM", "SKILL LAB [LAB-3]", "SKILL LAB [LAB-3]", "SKILL LAB [LAB-3]", "SKILL LAB [LAB-3]"],
                "Saturday":  ["TIF", "MDA", "POM", "HVE", "TT", "TT", "TT", "TT"]
            },
            "courses": [
                ("1", "GE3791", "Human Values and Ethics", "Mr.P.Sivakumar,AP/S&H", "4"),
                ("2", "GE3751", "Principles of Management", "Ms.B.Jeeva,AP/CSE", "5"),
                ("3", "AI3021", "IT in Agricultural System", "Mr.S.Gowtham,AP/CSE", "5"),
                ("4", "OFD352", "Traditional Indian Foods", "Ms.R.Anieshma,AP/CSE", "5"),
                ("5", "OMG355", "Multivariate Data Analysis-IV", "V.V.Vishnupriya,AP/CSE", "5"),
                ("6", "CS3711", "Summer internship", "Ms.R.Anieshma,AP/CSE", "-"),
                ("7", "TT", "Technical Training (TT)", "Ms.R.Anieshma,AP/CSE", "2"),
                ("8", "PT", "Placement Training (PT)", "Placement Team", "22")
            ]
        }
    ]
    
    for cdata in classes_data:
        pdf.add_page()
        pdf.page_header(
            class_name=cdata["class"],
            sem=cdata["sem"],
            hall=cdata["hall"],
            advisor=cdata["advisor"]
        )
        
        # Grid layout
        col_widths = [25, 16, 26, 26, 10, 26, 26, 14, 26, 26, 10, 26, 26]
        col_headers = [
            "Days/Hours",
            "09.00-\n09.05",
            "1\n09.05-\n09.55",
            "2\n09.55-\n10.45",
            "10.45 -\n11.00\nBreak",
            "3\n11.00-\n11.45",
            "4\n11.45-\n12.30",
            "12.30 -\n01.15\nLunch break",
            "5\n01.15-\n02.00",
            "6\n02.00-\n02.45",
            "2.45 -\n3.00\nbreak",
            "7\n03.00-\n03.45",
            "8\n03.45-\n04.30"
        ]
        
        # Draw table header
        pdf.set_font("Helvetica", "B", 7)
        x_offset = 10
        y_offset = pdf.get_y()
        max_h = 13
        
        # Draw columns
        for i, (width, header) in enumerate(zip(col_widths, col_headers)):
            pdf.set_xy(x_offset, y_offset)
            pdf.cell(width, max_h, "", border=1)
            
            # Print text inside the cells
            pdf.set_xy(x_offset, y_offset + 1)
            pdf.multi_cell(width, 3.5, header, border=0, align="C")
            x_offset += width
            
        y_offset += max_h
        pdf.set_font("Helvetica", "", 7.5)
        
        # Store cell data coordinates for merged cells (Orientation, Break, Lunch, Break2)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        
        # Draw day rows
        for d_idx, day in enumerate(days):
            pdf.set_xy(10, y_offset)
            # Day header cell
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(col_widths[0], 10, day, border=1, align="C")
            pdf.set_font("Helvetica", "", 7.5)
            
            x_pos = 10 + col_widths[0]
            
            # Column cells
            day_schedule = cdata["schedule"][day]
            p_idx = 0
            
            # Col 1: Orientation
            # Draw empty cells first, we will draw vertical text on top
            pdf.set_xy(x_pos, y_offset)
            pdf.cell(col_widths[1], 10, "", border=1)
            x_pos += col_widths[1]
            
            # P1 & P2
            for j in range(2):
                pdf.set_xy(x_pos, y_offset)
                pdf.cell(col_widths[2+j], 10, day_schedule[p_idx], border=1, align="C")
                x_pos += col_widths[2+j]
                p_idx += 1
                
            # Col 4: Morning Break
            pdf.set_xy(x_pos, y_offset)
            pdf.cell(col_widths[4], 10, "", border=1)
            x_pos += col_widths[4]
            
            # P3 & P4
            for j in range(2):
                pdf.set_xy(x_pos, y_offset)
                pdf.cell(col_widths[5+j], 10, day_schedule[p_idx], border=1, align="C")
                x_pos += col_widths[5+j]
                p_idx += 1
                
            # Col 7: Lunch Break
            pdf.set_xy(x_pos, y_offset)
            pdf.cell(col_widths[7], 10, "", border=1)
            x_pos += col_widths[7]
            
            # P5 & P6
            for j in range(2):
                pdf.set_xy(x_pos, y_offset)
                # Shrink text if it is a lab session
                subject = day_schedule[p_idx]
                if "[" in subject:
                    pdf.set_font("Helvetica", "B", 6.8)
                else:
                    pdf.set_font("Helvetica", "", 7.5)
                pdf.cell(col_widths[8+j], 10, subject, border=1, align="C")
                x_pos += col_widths[8+j]
                p_idx += 1
                
            # Col 10: Break 2
            pdf.set_xy(x_pos, y_offset)
            pdf.cell(col_widths[10], 10, "", border=1)
            x_pos += col_widths[10]
            
            # P7 & P8
            for j in range(2):
                pdf.set_xy(x_pos, y_offset)
                subject = day_schedule[p_idx]
                if "[" in subject:
                    pdf.set_font("Helvetica", "B", 6.8)
                else:
                    pdf.set_font("Helvetica", "", 7.5)
                pdf.cell(col_widths[11+j], 10, subject, border=1, align="C")
                x_pos += col_widths[11+j]
                p_idx += 1
                
            y_offset += 10
            
        # Draw vertical rotated text on top of merged cells
        # 1. Orientation Class (Col 1)
        # Total height of MON-SAT is 6 rows * 10mm = 60mm
        # Width is 16mm. Midpoint: x = 10 + 25 + 8 = 43
        # y start = y_offset - 60. Center: y_mid = y_start + 30
        y_start_grid = y_offset - 60
        pdf.set_font("Helvetica", "B", 7)
        # Rotate and place
        with pdf.rotation(90, 10 + col_widths[0] + col_widths[1]/2, y_start_grid + 30):
            pdf.text(10 + col_widths[0] + col_widths[1]/2 - 17, y_start_grid + 30 + 2, "Orientation Class")
            
        # 2. Morning Break (Col 4)
        # Center x = 10 + 25 + 16 + 26 + 26 + 5 = 108
        x_mbreak = 10 + sum(col_widths[:4]) + col_widths[4]/2
        with pdf.rotation(90, x_mbreak, y_start_grid + 30):
            pdf.text(x_mbreak - 15, y_start_grid + 30 + 1.5, "10.45 - 11.00 Break")
            
        # 3. Lunch Break (Col 7)
        x_lunch = 10 + sum(col_widths[:7]) + col_widths[7]/2
        with pdf.rotation(90, x_lunch, y_start_grid + 30):
            pdf.text(x_lunch - 16, y_start_grid + 30 + 1.5, "12.30 - 01.15 Lunch break")
            
        # 4. Break 2 (Col 10)
        x_break2 = 10 + sum(col_widths[:10]) + col_widths[10]/2
        with pdf.rotation(90, x_break2, y_start_grid + 30):
            pdf.text(x_break2 - 12, y_start_grid + 30 + 1.5, "2.45 - 3.00 break")
            
        # Draw Course details table at the bottom
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 8)
        
        # Table of courses header
        c_widths = [12, 25, 100, 115, 25]
        c_headers = ["S.No.", "Course code", "Course Name", "Faculty Name", "Hrs/Week"]
        
        y_table = pdf.get_y()
        pdf.set_xy(10, y_table)
        pdf.set_fill_color(245, 245, 245)
        for w, text in zip(c_widths, c_headers):
            pdf.cell(w, 5, text, border=1, align="C", fill=True)
        pdf.ln(5)
        
        pdf.set_font("Helvetica", "", 7.5)
        for c_row in cdata["courses"]:
            if pdf.get_y() > 185: # prevent spillover
                break
            pdf.set_x(10)
            pdf.cell(c_widths[0], 4, c_row[0], border=1, align="C")
            pdf.cell(c_widths[1], 4, c_row[1], border=1, align="C")
            pdf.cell(c_widths[2], 4, c_row[2], border=1)
            pdf.cell(c_widths[3], 4, c_row[3], border=1)
            pdf.cell(c_widths[4], 4, c_row[4], border=1, align="C")
            pdf.ln(4)
            
        # Draw bottom signatures (reposition to bottom-ish)
        pdf.set_font("Helvetica", "B", 8.5)
        y_sig = 188
        pdf.set_xy(15, y_sig)
        pdf.cell(50, 4, "Dept.Timetable Coordinator", border=0, align="C")
        pdf.set_xy(80, y_sig)
        pdf.cell(40, 4, "HoD", border=0, align="C")
        pdf.set_xy(140, y_sig)
        pdf.cell(50, 4, "Academic Coordinator", border=0, align="C")
        pdf.set_xy(215, y_sig)
        pdf.cell(50, 4, "Principal", border=0, align="C")
        
        # Add line graphics for signatures
        pdf.set_draw_color(0, 0, 0)
        # Dept Timetable Coordinator signature line
        pdf.line(20, y_sig - 4, 60, y_sig - 4)
        # HOD signature line
        pdf.line(90, y_sig - 4, 110, y_sig - 4)
        # Academic Coordinator line
        pdf.line(145, y_sig - 4, 185, y_sig - 4)
        # Principal line
        pdf.line(225, y_sig - 4, 255, y_sig - 4)
        
        # Draw handwritten-like signature marks or dates below signature text
        pdf.set_font("Courier", "I", 8)
        pdf.text(25, y_sig - 5, "P.Priya")
        pdf.text(25, y_sig - 1, "02/07/26")
        pdf.text(92, y_sig - 5, "Dr.K.G")
        pdf.text(92, y_sig - 1, "2/7/26")
        pdf.text(152, y_sig - 5, "S.Gowtham")
        pdf.text(230, y_sig - 5, "Principal")

    # Save PDF
    pdf.output("timetable_clean.pdf")
    print("timetable_clean.pdf generated successfully with 5 pages.")

if __name__ == "__main__":
    generate_clean_timetable()
