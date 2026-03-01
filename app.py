# برنامج تحليل البيانات المكانية - مشروع تخرج

import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
import zipfile
import io
import os
import tempfile
import warnings

warnings.filterwarnings("ignore")

# إعدادات الصفحة
st.set_page_config(
    page_title="تطبيق الربط المكاني والوصفي | GIS Join Tool",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# تنسيقات الواجهة (CSS)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
    }

    .main-header {
        background: linear-gradient(135deg, #0B3968 0%, #002244 100%);
        padding: 2.5rem;
        border-radius: 0;
        text-align: center;
        margin-bottom: 2.5rem;
        border-bottom: 5px solid #FFC400;
    }

    .main-header h1 {
        color: #FFFFFF;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }

    .main-header p {
        color: #9DC4E6;
        font-size: 1.1rem;
        margin-top: 0.8rem;
    }

    .info-card {
        background: linear-gradient(135deg, #16213e, #1a1a2e);
        border: 1px solid #0f3460;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    .success-box {
        background: linear-gradient(135deg, #0d3b2e, #1a5c3a);
        border: 1px solid #27ae60;
        border-radius: 10px;
        padding: 1rem;
        color: #2ecc71;
        margin: 0.5rem 0;
    }

    .error-box {
        background: linear-gradient(135deg, #3b0d0d, #5c1a1a);
        border: 1px solid #e74c3c;
        border-radius: 10px;
        padding: 1rem;
        color: #e74c3c;
        margin: 0.5rem 0;
    }

    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid #dee2e6;
        color: #0B3968;
    }

    .step-badge {
        background-color: #3E92F2;
        color: white;
        border-radius: 4px;
        padding: 4px 12px;
        font-weight: 600;
    }

    .stSelectbox > div > div {
        background-color: #16213e;
        border: 1px solid #0f3460;
        color: white;
    }

    div[data-testid="stSidebar"] {
        background-color: #0B3968;
    }

    .stButton>button {
        background-color: #3E92F2 !important;
        color: white !important;
        border-radius: 5px !important;
        border: none !important;
    }

    .sidebar-section {
        background: rgba(15, 52, 96, 0.3);
        border-radius: 10px;
        padding: 0.8rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(233, 69, 96, 0.2);
    }

    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# الدوال المساعدة للتحليل

def load_shapefile_from_zip(uploaded_zip) -> gpd.GeoDataFrame | None:
    # دالة لقراءة ملفات الشيب فايل من المضغوط
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_bytes = uploaded_zip.read()
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                zf.extractall(tmp_dir)

            # البحث عن ملف .shp داخل المجلد المؤقت
            shp_files = []
            for root, dirs, files in os.walk(tmp_dir):
                for f in files:
                    if f.lower().endswith(".shp"):
                        shp_files.append(os.path.join(root, f))

            if not shp_files:
                st.error("❌ لم يتم العثور على ملف .shp داخل ملف ZIP!")
                return None

            gdf = gpd.read_file(shp_files[0])
            return gdf
    except zipfile.BadZipFile:
        st.error("❌ الملف المرفوع ليس ملف ZIP صالحاً!")
        return None
    except Exception as e:
        st.error(f"❌ خطأ في قراءة ملف Shapefile: {str(e)}")
        return None


def load_geojson(uploaded_file) -> gpd.GeoDataFrame | None:
    # دالة لقراءة ملفات الجيوجيسون
    try:
        content = uploaded_file.read()
        gdf = gpd.read_file(io.BytesIO(content))
        if gdf.empty:
            st.error("❌ ملف GeoJSON فارغ!")
            return None
        return gdf
    except Exception as e:
        st.error(f"❌ خطأ في قراءة ملف GeoJSON: {str(e)}")
        return None


def render_map(gdf: gpd.GeoDataFrame, title: str, color: str = "#e94560") -> None:
    """
    عرض GeoDataFrame على خريطة Folium صغيرة.
    """
    try:
        # تحويل إلى WGS84 إذا لزم الأمر
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)

        # حساب مركز الخريطة
        bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles="CartoDB dark_matter",
        )

        # إضافة الطبقة
        folium.GeoJson(
            gdf.__geo_interface__,
            name=title,
            style_function=lambda x: {
                "fillColor": color,
                "color": color,
                "weight": 1.5,
                "fillOpacity": 0.4,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=[c for c in gdf.columns if c != "geometry"][:3],
                aliases=[c for c in gdf.columns if c != "geometry"][:3],
                localize=True,
            ),
        ).add_to(m)

        # ضبط حدود الخريطة
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        st_folium(m, width=None, height=320, returned_objects=[])
    except Exception as e:
        st.warning(f"⚠️ تعذّر عرض الخريطة: {str(e)}")


def gdf_to_geojson_bytes(gdf: gpd.GeoDataFrame) -> bytes:
    """
    تحويل GeoDataFrame إلى بايتات GeoJSON للتنزيل.
    """
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return gdf.to_json().encode("utf-8")


def validate_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    تصحيح الهندسات غير الصالحة.
    """
    if not gdf.is_valid.all():
        gdf["geometry"] = gdf["geometry"].buffer(0)
    return gdf


# واجهة البرنامج الرئيسية
st.markdown(
    """
    <div class="main-header">
        <h1>🗺️ أداة الربط المكاني والوصفي</h1>
        <p>أداة تحليل البيانات المكانية الاحترافية | ارفع ملفاتك وابدأ التحليل الآن</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# الشريط الجانبي (منطقة التحكم)
with st.sidebar:
    st.markdown("## 🛠️ لوحة التحكم")

    st.markdown("---")
    st.markdown("### 📋 دليل الاستخدام")
    st.markdown(
        """
        1. **ارفع الملف الأساسي (Left)** بصيغة ZIP أو GeoJSON
        2. **ارفع الملف الثانوي (Right)** بصيغة ZIP أو GeoJSON
        3. **اختر نوع الربط**: مكاني أو وصفي
        4. **اضغط زر التنفيذ** وشاهد النتائج
        5. **نزّل النتيجة** بصيغة GeoJSON
        """
    )
    st.markdown("---")

    # ── رفع الملف الأساسي ──
    st.markdown("### 📂 الملف الأول (Left)")
    left_file_type = st.radio(
        "نوع الملف الأساسي",
        ["Shapefile (ZIP)", "GeoJSON"],
        key="left_type",
        horizontal=True,
    )

    if left_file_type == "Shapefile (ZIP)":
        left_upload = st.file_uploader(
            "ارفع ملف Shapefile (ZIP)",
            type=["zip"],
            key="left_zip",
            help="يجب أن يحتوي الـ ZIP على ملفات .shp و .dbf و .shx",
        )
    else:
        left_upload = st.file_uploader(
            "ارفع ملف GeoJSON",
            type=["geojson", "json"],
            key="left_geojson",
            help="ملف بصيغة GeoJSON صالح",
        )

    st.markdown("---")

    # ── رفع الملف الثانوي ──
    st.markdown("### 📂 الملف الثاني (Right)")
    right_file_type = st.radio(
        "نوع الملف الثانوي",
        ["Shapefile (ZIP)", "GeoJSON"],
        key="right_type",
        horizontal=True,
    )

    if right_file_type == "Shapefile (ZIP)":
        right_upload = st.file_uploader(
            "ارفع ملف Shapefile (ZIP)",
            type=["zip"],
            key="right_zip",
            help="يجب أن يحتوي الـ ZIP على ملفات .shp و .dbf و .shx",
        )
    else:
        right_upload = st.file_uploader(
            "ارفع ملف GeoJSON",
            type=["geojson", "json"],
            key="right_geojson",
            help="ملف بصيغة GeoJSON صالح",
        )

    st.markdown("---")

    # ── نوع الربط ──
    st.markdown("### 🔗 نوع الربط")
    join_type = st.selectbox(
        "اختر نوع الربط",
        ["الربط المكاني", "الربط الوصفي"],
        key="join_type",
    )

# ─────────────────────────────────────────────
# تحميل الملفات وعرضها
# ─────────────────────────────────────────────

left_gdf = None
right_gdf = None

# ── تحميل الملف الأساسي ──
if left_upload is not None:
    with st.spinner("⏳ جارٍ تحميل الملف الأساسي..."):
        if left_file_type == "Shapefile (ZIP)":
            left_gdf = load_shapefile_from_zip(left_upload)
        else:
            left_gdf = load_geojson(left_upload)

    if left_gdf is not None:
        left_gdf = validate_geometry(left_gdf)

# ── تحميل الملف الثانوي ──
if right_upload is not None:
    with st.spinner("⏳ جارٍ تحميل الملف الثانوي..."):
        if right_file_type == "Shapefile (ZIP)":
            right_gdf = load_shapefile_from_zip(right_upload)
        else:
            right_gdf = load_geojson(right_upload)

    if right_gdf is not None:
        right_gdf = validate_geometry(right_gdf)

# عرض البيانات والخرائط
if left_gdf is not None or right_gdf is not None:
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### 🟥 عرض الملف الأول")
        if left_gdf is not None:
            st.success(f"✅ تم تحميل {len(left_gdf):,} معلم بنجاح")
            st.markdown("**أول 5 صفوف من البيانات:**")
            st.dataframe(
                left_gdf.drop(columns="geometry").head(5),
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("**معاينة على الخريطة:**")
            render_map(left_gdf, "الملف الأساسي", "#e94560")
        else:
            st.info("⬆️ ارفع الملف الأساسي من الشريط الجانبي")

    with col_r:
        st.markdown("#### 🟦 عرض الملف الثاني")
        if right_gdf is not None:
            st.success(f"✅ تم تحميل {len(right_gdf):,} معلم بنجاح")
            st.markdown("**أول 5 صفوف من البيانات:**")
            st.dataframe(
                right_gdf.drop(columns="geometry").head(5),
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("**معاينة على الخريطة:**")
            render_map(right_gdf, "الملف الثانوي", "#3498db")
        else:
            st.info("⬆️ ارفع الملف الثانوي من الشريط الجانبي")

# عمليات الربط والتحليل
result_gdf = None

if left_gdf is not None and right_gdf is not None:
    st.markdown("---")
    st.markdown("## 🔗 خيارات الربط")

    # ─── الربط المكاني ───
    if join_type == "الربط المكاني (Spatial Join)":
        st.markdown("### 📍 إعدادات الربط المكاني")
        col1, col2 = st.columns(2)

        with col1:
            predicate = st.selectbox(
                "نوع العلاقة المكانية",
                [
                    "intersects",
                    "contains",
                    "within",
                    "overlaps",
                    "crosses",
                    "touches",
                    "covers",
                    "covered_by",
                ],
                help="اختر العلاقة الهندسية بين الطبقتين",
            )

        with col2:
            how_spatial = st.selectbox(
                "كيفية الربط",
                ["left", "right", "inner"],
                help="left: الاحتفاظ بجميع معالم الطبقة اليسرى، inner: المتقاطعة فقط",
            )

        col_btn = st.columns([1, 2, 1])
        with col_btn[1]:
            run_spatial = st.button(
                "▶️ تنفيذ الربط المكاني",
                use_container_width=True,
                type="primary",
            )

        if run_spatial:
            with st.spinner("⏳ جارٍ تنفيذ الربط المكاني..."):
                try:
                    # توحيد نظام الإحداثيات
                    left_proj = left_gdf.copy()
                    right_proj = right_gdf.copy()

                    if left_proj.crs is None:
                        left_proj = left_proj.set_crs(epsg=4326)
                    if right_proj.crs is None:
                        right_proj = right_proj.set_crs(epsg=4326)

                    # تحويل إلى نفس نظام الإحداثيات
                    right_proj = right_proj.to_crs(left_proj.crs)

                    result_gdf = gpd.sjoin(
                        left_proj,
                        right_proj,
                        how=how_spatial,
                        predicate=predicate,
                    )

                    # حذف عمود index_right إذا وُجد
                    if "index_right" in result_gdf.columns:
                        result_gdf = result_gdf.drop(columns=["index_right"])
                    if "index_left" in result_gdf.columns:
                        result_gdf = result_gdf.drop(columns=["index_left"])

                    st.session_state["result_gdf"] = result_gdf
                    st.success("✅ تم تنفيذ الربط المكاني بنجاح!")
                except Exception as e:
                    st.error(f"❌ خطأ في الربط المكاني: {str(e)}")

    # ─── الربط الوصفي ───
    else:
        st.markdown("### 📋 إعدادات الربط الوصفي")

        left_cols = [c for c in left_gdf.columns if c != "geometry"]
        right_cols = [c for c in right_gdf.columns if c != "geometry"]

        col1, col2, col3 = st.columns(3)

        with col1:
            left_key = st.selectbox(
                "حقل الربط في الملف الأساسي",
                left_cols,
                help="اختر العمود المشترك في الملف الأساسي",
            )

        with col2:
            right_key = st.selectbox(
                "حقل الربط في الملف الثانوي",
                right_cols,
                help="اختر العمود المشترك في الملف الثانوي",
            )

        with col3:
            how_attr = st.selectbox(
                "نوع الربط الوصفي",
                ["left", "right", "inner", "outer"],
                help="left: كل سجلات اليسار، inner: المتطابقة فقط، outer: الجميع",
            )

        col_btn2 = st.columns([1, 2, 1])
        with col_btn2[1]:
            run_attr = st.button(
                "▶️ تنفيذ الربط الوصفي",
                use_container_width=True,
                type="primary",
            )

        if run_attr:
            with st.spinner("⏳ جارٍ تنفيذ الربط الوصفي..."):
                try:
                    # تحويل مفتاح الربط إلى نص لتجنب أخطاء النوع
                    left_copy = left_gdf.copy()
                    right_copy = right_gdf.drop(columns="geometry")

                    left_copy[left_key] = left_copy[left_key].astype(str)
                    right_copy[right_key] = right_copy[right_key].astype(str)

                    merged = left_copy.merge(
                        right_copy,
                        left_on=left_key,
                        right_on=right_key,
                        how=how_attr,
                        suffixes=("_left", "_right"),
                    )

                    result_gdf = gpd.GeoDataFrame(merged, geometry="geometry", crs=left_gdf.crs)
                    st.session_state["result_gdf"] = result_gdf
                    st.success("✅ تم تنفيذ الربط الوصفي بنجاح!")
                except Exception as e:
                    st.error(f"❌ خطأ في الربط الوصفي: {str(e)}")

# منطقة عرض النتائج النهائية

# استعادة النتيجة من الجلسة إذا كانت موجودة
if "result_gdf" in st.session_state:
    result_gdf = st.session_state["result_gdf"]

if result_gdf is not None:
    st.markdown("---")
    st.markdown("## 📊 نتائج الربط")

    row_count = len(result_gdf)

    if row_count == 0:
        st.warning("⚠️ لم يتم العثور على أي تطابق بين الملفين. جرّب تغيير معايير الربط.")
    else:
        # بطاقات إحصائية
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("📌 عدد النتائج", f"{row_count:,} سجل")
        with m2:
            st.metric("📐 عدد الأعمدة", f"{len(result_gdf.columns) - 1} عمود")
        with m3:
            geom_types = result_gdf.geometry.geom_type.unique()
            st.metric("🔷 نوع الهندسة", ", ".join(geom_types))

        st.markdown("### 🗂️ جدول النتائج")
        result_display = result_gdf.drop(columns="geometry", errors="ignore")
        st.dataframe(result_display, use_container_width=True, hide_index=True)

        st.markdown("### 🗺️ خريطة النتائج")
        render_map(result_gdf, "نتائج الربط", "#f39c12")

        # ── تنزيل النتيجة ──
        st.markdown("---")
        st.markdown("## ⬇️ تنزيل النتيجة")

        try:
            geojson_bytes = gdf_to_geojson_bytes(result_gdf)
            st.download_button(
                label="📥 تنزيل النتيجة بصيغة GeoJSON",
                data=geojson_bytes,
                file_name="join_result.geojson",
                mime="application/geo+json",
                use_container_width=True,
                type="primary",
            )
        except Exception as e:
            st.error(f"❌ خطأ في إعداد الملف للتنزيل: {str(e)}")

# تذييل الصفحة
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #0B3968; padding: 1rem; font-size: 0.95rem; font-weight: 600;'>
        🗺️ أداة الربط المكاني والوصفي | برمجة وتطوير أنس محمد زقوت
    </div>
    """,
    unsafe_allow_html=True,
)
