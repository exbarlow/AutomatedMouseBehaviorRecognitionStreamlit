import streamlit as st
import pandas as pd
from helpers import *
import zipfile

st.title("csv_analysis")

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
        if corresponding_video_name not in video_names or len(uploaded_csvs) != len(uploaded_videos):
            st.write("Make sure that each video has a corresponding .csv file and vice-versa")
            does_match = False
            break
    
    if does_match:
        zip_name = "results"
        z = zipfile.Zipfile(f"{zip_name}.zip",mode="w")

        for uploaded_csv in uploaded_csvs:
            write_bytesio_to_file(uploaded_csv.name,uploaded_csv)
            z.write(uploaded_csv.name)
        
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

                z.write("out_"+video_name)

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


        with open(f"{zip_name}.zip","rb") as fp:
            btn = st.download_button(label="Download results",data=fp,file_name=f"{zip_name}.zip",mime="application/zip")
    

            


