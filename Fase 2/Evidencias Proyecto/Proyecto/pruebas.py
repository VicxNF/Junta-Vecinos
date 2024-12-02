from datetime import datetime, timedelta
from django.utils.timezone import now
from django.contrib.auth.models import User
from junta_vecinos.models import (
    AdministradorComuna,
    Vecino,
    TokenRegistro,
    LoginAttempt,
    SolicitudCertificado,
    CertificadoResidencia,
    ProyectoVecinal,
    PostulacionProyecto,
    Noticia,
    Espacio,
    Reserva,
    ActividadVecinal,
    InscripcionActividad,
)

# 1. Crear un Administrador de Comuna
def test_crear_administrador_comuna():
    user = User.objects.create_user(username="admin_nunoa", password="admin1234")
    admin = AdministradorComuna.objects.create(
        user=user,
        comuna="ÑUÑOA",
        presidente_nombre="Juan",
        presidente_apellidos="Pérez",
        presidente_rut="12.345.678-9",
    )
    print(f"Administrador de comuna creado: {admin}")

# 2. Registrar un Vecino asociado a una comuna
def test_crear_vecino():
    user = User.objects.create_user(username="vecino1", password="vecino1234")
    admin = AdministradorComuna.objects.get(comuna="ÑUÑOA")
    vecino = Vecino.objects.create(
        user=user,
        nombres="María",
        apellidos="Gómez",
        direccion="Calle Falsa 123",
        telefono="987654321",
        fecha_nacimiento="1990-05-15",
        rut="22.333.444-5",
        comuna="ÑUÑOA",
        administrador=admin,
    )
    print(f"Vecino creado: {vecino}")

# 3. Registrar un intento de inicio de sesión
def test_crear_login_attempt():
    user = User.objects.get(username="vecino1")
    login_attempt = LoginAttempt.objects.create(
        user=user,
        ip_address="192.168.1.1",
        was_successful=False,
    )
    print(f"Intento de inicio de sesión registrado: {login_attempt}")

# 4. Solicitar un Certificado de Residencia
def test_solicitar_certificado():
    vecino = Vecino.objects.get(rut="22.333.444-5")
    solicitud = SolicitudCertificado.objects.create(
        vecino=vecino,
        motivo="Necesito un certificado para trámite bancario.",
        foto_carnet_frente="ruta/a/imagen1.jpg",
        foto_carnet_atras="ruta/a/imagen2.jpg",
        documento_residencia="ruta/a/documento.pdf",
    )
    print(f"Solicitud de certificado creada: {solicitud}")

# 5. Crear una Noticia para una comuna
def test_crear_noticia():
    admin = AdministradorComuna.objects.get(comuna="ÑUÑOA")
    noticia = Noticia.objects.create(
        titulo="Nueva actividad vecinal en Ñuñoa",
        contenido="Se realizará una actividad para promover la cultura local.",
        comuna=admin,
    )
    print(f"Noticia creada: {noticia}")

# 6. Crear un Espacio y una Reserva
def test_crear_espacio_y_reserva():
    admin = AdministradorComuna.objects.get(comuna="ÑUÑOA")
    espacio = Espacio.objects.create(
        nombre="Centro Comunitario",
        descripcion="Un espacio para actividades vecinales.",
        capacidad=50,
        ubicacion="Av. Principal 456",
        precio_por_hora=10.00,
        comuna=admin,
    )
    user = User.objects.get(username="vecino1")
    reserva = Reserva.objects.create(
        usuario=user,
        espacio=espacio,
        fecha="2024-12-01",
        hora_inicio="10:00",
        hora_fin="12:00",
        monto_pagado=20.00,
    )
    print(f"Espacio creado: {espacio}")
    print(f"Reserva creada: {reserva}")

# 7. Registrar un Proyecto Vecinal y su postulación
def test_crear_proyecto_vecinal_y_postulacion():
    vecino = Vecino.objects.get(rut="22.333.444-5")
    proyecto = ProyectoVecinal.objects.create(
        vecino=vecino,
        propuesta="Construcción de parque infantil",
        descripcion="Un parque para niños en el barrio.",
    )
    postulacion = PostulacionProyecto.objects.create(
        proyecto=proyecto,
        vecino=vecino,
        motivo="Quiero participar porque beneficia a mi familia.",
    )
    print(f"Proyecto vecinal creado: {proyecto}")
    print(f"Postulación al proyecto creada: {postulacion}")

# 8. Crear una Actividad Vecinal e Inscripción
def test_crear_actividad_e_inscripcion():
    admin = AdministradorComuna.objects.get(comuna="ÑUÑOA")
    actividad = ActividadVecinal.objects.create(
        titulo="Cine al aire libre",
        descripcion="Proyección de películas en el parque.",
        fecha="2024-12-10",
        hora_inicio="20:00",
        hora_fin="23:00",
        lugar="Plaza Ñuñoa",
        cupo_maximo=100,
        comuna=admin,
    )
    vecino = Vecino.objects.get(rut="22.333.444-5")
    inscripcion = InscripcionActividad.objects.create(
        actividad=actividad,
        vecino=vecino,
    )
    print(f"Actividad creada: {actividad}")
    print(f"Inscripción creada: {inscripcion}")
