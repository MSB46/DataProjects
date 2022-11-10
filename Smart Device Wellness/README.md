# Smart Device Wellness Case Study
## Last updated: 11/10/22

The purpose of this case study is to gain insight on any patterns based on recorded sleep patterns and physical activity of recorded participants.
Please note that the data used is based on data collected from 30 participants within a month.

Dataset used:
* [Fitbit Fitness Tracker Data Kaggle Dataset (CC0 Public Domain) by MÖBIUS](https://www.kaggle.com/datasets/arashnic/fitbit)

Tables used:
* dailyActivity_merged.csv
* sleepDay_merged.csv
* heartrate_seconds_merged.csv

## Steps Taken:
### 1. Working with the data in Sheets
Upon importing the tables I wanted to used, I filtered each of the columns in the dataset to see if there were any stray/invalid values. Fortunately, not much
was found and was quickly ready to move on to the next step after trimming a couple of rows of whitespaces.

Since I planed on using BigQuery for merging the tables in SQL, I also decided to reformat the Date column in both tables from MM/DD/YYYY into DD-Month-YYYY as 
I feel BigQuery reads the latter format more efficiently.

### 2. Importing/Combining the data in BigQuery
I've decided to use the follow query to make the merged table
![query](https://user-images.githubusercontent.com/33902649/201213455-8136dd41-e6b1-4c0f-8f7f-5faedf7d8473.png)

As both tables include a date and id, I chose to left join them together based on those two columns. 
Left join was ideal in this case as not every user might have sleep records for every date. As such, I had to find a way to replace those null values that will show up.

The way I did it was using `IFNULL` to replace any null values with default numeric values.

The three columns that should be considered for null values are *TotalSleepRecords, TotalMinutesAsleep, and TotalTimeInBed*
* The first column's default can be set to 0 to represent nothing logged from a user on a particular day 
* The second column's default is based on an assumption that the average adult sleeps for 8 hours a day (hench 8 * 60 = 480 minutes)
* TotalTimeInBed's default is based on the time it takes to fall asleep on your bed according to [this source:](https://www.sleepfoundation.org/sleep-faqs/how-long-should-it-take-to-fall-asleep) 
The source recalls that it should take a maximum for an average adult to fall asleep after going to bed, so 480+20 = 500 minutes

After taking everything into consideration, the merged table is ready to be extracted into Tableau for visualization.

#### You can see my findings in greater detail in the Case study pdf included. 

## Main findings:
* People tend to sleep more in the middle of the week than in the beginning or the end.
* The total amount of sleep and bed from users is on a slight decline
* The day of the week is not a strong indicator on the amount of steps walked by users.
* Total time spent on physical activity step count, and calories burnt are possibly on a decline as well.

Thanks for reading!
