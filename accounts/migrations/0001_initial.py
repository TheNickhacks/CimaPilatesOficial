import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email", models.EmailField(max_length=100, unique=True)),
                ("password_hash", models.CharField(max_length=255)),
                ("nombre", models.CharField(blank=True, max_length=100, null=True)),
                ("apellido", models.CharField(blank=True, max_length=100, null=True)),
                ("nombre_completo", models.CharField(blank=True, max_length=100, null=True)),
                ("rut", models.CharField(blank=True, max_length=15, null=True, unique=True)),
                ("fecha_nacimiento", models.DateField(blank=True, null=True)),
                ("genero", models.CharField(blank=True, max_length=20, null=True)),
                ("telefono", models.CharField(blank=True, max_length=20, null=True)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("administrador", "Administrador"),
                            ("recepcionista", "Recepcionista"),
                            ("profesor", "Profesor"),
                            ("alumna", "Alumna"),
                        ],
                        db_column="rol",
                        default="alumna",
                        max_length=20,
                    ),
                ),
                ("consentimiento_marketing", models.BooleanField(default=False)),
                ("fecha_consentimiento", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("foto_perfil_path", models.CharField(blank=True, max_length=255, null=True)),
                ("foto_perfil_data", models.BinaryField(blank=True, null=True)),
                ("foto_perfil_mime_type", models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                "db_table": "usuarios",
                "managed": False,
            },
        ),
    ]
