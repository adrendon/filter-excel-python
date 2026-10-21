from io import BytesIO
from zipfile import BadZipFile

import pandas as pd
import streamlit as st

EXPECTED_COLUMNS = {"component", "Deuda tecnica en minutos"}


def classify_project(project_name: str) -> str:
    normalized_name = project_name.upper()
    if "FRONT" in normalized_name:
        return "Front"
    if "BACK" in normalized_name:
        return "Back"
    return "Otros"


@st.cache_data(show_spinner=False)
def load_projects(workbook_data: bytes) -> pd.DataFrame:
    try:
        workbook = pd.ExcelFile(BytesIO(workbook_data), engine="openpyxl")
    except (BadZipFile, ValueError, OSError) as exc:
        raise ValueError("El archivo no parece ser un Excel .xlsx válido.") from exc

    sheet_name = next(
        (name for name in workbook.sheet_names if name.casefold() == "sheet1"),
        workbook.sheet_names[0] if workbook.sheet_names else None,
    )
    if sheet_name is None:
        raise ValueError("El archivo no contiene hojas para leer.")

    df = pd.read_excel(workbook, sheet_name=sheet_name, header=3)
    missing_columns = EXPECTED_COLUMNS.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Faltan columnas requeridas en la hoja: {missing}.")
    if "issue_id" not in df.columns:
        df["issue_id"] = pd.NA

    projects = df.loc[:, ["component", "Deuda tecnica en minutos", "issue_id"]].copy()
    projects["project_name"] = (
        projects["component"]
        .astype("string")
        .str.split(":", n=1)
        .str[0]
        .str.strip()
    )
    projects = projects.dropna(subset=["project_name"])
    projects = projects[projects["project_name"] != ""]
    projects["category"] = projects["project_name"].map(classify_project)
    projects["debt_minutes"] = pd.to_numeric(
        projects["Deuda tecnica en minutos"], errors="coerce"
    )

    result = (
        projects.groupby("project_name", as_index=False)
        .agg(
            category=("category", "first"),
            deuda_total=("debt_minutes", "sum"),
            cantidad_issues=("issue_id", "count"),
            issues_sin_deuda=("debt_minutes", lambda values: int(values.isna().sum())),
        )
        .sort_values(["deuda_total", "project_name"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return result


st.set_page_config(
    page_title="Deuda técnica por proyecto",
    page_icon="📊",
    layout="wide",
)

st.title("Deuda técnica por proyecto")
st.caption(
    "Carga el Excel para explorar los nombres de proyectos, su categoría y deuda técnica."
)

with st.sidebar:
    st.header("Archivo y filtros")
    uploaded_file = st.file_uploader(
        "Selecciona el archivo Excel",
        type=["xlsx"],
        help="El archivo se procesa en esta sesión; no está incluido en el repositorio.",
    )

if uploaded_file is None:
    st.info("Carga un archivo Excel .xlsx para comenzar.")
    st.stop()

try:
    projects = load_projects(uploaded_file.getvalue())
except (BadZipFile, ValueError, OSError, KeyError) as exc:
    st.error(f"No se pudo procesar el Excel: {exc}")
    st.stop()

if projects.empty:
    st.warning("No se encontraron proyectos en la hoja seleccionada.")
    st.stop()

with st.sidebar:
    category = st.selectbox("Categoría", ["Todos", "Front", "Back", "Otros"])
    debt_min, debt_max = st.slider(
        "Rango de deuda técnica (minutos)",
        min_value=0,
        max_value=max(1, int(projects["deuda_total"].max())),
        value=(0, max(1, int(projects["deuda_total"].max()))),
    )

filtered = projects[projects["deuda_total"].between(debt_min, debt_max)]
if category != "Todos":
    filtered = filtered[filtered["category"] == category]

metric_columns = st.columns(5)
metric_columns[0].metric("Proyectos", len(filtered))
metric_columns[1].metric("Front", int((filtered["category"] == "Front").sum()))
metric_columns[2].metric("Back", int((filtered["category"] == "Back").sum()))
metric_columns[3].metric("Otros", int((filtered["category"] == "Otros").sum()))
metric_columns[4].metric(
    "Deuda total", f"{filtered['deuda_total'].sum():,.0f} min"
)

chart_column, category_column = st.columns([1.8, 1])
with chart_column:
    st.subheader("Proyectos con más deuda")
    top_projects = filtered.nlargest(15, "deuda_total").sort_values("deuda_total")
    if top_projects.empty:
        st.info("No hay proyectos para los filtros seleccionados.")
    else:
        st.bar_chart(
            top_projects.set_index("project_name")["deuda_total"],
            x_label="Proyecto",
            y_label="Deuda técnica (minutos)",
        )

with category_column:
    st.subheader("Proyectos por categoría")
    category_counts = (
        filtered["category"]
        .value_counts()
        .rename_axis("Categoría")
        .reset_index(name="Proyectos")
    )
    st.dataframe(category_counts, hide_index=True, width="stretch")

st.subheader("Nombres de proyectos")
if filtered.empty:
    st.info("No hay proyectos para los filtros seleccionados.")
else:
    st.dataframe(
        filtered[["project_name"]].rename(columns={"project_name": "Proyecto"}),
        hide_index=True,
        width="stretch",
    )

with st.expander("Ver detalle de deuda e issues"):
    st.dataframe(
        filtered[
            ["project_name", "category", "deuda_total", "cantidad_issues", "issues_sin_deuda"]
        ].rename(
            columns={
                "project_name": "Proyecto",
                "category": "Categoría",
                "deuda_total": "Deuda total (min)",
                "cantidad_issues": "Issues",
                "issues_sin_deuda": "Issues sin deuda informada",
            }
        ),
        hide_index=True,
        width="stretch",
    )
