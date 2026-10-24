#Author: Kshitij Kshirsagar
#Filename: psus.py
#Last edited: 06/06/2026

from components.components import Components


class Storage(Components):
    def __init__(self, name, price, wattage, capacity_gb, storage_type):
        super().__init__(name, price, wattage)
        self.capacity_gb = capacity_gb
        self.storage_type = storage_type

    def display_info(self):
        return (
            f"Storage_Name: {self.name}, "
            f"Price: ${self.price}, "
            f"Wattage: {self.wattage}W, "
            f"Capacity: {self.capacity_gb}GB, "
            f"Type: {self.storage_type}"
        )
    
