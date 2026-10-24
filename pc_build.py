# Author: Kshitij Kshirsagar
# Filename: pc_build.py
# Last edited: 18/06/2026

import random
import os


# consists of all parts needed for a PC to function
class PCBUILD:
    def __init__(self):
        self.components = []

    def add_component(self, component):
        """
        used to add a component to the PC build
        :param component: component object being added
        :return: None
        """
        self.components.append(component)

    def choose_random_component(self, component_list):
        """
        used to choose and add a random component
        :param component_list: list of available component objects
        :return choice: randomly selected component object
        """
        if not component_list:
            return None

        choice = random.choice(component_list)
        self.add_component(choice)

        return choice

    def total_price(self):
        """
        used to calculate the total price of all components
        :return: total price of the PC build
        """
        return sum(
            component.price
            for component in self.components
        )

    def total_watts(self):
        """
        used to calculate the total wattage of all components
        :return: total wattage of the PC build
        """
        return sum(
            component.wattage
            for component in self.components
        )

    def display_build(self):
        """
        used to return the information of all components in the build
        :return: formatted string containing component information
        """
        return "\n".join(
            component.display_info()
            for component in self.components
        )

    def save_build(self, filename="output/build.txt"):
        """
        used to save the completed PC build into a text file
        :param filename: output file location
        :return: None
        """

        folder = os.path.dirname(filename)

        if folder:
            os.makedirs(folder, exist_ok=True)

        with open(filename, "w", encoding="utf8") as file:
            file.write("PC Build Summary\n")
            file.write("----------------\n")

            for component in self.components:
                file.write(component.display_info() + "\n")

            file.write(
                f"\nTotal price: ${self.total_price():.2f}\n"
            )

            file.write(
                f"Total wattage: {self.total_watts()}W\n"
            )

    def show_components(self):
        """
        used to return all components currently in the build
        :return components: list of component objects
        """
        return self.components