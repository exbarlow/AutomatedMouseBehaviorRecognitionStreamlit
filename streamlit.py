import streamlit as st
import pandas as pd
from statistics import mean, median
import cv2

st.title("csv_analysis")

class Period:
    def __init__(self,start:int,action=str):
        self.start = start
        self.end = None
        ## should either be "grooming", "rearing_mid", or "rearing_wall"
        self.action = action

    def set_end(self,end:int):
        self.end = end

    def get_length(self):
        if self.end is None:
            return 0
        else:
            return self.end-self.start + 1

    def __repr__(self):
        return f"<Period {self.action}: {self.start}-{self.end}>"

    def __lt__(self,other):
        return self.end < other.end

def get_current_action(line):
    grooming, rearing_mid, rearing_wall = line[4:7]
    # print(grooming,rearing_mid,rearing_wall)

    if grooming == 1:
        return "grooming"
    elif rearing_mid == 1:
        return "rearing_mid"
    elif rearing_wall == 1:
        return "rearing_wall"
    else:
        return "no_action"

## get mean, median
def get_summary_data(period_set):
    length_list = []
    for period in period_set:
        length_list.append(period.get_length())

    if len(length_list) == 0:
        return (0,0)
    
    mean_length = mean(length_list)
    median_length = median(length_list)

    return (mean_length,median_length)






def analyze_df(df):
    frame_counts = {"grooming":0,"rearing_mid":0,"rearing_wall":0}
    period_dict = {"grooming":set(),"rearing_mid":set(),"rearing_wall":set()}
    frame_labels = []

    current_period = None

    for index, line in df.iterrows():
        frame = int(index)
        assert(frame == line[0])
        current_action = get_current_action(line)
        frame_labels.append(current_action)


        if current_period is None or current_period.action != current_action:
            ## behavior changes, need to end the old period
            if current_period is not None:
                current_period.set_end(frame-1)
                period_dict[current_period.action].add(current_period)
            ## start new action period if necessary
            if current_action != "no_action":
                current_period = Period(frame,current_action)
            else:
                current_period = None

        if current_action != "no_action":
            frame_counts[current_action] += 1
    
    if current_period is not None:
        current_period.set_end(frame)
        period_dict[current_period.action].add(current_period)

    mean_grooming, median_grooming = get_summary_data(period_dict["grooming"])
    mean_rearing_mid, median_rearing_mid = get_summary_data(period_dict["rearing_mid"])
    mean_rearing_wall, median_rearing_wall = get_summary_data(period_dict["rearing_wall"])

    data = {}
    data["f_grooming"] = frame_counts["grooming"]
    data["f_rearing_mid"] = frame_counts["rearing_mid"]
    data["f_rearing_wall"] = frame_counts["rearing_wall"]
    data["p_grooming"] = sorted(list(period_dict["grooming"]))
    data["p_rearing_mid"] = sorted(list(period_dict["rearing_mid"]))
    data["p_rearing_wall"] = sorted(list(period_dict["rearing_wall"]))
    data["mean_grooming"] = mean_grooming
    data["mean_rearing_mid"] = mean_rearing_mid
    data["mean_rearing_wall"] = mean_rearing_wall
    data["median_grooming"] = median_grooming
    data["median_rearing_mid"] = median_rearing_mid
    data["median_rearing_wall"] = median_rearing_wall
    data["frame_labels"] = frame_labels

    return data



def anotate_videos(results,path_to_video):
    position = (10,50)
    for experiment in results.items():
        to_predict = experiment[1]["test_y"]
        label = experiment[1]["label"]
        predictions = experiment[1]["results"]
        df_acc = accuracy(to_predict[label],predictions)
        print(experiment[0],": \n", df_acc,"\n")
        videos = experiment[1]["test"]
        frame_int=0
        for video in videos:
            name_video = video.split("_")[2][:-4] + ".mp4"
            print(name_video)
            cap = cv2.VideoCapture(path_to_video+name_video)
            if not cap.isOpened(): 
                  print("Unable to read camera feed")
            frame_width = int(cap.get(3))
            frame_height = int(cap.get(4))
            out = cv2.VideoWriter("out/"+experiment[0]+"_"+name_video, cv2.VideoWriter_fourcc(*'MP4V'), 20, (frame_width,frame_height))
            returned = True
            while returned:
                returned, frame = cap.read()
                if returned:
                    label_out = label if predictions[frame_int] else "0"
                    cv2.putText(frame, label_out,position,cv2.FONT_HERSHEY_SIMPLEX, 1, (209, 80, 0, 255),3)
                    out.write(frame)
                    frame_int += 1
            cap.release()
            out.release()



