from django.contrib.auth.models import User
from junta_vecinos.models import Vecino, AdministradorComuna
from django.utils import timezone
from datetime import datetime, timedelta
import random

# Datos de prueba
nombres_hombres = [
    "Juan", "Diego", "José", "Pedro", "Carlos", "Miguel", "Francisco", "Jorge",
    "Luis", "Alberto", "Andrés", "Felipe", "Ricardo", "Eduardo", "Sergio",
    "Gabriel", "Mario", "Cristián", "Daniel", "Pablo"
]

nombres_mujeres = [
    "María", "Ana", "Carolina", "Patricia", "Claudia", "Andrea", "Paula",
    "Francisca", "Daniela", "Valentina", "Camila", "Catalina", "Isabel",
    "Carmen", "Sofía", "Victoria", "Javiera", "Constanza", "Gabriela", "Fernanda"
]

apellidos = [
    "González", "Rodríguez", "Muñoz", "Rojas", "Díaz", "Pérez", "Soto", "Silva",
    "Contreras", "López", "Martínez", "Sepúlveda", "Morales", "Torres", "Araya",
    "Flores", "Espinoza", "Valenzuela", "Castillo", "Ramírez", "Acosta", "Álvarez",
    "Vega", "Campos", "Vásquez", "Tapia", "Pizarro", "Santos", "Reyes", "Guzmán"
]

calles = [
    "Av. Irarrázaval", "Los Alerces", "Las Encinas", "Los Olmos", "Pedro de Valdivia",
    "José Pedro Alessandri", "Grecia", "Macul", "Quilín", "Vicuña Mackenna",
    "Los Presidentes", "Santa Julia", "Walker Martínez", "La Florida", "Rojas Magallanes",
    "Trinidad", "Concha y Toro", "Santa Rosa", "Eyzaguirre", "Nonato Coo"
]

def generar_rut():
    """Genera un RUT chileno válido"""
    while True:
        # Genera un número aleatorio entre 5.000.000 y 25.000.000
        num = random.randint(5000000, 25000000)
        suma = 0
        multiplicador = 2
        
        # Calcula dígito verificador
        temp = str(num)
        reverso = map(int, reversed(temp))
        for digito in reverso:
            suma += digito * multiplicador
            multiplicador += 1
            if multiplicador == 8:
                multiplicador = 2
        
        digito = 11 - (suma % 11)
        if digito == 11:
            dv = '0'
        elif digito == 10:
            dv = 'K'
        else:
            dv = str(digito)
        
        rut = f"{num}-{dv}"
        
        # Verifica si el RUT ya existe
        if not Vecino.objects.filter(rut=rut).exists():
            return rut

def generar_telefono():
    """Genera un número de teléfono chileno válido"""
    return f"+569{random.randint(10000000, 99999999)}"

def generar_direccion():
    """Genera una dirección aleatoria"""
    calle = random.choice(calles)
    numero = random.randint(100, 9999)
    return f"{calle} {numero}"

def generar_fecha_nacimiento():
    """Genera una fecha de nacimiento para una persona mayor de 18 años"""
    hoy = timezone.now().date()
    inicio = hoy - timedelta(days=80*365)  # 80 años atrás
    fin = hoy - timedelta(days=18*365)     # 18 años atrás
    dias = random.randint(0, (fin - inicio).days)
    return inicio + timedelta(days=dias)

def crear_vecinos(cantidad):
    """Crea la cantidad especificada de vecinos"""
    comunas = ['ÑUÑOA', 'PUENTE_ALTO', 'LA_FLORIDA']
    admin_comunas = {comuna: AdministradorComuna.objects.get(comuna=comuna) for comuna in comunas}
    
    vecinos_creados = 0
    errores = []
    
    while vecinos_creados < cantidad:
        try:
            # Decide género para mantener nombres consistentes
            es_mujer = random.choice([True, False])
            nombre = random.choice(nombres_mujeres if es_mujer else nombres_hombres)
            apellido1 = random.choice(apellidos)
            apellido2 = random.choice(apellidos)
            
            email = f"{nombre.lower()}.{apellido1.lower()}{random.randint(1, 999)}@example.com"
            
            # Verifica si el email ya existe
            if User.objects.filter(email=email).exists():
                continue
                
            # Crea el usuario
            user = User.objects.create_user(
                username=email,
                email=email,
                password="vecino123",
                first_name=nombre,
                last_name=f"{apellido1} {apellido2}",
                is_active=True
            )
            
            # Selecciona una comuna aleatoria
            comuna = random.choice(comunas)
            
            # Crea el vecino
            vecino = Vecino.objects.create(
                user=user,
                nombres=nombre,
                apellidos=f"{apellido1} {apellido2}",
                direccion=generar_direccion(),
                telefono=generar_telefono(),
                fecha_nacimiento=generar_fecha_nacimiento(),
                rut=generar_rut(),
                comuna=comuna,
                administrador=admin_comunas[comuna]
            )
            
            vecinos_creados += 1
            print(f"Vecino creado {vecinos_creados}/{cantidad}: {nombre} {apellido1}")
            
        except Exception as e:
            errores.append(f"Error al crear vecino: {str(e)}")
            continue
    
    return errores

# Para ejecutar el script:
if __name__ == "__main__":
    errores = crear_vecinos(100)
    if errores:
        print("\nErrores encontrados:")
        for error in errores:
            print(error)
    else:
        print("\nTodos los vecinos fueron creados exitosamente!")