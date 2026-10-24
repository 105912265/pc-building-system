#Author: Kshitij Kshirsagar
#Filename: components.py
#Last edited: 07/06/2026

class Components: 
    def __init__(self, name, price, wattage):
        self.name = name
        self.price = price
        self.wattage = wattage

    def display_info(self):
        return f"Name: {self.name}, Price: {self.price}, Wattage: {self.wattage}"
        
