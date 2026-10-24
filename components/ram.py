#Author: Kshitij Kshirsagar
#Filename: ram.py
#Last edited: 06/06/2026

from components.components import Components


class RAM(Components):
    def __init__(self, name, price, wattage, size_gb, ram_type):
        super().__init__(name, price, wattage)
        self.size_gb = size_gb
        self.ram_type = ram_type

    def display_info(self):
        return (
            f"RAM_Name: {self.name}, "
            f"Price: ${self.price}, "
            f"Wattage: {self.wattage}W, "
            f"Size: {self.size_gb}GB, "
            f"RAM Type: {self.ram_type}"
        )
    
