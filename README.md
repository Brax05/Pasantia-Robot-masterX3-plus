# yahboomcar_pet_behavior

Paquete ROS1 para agregar una capa de control tipo mascota sobre el
ROSMASTER/Yahboom X3 Plus.

Este paquete no reemplaza el driver base del robot. Su funcion es actuar como
una capa intermedia segura entre backend, UI o LLM y los topics reales del
robot.

## Objetivo

El paquete separa tres responsabilidades:

- observar contexto del robot, como LiDAR, joystick y navegacion;
- recibir comandos de alto nivel y convertirlos en movimiento seguro;
- publicar telemetria central para backend, UI y pruebas.

El flujo recomendado es:

```text
backend/UI/LLM
  -> /robot/command
  -> robot_controller.py
  -> /cmd_vel
  -> base fisica del robot
```

El backend no debe publicar directo en `/cmd_vel`, porque saltaria watchdog,
limites de velocidad, emergency stop, bloqueo por obstaculo y modo manual.

## Estado Actual

Semana 1:

- control fisico seguro por `/robot/command`;
- limites de velocidad y duracion de comandos;
- watchdog;
- parada explicita;
- emergency stop;
- telemetria base por `/robot/status`.

Semana 2:

- estabilidad del movimiento fisico;
- LiDAR integrado dentro del flujo normal;
- eventos para backend por `/robot/events`;
- callbacks ROS preparados para recibir comandos, estado y sensores;
- contrato basico para que backend lea estado y reaccione a eventos.

## Nodos Principales

- `scripts/autopilot_monitor.py`: observa contexto del robot. Lee LiDAR,
  joystick, goals y estado de navegacion. No mueve motores.
- `scripts/robot_controller.py`: recibe comandos seguros, valida condiciones y
  publica velocidad final hacia `/cmd_vel`.
- `scripts/robot_status.py`: junta estado del controlador, sensores y robot en
  un solo JSON publicado en `/robot/status`.

## Launch Principal

El main recomendado es:

```bash
roslaunch yahboomcar_pet_behavior pet_robot.launch
```

Ese launch levanta la capa completa: monitor, controlador seguro y telemetria.

## Topics Importantes

```text
/robot/command                 entrada segura de comandos JSON
/robot/cmd_vel_safe            entrada Twist segura para pruebas locales
/robot/emergency_stop          parada de emergencia
/robot/controller_state        estado interno del controlador
/robot/events                  eventos, rechazos y paradas
/robot/status                  telemetria central para backend/UI
/pet_behavior/autopilot_state  estado observado por el monitor
/pet_behavior/autopilot_event  eventos del monitor
/cmd_vel                       salida final hacia driver/motores
/scan                          datos del LiDAR
/vel_raw                       velocidad real reportada por la base
/odom_raw                      odometria cruda
/voltage                       bateria
```

## Comandos Soportados

Los comandos entran como JSON por `/robot/command`.

```text
move_forward
move_backward
turn_left
turn_right
move
stop
emergency_stop
clear_emergency_stop
set_mode
```

Modos soportados:

```text
idle
manual
autonomous
backend_controlled
```

## Archivos De Configuracion

- `config/robot_control.yaml`: topics, limites de movimiento, watchdog,
  tiempos de comando, emergency stop y telemetria.
- `config/autopilot_base.yaml`: parametros del monitor pasivo y LiDAR.

## Pruebas

La guia operativa esta separada en:

- [`README_PRUEBAS.md`](README_PRUEBAS.md)

Ese archivo contiene los pasos para levantar ROS, probar movimiento fisico,
verificar `/robot/status`, revisar `/robot/events` y confirmar el contrato para
backend.
