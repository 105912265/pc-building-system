#Author: Kshitij Kshirsagar
#Filename: psu.py
#Last edited: 24/05/2026

from components.components import Components


class PSU(Components):
    def __init__(self, name, price, wattage, efficiency):
        super().__init__(name, price, wattage)
        self.efficiency = efficiency

    def display_info(self):
        return (
            f"PSU_Name: {self.name}, "
            f"Price: ${self.price}, "
            f"Wattage: {self.wattage}W, "
            f"Efficiency: {self.efficiency}"
        )
    
