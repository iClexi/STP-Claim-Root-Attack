# STP Claim Root Attack Lab

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-red)
![Lab](https://img.shields.io/badge/Environment-GNS3%20%7C%20IOSvL2-orange)
![Attack](https://img.shields.io/badge/Attack-STP%20Claim%20Root-purple)
![Mitigation](https://img.shields.io/badge/Mitigation-BPDU%20Guard%20%7C%20Root%20Guard-darkgreen)
![Status](https://img.shields.io/badge/Use-Controlled%20Lab-yellow)
![Security](https://img.shields.io/badge/Topic-Layer%202%20Security-purple)

## Aviso de uso responsable

Este proyecto fue desarrollado únicamente con fines educativos, académicos y de laboratorio controlado.

El script debe ejecutarse solamente en redes propias, laboratorios autorizados o entornos virtuales como GNS3, EVE-NG, PNETLab o ambientes internos de prueba.

No debe utilizarse en redes públicas, empresariales o de terceros sin autorización explícita.

---

## Archivos del repositorio

| Archivo                                                          | Descripción                                                                                                  |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| [`stp-claim-root.py`](./stp-claim-root.py)                       | Script principal utilizado para ejecutar el ataque STP Claim Root desde Kali Linux.                          |
| [`mitigacion-stp-claim-root.md`](./mitigacion-stp-claim-root.md) | Documento técnico con la mitigación contra STP Claim Root usando BPDU Guard y Root Guard.                    |
| [`README.md`](./README.md)                                       | Documentación principal del laboratorio, uso del script, evidencia esperada, mitigación y flujo recomendado. |

---

## Descripción

Este laboratorio demuestra un ataque **STP Claim Root**, donde una máquina atacante conectada a un puerto de acceso envía BPDUs falsas con una prioridad superior a la del Root Bridge legítimo.

STP, Spanning Tree Protocol, es un protocolo de capa 2 utilizado para evitar loops en redes conmutadas. Para lograrlo, STP elige un **Root Bridge** y calcula una topología lógica libre de bucles.

El ataque consiste en enviar BPDUs falsificadas anunciando un Root Bridge con prioridad más baja, por ejemplo prioridad `0`, para que los switches crean que el atacante representa el mejor root disponible.

En este laboratorio, Kali Linux envía BPDUs falsas hacia SW2. Como resultado, los switches aceptan un Root ID falso y recalculan la topología STP.

---

## Base del direccionamiento IP

El direccionamiento IP del laboratorio fue definido tomando como base la matrícula:

```text
20250845
```

Separando la matrícula en octetos, se obtuvo la dirección base:

```text
20.25.8.45
```

A partir de esta dirección se creó la red del laboratorio:

```text
20.25.8.0/24
```

---

## Objetivo del laboratorio

Demostrar cómo un atacante conectado a un puerto de acceso puede manipular STP enviando BPDUs superiores para reclamar el rol de Root Bridge.

---

## Objetivo del script

El script [`stp-claim-root.py`](./stp-claim-root.py) permite:

* Seleccionar la interfaz conectada al switch.
* Enviar BPDUs STP falsificadas.
* Anunciar una prioridad Root falsa.
* Anunciar una MAC falsa como Root Bridge.
* Forzar recálculos de la topología STP.
* Evidenciar cambios de Root ID, Root Port y estados de puertos.
* Validar mitigaciones como BPDU Guard y Root Guard.

---

## Topología utilizada

```text
                         +----------------+
                         |      R-1       |
                         | 20.25.8.45     |
                         | Fa0/0          |
                         +-------+--------+
                                 |
                                 | SW1 Gi0/0
                         +-------+--------+
                         |      SW1       |
                         | Root legítimo  |
                         +---+--------+---+
                             |        |
                SW1 Gi0/1    |        |    SW1 Gi0/2
                             |        |
                       SW2 Gi0/0    SW3 Gi0/0
                         +---+--------+---+
                         |                |
                         |                |
                         |                |
                         |  SW2 Gi0/1     | SW3 Gi0/1
                         +-------+--------+
                                 |
                                 |
                 +---------------+---------------+
                 |                               |
           SW2 Gi0/2                       SW3 Gi0/2
                 |                               |
              +--+---+                       +---+--+
              | Kali |                       | VPC1 |
              | .46  |                       | DHCP |
              +------+                       +------+
```

---

## Mapeo de conexiones

| Enlace | Equipo origen | Puerto origen | Equipo destino | Puerto destino |
| ------ | ------------- | ------------- | -------------- | -------------- |
| 1      | R-1           | Fa0/0         | SW1            | Gi0/0          |
| 2      | SW1           | Gi0/1         | SW2            | Gi0/0          |
| 3      | SW1           | Gi0/2         | SW3            | Gi0/0          |
| 4      | SW2           | Gi0/1         | SW3            | Gi0/1          |
| 5      | SW2           | Gi0/2         | Kali           | eth0           |
| 6      | SW3           | Gi0/2         | VPC1           | eth0           |

---

## Direccionamiento IP del laboratorio

| Dispositivo | Rol                   | Interfaz | Dirección IP  | Descripción                         |
| ----------- | --------------------- | -------- | ------------- | ----------------------------------- |
| R-1         | Gateway               | Fa0/0    | 20.25.8.45/24 | Router principal                    |
| SW1         | Root Bridge legítimo  | N/A      | N/A           | Switch raíz antes del ataque        |
| SW2         | Switch intermedio     | N/A      | N/A           | Switch conectado a Kali             |
| SW3         | Switch intermedio     | N/A      | N/A           | Switch conectado a la VPC           |
| Kali        | Atacante              | eth0     | 20.25.8.46/24 | Máquina que envía BPDUs falsas      |
| VPC1        | Cliente de validación | eth0     | DHCP o .47    | Equipo para pruebas de conectividad |

---

## Configuración IP base

### R-1

```cisco
enable
configure terminal

interface fastEthernet0/0
description LAN_20250845
ip address 20.25.8.45 255.255.255.0
no shutdown
exit

end
write memory
```

---

### Kali Linux

Si la interfaz conectada al switch es `eth0`:

```bash
sudo ip addr flush dev eth0
sudo ip addr add 20.25.8.46/24 dev eth0
sudo ip link set eth0 up
sudo ip route replace default via 20.25.8.45
```

Verificar:

```bash
ip -br addr
ping -c 4 20.25.8.45
```

---

### VPC1

Con IP fija:

```text
ip 20.25.8.47/24 20.25.8.45
```

Con DHCP:

```text
dhcp
show ip
```

---

## Configuración STP base

Para que el laboratorio sea claro, SW1 debe ser el Root Bridge legítimo antes del ataque.

### SW1

```cisco
enable
configure terminal

hostname SW1
spanning-tree mode pvst
spanning-tree vlan 1 priority 4096

interface gigabitEthernet0/0
description HACIA-R1
switchport mode access
exit

interface gigabitEthernet0/1
description HACIA-SW2
switchport mode trunk
exit

interface gigabitEthernet0/2
description HACIA-SW3
switchport mode trunk
exit

end
write memory
```

---

### SW2

```cisco
enable
configure terminal

hostname SW2
spanning-tree mode pvst
spanning-tree vlan 1 priority 32768

interface gigabitEthernet0/0
description HACIA-SW1
switchport mode trunk
exit

interface gigabitEthernet0/1
description HACIA-SW3
switchport mode trunk
exit

interface gigabitEthernet0/2
description HACIA-KALI
switchport mode access
exit

end
write memory
```

---

### SW3

```cisco
enable
configure terminal

hostname SW3
spanning-tree mode pvst
spanning-tree vlan 1 priority 32768

interface gigabitEthernet0/0
description HACIA-SW1
switchport mode trunk
exit

interface gigabitEthernet0/1
description HACIA-SW2
switchport mode trunk
exit

interface gigabitEthernet0/2
description HACIA-VPC1
switchport mode access
exit

end
write memory
```

---

## Verificación antes del ataque

En SW1, SW2 y SW3:

```cisco
show spanning-tree vlan 1
```

En SW1 debe aparecer:

```text
This bridge is the root
```

En SW2 y SW3 debe aparecer que el Root ID corresponde a SW1.

También se recomienda revisar:

```cisco
show spanning-tree vlan 1 detail
```

Valores importantes:

```text
Root ID
Bridge ID
Root Port
Number of topology changes
Time since last topology change
```

---

## Requisitos

### Sistema atacante

* Kali Linux
* Python 3
* Scapy instalado
* Permisos de superusuario
* Conectividad directa de capa 2 con SW2
* Interfaz conectada al puerto de acceso donde se ejecutará el ataque

### Dispositivos de red

* Tres switches Cisco IOSvL2
* Router Cisco o dispositivo gateway
* Topología con redundancia física entre switches
* STP activo en VLAN 1
* Laboratorio en GNS3, EVE-NG, PNETLab o entorno equivalente

---

## Verificar Scapy

```bash
python3 -c "import scapy; print('Scapy instalado')"
```

Si Scapy no está instalado:

```bash
sudo apt update
sudo apt install -y python3-scapy
```

---

## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/iClexi/STP-Claim-Root-Attack.git
cd STP-Claim-Root-Attack
```

Dar permisos de ejecución:

```bash
chmod +x stp-claim-root.py
```

Verificar sintaxis:

```bash
python3 -m py_compile stp-claim-root.py
```

---

## Uso básico

Ejecutar el script:

```bash
sudo python3 stp-claim-root.py
```

El script solicitará los valores necesarios de forma interactiva:

```text
Interfaz conectada al switch
Pausa entre BPDUs
Duración
Prioridad Root Bridge falsa
Prioridad Bridge falsa
MAC falsa del Root Bridge
MAC falsa del Bridge atacante
Port ID anunciado
```

Ejemplo recomendado:

```text
Interfaz: eth0
Pausa entre BPDUs: 1
Duración: 0
Prioridad Root falsa: 0
Prioridad Bridge falsa: 0
MAC Root falsa: 00:00:00:00:00:01
MAC Bridge falsa: 00:00:00:00:00:01
Port ID: 32769
```

---

## Funcionamiento técnico

STP elige el Root Bridge usando el Bridge ID, compuesto principalmente por:

```text
Prioridad STP + MAC del bridge
```

El valor más bajo gana.

Antes del ataque:

```text
SW1 Priority 4096
SW2 Priority 32768
SW3 Priority 32768
```

Durante el ataque, Kali anuncia:

```text
Root Priority 0
Root MAC 00:00:00:00:00:01
```

Como `0` es menor que `4096`, los switches consideran que el BPDU falso es superior y aceptan el Root ID anunciado por Kali.

---

## Evidencia esperada del ataque

Durante el ataque, en SW1, SW2 y SW3:

```cisco
show spanning-tree vlan 1
```

Resultado esperado:

```text
Root ID    Priority    0
           Address     0000.0000.0001
```

En SW2 se espera ver que el puerto hacia Kali se convierte en Root Port:

```text
Port        3 (GigabitEthernet0/2)
Gi0/2       Root FWD
```

En SW3 se puede observar que STP sigue evitando loops bloqueando un puerto alterno:

```text
Gi0/0       Altn BLK
```

Esto confirma que el ataque no necesariamente genera una tormenta broadcast, pero sí altera la elección del Root Bridge y recalcula la topología STP.

---

## Captura con tcpdump

En Kali, se puede capturar tráfico STP:

```bash
sudo tcpdump -eni eth0 ether dst 01:80:c2:00:00:00
```

También se puede usar:

```bash
sudo tcpdump -eni eth0 stp
```

Resultado esperado:

```text
STP 802.1d, Config, Flags
```

---

## Comandos de validación

### En SW1, SW2 y SW3

```cisco
terminal length 0
show spanning-tree vlan 1
show spanning-tree vlan 1 detail
show spanning-tree root
```

### En SW2

```cisco
show spanning-tree interface gigabitEthernet0/2 detail
show running-config interface gigabitEthernet0/2
```

### En Kali

```bash
ip -br addr
sudo python3 stp-claim-root.py
sudo tcpdump -eni eth0 ether dst 01:80:c2:00:00:00
```

### En VPC1

```text
ping 20.25.8.45
show ip
```

---

## Impacto esperado

El impacto del ataque puede incluir:

* Cambio del Root Bridge.
* Cambio del Root Port.
* Recalculo de la topología STP.
* Aumento de topology changes.
* Pérdida temporal de paquetes durante la reconvergencia.
* Posible inestabilidad en enlaces redundantes.
* Alteración del camino lógico de capa 2.

El ataque no siempre provoca una tormenta broadcast, porque STP puede seguir bloqueando un puerto alterno para evitar loops.

---

## Mitigación

La mitigación recomendada contra STP Claim Root es:

* BPDU Guard en puertos de acceso.
* Root Guard en enlaces donde nunca debe aparecer un Root Bridge superior.
* Definir explícitamente el Root Bridge legítimo.
* No conectar equipos finales a puertos sin protección STP.

La documentación completa de mitigación está disponible aquí:

* [`mitigacion-stp-claim-root.md`](./mitigacion-stp-claim-root.md)

---

## Configuración básica de mitigación

En el puerto hacia Kali, SW2 Gi0/2:

```cisco
enable
configure terminal

interface gigabitEthernet0/2
description HACIA-KALI-ATACANTE
switchport mode access
spanning-tree portfast
spanning-tree bpduguard enable
exit

end
write memory
```

En SW1, para evitar que un root superior aparezca por enlaces hacia otros switches:

```cisco
enable
configure terminal

interface gigabitEthernet0/1
description HACIA-SW2
spanning-tree guard root
exit

interface gigabitEthernet0/2
description HACIA-SW3
spanning-tree guard root
exit

end
write memory
```

---

## Verificación de la mitigación

Después de aplicar BPDU Guard, ejecutar nuevamente el ataque desde Kali.

Resultado esperado:

```text
%SPANTREE-2-BLOCK_BPDUGUARD
%PM-4-ERR_DISABLE: bpduguard error detected on Gi0/2
```

Comandos:

```cisco
show interfaces status
show spanning-tree interface gigabitEthernet0/2 detail
show logging
```

El puerto `Gi0/2` de SW2 debe quedar en estado `err-disabled`.

---

## Levantar el puerto después de BPDU Guard

Primero detener el ataque en Kali:

```bash
sudo pkill -f stp-claim-root
```

Luego en SW2:

```cisco
configure terminal
interface gigabitEthernet0/2
shutdown
no shutdown
exit
end
```

---

## Flujo recomendado para el video

1. Mostrar la topología en GNS3.
2. Mostrar nombre, matrícula, fecha y hora.
3. Mostrar direccionamiento IP del laboratorio.
4. Mostrar configuración STP base.
5. Mostrar que SW1 es el Root Bridge legítimo.
6. Mostrar estados STP en SW1, SW2 y SW3.
7. Ejecutar `stp-claim-root.py` desde Kali.
8. Mostrar que el Root ID cambió a prioridad `0` y MAC `0000.0000.0001`.
9. Mostrar que SW2 usa `Gi0/2` como Root Port.
10. Mostrar topology changes con `show spanning-tree vlan 1 detail`.
11. Detener el ataque.
12. Aplicar BPDU Guard en SW2 Gi0/2.
13. Ejecutar nuevamente el ataque.
14. Mostrar que el puerto cae por BPDU Guard.
15. Aplicar o explicar Root Guard como refuerzo.
16. Cerrar con una conclusión técnica.

---

## Troubleshooting

### El Root Bridge no cambia

Verificar que el puerto hacia Kali no tenga defensas activas:

```cisco
show running-config interface gigabitEthernet0/2
```

No debe tener todavía:

```text
spanning-tree bpduguard enable
spanning-tree guard root
switchport port-security
```

Verificar que Kali esté conectada a SW2 Gi0/2:

```cisco
show interfaces status
show mac address-table dynamic
```

---

### No se ven BPDUs en Kali

Verificar interfaz:

```bash
ip -br addr
```

Capturar STP:

```bash
sudo tcpdump -eni eth0 ether dst 01:80:c2:00:00:00
```

---

### No hay pérdida de tráfico

Esto puede ser normal. STP puede aceptar el Root Bridge falso y aun así mantener un árbol libre de loops. La evidencia principal es el cambio del Root ID, Root Port y topology changes.

---

### Se quiere provocar más recálculo

Ejecutar y detener el script varias veces mientras se mantiene un ping desde la VPC hacia R-1.

En VPC:

```text
ping 20.25.8.45
```

En SW1, SW2 y SW3:

```cisco
show spanning-tree vlan 1 detail
```

Revisar:

```text
Number of topology changes
Time since last topology change
```

---

## Estructura recomendada del repositorio

```text
STP-Claim-Root-Attack/
├── README.md
├── stp-claim-root.py
├── mitigacion-stp-claim-root.md
├── captures/
│   ├── stp-before-sw1-root.png
│   ├── stp-attack-running.png
│   ├── stp-root-changed-sw2.png
│   ├── stp-root-changed-sw3.png
│   ├── stp-topology-changes.png
│   └── bpduguard-mitigation.png
├── docs/
│   └── technical-report.md
└── video/
    └── youtube-link.txt
```

---

## Evidencias recomendadas

| Evidencia                  | Descripción                                               |
| -------------------------- | --------------------------------------------------------- |
| `stp-before-sw1-root.png`  | SW1 como Root Bridge legítimo antes del ataque            |
| `stp-attack-running.png`   | Kali ejecutando el script de STP Claim Root               |
| `stp-root-changed-sw2.png` | SW2 aceptando Root ID falso y usando Gi0/2 como Root Port |
| `stp-root-changed-sw3.png` | SW3 aceptando Root ID falso y recalculando la topología   |
| `stp-topology-changes.png` | Evidencia de cambios de topología STP                     |
| `bpduguard-mitigation.png` | Puerto hacia Kali bloqueado por BPDU Guard                |

---

## Topics sugeridos para GitHub

```text
stp
spanning-tree
claim-root
bpdu
bpduguard
rootguard
kali-linux
python
scapy
gns3
iosvl2
network-security
cybersecurity
layer2-security
ethical-hacking
packet-crafting
```

---

## Conclusión

Este laboratorio demuestra cómo un atacante conectado a un puerto de acceso puede manipular STP enviando BPDUs superiores para reclamar falsamente el rol de Root Bridge.

El ataque fue validado al observar que los switches aceptaron un Root ID con prioridad `0` y dirección `0000.0000.0001`. Además, SW2 cambió su Root Port hacia el puerto conectado a Kali, demostrando que la topología lógica de capa 2 fue alterada.

La mitigación principal es aplicar **BPDU Guard** en puertos de usuario y **Root Guard** en enlaces donde nunca debe aparecer un Root Bridge superior. Estas medidas evitan que equipos no autorizados manipulen STP y protegen la estabilidad de la red conmutada.

Para más detalles, revisar el documento de mitigación:

* [`mitigacion-stp-claim-root.md`](./mitigacion-stp-claim-root.md)

---

## Autor

**Michael Robles / iClexi**
Laboratorio de Seguridad de Redes
Proyecto académico de ataque y mitigación STP Claim Root
