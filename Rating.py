import pandas as pd
import numpy as np
import re

class Subject:
    def __init__(self, code, title, units):
        self.title = title
        self.code = code
        self.units = units


def get_subject(code, course, units):
    return Subject(code, course , units)

def count_total(courseobjectlist):
    tots = 0
    for obj in courseobjectlist:
        tots += obj.units 
    return tots

def subjects_to_object_list(df):
    subjects = []
    for sub in df['index']:
        subber = get_subject(df['Code'][sub], df['Courses'][sub], df['Units'][sub])
        subjects.append(subber)
    return subjects

def check_early(df):
    counter = 5
    for slot in df.loc[0]:
        if slot == '-':
            counter -=1
    return counter

def check_late(df):
    counter = 15
    cols = []
    irrele = ['index', 'Code', 'Courses', 'Units', 'TIME']
    for index, slot in df.loc[6].items():
        if slot == '-':
            counter -=1
        elif index not in irrele:
            cols.append(index)
    for index, slot in df.loc[7].items():
        if slot == '-':
            counter -=1
        elif index not in cols and index not in irrele:
            cols.append(index)
    for index, slot in df.loc[8].items():
        if slot == '-':
            counter -=1
        elif index not in cols and index not in irrele:
            cols.append(index)
    return counter,cols


def check_freeday(df):
    counter = 0
    for col in df.columns.values:
        if col in ['M', 'TU', 'W', 'TH', 'F']:
            free  = 0
            for s in df[col]:
                if s == '-':
                    free +=1
            if free == 9:
                counter +=1
    return counter

def check_breaks(df):
    break_tally = 0
    break_total = 0
    break_len = []
    for col in df.columns.values:
        if col in ['M', 'TU', 'W', 'TH', 'F']:
            no_pre_class = True
            break_sf = 0
            broken = True
            for s in df[col]:
                not_brk = re.findall(r"[^-]",s)
                if not_brk == [] and no_pre_class == True:
                    pass
                elif not_brk != [] and no_pre_class == True:
                    no_pre_class = False
                elif not_brk == [] and no_pre_class == False:
                    break_sf+=1
                elif not_brk != [] and no_pre_class == False:
                    if break_sf >0:
                        break_total+=break_sf
                        break_tally+=1
                        break_len.append(break_sf)
                        break_sf = 0

    return break_total, break_tally,break_len

def check_blocks(df):
    block_tally = 0
    block_total = 0
    block_len = []
    for col in df.columns.values:
        if col in ['M', 'TU', 'W', 'TH', 'F']:
            no_pre_class = True
            block_sf = 0
            broken = True
            for s in df[col]:
                not_brk = re.findall(r"[^-]",s)
                if not_brk == [] and no_pre_class == True:
                    #no class yet
                    pass
                elif not_brk != [] and no_pre_class == True:
                    #class start
                    no_pre_class = False
                    block_sf+=1
                elif not_brk == [] and no_pre_class == False:
                    #no class after class
                    if block_sf >0:
                        block_total+=block_sf
                        block_tally+=1
                        block_len.append(block_sf)
                        block_sf = 0
                elif not_brk != [] and no_pre_class == False:
                    #class at anypoint after class
                    block_sf += 1

    return block_tally,block_len

def timetable_to_csv_table(c_sem, tot_sess, sess):
    