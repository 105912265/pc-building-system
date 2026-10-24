#Author: Kshitij Kshirsagar
#Filename: gpu.py
#Last edited: 06/06/2026

from components.components import Components

class GPU(Components):
    def __init__(self, name, price, g3d_mark, g2d_mark, wattage, power_perf):
        super().__init__(name, price, wattage)
        self.g3d_mark = g3d_mark
        self.g2d_mark = g2d_mark
        self.wattage = wattage
        self.power_perf = power_perf

    def display_info(self):
        return (
            f"GPU_Name: {self.name}, "
            f"Price: ${self.price}, "
            f"Wattage: {self.wattage}W, "
            f"G3D Mark: {self.g3d_mark}, "
            f"G2D Mark: {self.g2d_mark}, "
            f"Power Efficiency: {self.power_perf}"
        )