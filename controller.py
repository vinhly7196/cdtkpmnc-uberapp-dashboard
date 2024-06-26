import unicodedata
import requests
import json 
import pandas as pd
import streamlit as st
from citys import citys_list


BANG_XOA_DAU = str.maketrans(
    "ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴáàảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ",
    "A"*17 + "D" + "E"*11 + "I"*5 + "O"*17 + "U"*11 + "Y"*5 + "a"*17 + "d" + "e"*11 + "i"*5 + "o"*17 + "u"*11 + "y"*5
)

def xoa_dau(txt: str) -> str:
    if not unicodedata.is_normalized("NFC", txt):
        txt = unicodedata.normalize("NFC", txt)
    return txt.translate(BANG_XOA_DAU)


def get_data(api_link): 
    # get api trip
    res = requests.get(api_link)
    response = json.loads(res.text)
    jsondict = json.dumps(response)
    df =  pd.read_json(jsondict, orient='records')
    return df 

def formatter(x, pos):
    return str(round(x / 1e6, 1))

@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8-sig')


def add_city_col(row):
    address = [xoa_dau(x.strip()) for x in row.pickup['address'].split(',')]
    print(address)
    for item in citys_list:
        if xoa_dau(item["city"]) in address:
            return item["city"]
    return "_"