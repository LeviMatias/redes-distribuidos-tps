import time
import os

abc = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
    'k', 'l', 'm', 'n', 'l', 'o', 'p', 'q', 'r', 's']


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


for i in range(20):
    time.sleep(0.2)
    clear_screen()
    __print_prevs_prints()
    msg = f"""
        numero ahora es: {i}
        numero ahora es: {abc[i]}
    """
    print(msg, end='\r')
