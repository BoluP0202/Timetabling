import pandas as pd
import numpy as np
import re
import pickle

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
def timetable_to_values(df):
    subjects = subjects_to_object_list(df)
    c_sem = len(subjects)
    earlies = check_early(df)
    tot_sess = count_total(subjects)
    x, y = check_late(df)
    popday = 5 - check_freeday(df)
    total_breaks, break_no, break_list = check_breaks(df)
    if x == 0:
        late_pday = 0
    else:
        late_pday = x/len(y)
    tot_block, blocks = check_blocks(df)
    largest_block = max(blocks)
    block_pday = tot_block/popday
    sesspday = tot_sess/popday
    avg_blk = sum(blocks)/tot_block
    if break_no == 0:
        avg_brk = 0
    else:
        avg_brk = total_breaks/break_no
    
    tarb = pd.DataFrame(columns = ['C/semester', 'total sessions', 'sess/popday', 'Number of Blocks', 'Block/pday',
       'Avergae Block size', 'Norm Block', 'Early Sessions', 'Late/day',
       'Avg Break', 'Combined Score', 'Score based Rating'])
    tarb.loc[1,'C/semester'] = len(subjects)
    tarb.loc[1,'total sessions'] = tot_sess
    tarb.loc[1,'sess/popday'] = sesspday
    tarb.loc[1,'Number of Blocks'] =  tot_block
    tarb.loc[1,'Block/pday'] = block_pday
    tarb.loc[1,'Avergae Block size'] = avg_blk
    tarb.loc[1,'Norm Block'] = largest_block
    tarb.loc[1,'Early Sessions'] = earlies
    tarb.loc[1,'Late/day'] = late_pday
    tarb.loc[1,'Avg Break'] = avg_brk
    return tarb

def de_nan(df):
    df = df.replace(np.nan, 0)
    return df
def normnew(original, new):
    new = (new - original.min())/(original.max()-original.min())
    new.loc[1,'Norm Block'] = ((new.loc[1,'Norm Block']-2)**2)/((6-2)**2)
    return new
weight = (0.28, 0.22, 0.1, 0.15, 0.35, 0.2, 0.6, 0.15, 0.3, 0.03)
def scoring(df):
    positives = ((df['Number of Blocks'] * weight[0]) + (df['Block/pday']*weight[1]))
    
    negatives = ((df['Avg Break'] * weight[2]) + (df['Early Sessions'] * weight[3])
                 + (df['Late/day'] * weight[4]) + (df['Norm Block']* weight[5])  
                 + (df['Avergae Block size'] * weight[6]))
    
    penalty = (((df['Norm Block'] + df['Avg Break'])/4) * weight[7]) +((df['C/semester']-df['Number of Blocks'])*.6)
            #+((abs(df['Number of Blocks']-df['total sessions']).item()/df['total sessions'])*weight[8]))
    
    bonus = (df['total sessions']*weight[9])
    score = positives + bonus - penalty - negatives
    df['Combined Score'] = (score - (-1.1025604865868774))/(0.27416115190939894- (-1.1025604865868774))
    above_median = df['Combined Score'] >= 0.6084953052017024

    df['Score based Rating'] = np.where(above_median, 1, 0)
    return df



def feedback(data):
    block_model =pickle.load(open('Models/BlockModel.sav','rb'))
    break_model = pickle.load(open('Models/Breakmodel.sav','rb'))
    earlate_model = pickle.load(open('Models/Early-LateModel.sav', 'rb'))
    session_model = pickle.load(open('Models/SessionsModel.sav','rb'))

    blk_cols = ['Number of Blocks','Block/pday','Avergae Block size','Norm Block']
    sess_cols = ['total sessions', 'sess/popday']
    earlate_cols = ['Early Sessions', 'Late/day']

    blk_data = pd.DataFrame(data,columns= blk_cols)
    
    brk_data = data['Avg Break']
    brk_data = brk_data.to_frame()
    sess_data = pd.DataFrame(data, columns = sess_cols)
    earlate_data = pd.DataFrame(data, columns = earlate_cols)

    blk_fb = block_model.predict(blk_data)
    brk_fb = break_model.predict(brk_data)
    earlate_fb = earlate_model.predict(earlate_data)
    sess_fb = session_model.predict(sess_data)

        
    loaded_model = pickle.load(open('Models/Learned.sav', 'rb'))
    rating = loaded_model.predict(data)

    if rating[0] == 1:
        print('Overall, Its good')
    else:
        print('Overall, Its poor')

    print('Some Ideas, in order of most impactful/reliable to least:')
    if blk_fb == [0]:
        print('The blocks are rating poorly, which means that there are too many classes grouped together, too frequently. Consider adding breaks to split them up or moving a period to a less congested day')
    else:
        print('The blocks are in order')
    
    if earlate_fb ==[0]:
        print('The timetable likely has too many sessions outside of the optimal learning zone (10AM to 3PM), consider adjustments there')
    else:
        print('There arent major problems with the number of early or late classes (those outside 10AM-3PM')

    if sess_fb == [0]:
        print('This course or semester is likely harder to create timetables for, you might want to cosider using up the free day(if it exists), or adjusting the overall balance between the days')
    else:
        print('The issue is likely not related to the nature of this specific course')
        
    if brk_fb == [0]:
        print('The breaks are likely too large; consider shortening them, or moving one some classes around')
    else:
        print('the breaks seem to be in order, not too large or frequent. but breaks are often consequential, not causal of issues')


    return rating[0]