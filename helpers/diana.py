#!/usr/bin/env python

import csv
import codecs
import collections

import poioapi.io.graf
import poioapi.annotationgraph
import poioapi.data

class WrongAnnotationCount(Exception): pass

WordOrder = collections.namedtuple("WordOrder",
    "clause_id word_order clause_type agreement")

def from_excel(filepath, skip_lines=[], tier_numbers=None):
    ag = poioapi.annotationgraph.AnnotationGraph()
    parser = ExcelParser(filepath, skip_lines, tier_numbers)
    converter = poioapi.io.graf.GrAFConverter(parser)
    converter.parse()
    ag.tier_hierarchies = converter.tier_hierarchies
    ag.structure_type_handler = poioapi.data.DataStructureType(
        ag.tier_hierarchies[0])
    ag.graf = converter.graf
    return ag

def unicode_csv_reader(unicode_csv_data, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data), **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

def word_orders(ag, search_terms = None, annotation_map = {}, with_agreement = False):
    clause_unit_nodes = ag.nodes_for_tier("clause_id")
    for parent_node in clause_unit_nodes:
        word_order = []
        agreement = []
        clause_type = None
        type_node = ag.nodes_for_tier("clause_type", parent_node)
        if len(type_node) == 1:
            clause_type = ag.annotation_value_for_node(type_node[0])
        else:
            raise WrongAnnotationCount(
                "no clause type in clause unit {0}".format(parent_node.id))
        for gramm_node in ag.nodes_for_tier("grammatical_relation", parent_node):
            a_value = ag.annotation_value_for_node(gramm_node)
            if search_terms and a_value in search_terms:
                if a_value in annotation_map:
                    a_value = annotation_map[a_value]
                word_order.append(a_value)

                if with_agreement:
                    agr_nodes = ag.nodes_for_tier("agreement", gramm_node)
                    if len(agr_nodes) != 1:
                        print("no agreement annotation in clause unit {0} for grammatical relation '{1}'".format(parent_node.id, a_value))
                    else:
                        agr_node = ag.nodes_for_tier("agreement", gramm_node)[0]
                        agr = ag.annotation_value_for_node(agr_node)
                        agreement.append(agr)

        yield WordOrder(parent_node.id, word_order, clause_type, agreement)

class ExcelParser(poioapi.io.graf.BaseParser):

    def __init__(self, filepath, skip_lines=[], tier_numbers=None):
        self.word_orders = dict()
        self.agreements = dict()
        self.clauses = list()
        self.clause_types = dict()
        self.last_id = -1
        with codecs.open(filepath, "r", "utf-8") as csvfile:
            hinuq2 = csv.reader(csvfile, delimiter="\t")
            i = 0
            for row in hinuq2:
                if row[0] in skip_lines:
                    continue

                if i == tier_numbers["clause_id"]:
                    clause_ids = row
                elif i == tier_numbers["clause_type"]:
                    clause_types = row
                elif i == tier_numbers["grammatical_relation"]:
                    grammatical_relations = row
                elif i == tier_numbers["pos_agreement"]:
                    pos_agreements = row
                i += 1  
                if i > tier_numbers["last_line"]:
                    # now parse
                    word_order = []
                    pos_agreement = []
                    c_id = None
                    prev_c_id = None
                    for j, clause_id in enumerate(clause_ids):

                        # new clause
                        if clause_id != "":
                            # add word order to previous clause
                            self.word_orders[c_id] = word_order
                            word_order = []
                            
                            # add new clause
                            c_id = clause_id # self._next_id()
                            if c_id in self.clauses:
                                print("Error: duplicate clause ID: {0}".format(c_id))
                                continue
                            self.clauses.append(c_id)
                            self.clause_types[c_id] = clause_types[j].strip()
                        
                        grammatical_relation = grammatical_relations[j].strip()
                        if grammatical_relation:
                            pos_agreement = pos_agreements[j].strip()
                            if "zero" in pos_agreement:
                                grammatical_relation = "zero-{0}".format(grammatical_relation)
                            if grammatical_relation == "say":
                                grammatical_relation = "SAY"
                            gr_id = self._next_id()
                            self.agreements[gr_id] = pos_agreement
                            word_order.append((gr_id, grammatical_relation))

                    self.word_orders[c_id] = word_order

                    i = 0

    def _next_id(self):
        self.last_id += 1
        return self.last_id

    def get_root_tiers(self):
        return [poioapi.io.graf.Tier("clause_id")]

    def get_child_tiers_for_tier(self, tier):
        if tier.name == "clause_id":
            return [poioapi.io.graf.Tier("grammatical_relation"),
                    poioapi.io.graf.Tier("clause_type")]
        elif tier.name == "grammatical_relation":
            return [poioapi.io.graf.Tier("agreement")]

        return None

    def get_annotations_for_tier(self, tier, annotation_parent=None):
        if tier.name == "clause_id":
            return [poioapi.io.graf.Annotation(v, v) for i, v in enumerate(self.clauses)]

        elif tier.name == "clause_type":
            return [poioapi.io.graf.Annotation(self._next_id(), self.clause_types[annotation_parent.id])]

        elif tier.name == "grammatical_relation":
            return [poioapi.io.graf.Annotation(gr_id, v) for gr_id, v in self.word_orders[annotation_parent.id]]
        
        elif tier.name == "agreement":
            if annotation_parent and self.agreements[annotation_parent.id]:
                return [poioapi.io.graf.Annotation(self._next_id(), self.agreements[annotation_parent.id]) ]

        return []

    def tier_has_regions(self, tier):
        return False

    def region_for_annotation(self, annotation):
        pass

    def get_primary_data(self):
        pass
