# README_PRUEBAS - Semana 1 y Semana 2

Objetivo: validar en una prueba normal lo construido en Semana 1 y Semana 2.

Esta prueba cubre:

- control fisico seguro por `/robot/command`;
- telemetria aislada por `/robot/status`;
- eventos para backend por `/robot/events`;
- LiDAR activo dentro de la seguridad normal;
- watchdog, duracion de comandos y parada;
- emergency stop;
- contrato basico que consumiran backend, UI o LLM.

Orden recomendado:

```text
1. Preparar terminales ROS.
2. Levantar la capa completa del robot.
3. Mirar /robot/status y /robot/events.
4. Poner modo backend_controlled.
5. Probar avance, retroceso, giros y parada.
6. Probar emergency stop.
7. Confirmar campos minimos para backend.
```

## Preparar Terminales

En cada terminal nueva donde uses `roslaunch`, `rostopic`, `rosnode`, `rosrun`
o `rosparam`, preparar primero el entorno:

```bash
export ROS_MASTER_URI=http://127.0.0.1:11311
export ROS_IP=127.0.0.1
cd ~/yahboomcar_ws
source devel/setup.bash
```

## Prueba Normal

Terminal A, levantar la capa completa:

```bash
export ROS_MASTER_URI=http://127.0.0.1:11311
export ROS_IP=127.0.0.1
cd ~/yahboomcar_ws
source devel/setup.bash
roslaunch yahboomcar_pet_behavior pet_robot.launch
```

En esta Yahboom X3 Plus la Rosmaster responde por una ruta serial estable de
`/dev/serial/by-path/...2.4.2...`; el launch la configura en el bringup. Evitar
dejar dos `pet_robot.launch` vivos a la vez porque ROS reemplaza nodos con el
mismo nombre.

Terminal B, ver telemetria:

```bash
export ROS_MASTER_URI=http://127.0.0.1:11311
export ROS_IP=127.0.0.1
cd ~/yahboomcar_ws
source devel/setup.bash
rostopic echo /robot/status
```

Terminal C, ver eventos:

```bash
export ROS_MASTER_URI=http://127.0.0.1:11311
export ROS_IP=127.0.0.1
cd ~/yahboomcar_ws
source devel/setup.bash
rostopic echo /robot/events
```

Terminal D, limpiar estado y poner modo backend:

```bash
export ROS_MASTER_URI=http://127.0.0.1:11311
export ROS_IP=127.0.0.1
cd ~/yahboomcar_ws
source devel/setup.bash
rostopic pub -1 /robot/emergency_stop std_msgs/Bool "data: false"
rostopic pub -1 /robot/command std_msgs/String \
"data: '{\"command\":\"set_mode\",\"mode\":\"backend_controlled\",\"source\":\"physical_test\"}'"
```

Enviar avance:

```bash
rostopic pub -1 /robot/command std_msgs/String \
"data: '{\"command\":\"move_forward\",\"speed\":0.10,\"duration\":1.0,\"source\":\"physical_test\"}'"
```

Enviar retroceso:

```bash
rostopic pub -1 /robot/command std_msgs/String \
"data: '{\"command\":\"move_backward\",\"speed\":0.10,\"duration\":1.0,\"source\":\"physical_test\"}'"
```

Girar izquierda:

```bash
rostopic pub -1 /robot/command std_msgs/String \
"data: '{\"command\":\"turn_left\",\"angular\":0.45,\"duration\":1.0,\"source\":\"physical_test\"}'"
```

Girar derecha:

```bash
rostopic pub -1 /robot/command std_msgs/String \
"data: '{\"command\":\"turn_right\",\"angular\":0.45,\"duration\":1.0,\"source\":\"physical_test\"}'"
```

Resultado esperado:

```text
/robot/events muestra command_accepted
commanded_velocity.linear_x sube cerca de 0.16 al avanzar
raw_velocity cambia si la base reporta movimiento real
last_stop_reason termina como command_duration_elapsed
```

Nota: aunque el comando de prueba pida `speed: 0.10`, el controlador eleva el
avance no cero a `min_effective_linear_x` para superar la zona muerta de los
motores. El valor esta en `config/robot_control.yaml`.

Parar explicitamente:

```bash
rostopic pub -1 /robot/command std_msgs/String \
"data: '{\"command\":\"stop\",\"source\":\"physical_test\"}'"
```

## Prueba De Emergency Stop

Activar parada de emergencia:

```bash
rostopic pub -1 /robot/command std_msgs/String \
"data: '{\"command\":\"emergency_stop\",\"active\":true,\"source\":\"physical_test\"}'"
```

Intentar avanzar mientras esta activa:

```bash
rostopic pub -1 /robot/command std_msgs/String \
"data: '{\"command\":\"move_forward\",\"speed\":0.10,\"duration\":1.0,\"source\":\"physical_test\"}'"
```

Resultado esperado:

```text
/robot/events muestra command_rejected
last_error: "emergency_stop_active"
emergency_stop: true
state: "emergency"
```

Limpiar emergency stop:

```bash
rostopic pub -1 /robot/command std_msgs/String \
"data: '{\"command\":\"clear_emergency_stop\",\"source\":\"physical_test\"}'"
rostopic pub -1 /robot/command std_msgs/String \
"data: '{\"command\":\"set_mode\",\"mode\":\"backend_controlled\",\"source\":\"physical_test\"}'"
```

## Campos Minimos Para Backend

Mientras Terminal B muestra `/robot/status`, confirmar que existan estos campos:

```text
state
mode
emergency_stop
joy_active
front_blocked
front_range
last_command
last_source
last_error
last_stop_reason
topics
commanded_velocity
raw_velocity
battery_voltage
tf
```

Mientras Terminal C muestra `/robot/events`, confirmar estos eventos durante la
prueba:

```text
controller_ready
mode_changed
command_accepted
robot_stop
command_rejected
```

Con esto queda probado que el backend puede:

```text
enviar comandos por /robot/command
leer estado actual desde /robot/status
reaccionar a aceptados, rechazos y paradas desde /robot/events
```

Al terminar, cerrar el launch de Terminal A con `Ctrl+C`.
