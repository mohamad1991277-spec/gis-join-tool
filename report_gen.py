from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# دالة لتعديل اتجاه النص للعربي
def rtl_text(p):
    p_pr = p._element.get_or_add_pPr()
    bidi = OxmlElement('w:bidi')
    bidi.set(qn('w:val'), '1')
    p_pr.append(bidi)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

def make_report():
    docx = Document()
    
    # عنوان البحث
    h = docx.add_heading("بحث مشروع نظم المعلومات الجغرافية - دمج البيانات", 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = docx.add_paragraph("إعداد الطالب: [اسم الطالب]")
    rtl_text(p)
    p = docx.add_paragraph("تحت إشراف قسم نظم المعلومات")
    rtl_text(p)

    docx.add_heading("1. فكرة البرنامج", level=1)
    p = docx.add_paragraph("البرنامج يهدف لعمل ربط بين الملفات الجغرافية (شيب فايل وجيوجيسون) بطريقتين: الربط المكاني والربط الوصفي. الفكرة إننا نسهل عملية التحليل بدون تعقيد البرامج الكبيرة.")
    rtl_text(p)

    docx.add_heading("2. كيف سوينا المشروع", level=1)
    p = docx.add_paragraph("استخدمنا لغة بايثون مع مكتبة Streamlit عشان نسوي الواجهة، ومكتبة GeoPandas عشان نعالج البيانات والخرائط. البرنامج يقدر يقرأ الملفات المضغوطة ZIP ويطلع منها البيانات ويرسمها على الخريطة.")
    rtl_text(p)

    docx.add_heading("3. معالجة الأخطاء", level=1)
    p = docx.add_paragraph("اشتغلنا على حل مشاكل الملفات التالفة أو اللي فيها أنظمة إحداثيات مختلفة، وعملنا أكواد برمجية تحول الإحداثيات تلقائياً عشان ما يطلع خطأ عند الربط.")
    rtl_text(p)

    docx.add_heading("4. التحديات والمشاكل", level=1)
    p = docx.add_paragraph("أصعب تحدي كان التعامل مع الملفات المضغوطة ZIP والتأكد من استخراجها وقراءتها بشكل صحيح في كل مرة، بالإضافة لمشكلة اختلاف أنظمة الإحداثيات بين الملفات، وتم حلها برمجياً لضمان دقة الربط.")
    rtl_text(p)

    docx.add_heading("5. اللمسات النهائية والمظهر الاحترافي", level=1)
    p = docx.add_paragraph("تم إخفاء القوائم الافتراضية لأطر العمل (Streamlit Menu) والأزرار البرمجية من الواجهة باستخدام أكواد CSS مخصصة، وذلك لضمان ظهور التطبيق كموقع ويب مستقل ومحتوي على تصميم خاص وفريد، مما يعزز من المظهر الاحترافي للمشروع.")
    rtl_text(p)

    docx.save("GIS_Project_Report_Arabic.docx")
    print("تم حفظ التقرير باسم GIS_Project_Report_Arabic.docx")

if __name__ == "__main__":
    make_report()
