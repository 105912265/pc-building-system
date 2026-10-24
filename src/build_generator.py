# Author: Kshitij Kshirsagar
# Filename: build_generator.py
# Last edited: 19/06/2026

from src.compatibility_checker import (
    calculate_total_wattage,
    is_psu_compatible,
    normalise_socket
)


def cpu_matches_preference(cpu, preferred_brand):
    """
    used to check whether a CPU matches the user's brand preference
    :param cpu: CPU object
    :param preferred_brand: AMD, Intel or Any
    :return: Boolean value showing whether the CPU matches
    """
    if preferred_brand == "Any":
        return True

    cpu_name = cpu.name.upper()

    if preferred_brand == "AMD":
        return "AMD" in cpu_name or "RYZEN" in cpu_name

    if preferred_brand == "Intel":
        return "INTEL" in cpu_name or "CORE" in cpu_name

    return False


def gpu_matches_preference(gpu, preferred_brand):
    """
    used to check whether a GPU matches the user's brand preference
    :param gpu: GPU object
    :param preferred_brand: NVIDIA, Radeon or Any
    :return: Boolean value showing whether the GPU matches
    """
    if preferred_brand == "Any":
        return True

    gpu_name = gpu.name.upper()

    if preferred_brand == "NVIDIA":
        return (
            "NVIDIA" in gpu_name
            or "GEFORCE" in gpu_name
            or "RTX" in gpu_name
            or "GTX" in gpu_name
        )

    if preferred_brand == "Radeon":
        return (
            "RADEON" in gpu_name
            or gpu_name.startswith("RX ")
            or "AMD RADEON" in gpu_name
        )

    return False


def cpu_score(cpu):
    """
    used to calculate the CPU's performance and value score
    :param cpu: CPU object
    :return: combined CPU score
    """
    value_score = cpu.cpu_mark / cpu.price

    return (
        cpu.cpu_mark * 0.80
        + cpu.single_thread_score * 0.15
        + value_score * 100 * 0.05
    )


def gpu_score(gpu):
    """
    used to calculate the GPU's performance and value score
    :param gpu: GPU object
    :return: combined GPU score
    """
    value_score = gpu.g3d_mark / gpu.price

    return (
        gpu.g3d_mark * 0.90
        + gpu.g2d_mark * 0.05
        + value_score * 100 * 0.05
    )


def choose_top_cpus(
    cpus,
    budget,
    preferred_brand="Any",
    limit=40
):
    """
    used to choose strong CPU candidates matching user preferences
    :param cpus: list of CPU objects
    :param budget: user budget
    :param preferred_brand: AMD, Intel or Any
    :param limit: maximum number of CPUs returned
    :return candidates: ranked CPU candidate list
    """
    candidates = [
        cpu
        for cpu in cpus
        if cpu.price <= budget * 0.35
        and cpu_matches_preference(cpu, preferred_brand)
    ]

    candidates.sort(
        key=cpu_score,
        reverse=True
    )

    return candidates[:limit]


def choose_top_gpus(
    gpus,
    budget,
    preferred_brand="Any",
    limit=40
):
    """
    used to choose strong GPU candidates matching user preferences
    :param gpus: list of GPU objects
    :param budget: user budget
    :param preferred_brand: NVIDIA, Radeon or Any
    :param limit: maximum number of GPUs returned
    :return candidates: ranked GPU candidate list
    """
    candidates = [
        gpu
        for gpu in gpus
        if gpu.price <= budget * 0.65
        and gpu_matches_preference(gpu, preferred_brand)
    ]

    candidates.sort(
        key=gpu_score,
        reverse=True
    )

    return candidates[:limit]


