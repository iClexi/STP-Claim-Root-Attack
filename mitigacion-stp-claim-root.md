# Mitigación STP Claim Root Attack

## Aviso de uso responsable

Este documento fue desarrollado únicamente con fines educativos, académicos y de laboratorio controlado.

Las configuraciones presentadas deben aplicarse solamente en entornos propios o autorizados, como GNS3, EVE-NG, PNETLab o laboratorios internos de pruebas.

---

## Descripción de la mitigación

El ataque **STP Claim Root** consiste en enviar BPDUs falsas con una prioridad superior a la del Root Bridge legítimo para manipular la elección del Root Bridge en una red conmutada.

Cuando el ataque es exitoso, los switches aceptan un Root ID falso y recalculan la topología STP. Esto puede provocar cambios de camino, pérdida temporal de paquetes, inestabilidad o alteración del diseño lógico de capa 2.

Para mitigar este ataque se utilizan principalmente:

* BPDU Guard
* Root Guard
* Configuración explícita del Root Bridge legítimo
* Protección de puertos de acceso

---

## Topología del laboratorio

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

## Direccionamiento IP

| Dispositivo | Rol                   | Interfaz | Dirección IP  | Descripción                   |
| ----------- | --------------------- | -------- | ------------- | ----------------------------- |
| R-1         | Gateway               | Fa0/0    | 20.25.8.45/24 | Router principal              |
| SW1         | Root Bridge legítimo  | N/A      | N/A           | Switch raíz esperado          |
| SW2         | Switch intermedio     | N/A      | N/A           | Switch conectado a Kali       |
| SW3         | Switch intermedio     | N/A      | N/A           | Switch conectado a la VPC     |
| Kali        | Atacante              | eth0     | 20.25.8.46/24 | Equipo que envía BPDUs falsas |
| VPC1        | Cliente de validación | eth0     | DHCP o .47    | Equipo de prueba              |

---

## Objetivo de la mitigación

El objetivo es impedir que un equipo final conectado a un puerto de acceso pueda participar en STP o enviar BPDUs superiores.

La defensa busca lograr lo siguiente:

* Mantener a SW1 como Root Bridge legítimo.
* Impedir que Kali envíe BPDUs falsas desde un puerto de usuario.
* Bloquear puertos que reciban BPDUs donde no deberían.
* Evitar que un switch no autorizado reclame el rol de Root Bridge.
* Mantener estable la topología de capa 2.

---

## Concepto de BPDU Guard

**BPDU Guard** es una función de seguridad que se aplica normalmente en puertos de acceso con PortFast.

La lógica es:

```text
Un puerto de usuario no debe recibir BPDUs.
Si recibe BPDUs, el puerto se apaga.
```

Esto protege contra equipos finales que intenten participar en STP.

En este laboratorio, Kali está conectada a:

```text
SW2 Gi0/2
```

Por eso BPDU Guard debe aplicarse en ese puerto.

---

## Configuración de BPDU Guard en el puerto de Kali

En SW2:

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

---

## Explicación de la configuración BPDU Guard

### Modo acceso

```cisco
switchport mode access
```

Define el puerto como puerto de usuario final.

### PortFast

```cisco
spanning-tree portfast
```

Permite que el puerto pase rápidamente a forwarding porque se supone que conecta a un equipo final.

### BPDU Guard

```cisco
spanning-tree bpduguard enable
```

Si el puerto recibe cualquier BPDU, se considera una condición anormal y el puerto entra en estado `err-disable`.

---

## Evidencia esperada con BPDU Guard

Después de aplicar BPDU Guard, ejecutar nuevamente el ataque desde Kali.

El switch debe mostrar mensajes parecidos a:

```text
%SPANTREE-2-BLOCK_BPDUGUARD
%PM-4-ERR_DISABLE: bpduguard error detected on Gi0/2, putting Gi0/2 in err-disable state
```

Esto confirma que el switch detectó BPDUs en un puerto de usuario y bloqueó el ataque.

---

## Verificación de BPDU Guard

En SW2:

