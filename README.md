# PC Builder

A Python object-oriented PC builder program that recommends or allows users to create a PC build using CSV component data.

## Features

- Reads CPU, GPU, RAM, storage, motherboard, and PSU data from CSV files
- Uses classes and inheritance for different PC components
- Uses polymorphism through each component's display_info() method
- Checks motherboard compatibility using CPU socket and RAM type
- Checks PSU wattage requirements
- Allows random or custom PC builds
- Calculates total price and total wattage
- Saves final build to a text file

## How to Run

```bash
python main.py
