#Author: Kshitij Kshirsagar
#Filename: file_reading.py
#Last edited: 24/05/2026

import csv
from components.cpu import CPU
from components.gpu import GPU
from components.ram import RAM
from components.storage import Storage
from components.psu import PSU
from components.motherboard import Motherboard

#read the various component files and assign the to a list
#items[]: function returns the filtered component list as per user specification
#total_wattage: program can list PSU with enough power for specs
#budget: cheap, okay, or expensive build
def read_files(file_path, object_type, build_type):
    items = []
    total_wattage = 0
    budget = ""
    if build_type == 1:
        budget = "cheap"
    elif build_type == 2:
        budget = "okay"
    elif build_type == 3:
        budget = "expensive"

    with open(file_path, 'r', encoding='utf8') as file:
        reader = csv.DictReader(file, skipinitialspace=True) #skips headings

        for row in reader:
            if object_type is CPU:
                item = CPU(row['name'], row['brand'], float(row['price']), int(row['wattage']), int(row['cores']), row['socket'])
                total_wattage += int(row['wattage'])
            elif object_type is GPU:
                item = GPU(row['name'], row['brand'], float(row['price']), int(row['wattage']), int(row['vram_gb']))
                total_wattage += int(row['wattage'])
            elif object_type is PSU:
                item = PSU(row['name'], row['brand'], float(row['price']), int(row['wattage']))
            elif object_type is RAM:
                item = RAM(row['name'], row['brand'], float(row['price']), int(row['wattage']), int(row['capacity_gb']), row['type'], row['speed_mhz'])
                total_wattage += int(row['wattage'])
            elif object_type is Storage:
                item = Storage(row['name'], row['brand'], float(row['price']), int(row['wattage']),row['type'], int(row['capacity_gb']))
                total_wattage += int(row['wattage'])
            elif object_type is Motherboard:
                item = Motherboard(row['name'], row['brand'], float(row['price']), int(row['wattage']), row['socket'], row['ram_type'], row['wifi'])
                total_wattage += int(row['wattage'])
            else:
                raise ValueError(f"Unsupported object_type: {object_type}")

            # Motherboards are listed based on ram and cpu socket
            if object_type is Motherboard:
                items.append(item)
                continue

            #PSUs are listed based on specs power requirements
            if object_type is PSU:
                items.append(item)
                continue

            #other parts are listed absed on type of build (cheap, okay, or expensive)
            build_value = row.get('build_type', '').strip().lower()
            if build_value == budget:
                items.append(item)

    return items