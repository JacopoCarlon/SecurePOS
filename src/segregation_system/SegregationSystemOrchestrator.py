import json
import threading
import os
import time

from src.segregation_system.ClassBalancing import CheckClassBalancing, ViewClassBalancing, BalancingReport
from src.segregation_system.InputCoverage import CheckInputCoverage, ViewInputCoverage, CoverageReport
from src.segregation_system.PreparedSession import PreparedSessionController
from src.segregation_system.LearningSetsController import LearningSetsController
from src.comms import ServerREST
from src.comms.file_transfer_api import FileReceptionAPI

path_config = "segregationConfig.json"

"""
Class that holds the configuration of the segregation system. It reads the configuration file and loads the parameters
into the object. The parameters are:
- minimum_session_number: the minimum number of sessions to collect before starting the segregation process
- operation_mode: the current operation mode of the segregation system
"""
class SegregationSystemConfiguration:
    def __init__(self):
        # open configuration file to read all the parameters
        try:
            with open(path_config) as f:
                # load the configuration file
                config = json.load(f)
                # load the JSON attributes into the object
                self.minimum_session_number = int(config["sessionNumber"])
                self.operation_mode = str(config["operationMode"])
                print("DEBUG> Minimum session number: ", self.minimum_session_number)
                print("DEBUG> Operation mode: ", self.operation_mode)
        except FileNotFoundError:
            print("Configuration file not found")
        except json.JSONDecodeError:
            print("Error decoding JSON file")


class SegregationSystemOrchestrator:
    # initialize the segregation system
    def __init__(self):
        # load the configuration
        self.segregation_config = SegregationSystemConfiguration()

        # object for the prepared sessions
        self.sessions = PreparedSessionController()

        # Start REST server in a separate thread
        self.rest_server = ServerREST()
        self.rest_server.api.add_resource(
            FileReceptionAPI,
            '/upload',
            resource_class_kwargs={'filename': 'prova.json'}
        )
        self.server_thread = threading.Thread(
            target=self.rest_server.run,
            kwargs={'host': '0.0.0.0', 'port': 5000, 'debug': False}
        )
        self.server_thread.daemon = True
        self.server_thread.start()

    def receive(self):
        # Wait for file to appear in the data folder
        filepath = "prova.json"
        while not os.path.exists(filepath):
            print("DEBUG> Waiting for file reception...")
            time.sleep(5)
        print("DEBUG> File received: ", filepath)
        return filepath

    def run(self):
        # object for generating the balancing report
        balancing_check = CheckClassBalancing()
        # object for generating the coverage report
        coverage_check = CheckInputCoverage()

        while True:
            if self.segregation_config.operation_mode == "wait_sessions":
                received_file = self.receive()

                self.sessions.store(received_file)

                to_collect = self.segregation_config.minimum_session_number
                collected = self.sessions.sessions_count()

                if collected < to_collect:
                    print("DEBUG> Not enough sessions collected")
                    time.sleep(2)
                    continue

                # go to the balancing report
                self.segregation_config.operation_mode = "check_balancing"
                print("DEBUG> Operation mode: ", self.segregation_config.operation_mode)

            if self.segregation_config.operation_mode == "check_balancing":
                balancing_check.set_stats()
                print("DEBUG> Set stats for balancing check")

                balancing_check_view = ViewClassBalancing(balancing_check)
                balancing_check_view.show_plot()
                print("DEBUG> Generated plot for balancing check")

                # Prompt user to confirm they've made changes
                while True:
                    user_input = input("Have you modified the outcome file? (yes/no): ").strip().lower()
                    if user_input == "yes":
                        print("DEBUG> User confirmed file modification.")
                        break
                    elif user_input == "no":
                        print("DEBUG> Waiting for user to modify the file...")
                        time.sleep(2)
                    else:
                        print("Invalid input. Please enter 'yes' or 'no'.")

                self.segregation_config.operation_mode = "generate_balancing_outcome"
                print("DEBUG> Operation mode: ", self.segregation_config.operation_mode)

            if self.segregation_config.operation_mode == "generate_balancing_outcome":
                balancing_report = BalancingReport()
                print("DEBUG> Balancing report generated")
                print("DEBUG> Balancing approved: ", balancing_report.approved)
                print("DEBUG> Unbalanced classes: ", balancing_report.unbalanced_classes)
                # check if the balancing is approved
                if balancing_report.approved:
                    # go to the coverage report
                    print("DEBUG> Balancing approved")
                    self.segregation_config.operation_mode = "check_coverage"
                else:
                    # send the balancing outcome
                    print("DEBUG> Balancing not approved")
                    # go back to the wait sessions
                    self.segregation_config.operation_mode = "wait_sessions"

            if self.segregation_config.operation_mode == "check_coverage":
                coverage_check.set_stats()
                print("DEBUG> Set stats for coverage check")

                coverage_check_view = ViewInputCoverage(coverage_check)
                coverage_check_view.show_plot()
                print("DEBUG> Generated plot for coverage check")
                # Prompt user to confirm they've made changes
                while True:
                    user_input = input("Have you modified the required file? (yes/no): ").strip().lower()
                    if user_input == "yes":
                        print("DEBUG> User confirmed file modification.")
                        break
                    elif user_input == "no":
                        print("DEBUG> Waiting for user to modify the file...")
                    else:
                        print("Invalid input. Please enter 'yes' or 'no'.")

                self.segregation_config.operation_mode = "generate_coverage_outcome"
                print("DEBUG> Operation mode: ", self.segregation_config.operation_mode)

            if self.segregation_config.operation_mode == "generate_coverage_outcome":
                coverage_report = CoverageReport()
                print("DEBUG> Coverage report generated")
                print("DEBUG> Coverage approved: ", coverage_report.approved)
                print("DEBUG> Uncovered features: ", coverage_report.uncovered_features_suggestions)

                # check if the coverage is approved
                if coverage_report.approved:
                    # go to the wait sessions
                    print("DEBUG> Coverage approved")
                    self.segregation_config.operation_mode = "generate_sets"
                else:
                    # send the coverage outcome
                    print("DEBUG> Coverage not approved")
                    # go back to the wait sessions
                    self.segregation_config.operation_mode = "wait_sessions"

            if self.segregation_config.operation_mode == "generate_sets":
                learning_sets_controller = LearningSetsController()
                learning_sets_controller.save_sets()
                print("DEBUG> Learning sets generated and saved")

                return False


