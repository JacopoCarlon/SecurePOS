import logging
import threading

import pandas as pd

from evaluation_system.label import Label
from evaluation_system.label_store import LabelStore
from evaluation_system.evaluation_report_controller import EvaluationReportController


class LabelStoreController:
    def __init__(self):
        """
        Need to keep count of labels from expert and classifier,
        will increase count upon label storing, based on label_source field value.
        """
        self.num_labels_from_expert = 0
        self.num_labels_from_classifier = 0
        self.enough_total_labels = False
        self.enough_matching_labels = False  # redundancy value, can be only local
        self.store = LabelStore()
        self.report = EvaluationReportController()
        # control access to db ? (if local for each instance, not needed)

    def update_count_labels(self, label_source):
        if label_source == 'classifier':
            self.num_labels_from_classifier += 1
        elif label_source == 'expert':
            self.num_labels_from_expert += 1
        else:
            logging.error(f'Non standard label is being processed in EvalSys; \nlabel_src : {label_source}')
            raise ValueError("Evaluation System working on unknown-origin label")

    def store_label(self, min_labels_opinionated: int, label):
        logging.info("Label storage")
        # receive labels as json, need to convert them to Label object.
        session_id = label["session_id"]
        label_value = label["value"]
        label_source = label["source"]
        label = Label(session_id, label_value, label_source)
        label_dataframe = pd.DataFrame(label.to_dict(), index=[0],
                                       columns=["session_id", "value"])
        if label.label_source == "classifier":
            self.store.ls_store_label_df(label_dataframe, 'classifierLabel')
            self.update_count_labels('classifier')
        elif label.label_source == "expert":
            self.store.ls_store_label_df(label_dataframe, 'expertLabel')
            self.update_count_labels('expert')
        else:
            logging.error(f'Non standard label arrived to store_label in EvalSys;\nlabel_src : {label.label_source}')
            raise ValueError("Evaluation System working on unknown-origin label")

        # in order to there be enough opinionated,
        # there first need to be enough for each group, this is a <NECESSARY> condition,
        # but obv it is <NOT SUFFICIENT>
        if not self.enough_total_labels:
            if self.num_labels_from_expert >= min_labels_opinionated and \
                    self.num_labels_from_classifier >= min_labels_opinionated:
                self.enough_total_labels = True
        if self.enough_total_labels:
            logging.info("Enough labels to generate a report")
            print("generate report")

            # load labels that have opinion from classifier AND expert, matching on uuid
            load_matching_labels_query = \
                "SELECT expertLT.session_id, " \
                "expertLT.value as expertValue," \
                "classifierLT.value as classifierValue " \
                "FROM expertLabelTable AS expertLT " \
                "INNER JOIN classifierLabelTable AS classifierLT " \
                "ON expertLT.session_id = classifierLT.session_id"
            opinionated_labels = self.store.ls_select_labels(load_matching_labels_query)

            opinionated_session_id_list = opinionated_labels["session_id"].to_list()

            num_usable_labels = len(opinionated_session_id_list)

            # in order to complete the evaluation,
            # we need a minimum threshold of
            # labels with opinions from both classifier and expert
            if num_usable_labels >= min_labels_opinionated:
                query = "DELETE FROM expertLT " + \
                        "WHERE session_id IN (" + \
                        str(opinionated_session_id_list)[1:-1] + ")"
                self.store.ls_delete_labels(query)

                query = "DELETE FROM classifierLT " + \
                        "WHERE session_id IN (" + \
                        str(opinionated_session_id_list)[1:-1] + ")"
                self.store.ls_delete_labels(query)

                self.num_labels_from_expert -= min_labels_opinionated
                self.num_labels_from_classifier -= min_labels_opinionated
                # since all of these labels have been used,
                # (but not all the labels that exist in our db),
                # we clean this field, and it will be re-evaluated as a new label comes.
                self.enough_matching_labels = False

                # now we have all the labels with the correct requirements,
                # we can start evaluating
                logging.info("Start EvaluationReport generation")
                thread = threading.Thread(target=self.report.generate_report,
                                          args=[opinionated_labels])
                thread.start()