```cisco
show interfaces status
show spanning-tree interface gigabitEthernet0/2 detail
show running-config interface gigabitEthernet0/2
show logging
```

Resultado esperado:

```text
Gi0/2    err-disabled
```

También se puede verificar que el Root Bridge no cambió:

```cisco
show spanning-tree vlan 1
```

SW1 debe seguir siendo el Root Bridge legítimo.

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

Verificar:

```cisco
show interfaces status
```

---

## Recuperación automática por BPDU Guard

Opcionalmente, se puede habilitar recuperación automática del puerto:

```cisco
configure terminal
errdisable recovery cause bpduguard
errdisable recovery interval 30
end
write memory
```

Verificar:

```cisco
show errdisable recovery
```

Con esta configuración, el switch intentará levantar el puerto automáticamente después de 30 segundos.

---

## Concepto de Root Guard

**Root Guard** se utiliza en puertos donde nunca se debe recibir un BPDU superior que intente cambiar el Root Bridge.

A diferencia de BPDU Guard, Root Guard no necesariamente apaga el puerto en `err-disable`. En su lugar, si detecta un BPDU superior, coloca el puerto en estado:

```text
root-inconsistent
```

Cuando el BPDU superior desaparece, el puerto puede volver automáticamente a su estado normal.

---

## Configuración de Root Guard en SW1

Como SW1 es el Root Bridge legítimo, se puede proteger sus enlaces hacia otros switches.

En SW1:

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

## Explicación de Root Guard

Si SW1 recibe un BPDU superior desde SW2 o SW3, Root Guard evita que ese puerto acepte al nuevo root.

La lógica es:

```text
SW1 debe seguir siendo root.
Si por este enlace aparece un root mejor, se bloquea el puerto temporalmente.
```

Esto evita que un atacante conectado aguas abajo pueda cambiar la raíz STP.

---

## Evidencia esperada con Root Guard

Al ejecutar el ataque, si el BPDU superior llega hacia SW1 por un puerto protegido, se puede observar:

```text
Root guard blocking port
root-inconsistent
```

Comandos de verificación:

```cisco
show spanning-tree inconsistentports
show spanning-tree vlan 1
show logging
```

Resultado esperado:

```text
Name                 Interface             Inconsistency
VLAN0001             Gi0/1                 Root Inconsistent
```

---

## Definir explícitamente el Root Bridge legítimo

Además de BPDU Guard y Root Guard, se recomienda definir el root esperado.

En SW1:

```cisco
enable
configure terminal
spanning-tree vlan 1 priority 4096
end
write memory
```

En SW2 y SW3:

```cisco
enable
configure terminal
spanning-tree vlan 1 priority 32768
end
write memory
```

Verificar:

```cisco
show spanning-tree vlan 1
```

En SW1 debe aparecer:

```text
This bridge is the root
```

---

## Protección adicional en puertos de usuario

También se recomienda aplicar BPDU Guard en otros puertos de usuario, por ejemplo en el puerto hacia la VPC.

En SW3:

```cisco
enable
configure terminal

interface gigabitEthernet0/2
description HACIA-VPC1
switchport mode access
spanning-tree portfast
spanning-tree bpduguard enable
exit

end
write memory
```

---

## Prueba antes de la mitigación

Antes de aplicar la mitigación, Kali puede reclamar el rol de Root Bridge.

En los switches:

```cisco
show spanning-tree vlan 1
```

Evidencia esperada durante el ataque:

```text
Root ID    Priority    0
           Address     0000.0000.0001
```

En SW2:

```text
Gi0/2      Root FWD
```

Esto confirma que SW2 acepta el puerto hacia Kali como camino hacia el root falso.

---

## Prueba después de la mitigación

Después de aplicar BPDU Guard en SW2 Gi0/2, ejecutar nuevamente el ataque.

Resultado esperado:

* SW2 detecta BPDUs en un puerto de usuario.
* Gi0/2 cae en `err-disable`.
* Kali no logra reclamar el Root Bridge.
* SW1 se mantiene como Root Bridge legítimo.
* La topología STP permanece protegida.

---

## Comandos útiles de verificación

### En SW1

