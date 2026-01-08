# blueprints/planes/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, HiddenField, FileField, SelectField
from wtforms.validators import Length, Optional
from wtforms.validators import DataRequired

# blueprints/planes/forms.py
from flask_wtf import FlaskForm
from wtforms import FileField, SelectField, SubmitField
from wtforms.validators import DataRequired

class ImportExcelForm(FlaskForm):
    """Importa un .xlsx para la dimensión activa (sin selector de alcance)."""
    file = FileField("Archivo .xlsx", validators=[DataRequired()])
    submit = SubmitField("Importar")

class EditRowForm(FlaskForm):
    # Ajusta/duplica según campos que quieras editar rápidamente
    Brecha = TextAreaField("Brecha", validators=[Optional(), Length(max=10000)])
    Nombre_Actividad_Hito_Diego = TextAreaField("Nombre_Actividad_Hito_Diego", validators=[Optional(), Length(max=20000)])
    Nombre_Actividad_Hito_Luis = TextAreaField("Nombre_Actividad_Hito_Luis", validators=[Optional(), Length(max=20000)])
    submit = SubmitField("Guardar")

class CreateRowForm(FlaskForm):
    # Campos mínimos; agrega según necesites
    Dimension = StringField("Dimension", validators=[Optional(), Length(max=255)])
    Subdimension = StringField("Subdimension", validators=[Optional(), Length(max=255)])
    Subdimensión = StringField("Subdimensión", validators=[Optional(), Length(max=255)])
    indicador = StringField("indicador", validators=[Optional(), Length(max=1000)])
    Brecha = TextAreaField("Brecha", validators=[Optional(), Length(max=10000)])
    Iniciativa = StringField("Iniciativa", validators=[Optional(), Length(max=1000)])
    Nombre_Iniciativa = StringField("Nombre_Iniciativa", validators=[Optional(), Length(max=1000)])
    Nombre_Actividad_Hito_Diego = TextAreaField("Nombre_Actividad_Hito_Diego", validators=[Optional(), Length(max=20000)])
    Nombre_Actividad_Hito_Luis = TextAreaField("Nombre_Actividad_Hito_Luis", validators=[Optional(), Length(max=20000)])
    submit = SubmitField("Crear")
