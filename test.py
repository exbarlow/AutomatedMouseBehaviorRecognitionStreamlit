import cv2
from statistics import mean, median


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
