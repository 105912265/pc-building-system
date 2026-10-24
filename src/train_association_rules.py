# Author: Kshitij Kshirsagar
# Filename: train_association_rules.py
# Last edited: 19/06/2026

import os

import joblib
import pandas as pd

from mlxtend.frequent_patterns import (
    apriori,
    association_rules
)
from mlxtend.preprocessing import TransactionEncoder


def create_transactions(data):
    """
    used to convert every PC build row into a transaction containing its components
    :param data: DataFrame containing synthetic PC build transactions
    :return transactions: list containing one component transaction per PC build
    """
    transactions = []

    for _, row in data.iterrows():
        transaction = [
            f"CPU:{row['cpu']}",
            f"GPU:{row['gpu']}",
            f"Motherboard:{row['motherboard']}",
            f"RAM:{row['ram']}",
            f"Storage:{row['storage']}",
            f"PSU:{row['psu']}"
        ]

        transactions.append(transaction)

    return transactions


def train_association_rules(
    input_file="data/build_transactions.csv",
    model_file="models/association_rules.pkl",
    csv_file="models/association_rules.csv",
    minimum_support=0.01,
    minimum_confidence=0.20
):
    """
    used to train association rules from synthetic PC build transactions
    :param input_file: location of the transaction dataset
    :param model_file: location used to save the association rule model
    :param csv_file: location used to save a readable version of the rules
    :param minimum_support: minimum percentage of builds containing an item combination
    :param minimum_confidence: minimum reliability required for a rule
    :return rules: DataFrame containing generated association rules
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(
            f"Transaction file was not found: {input_file}"
        )

    data = pd.read_csv(input_file)

    required_columns = [
        "cpu",
        "gpu",
        "motherboard",
        "ram",
        "storage",
        "psu"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    data = data.dropna(
        subset=required_columns
    )

    if data.empty:
        raise ValueError(
            "The transaction dataset contains no valid rows."
        )

    transactions = create_transactions(data)

    encoder = TransactionEncoder()

    encoded_array = encoder.fit(
        transactions
    ).transform(
        transactions
    )

    encoded_data = pd.DataFrame(
        encoded_array,
        columns=encoder.columns_
    )

    frequent_itemsets = apriori(
        encoded_data,
        min_support=minimum_support,
        use_colnames=True,
        max_len=3
    )

    if frequent_itemsets.empty:
        raise ValueError(
            "No frequent itemsets were found. "
            "Lower minimum_support or check the dataset."
        )

    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=minimum_confidence
    )

    if rules.empty:
        raise ValueError(
            "No association rules were found. "
            "Lower minimum_confidence or minimum_support."
        )

    rules = rules[
        [
            "antecedents",
            "consequents",
            "support",
            "confidence",
            "lift"
        ]
    ].copy()

    rules = rules[
        rules["lift"] > 1
    ]

    if rules.empty:
        raise ValueError(
            "No rules with lift greater than 1 were found."
        )

    rules = rules.sort_values(
        by=[
            "lift",
            "confidence",
            "support"
        ],
        ascending=False
    )

    model_directory = os.path.dirname(
        model_file
    )

    if model_directory:
        os.makedirs(
            model_directory,
            exist_ok=True
        )

    csv_directory = os.path.dirname(
        csv_file
    )

    if csv_directory:
        os.makedirs(
            csv_directory,
            exist_ok=True
        )

    joblib.dump(
        rules,
        model_file
    )

    readable_rules = rules.copy()

    readable_rules["antecedents"] = (
        readable_rules["antecedents"].apply(
            lambda items: " | ".join(
                sorted(items)
            )
        )
    )

    readable_rules["consequents"] = (
        readable_rules["consequents"].apply(
            lambda items: " | ".join(
                sorted(items)
            )
        )
    )

    readable_rules.to_csv(
        csv_file,
        index=False
    )

    print(
        f"Generated {len(rules)} association rules."
    )

    print(
        f"Model saved to {model_file}."
    )

    print(
        f"Readable rules saved to {csv_file}."
    )

    return rules


if __name__ == "__main__":
    train_association_rules()