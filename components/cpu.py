#Author: Kshitij Kshirsagar
#Filename: cpu.py
#Last edited: 06/06/2026

from components.components import Components

class CPU(Components):
    def __init__(self, name, price, cpu_mark, single_thread_score, wattage, power_perf, cores, socket):
        super().__init__(name, price, wattage)
        self.cpu_mark = cpu_mark
        self.single_thread_score = single_thread_score
        self.wattage = wattage
        self.power_perf = power_perf
        self.cores = cores
        self.socket = socket

    def display_info(self):
        return (
            f"CPU_Name: {self.name}, "
            f"Price: ${self.price}, "
            f"Wattage: {self.wattage}W, "
            f"CPU Mark: {self.cpu_mark}, "
            f"Single Thread Score: {self.single_thread_score}, "
            f"Power Performance: {self.power_perf}, "
            f"Cores: {self.cores}, "
            f"Socket: {self.socket}"
        )  


