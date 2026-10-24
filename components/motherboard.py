#Author: Kshitij Kshirsagar
#Filename: motherboard.py
#Last edited: 06/06/2026

from components.components import Components


class Motherboard(Components):
    def __init__(self, name, price, wattage, socket, ram_type):
        super().__init__(name, price, wattage)
        self.socket = socket
        self.ram_type = ram_type

    def display_info(self):
        return (
            f"Motherboad_Name: {self.name}, "
            f"Price: ${self.price}, "
            f"Wattage: {self.wattage}W, "
            f"Socket: {self.socket}, "
            f"RAM Type: {self.ram_type}"
        )
    