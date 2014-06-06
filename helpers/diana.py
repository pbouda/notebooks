#!/usr/bin/env python

import csv
import codecs

import poioapi.io.graf
import poioapi.annotationgraph
import poioapi.data

def from_excel(filepath):
    ag = poioapi.annotationgraph.AnnotationGraph()
    parser = ExcelParser(filepath)
    converter = poioapi.io.graf.GrAFConverter(parser)
    converter.parse()
    ag.tier_hierarchies = converter.tier_hierarchies
    ag.structure_type_handler = poioapi.data.DataStructureType(ag.tier_hierarchies[0])
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

class ExcelParser(poioapi.io.graf.BaseParser):

    def __init__(self, filepath):
        self.word_orders = dict()
        self.clauses = list()
        self.clause_types = dict()
        self.last_id = -1
        with codecs.open(filepath, "r", "utf-8") as csvfile:
            hinuq2 = unicode_csv_reader(csvfile, delimiter="\t")
            i = 0
            for row in hinuq2:
                if i == 2:
                    clause_ids = row
                elif i == 3:
                    clause_types = row
                elif i == 4:
                    grammatical_relations = row
                elif i == 5:
                    pos_agreement = row
                i += 1  
                if i > 7:
                    # now parse
                    word_order = []
                    c_id = None
                    prev_c_id = None
                    for j, clause_id in enumerate(clause_ids):

                        # new clause
                        if clause_id != "":
                            # add word order to previous clause
                            if len(word_order) > 0:
                                self.word_orders[c_id] = word_order
                            word_order = []
                            
                            # add new clause
                            c_id = self._next_id()
                            self.clauses.append(c_id)
                            self.clause_types[c_id] = clause_types[j].strip()
                        
                        grammatical_relation = grammatical_relations[j].strip()
                        if "zero" in pos_agreement[j].strip():
                            grammatical_relation = "zero-{0}".format(grammatical_relation)
                        word_order.append(grammatical_relation)

                    if len(word_order) > 0:
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

        return None

    def get_annotations_for_tier(self, tier, annotation_parent=None):
        if tier.name == "clause_id":
            return [poioapi.io.graf.Annotation(i, v) for i, v in enumerate(self.clauses)]

        elif tier.name == "clause_type":
            return [poioapi.io.graf.Annotation(self._next_id(), self.clause_types[annotation_parent.id])]

        elif tier.name == "grammatical_relation":
            return [poioapi.io.graf.Annotation(self._next_id(), v)  for v in self.word_orders[annotation_parent.id]]
        
        return []

    def tier_has_regions(self, tier):
        return False

    def region_for_annotation(self, annotation):
        pass

    def get_primary_data(self):
        pass
