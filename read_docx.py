from docx import Document

doc = Document("GIS_Project_Report.docx")
for para in doc.paragraphs:
    print(para.text)
