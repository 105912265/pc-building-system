# Author: Kshitij Kshirsagar
# Filename: compatibility_checker.py
# Last edited: 19/06/2026


def normalise_socket(socket):
    """
    used to convert different CPU socket formats into a consistent format
    :param socket: CPU or motherboard socket name
    :return cleaned_socket: normalised socket name
    """
    cleaned_socket = socket.strip().upper()
    cleaned_socket = cleaned_socket.replace(" ", "")
    cleaned_socket = cleaned_socket.replace("FCLGA", "LGA")

    return cleaned_socket


def is_cpu_motherboard_compatible(cpu, motherboard):
    """
    used to check whether the CPU and motherboard use the same socket
    :param cpu: CPU object
    :param motherboard: motherboard object
    :return: Boolean value showing whether the sockets are compatible
    """
    return (
        normalise_socket(cpu.socket)
        == normalise_socket(motherboard.socket)
    )


def is_ram_motherboard_compatible(ram, motherboard):
    """
    used to check whether the RAM type matches the motherboard
    :param ram: RAM object
    :param motherboard: motherboard object
    :return: Boolean value showing whether the RAM is compatible
    """
    return ram.ram_type == motherboard.ram_type


def calculate_total_price(
    cpu,
    gpu,
    motherboard,
    ram,
    storage,
    psu
):
    """
    used to calculate the total price of a complete PC build
    :return: total component price
    """
    return (
        cpu.price
        + gpu.price
        + motherboard.price
        + ram.price
        + storage.price
        + psu.price
    )


def calculate_total_wattage(
    cpu,
    gpu,
    motherboard,
    ram,
    storage
):
    """
    used to calculate the total wattage of a PC build before adding the PSU
    :return: total component wattage
    """
    return (
        cpu.wattage
        + gpu.wattage
        + motherboard.wattage
        + ram.wattage
        + storage.wattage
    )


def is_psu_compatible(total_wattage, psu):
    """
    used to check whether the PSU has at least thirty percent wattage headroom
    :param total_wattage: total wattage required by the build
    :param psu: PSU object
    :return: Boolean value showing whether the PSU is suitable
    """
    required_wattage = total_wattage * 1.3

    return psu.wattage >= required_wattage


def is_within_budget(total_price, budget):
    """
    used to check whether the total build price is within budget
    :param total_price: total build price
    :param budget: maximum user budget
    :return: Boolean value showing whether the price is valid
    """
    return total_price <= budget


def is_build_compatible(
    cpu,
    gpu,
    motherboard,
    ram,
    storage,
    psu,
    budget
):
    """
    used to check compatibility, wattage and budget requirements
    :return: Boolean value showing whether the complete build is valid
    """
    if not is_cpu_motherboard_compatible(cpu, motherboard):
        return False

    if not is_ram_motherboard_compatible(ram, motherboard):
        return False

    total_wattage = calculate_total_wattage(
        cpu,
        gpu,
        motherboard,
        ram,
        storage
    )

    if not is_psu_compatible(total_wattage, psu):
        return False

    total_price = calculate_total_price(
        cpu,
        gpu,
        motherboard,
        ram,
        storage,
        psu
    )

    return is_within_budget(total_price, budget)