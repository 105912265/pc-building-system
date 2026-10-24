# Author: Kshitij Kshirsagar
# Filename: fps_estimator.py
# Last edited: 23/06/2026

import pandas as pd


def load_game_fps_baselines(
    filename="data/game_fps_baselines.csv"
):
    """
    used to load the game FPS baseline dataset
    :param filename: path to baseline FPS CSV
    :return: DataFrame containing baseline game FPS values
    """
    return pd.read_csv(filename)


def estimate_fps_for_game(
    selected_cpu,
    selected_gpu,
    game_name,
    fps_data
):
    """
    used to estimate FPS for one game using CPU and GPU benchmark scaling
    :param selected_cpu: selected CPU object
    :param selected_gpu: selected GPU object
    :param game_name: game name to estimate
    :param fps_data: DataFrame containing FPS baselines
    :return: dictionary containing game name and estimated FPS
    """
    matching_rows = fps_data[
        fps_data["game"] == game_name
    ]

    if matching_rows.empty:
        return {
            "game": game_name,
            "estimated_fps": 0
        }

    baseline = matching_rows.iloc[0]

    gpu_factor = (
        selected_gpu.g3d_mark
        / baseline["baseline_gpu_score"]
    )

    cpu_factor = (
        selected_cpu.cpu_mark
        / baseline["baseline_cpu_score"]
    )

    scaling_factor = (
        gpu_factor * 0.75
        + cpu_factor * 0.25
    )

    estimated_fps = round(
        baseline["baseline_fps"]
        * scaling_factor
    )

    estimated_fps = max(
        20,
        min(estimated_fps, 400)
    )

    return {
        "game": game_name,
        "estimated_fps": estimated_fps
    }


def estimate_fps_for_games(
    selected_cpu,
    selected_gpu,
    selected_games,
    fps_data
):
    """
    used to estimate FPS for multiple selected games
    :param selected_cpu: selected CPU object
    :param selected_gpu: selected GPU object
    :param selected_games: list of selected games
    :param fps_data: DataFrame containing FPS baselines
    :return: list of estimated FPS dictionaries
    """
    estimates = []

    for game_name in selected_games:
        estimate = estimate_fps_for_game(
            selected_cpu,
            selected_gpu,
            game_name,
            fps_data
        )

        estimates.append(estimate)

    return estimates