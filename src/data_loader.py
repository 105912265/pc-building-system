# Author: Kshitij Kshirsagar
# Filename: data_loader.py
# Last edited: 06/06/2026

import csv

from components.cpu import CPU
from components.gpu import GPU
from components.motherboard import Motherboard
from components.ram import RAM
from components.storage import Storage
from components.psu import PSU

def load_cpus(file_path):
    cpus = []

    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            cpu = CPU(
                row["name"],
                float(row["price"]),
                int(float(row["cpu_mark"])),
                int(float(row["single_thread_score"])),
                int(float(row["wattage"])),
                float(row["power_perf"]),
                int(float(row["cores"])),
                row["socket"]
            )

            cpus.append(cpu)

    return cpus


def load_gpus(file_path):
    gpus = []

    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            gpu = GPU(
                row["name"],
                float(row["price"]),
                int(float(row["g3d_mark"])),
                int(float(row["g2d_mark"])),
                int(float(row["wattage"])),
                float(row["power_perf"])
            )

            gpus.append(gpu)

    return gpus

def load_motherboards(file_path):
    motherboards = []

    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            motherboard = Motherboard(
                row["name"],
                float(row["price"]),
                int(float(row["wattage"])),
                row["socket"],
                row["ram_type"]
            )

            motherboards.append(motherboard)

    return motherboards

def load_ram(file_path):
    rams =[]

    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            ram = RAM(
                row["name"],
                float(row["price"]),
                int(float(row["wattage"])),
                int(float(row["size_gb"])),
                row["ram_type"]
            )

            rams.append(ram)

    return rams

def load_psu(file_path):
    psus = []

    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            psu = PSU(
                row["name"],
                float(row["price"]),
                int(float(row["wattage"])),
                row["efficiency"]
            )

            psus.append(psu)

    return psus

def load_storage(file_path):
    storages = []

    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            storage = Storage(
                row["name"],
                float(row["price"]),
                int(float(row["wattage"])),
                int(float(row["capacity_gb"])), 
                row["storage_type"]
            )

            storages.append(storage)

    return storages