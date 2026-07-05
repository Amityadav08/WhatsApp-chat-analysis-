import pandas as pd
import re

def preprocess(data,data_is_12_24):
    if data_is_12_24==False:
        pattern='\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s'
        messages=re.split(pattern,data)[1:]
        dates=re.findall(pattern,data)
        df=pd.DataFrame({'user_message':messages,'message_date':dates})
        df['message_date']=pd.to_datetime(df['message_date'],format='%d/%m/%Y, %H:%M - ')
        

    else:
        pattern_pm='\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2}\spm\s-\s'
        pattern_am='\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2}\sam\s-\s'
        messages_pm=re.split(pattern_pm,data)[1:]
        messages_am=re.split(pattern_am,data)[1:]
        dates_pm=re.findall(pattern_pm,data)
        dates_am=re.findall(pattern_am,data)
        df_pm=pd.DataFrame({'user_message':messages_pm,'message_date':dates_pm})
        df_am=pd.DataFrame({'user_message':messages_am,'message_date':dates_am})
        df=pd.concat([df_am,df_pm],ignore_index=True)
        df['message_date']=df['message_date'].apply(lambda x: x[:-3])
        df['message_date']=pd.to_datetime(df['message_date'],format='mixed',dayfirst=True)
        df=df.sort_values('message_date').reset_index(drop=True)
        

    users=[]
    messages=[]
    for message in df['user_message']:
        entry=re.split('([\w\W]+?):\s',message)
        if entry[1:]:# user name
            users.append(entry[1])
            messages.append(entry[2])
        else:
            users.append('group_notification')
            messages.append(entry[0])


     
    df.rename(columns={'message_date':'date'},inplace=True)        
    df['user']=users
    df['message']=messages
    df.drop(columns=['user_message'],inplace=True)

    df['only_date']=df['date'].dt.date
    df['year']=df['date'].dt.year
    df['month_num']=df['date'].dt.month
    df['month']=df['date'].dt.month_name()
    df['day']=df['date'].dt.day

    df['day_name']=df['date'].dt.day_name()
    df['hour']=df['date'].dt.hour
    df['minute']=df['date'].dt.minute


    period = []
    for hour in df[['day_name', 'hour']]['hour']:
        if hour == 23:
            period.append(str(hour) + "-" + str('00'))
        elif hour == 0:
            period.append(str('00') + "-" + str(hour + 1))
        else:
            period.append(str(hour) + "-" + str(hour + 1))

    df['period'] = period

    return df
