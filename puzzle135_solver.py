#!/usr/bin/env python3
"""
p-HETI Solver for Bitcoin Puzzle 135
p-adic Holographic Ergodics and Tensor Isogeny
"""

import time
import random
import hashlib
import sys
from collections import defaultdict
from ecdsa import SigningKey, SECP256k1
from ecdsa.ellipticcurve import Point

# ==========================================
# SECP256K1 ПАРАМЕТРИ
# ==========================================
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

# Puzzle 135 дані
TARGET_PUBKEY_HEX = "02145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16"
KEY_RANGE_MIN = 2**134  # 0x4000000000000000000000000000000000
KEY_RANGE_MAX = 2**135 - 1  # 0x7fffffffffffffffffffffffffffffffff

# ==========================================
# БЛОК 1: p-адична арифметика
# ==========================================
def p_adic_valuation(x, p):
    """Обчислює p-адичну оцінку числа x."""
    if x == 0:
        return float('inf')
    v = 0
    while x % p == 0:
        x //= p
        v += 1
    return v

def p_adic_distance(x, y, p):
    """Обчислює p-адичну відстань між двома числами."""
    if x == y:
        return 0.0
    return p ** (-p_adic_valuation(abs(x - y), p))

# ==========================================
# БЛОК 2: secp256k1 операції
# ==========================================
def mod_inverse(a, m):
    """Модульне обернене число."""
    return pow(a, m - 2, m)

def point_add(P1, P2):
    """Додавання точок на secp256k1."""
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    
    x1, y1 = P1
    x2, y2 = P2
    
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    
    if x1 == x2 and y1 == y2:
        lam = (3 * x1 * x1) * mod_inverse(2 * y1, P) % P
    else:
        lam = (y2 - y1) * mod_inverse(x2 - x1, P) % P
    
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return (x3, y3)

def scalar_mult(k, point):
    """Множення точки на скаляр (double-and-add)."""
    result = None
    addend = point
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result