def find_supporting_packages(
    cpu,
    motherboards,
    ram_list,
    storage_list,
    limit=20
):
    """
    used to create compatible motherboard, RAM and storage packages
    :param cpu: CPU object
    :param motherboards: list of motherboard objects
    :param ram_list: list of RAM objects
    :param storage_list: list of storage objects
    :param limit: maximum number of packages returned
    :return packages: compatible supporting component packages
    """
    packages = []

    compatible_motherboards = [
        motherboard
        for motherboard in motherboards
        if normalise_socket(motherboard.socket)
        == normalise_socket(cpu.socket)
    ]

    for motherboard in compatible_motherboards:
        compatible_ram = [
            ram
            for ram in ram_list
            if ram.ram_type == motherboard.ram_type
        ]

        for ram in compatible_ram:
            for storage in storage_list:
                package_price = (
                    motherboard.price
                    + ram.price
                    + storage.price
                )

                packages.append({
                    "motherboard": motherboard,
                    "ram": ram,
                    "storage": storage,
                    "price": package_price
                })

    packages.sort(
        key=lambda package: package["price"]
    )

    return packages[:limit]


def choose_best_psu(
    cpu,
    gpu,
    motherboard,
    ram,
    storage,
    psus
):
    """
    used to choose the cheapest PSU that safely powers a complete build
    :return: valid PSU object or None
    """
    total_wattage = calculate_total_wattage(
        cpu,
        gpu,
        motherboard,
        ram,
        storage
    )

    valid_psus = [
        psu
        for psu in psus
        if is_psu_compatible(total_wattage, psu)
    ]

    if not valid_psus:
        return None

    valid_psus.sort(
        key=lambda psu: (
            psu.price,
            psu.wattage
        )
    )

    return valid_psus[0]


def calculate_candidate_score(cpu, gpu):
    """
    used to calculate the performance score of a CPU and GPU pair
    :param cpu: CPU object
    :param gpu: GPU object
    :return: combined core performance score
    """
    return (
        cpu_score(cpu) * 0.30
        + gpu_score(gpu) * 0.70
    )


def generate_candidate_builds(
    cpus,
    gpus,
    motherboards,
    ram_list,
    storage_list,
    psus,
    budget,
    preferred_cpu_brand="Any",
    preferred_gpu_brand="Any",
    cpu_limit=40,
    gpu_limit=40
):
    """
    used to generate complete candidate builds before selecting three recommendations
    :return candidates: list of complete candidate build dictionaries
    """
    candidates = []

    selected_cpus = choose_top_cpus(
        cpus,
        budget,
        preferred_cpu_brand,
        cpu_limit
    )

    selected_gpus = choose_top_gpus(
        gpus,
        budget,
        preferred_gpu_brand,
        gpu_limit
    )

    for cpu in selected_cpus:
        supporting_packages = find_supporting_packages(
            cpu,
            motherboards,
            ram_list,
            storage_list
        )

        for gpu in selected_gpus:
            for package in supporting_packages:
                motherboard = package["motherboard"]
                ram = package["ram"]
                storage = package["storage"]

                psu = choose_best_psu(
                    cpu,
                    gpu,
                    motherboard,
                    ram,
                    storage,
                    psus
                )

                if psu is None:
                    continue

                total_price = (
                    cpu.price
                    + gpu.price
                    + motherboard.price
                    + ram.price
                    + storage.price
                    + psu.price
                )

                candidates.append({
                    "cpu": cpu,
                    "gpu": gpu,
                    "psu": psu,
                    "motherboard": motherboard,
                    "ram": ram,
                    "storage": storage,
                    "core_price": (
                        cpu.price
                        + gpu.price
                        + psu.price
                    ),
                    "supporting_price": package["price"],
                    "estimated_total": total_price,
                    "score": calculate_candidate_score(
                        cpu,
                        gpu
                    )
                })

    return candidates


def choose_build_for_target(
    candidates,
    target_price,
    minimum_price,
    maximum_price
):
    """
    used to select the strongest build near a target price
    :param candidates: generated candidate builds
    :param target_price: preferred price for the recommendation
    :param minimum_price: lowest accepted price
    :param maximum_price: highest accepted price
    :return: selected candidate build or None
    """
    suitable_candidates = [
        candidate
        for candidate in candidates
        if minimum_price
        <= candidate["estimated_total"]
        <= maximum_price
    ]

    if not suitable_candidates:
        return None

    suitable_candidates.sort(
        key=lambda candidate: (
            abs(
                candidate["estimated_total"]
                - target_price
            ),
            -candidate["score"]
        )
    )

    closest_distance = abs(
        suitable_candidates[0]["estimated_total"]
        - target_price
    )

    close_candidates = [
        candidate
        for candidate in suitable_candidates
        if abs(
            candidate["estimated_total"]
            - target_price
        ) <= closest_distance + 75
    ]

    close_candidates.sort(
        key=lambda candidate: candidate["score"],
        reverse=True
    )

    return close_candidates[0]