def annotate_video(labels,video_name,path_to_video):
    position = (10,50)
    cap = cv2.VideoCapture(path_to_video+video_name)
    print(path_to_video+video_name)
    if not cap.isOpened():
        print("Unable to read camera feed")
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    out = cv2.VideoWriter("out_"+video_name,cv2.VideoWriter_fourcc(*'mp4v'),10,(frame_width,frame_height))
    returned = True
    frame_count = 0
    while returned:
        returned, frame = cap.read()
        if returned:
            label_out = labels[frame_count] if labels[frame_count] != "no_action" else "0"
            # print(label_out)
            cv2.putText(frame,label_out,position,cv2.FONT_HERSHEY_SIMPLEX,1,(209,80,0,255),3)
            out.write(frame)
            frame_count += 1
    cap.release()
    out.release()
    print("finished")

def write_bytesio_to_file(filename,bytesio):
    """
    Write the contents of the given BytesIO to a file.
    Creates the file or overwrites the file if it does
    not exist yet. 
    """
    with open(filename, "wb") as outfile:
    # Copy the BytesIO stream to the output file
        outfile.write(bytesio.getbuffer())

uploaded_csvs = st.file_uploader("Upload CSV files",type=["csv"],accept_multiple_files=True)
uploaded_videos = st.file_uploader("Upload Video files",type=["mp4"],accept_multiple_files=True)

if len(uploaded_csvs) != len(uploaded_videos):
    st.write("Make sure that each video has a corresponding .csv file and vice-versa")

video_names = set()

for uploaded_video in uploaded_videos:
    write_bytesio_to_file(uploaded_video.name,uploaded_video)
    video_names.add(uploaded_video.name)


if len(uploaded_csvs) > 0:
    tab_names = []

    for ind, uploaded_csv in enumerate(uploaded_csvs):
        tab_names.append(uploaded_csv.name)

    does_match = True
    for csv_name in tab_names:
        corresponding_video_name = csv_name.split("_")[2][:-4] + ".mp4"
        if corresponding_video_name not in video_names:
            st.write("Make sure that each video has a correpsonding .csv file and vice-versa")
            does_match = False
            break
    
    if does_match:
        tabs = st.tabs(tab_names)
            
        for index,tab in enumerate(tabs):
            with tab:
                df = pd.read_csv(uploaded_csvs[index])

                ob = analyze_df(df)

                frames = list(ob.values())[0:3]
                periods = list(ob.values())[3:6]
                means = list(ob.values())[6:9]
                medians = list(ob.values())[9:12]
        
                ## TEMP
                video_name = uploaded_csvs[index].name.split("_")[2][:-4] + ".mp4"
                annotate_video(ob["frame_labels"],video_name,"")

                f = {'Frames':frames}
                mean_data = {'Mean frames per action':means}
                median_data = {'Median frames per action':medians}

                ## TEMP
                video_file = open("out_"+video_name, 'rb')
                st.video(video_file)
                
                instance_data = {'Unique instances of action':[len(period) for period in periods]}
                st.bar_chart(pd.DataFrame(data=f,index=['Grooming','Mid-Rearing','Wall-Rearing']))
                st.bar_chart(pd.DataFrame(data=mean_data,index=['Grooming','Mid-Rearing','Wall-Rearing']))
                st.bar_chart(pd.DataFrame(data=median_data,index=['Grooming','Mid-Rearing','Wall-Rearing']))
                st.bar_chart(pd.DataFrame(data=instance_data,index=['Grooming','Mid-Rearing','Wall-Rearing']))


            
    

            