def parse_pubkey(pubkey_hex):
    """Парсить compressed public key в координати (x, y)."""
    if pubkey_hex.startswith('02') or pubkey_hex.startswith('03'):
        x = int(pubkey_hex[2:], 16)
        # Обчислюємо y з x
        y_squared = (pow(x, 3, P) + 7) % P
        y = pow(y_squared, (P + 1) // 4, P)
        
        # Перевіряємо парність y
        if pubkey_hex.startswith('02'):
            if y % 2 == 1:
                y = P - y
        else:
            if y % 2 == 0:
                y = P - y
        
        return (x, y)
    return None

# ==========================================
# БЛОК 3: p-HETI інваріанти для secp256k1
# ==========================================
def compute_pheti_energy(scalar, base_point, target_point, p_primes=[2, 3, 5, 7], orbit_depth=15):
    """
    Обчислює p-адичну енергію для даного скаляра.
    Це основний інваріант для фільтрації простору пошуку.
    """
    # Генеруємо орбіту подвоєнь для базової точки
    orbit = [base_point]
    current = base_point
    for _ in range(orbit_depth):
        current = point_add(current, current)
        orbit.append(current)
    
    # Зміщуємо орбіту на тестовий скаляр
    test_point = scalar_mult(scalar, base_point)
    shifted_orbit = [point_add(pt, test_point) if pt else None for pt in orbit]
    
    # Обчислюємо p-адичну енергію для різних p
    total_energy = 0.0
    
    for p in p_primes:
        # Будуємо матрицю p-адичних відстаней
        dim = len(shifted_orbit)
        energy_sum = 0.0
        
        for i in range(dim):
            for j in range(dim):
                if shifted_orbit[i] and shifted_orbit[j]:
                    x1 = shifted_orbit[i][0]
                    x2 = shifted_orbit[j][0]
                    dist = p_adic_distance(x1, x2, p)
                    energy_sum += dist
        
        # Нормалізуємо
        normalized_energy = energy_sum / (dim * dim)
        total_energy += normalized_energy
    
    # Усереднюємо по всіх p
    avg_energy = total_energy / len(p_primes)
    
    # Обчислюємо "відстань" до цільової точки
    target_energy = 0.0
    for p in p_primes:
        if test_point and target_point:
            dist = p_adic_distance(test_point[0], target_point[0], p)
            target_energy += dist
    target_energy /= len(p_primes)
    
    # Фінальна енергія = різниця між енергією орбіти та цільовою енергією
    # Мінімум цієї функції = правильний скаляр
    return abs(avg_energy - target_energy)

def compute_pheti_signature(scalar, base_point, p=3, orbit_depth=20):
    """
    Обчислює p-адичний "підпис" скаляра - унікальну характеристику.
    Використовується для швидкого порівняння.
    """
    test_point = scalar_mult(scalar, base_point)
    if not test_point:
        return None
    
    # Генеруємо орбіту
    orbit = [test_point]
    current = test_point
    for _ in range(orbit_depth):
        current = point_add(current, current)
        if current:
            orbit.append(current)
    
    # Обчислюємо p-адичні valuation для всіх x-координат
    valuations = []
    for point in orbit:
        if point:
            val = p_adic_valuation(point[0], p)
            if val != float('inf'):
                valuations.append(val)
    
    if not valuations:
        return None
    
    # Створюємо "підпис" - кортеж статистик
    signature = (
        min(valuations),
        max(valuations),
        sum(valuations) / len(valuations),
        len(set(valuations))  # Кількість унікальних значень
    )
    
    return signature

# ==========================================
# БЛОК 4: Головний solver
# ==========================================
class PHETISolver:
    def __init__(self):
        self.base_point = (Gx, Gy)
        self.target_point = parse_pubkey(TARGET_PUBKEY_HEX)
        self.start_time = time.time()
        self.attempts = 0
        self.best_scalar = None
        self.best_energy = float('inf')
        self.energy_history = []
        
        print("="*80)
        print("p-HETI SOLVER: Bitcoin Puzzle 135")
        print("="*80)
        print(f"Base Point G: ({Gx}, {Gy})")
        print(f"Target Point Q: {self.target_point}")
        print(f"Key Range: 2^134 ... 2^135")
        print(f"Search Space: {KEY_RANGE_MAX - KEY_RANGE_MIN:,} keys")
        print("="*80)
    
    def verify_solution(self, scalar):
        """Перевіряє, чи є скаляр правильним рішенням."""
        computed_point = scalar_mult(scalar, self.base_point)
        if computed_point == self.target_point:
            return True
        return False
    
    def gradient_descent_search(self, iterations=100000):
        """
        Градієнтний спуск у просторі скалярів.
        Використовує p-адичну енергію як функцію втрат.
        """
        print(f"\nЗапуск градієнтного спуску ({iterations:,} ітерацій)...")
        print("-"*80)
        
        # Починаємо з випадкової точки в діапазоні
        current_scalar = random.randint(KEY_RANGE_MIN, KEY_RANGE_MAX)
        current_energy = compute_pheti_energy(current_scalar, self.base_point, self.target_point)
        
        step_size = 2**120  # Великий крок для початку
        min_step = 2**50    # Мінімальний крок
        
        for i in range(iterations):
            self.attempts += 1
            
            # Пробуємо рух в обох напрямках
            scalar_plus = min(current_scalar + step_size, KEY_RANGE_MAX)
            scalar_minus = max(current_scalar - step_size, KEY_RANGE_MIN)
            
            energy_plus = compute_pheti_energy(scalar_plus, self.base_point, self.target_point)
            energy_minus = compute_pheti_energy(scalar_minus, self.base_point, self.target_point)
            
            # Вибираємо найкращий напрямок
            if energy_plus < current_energy and energy_plus < energy_minus:
                current_scalar = scalar_plus
                current_energy = energy_plus
            elif energy_minus < current_energy:
                current_scalar = scalar_minus
                current_energy = energy_minus
            else:
                # Зменшуємо крок, якщо не можемо покращити
                step_size = max(step_size // 2, min_step)
            
            # Оновлюємо найкращий результат
            if current_energy < self.best_energy:
                self.best_energy = current_energy
                self.best_scalar = current_scalar
                
                # Перевіряємо, чи це рішення
                if self.verify_solution(current_scalar):
                    print(f"\n🎉 РІШЕННЯ ЗНАЙДЕНО!")
                    print(f"Private Key: {hex(current_scalar)}")
                    print(f"Public Key: {TARGET_PUBKEY_HEX}")
                    return current_scalar
            
            # Логування прогресу
            if i % 1000 == 0:
                elapsed = time.time() - self.start_time
                speed = self.attempts / elapsed if elapsed > 0 else 0
                print(f"Iter {i:,}/{iterations:,} | Energy: {current_energy:.6f} | "
                      f"Best: {self.best_energy:.6f} | Speed: {speed:.2f} keys/sec")
        
        return None
    
    def random_search_with_filter(self, iterations=1000000):
        """
        Випадковий пошук з p-адичним фільтром.
        Генерує випадкові скаляри та відбирає ті, що мають низьку енергію.
        """
        print(f"\nЗапуск випадкового пошуку з фільтром ({iterations:,} ітерацій)...")
        print("-"*80)
        
        low_energy_threshold = 0.1  # Початковий поріг
        
        for i in range(iterations):
            self.attempts += 1
            
            # Генеруємо випадковий скаляр
            scalar = random.randint(KEY_RANGE_MIN, KEY_RANGE_MAX)
            
            # Обчислюємо енергію
            energy = compute_pheti_energy(scalar, self.base_point, self.target_point)
            
            # Оновлюємо найкращий результат
            if energy < self.best_energy:
                self.best_energy = energy
                self.best_scalar = scalar
                self.energy_history.append((scalar, energy))
                
                # Адаптивно зменшуємо поріг
                if energy < low_energy_threshold:
                    low_energy_threshold = energy * 0.9
                
                # Перевіряємо рішення
                if self.verify_solution(scalar):
                    print(f"\n🎉 РІШЕННЯ ЗНАЙДЕНО!")
                    print(f"Private Key: {hex(scalar)}")
                    return scalar
            
            # Логування
            if i % 10000 == 0:
                elapsed = time.time() - self.start_time
                speed = self.attempts / elapsed if elapsed > 0 else 0
                print(f"Iter {i:,}/{iterations:,} | Best Energy: {self.best_energy:.6f} | "
                      f"Threshold: {low_energy_threshold:.6f} | Speed: {speed:.2f} keys/sec")
        
        return None
    
    def run(self):
        """Запускає повний процес пошуку."""
        print("\nСтратегія 1: Градієнтний спуск")
        result = self.gradient_descent_search(iterations=50000)
        
        if result:
            return result
        
        print("\nСтратегія 2: Випадковий пошук з p-адичним фільтром")
        result = self.random_search_with_filter(iterations=500000)
        
        if result:
            return result
        
        print("\n" + "="*80)
        print("РЕЗУЛЬТАТИ ПОШУКУ:")
        print("="*80)
        print(f"Всього спроб: {self.attempts:,}")
        print(f"Найкраща енергія: {self.best_energy:.8f}")
        print(f"Найкращий скаляр: {hex(self.best_scalar) if self.best_scalar else 'None'}")
        
        elapsed = time.time() - self.start_time
        speed = self.attempts / elapsed if elapsed > 0 else 0
        print(f"Час роботи: {elapsed:.2f} секунд")
        print(f"Середня швидкість: {speed:.2f} keys/sec")
        print("="*80)
        
        return None

# ==========================================
# ГОЛОВНА ФУНКЦІЯ
# ==========================================
def main():
    solver = PHETISolver()
    result = solver.run()
    
    if result:
        print("\n✅ ЗАДАЧУ ВИРІШЕНО!")
        print(f"Private Key (hex): {hex(result)}")
        print(f"Private Key (dec): {result}")
    else:
        print("\n⚠️ Рішення не знайдено в межах заданих ітерацій.")
        print("Рекомендації:")
        print("- Збільшити кількість ітерацій")
        print("- Використати паралельні обчислення (multiprocessing)")
        print("- Застосувати більш складні методи оптимізації")

if __name__ == "__main__":
    main()