```cisco
terminal length 0
show spanning-tree vlan 1
show spanning-tree vlan 1 detail
show spanning-tree inconsistentports
show logging
```

### En SW2

```cisco
terminal length 0
show spanning-tree vlan 1
show spanning-tree vlan 1 detail
show spanning-tree interface gigabitEthernet0/2 detail
show running-config interface gigabitEthernet0/2
show interfaces status
show logging
```

### En SW3

```cisco
terminal length 0
show spanning-tree vlan 1
show spanning-tree vlan 1 detail
show interfaces status
show logging
```

### En Kali

```bash
ip -br addr
sudo python3 stp-claim-root.py
sudo pkill -f stp-claim-root
```

---

## Quitar BPDU Guard para repetir el ataque

Si se desea repetir la prueba sin mitigación, retirar BPDU Guard del puerto de Kali.

En SW2:

```cisco
enable
configure terminal

interface gigabitEthernet0/2
no spanning-tree bpduguard enable
no spanning-tree portfast
shutdown
no shutdown
exit

end
write memory
```

---

## Quitar Root Guard

En SW1:

```cisco
enable
configure terminal

interface gigabitEthernet0/1
no spanning-tree guard root
exit

interface gigabitEthernet0/2
no spanning-tree guard root
exit

end
write memory
```

---

## Troubleshooting

### El puerto queda en err-disable

Verificar:

```cisco
show interfaces status
show logging
```

Detener el ataque en Kali:

```bash
sudo pkill -f stp-claim-root
```

Levantar el puerto:

```cisco
configure terminal
interface gigabitEthernet0/2
shutdown
no shutdown
exit
end
```

---

### BPDU Guard no se activa

Verificar que esté configurado en el puerto correcto:

```cisco
show running-config interface gigabitEthernet0/2
```

Verificar que Kali esté conectada realmente a SW2 Gi0/2:

```cisco
show interfaces status
show mac address-table dynamic
```

---

### Root Guard no bloquea

Root Guard solo actúa si recibe BPDUs superiores en el puerto donde está configurado.

Verificar:

```cisco
show spanning-tree inconsistentports
show logging
```

También confirmar que SW1 está configurado como root legítimo:

```cisco
show spanning-tree vlan 1
```

---

### El ataque no genera broadcast storm

Esto puede ser normal. STP puede aceptar un root falso y aun así bloquear un puerto alterno para evitar loops.

La evidencia principal del ataque no es necesariamente una tormenta broadcast, sino:

* Cambio de Root ID.
* Cambio de Root Port.
* Topology changes.
* Recalculo de la topología.
* Puerto hacia Kali usado como camino hacia el root falso.

---

## Recomendaciones finales

Para una red real o un laboratorio más completo, se recomienda:

* Configurar explícitamente el Root Bridge legítimo.
* Aplicar BPDU Guard en todos los puertos de acceso.
* Aplicar Root Guard en enlaces donde nunca debe aparecer un Root Bridge superior.
* No conectar equipos finales a puertos sin protección STP.
* Documentar qué puertos son trunk y cuáles son acceso.
* Revisar periódicamente `show spanning-tree vlan`.
* Monitorear eventos de BPDU Guard y Root Guard.
* Usar PortFast solo en puertos de usuario final.
* Evitar que dispositivos no autorizados participen en STP.

---

## Conclusión

El ataque STP Claim Root demuestra que un puerto de acceso sin protección puede permitir que un atacante envíe BPDUs superiores y manipule la elección del Root Bridge.

La mitigación más directa es aplicar **BPDU Guard** en puertos de usuario, ya que bloquea inmediatamente cualquier puerto que reciba BPDUs donde no deberían existir. Como defensa adicional, **Root Guard** protege enlaces estratégicos contra BPDUs superiores que intenten reemplazar al Root Bridge legítimo.

En conjunto, BPDU Guard, Root Guard y una elección explícita del Root Bridge ayudan a mantener estable y segura la topología de capa 2.

---

## Autor

**Michael Robles / iClexi**
Laboratorio de Seguridad de Redes
Proyecto académico de mitigación STP Claim Root