def recommend_three_builds(
    cpus,
    gpus,
    motherboards,
    ram_list,
    storage_list,
    psus,
    budget,
    preferred_cpu_brand="Any",
    preferred_gpu_brand="Any"
):
    """
    used to return one value, one balanced and one performance build
    :param budget: total budget entered by user
    :return recommendations: three build recommendation dictionaries
    """
    candidates = generate_candidate_builds(
        cpus,
        gpus,
        motherboards,
        ram_list,
        storage_list,
        psus,
        budget,
        preferred_cpu_brand,
        preferred_gpu_brand
    )

    value_build = choose_build_for_target(
        candidates,
        target_price=budget * 0.85,
        minimum_price=budget * 0.75,
        maximum_price=budget * 0.92
    )

    balanced_build = choose_build_for_target(
        candidates,
        target_price=budget * 0.98,
        minimum_price=budget * 0.92,
        maximum_price=budget * 1.02
    )

    performance_build = choose_build_for_target(
        candidates,
        target_price=budget * 1.08,
        minimum_price=budget * 1.02,
        maximum_price=budget * 1.12
    )

    recommendations = []

    if value_build is not None:
        value_build["type"] = "Value Build"
        value_build["description"] = (
            "A strong build that leaves some money below the budget."
        )
        recommendations.append(value_build)

    if balanced_build is not None:
        balanced_build["type"] = "Balanced Build"
        balanced_build["description"] = (
            "A build designed to use almost all of the selected budget."
        )
        recommendations.append(balanced_build)

    if performance_build is not None:
        performance_build["type"] = "Performance Build"
        performance_build["description"] = (
            "A stronger build slightly above budget that can be customised."
        )
        recommendations.append(performance_build)

    return recommendations


def find_compatible_motherboards(
    cpu,
    motherboards,
    maximum_price
):
    """
    used to find motherboards compatible with the selected CPU
    """
    options = [
        motherboard
        for motherboard in motherboards
        if normalise_socket(motherboard.socket)
        == normalise_socket(cpu.socket)
        and motherboard.price <= maximum_price
    ]

    options.sort(
        key=lambda motherboard: motherboard.price
    )

    return options


def find_compatible_ram(
    motherboard,
    ram_list,
    maximum_price
):
    """
    used to find RAM compatible with the selected motherboard
    """
    options = [
        ram
        for ram in ram_list
        if ram.ram_type == motherboard.ram_type
        and ram.price <= maximum_price
    ]

    options.sort(
        key=lambda ram: (
            ram.size_gb,
            ram.size_gb / ram.price
        ),
        reverse=True
    )

    return options


def find_affordable_storage(
    storage_list,
    maximum_price
):
    """
    used to find storage options below the provided price
    """
    options = [
        storage
        for storage in storage_list
        if storage.price <= maximum_price
    ]

    options.sort(
        key=lambda storage: (
            storage.capacity_gb,
            storage.capacity_gb / storage.price
        ),
        reverse=True
    )

    return options


def final_build_is_compatible(
    cpu,
    gpu,
    psu,
    motherboard,
    ram,
    storage
):
    """
    used to check compatibility and PSU wattage without rejecting an over-budget build
    :return: Boolean value showing whether the selected components are compatible
    """
    if (
        normalise_socket(cpu.socket)
        != normalise_socket(motherboard.socket)
    ):
        return False

    if motherboard.ram_type != ram.ram_type:
        return False

    total_wattage = calculate_total_wattage(
        cpu,
        gpu,
        motherboard,
        ram,
        storage
    )

    return is_psu_compatible(total_wattage, psu)