# Deuda técnica por proyecto

Aplicación Streamlit para cargar un Excel, agrupar los registros por nombre de
proyecto y visualizar la deuda técnica. Los proyectos se clasifican como Front,
Back u Otros según el nombre.

## Ejecutar localmente

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

La aplicación solicita el archivo `.xlsx` en la barra lateral. Lee la hoja
`sheet1` (o, si no existe, la primera hoja) y espera los encabezados en la fila
4, incluidas las columnas `component` y `Deuda tecnica en minutos`.

## Desplegar en Streamlit Community Cloud

1. Publica este repositorio en GitHub.
2. En [Streamlit Community Cloud](https://share.streamlit.io/), inicia sesión
   con GitHub y selecciona **Create app**.
3. Selecciona este repositorio, la rama `main` y el archivo `app.py`.
4. Pulsa **Deploy**.

El Excel no forma parte del repositorio: cada usuario debe cargarlo en la app.
Antes de compartir el enlace, confirma que la política de tu organización permite
procesar ese archivo en un servicio externo. Para datos internos o personales,
usa una plataforma aprobada por la organización y limita el acceso a la app.
