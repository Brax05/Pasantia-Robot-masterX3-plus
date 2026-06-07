import time
import sys

total = 500

for i in range(total, -1, -1):
    barra = "▓" * i
    vacio = "░" * (total - i)

    sys.stdout.write(f"\rHambre: [{barra}{vacio}]")
    sys.stdout.flush()

    time.sleep(0.1)

print("\nSistema apagado")