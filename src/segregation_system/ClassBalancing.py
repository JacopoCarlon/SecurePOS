"""
This module is responsible for checking the class balancing of the dataset.
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from src.segregation_system.DataExtractor import DataExtractor

outcome_path = "../../data/segregation_system/outcomes/balancing_outcome.json"
parameters_path = "../../data/segregation_system/config/balancing_parameters.json"
image_path = "../../data/segregation_system/plots/balancing_plot.png"

class BalancingParameters:
    """
    Class that holds the parameters for the class balancing check.
    """
    def __init__(self):
        """
        Constructor for the BalancingParameters class.
        """

        """
        Load the parameters from the JSON file.
        """
        try:
            with open(parameters_path) as f:
                self.parameters = json.load(f)
        except FileNotFoundError:
            print("ERROR> Parameters file not found")
        except json.JSONDecodeError:
            print("ERROR> Error decoding JSON file")

        """
        Load the JSON attributes into the object.
        # - tolerance: float, percentage of tolerance for the class balancing
        """
        self.tolerance = self.parameters["tolerance"]

class BalancingReport:
    """
    Class that holds the outcome of the class balancing check provided
    by the Data Analyst.
    """
    def __init__(self):
        """
        Constructor for the BalancingReport class.
        """

        """
        Load the outcome from the JSON file.
        """
        try:
            with open(outcome_path) as f:
                self.outcome = json.load(f)
        except FileNotFoundError:
            print("ERROR> Outcome file not found")
        except json.JSONDecodeError:
            print("ERROR> Error decoding JSON file")


        """
        Load the JSON attributes into the object.
        # - approved: boolean, whether the class balancing is approved
        # - unbalanced_classes: list of classes that are unbalanced and how many
        # samples the Data Analyst wants
        """
        self.approved = self.outcome["approved"]
        self.unbalanced_classes = self.outcome["unbalanced_classes"]

class CheckClassBalancing:
    """
    Class that prepare the data for the balancing analysis of the risk labels of the dataset.
    """
    def __init__(self):
        """
        Constructor for the CheckClassBalancing class.
        """

        """
        Initialize the labels_stat dictionary.
        - labels_stat: dictionary, statistics of the labels that are shown in the balancing plot
        - data_extractor: DataExtractor, object that extracts the data from the dataset
        """
        self.labels_stat = {}
        self.data_extractor = DataExtractor()

    def retrieve_labels(self):
        """
        Set the statistics of the labels that are shown in the balancing plot.
        """

        """
        Extract the labels from the dataset and prepare the dictionary.
        """
        labels = self.data_extractor.extract_grouped_labels()
        dictionary = {}
        for row in labels.itertuples(index=False):
            dictionary[row.label] = row.samples

        """
        Set the labels_stat dictionary.
        """
        self.labels_stat = dictionary


class ViewClassBalancing:
    """
    Class that shows the plot of the risk class balancing.
    """
    def __init__(self, report):
        """
        Constructor for the ViewClassBalancing class.
        :param report: data structure that holds the input of the plot
        """
        self.report = report

    def show_plot(self):
        """
        Show the plot of the risk class balancing.
        """

        """
        Retrieve the labels and relative values from the report.
        """
        labels = list(self.report.labels_stat.keys())
        values = list(self.report.labels_stat.values())

        """
        Calculate the average value of the labels and the tolerance lower and upper limit.
        """
        config = BalancingParameters()
        avg = np.mean(np.array(values))
        lower_tolerance = avg - (avg * config.tolerance)
        upper_tolerance = avg + (avg * config.tolerance)

        """
        Plot the data and save the plot as a PNG file.
        """
        plt.bar(labels, values)
        plt.axhline(y=avg, color='r', linestyle='-', label='Average')
        plt.axhline(y=lower_tolerance, color='g', linestyle='--', label='Lower Tolerance')
        plt.axhline(y=upper_tolerance, color='g', linestyle='--', label='Upper Tolerance')

        plt.xlabel('Classes')
        plt.ylabel('Number of samples')
        plt.title('Risk Level Balancing')

        plt.savefig(image_path)
