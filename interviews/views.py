# -*- coding: utf-8 -*-
#import torch
#from kobart import get_kobart_tokenizer
#from transformers.models.bart import BartForConditionalGeneration
import plistlib
from .forms import ClientForm
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .models import Interviews, Client, Manager, CodeShare, Purchase
from .clova_speech import ClovaSpeechClient
from .clova_sentimental import ClovaSentimental
from .clova_summary import ClovaSummary
from .enc_dec import enc, dec, dict_to_binary, binary_to_dict
from .vito_lib import vito_auto_process, create_presigned_url

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import shutil
import win32com.client as win32  # win32com.client
from openpyxl import Workbook

import pythoncom  # 추가)Q
from wordcloud import WordCloud
import matplotlib.pyplot as plt

import time
from datetime import datetime, date, timedelta

import requests
import json
import random
import re

from collections import Counter
from konlpy.tag import Okt
#from konlpy.tag import Hannanum

import os
import environ   # pip install django-environ

from pathlib import Path

from nltk.tokenize import word_tokenize
import string
from django.http.response import JsonResponse

#from mutagen import mp3, mp4, wave, ac3, flac, aac, ogg, oggflac, oggvorbis
#from tinytag import TinyTag
import subprocess
#import ffprobe
#import FFProbe
import math
import copy

import pytextrank   # pip install pytextrank
import spacy        # spacy download en_core_web_sm
from django.utils.translation import gettext_lazy as _

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

import base64
from docx import Document  # pip install python-docx
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.table import Table

import telegram # pip install python-telegram-bot

import boto3  # pip install boto3==1.6.19
# python-dateutil 2.6.1  => 2.8.1

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, HashingVectorizer
import numpy as np
import pandas as pd
from django.core.files.storage import FileSystemStorage
import distance
from rank_bm25 import BM25Okapi, BM25Plus
from scipy.spatial.distance import correlation

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = os.path.join(BASE_DIR, '_media')

cyp_key = bytes([0x82, 0xC8, 0xA9, 0xC3, 0xD2, 0xE1, 0xF0, 0x3F, 0x28, 0x2d, 0x3c, 0x4b, 0x5a, 0x69, 0x78, 0x87])
aad = bytes([0x38, 0xA6, 0xB7, 0x08, 0xC9, 0xDA, 0x91, 0x82, 0x73, 0x64, 0x5B, 0x4C, 0x3D, 0x2E])
nonce = bytes([0xF6, 0xE7, 0xD8, 0xC9, 0xB1, 0xA2, 0x93, 0x84, 0x75,  0x6A, 0x5B, 0x5C])  # 기본 12(96bit)byte이며 길이 변경 가능.

def evalDoc(request):
    efile = request.FILES['evalFile']
    evalMethod = request.POST.get("evalMethod")
    docu = request.POST.get("docu")

    rstr = ''
    #with open(efile, 'rb') as sent_file:
    rdata = efile.read().decode('utf8')  #read
    for data in rdata:
        if(data!="\n"):        
            rstr = rstr + data

    score = similarity(request, evalMethod, docu, rstr)*100
    #intv = Interviews.objects.get(id=docu)
    #fs = FileSystemStorage()
    #filename = fs.save("파일명.csv", efile)
    return HttpResponse(f"{score:.2f}")

def cos_similarity(v1, v2):
    dot_product = v1 @ v2
    ab_norm = np.sqrt(sum(np.square(v1))) * np.sqrt(sum(np.square(v2)))
    similarity = dot_product / ab_norm
    
    return similarity

def jaccard_similarity(list1, list2):
    s1 = set(list1)
    s2 = set(list2)
    return float(len(s1.intersection(s2)) / len(s1.union(s2)))


def similarity(request, method, sid, label):
    doc_list = []
    intv = Interviews.objects.get(id=sid)
    with open(intv.content, 'rb') as sent_file:
        rdata = sent_file.read()
        sent_data = dec(cyp_key, aad, nonce, rdata, intv.gd_cmk)
    sent_data = binary_to_dict(sent_data)
    
    if intv.stt_engine=='naver':
        #sdata = sent_data['text'].replace('\r',' ')
        sdata = sent_data['text']
        doc_list.append(sdata)
    elif intv.stt_engine=='vito':
        tstr = ''
        for st in sent_data:
            tstr = tstr + st['msg'] + ' '
        #tstr = tstr.replace('\r',' ')
        doc_list.append(tstr)

    label = label.replace('\r',' ')
    doc_list.append(label)

    if method == 'tfidf' or method == 'count' or method == 'jaccard':
        if method == 'tfidf':
            tfidf_vect = TfidfVectorizer()
        elif method == 'count':
            tfidf_vect = CountVectorizer()  # 유사도 측정 방법 카운트 벡터 활용
        elif method == 'jaccard':
            tfidf_vect = TfidfVectorizer() #HashingVectorizer()
        feature_vect = tfidf_vect.fit_transform(doc_list)
        # Sparse Matrix형태를 Dense Matrix로 변환
        feature_vect_dense = feature_vect.todense() # toarray()도 가능

        # 첫 번째, 두 번째 문서 피처 벡터 추출
        vect1 = np.array(feature_vect_dense[0]).reshape(-1,)
        vect2 = np.array(feature_vect_dense[1]).reshape(-1,)
        #print(f"\nSTT 처리문서 feacture vector:\n {vect1}\n")
        #print(f"Label 문서(정답지) feacture vector:\n {vect2}")    
        
        if method == 'jaccard':
            similarity_simple = jaccard_similarity(doc_list[0], doc_list[1])
        else:   # 코사인 유사도 
            similarity_simple = cos_similarity(vect1, vect2 )           
    elif method == 'bm25':
        
        ltokenize = [doc_list[0].split(" ")]
        qtokenize = doc_list[1].split(" ")
        qtokenize = query.split(" ")
        ltokenize.append(qtokenize)

        print(f"ltokenNize\n {ltokenize}")        
        print(f"QtokenNize\n {qtokenize}")
        bm25_vect = BM25Okapi(ltokenize)
        bm25_result = bm25_vect.get_scores(qtokenize)
        print(f"Bm25=> {bm25_result}")
        similarity_simple = bm25_result[0]


    elif method == 'bm25plus':
        '''
        corpus = [
            "세계 배달 피자 리더 도미노피자가 우리 고구마를 활용한 신메뉴를 출시한다.도미노피자는 오는 2월 1일 국내산 고구마와 4가지 치즈가 어우러진 신메뉴 `우리 고구마 피자`를 출시하고 전 매장에서 판매를 시작한다. 이번에 도미노피자가 내놓은 신메뉴 `우리 고구마 피자`는 까다롭게 엄선한 국내산 고구마를 무스와 큐브 형태로 듬뿍 올리고, 모차렐라, 카망베르, 체더 치즈와 리코타 치즈 소스 등 4가지 치즈와 와규 크럼블을 더한 프리미엄 고구마 피자다.",
            "피자의 발상지이자 원조라고 할 수 있는 남부의 나폴리식 피자(Pizza Napolitana)는 재료 본연의 맛에 집중하여 뛰어난 식감을 자랑한다. 대표적인 나폴리 피자로는 피자 마리나라(Pizza Marinara)와 피자 마르게리타(Pizza Margherita)가 있다.",
            "도미노피자가 삼일절을 맞아 '방문포장 1+1' 이벤트를 진행한다. 이번 이벤트는 도미노피자 102개 매장에서 3월 1일 단 하루 동안 방문포장 온라인, 오프라인 주문 시 피자 1판을 더 증정하는 이벤트다. 온라인 주문 시 장바구니에 2판을 담은 후 할인 적용이 가능하며, 동일 가격 또는 낮은 가격의 피자를 고객이 선택하면 무료로 증정한다."
        ]   
        query = "도미노피자 신메뉴"

        ltokenize = [doc.split(" ") for doc in corpus]     
        qtokenize = query.split(" ")
        '''

        ltokenize = [doc_list[1].split(" ")]
        qtokenize = doc_list[0].split(" ")

        bm25_vect = BM25Plus(ltokenize)
        bm25_result = bm25_vect.get_scores(qtokenize)        
        print(f"Bm25Plus=> {bm25_result}")
        similarity_simple = bm25_result[0]
 
    '''
    if method == 'tfidf':
        similarity_simple = cos_similarity(vect1, vect2 )
    elif method == 'hamming':
        similarity_simple = float(distance.hamming(vect1, vect2)/1000)        
    elif method == 'jaccard':
        similarity_simple = distance.jaccard(vect1, vect2)
    '''
    #print(f"\nSTT 처리문서와 Label 문서 {method} 유사도: {similarity_simple:.3f}\n")
    print(f"\nSTT 처리문서와 Label 문서 {method} 유사도: {similarity_simple}\n")
    return similarity_simple
    '''
    return render(
        request,
        'interviews/interviews_realtime.html',
    )      
    '''

def RealtimeInterviews(request):
    return render(
        request,
        'interviews/interviews_realtime.html',
    )  

def RealtimeSave(request):
    current_user = request.user
    if not current_user.is_authenticated:
        return redirect('/interviews/')

    try:
        pauthor = Manager.objects.get(mid=current_user)
    except ObjectDoesNotExist:
        pauthor = Manager.objects.create(mid=current_user, use_time=0, max_time=300)   # 300 minutes   millisec * 60000


    if request.method == "POST":

        all_sentence = request.POST.get("all_sentence")
        all_sentence = json.loads(all_sentence)
        quiet_basis = 0#request.POST.get("quiet_basis")
        title = request.POST.get("title")

        context = RealtimeAnalysis(all_sentence, title, current_user, pauthor)

        #print(f"sentenceUpdate::{all_sentence[0]['speaker']}:{all_sentence[0]['sentence']}")
        #return HttpResponse("{{intv.pk}}")    
        return JsonResponse(context)

def RealtimeAnalysis(all_sentence, title, current_user, pauthor):
    gen_idx = -1
    gen_sentences = []
    context = {'result':'', 'msg':''}
    print(f"All::{all_sentence}")
    #all_sentence = json.loads(all_sentence)
    #print(all_sentence)

    stn_no_speaker = {}
    prev_speaker = 'superman'
    context={'result':'','msg':''}

    speakers = [{"label": "0", "name": "A", "edited": "false"}, {"label": "1", "name": "B", "edited": "false"},{"label": "2", "name": "C", "edited": "false"}]
    group_sent = []
    sentimental = dict()
    group_idx = 0

    for si in range(len(speakers)):
        stn_no_speaker[speakers[si]["label"]] = 0

    i = 0
    for sent in all_sentence:

        if sent['generated'] == 'false':
            gen_idx = gen_idx + 1

        fspk = sent['speaker']

        x = time.strptime(sent['start_time'],'%H:%M:%S')
        start_time = timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds() * 1000        

        end_time = start_time
        #gen_sentences[i]['sentence'] = sent['sentence']
        #gen_sentences[i]['speaker'] = fspk
        sindex = next((index for (index, d) in enumerate(speakers) if d["label"] == fspk), None)

        #print(f"Sindex:{sindex}, fspk:{fspk}, i:{i}, gen_sentence:{gen_sentences[i]}")    
        #gen_sentences[i]['name'] = speakers[sindex]['name']

        gen_sentences.append({"speaker": fspk, "name": speakers[sindex]['name'], "sentence": sent['sentence'], "first_sentence": "true",
                        "quiet_time": 0, "start": start_time, "end": end_time, "senti": "None", "sent_no": 0, "confidence": 0})

        if i!=0:
            gen_sentences[i]["end"]= gen_sentences[i-1]["end"] 

        speaker = gen_sentences[i]['speaker']

        stn_no_speaker[speaker] = stn_no_speaker[speaker] + 1

        gen_sentences[i]["sent_no"] = stn_no_speaker[speaker]

        if i != 0:
            gen_sentences[i]["quiet_time"] = round((gen_sentences[i]["start"] - gen_sentences[i-1]["end"])/1000)
        else:
            gen_sentences[i]["quiet_time"] = 0

        i = i + 1
    
    gen_sentences[-1]['end'] = gen_sentences[-1]['start'] + 1000*len(gen_sentences[-1]["sentence"])//10

    intv_duration = math.ceil(gen_sentences[-1]['end']/60000)

    try:
        gs_cyp, gs_mac = enc(cyp_key, aad, nonce, dict_to_binary(gen_sentences))

    except Exception as e:
        print(f"SentenceUpdate Encryp Error::{e}")
        context['result'] ='fail'
        context['msg'] = "SentenceUpdate Encryp Error"
        #return HttpResponse("SentenceUpdate Encryp Error")
        return context

    try:
        timestr = datetime.now().strftime('\%Y\%m\%d')
        save_path = MEDIA_ROOT + f"\interviews\\files{timestr}\Realtime_{title}.faj"
        with open(save_path, 'wb') as outfile1:
            outfile1.write(gs_cyp)
    except Exception as e:
        print(f"SentenceUpdate Write Error::{e}")
        context['result'] ='fail'
        context['msg'] = "SentenceUpdate Write Error"            
        #return HttpResponse("SentenceUpdate Write Error")
        return context

    try:
        clt = Client.objects.get(name='고객미정', counselor=current_user)
    except ObjectDoesNotExist:
        clt = Client.objects.create(name='고객미정', counselor=current_user)

    speakers = json.dumps(speakers).replace(r"'false'", r'"false"').replace(r"'true'", r'"true"')

    intv = Interviews.objects.create(content_div=save_path, duration=intv_duration, client=clt, author=pauthor, \
        speakers=speakers, client_name='고객미정',gs_cmk=gs_mac, quiet_basis=0, title= title)        

    context['result'] ='pass'
    context['msg'] = f"{intv.pk}"    
    return context

def test_storage(request):

    env = environ.Env(
        # set casting, default value
        DEBUG=(bool, False)
    )        
    environ.Env.read_env(os.path.join(BASE_DIR, '.env'))        

    sec_key = env('STORE_SEC_KEY')
    acc_key = env('STORE_ACC_KEY') 

    s3 = boto3.client('s3', endpoint_url='https://kr.object.ncloudstorage.com', aws_access_key_id=acc_key,
                      aws_secret_access_key=sec_key)

    bucket_name = "fingerai-test"

    # upload file
    object_name = 'stopwords.txt'
    local_file_path = './interviews/stopwords_korean.txt'

    s3.upload_file(local_file_path, bucket_name, object_name)

    return render(
        request,
        'interviews/test_storage.html',
        {
            'sec_key' : sec_key,
            'acc_key' : acc_key
        }
    )  

def test_storage1(request):

    env = environ.Env(
        # set casting, default value
        DEBUG=(bool, False)
    )        
    environ.Env.read_env(os.path.join(BASE_DIR, '.env'))        

    sec_key = env('STORE_SEC_KEY')
    acc_key = env('STORE_ACC_KEY') 

    res = ClovaSpeechClient().req_object_storage(data_key='data/breed_9m_57s.mp3', completion='sync')
    #res = ClovaSpeechClient().req_upload(file=u'./_media/{}'.format(file_upload_name),
    #                                        completion='sync', diarization=diarize_set, stt_lang=stt_lang)
    print(f"ClovaRes:{res}")
    get_data = json.loads(res.text)
    print(f"Analysis:{get_data}")  

    return render(
        request,
        'interviews/test_storage.html',
        {
            'sec_key' : sec_key,
            'acc_key' : acc_key
        }
    )    

def dbupdate(request, msg):
    current_user = request.user
    if not (current_user.is_authenticated and (current_user.is_staff or current_user.is_superuser)):
        return redirect('/interviews/')

    interviews = Interviews.objects.all()

    if msg =='duration':
        for interview in interviews:
            try:
                interview.content = interview.content.replace('\0', '')
                get_data = json.loads(interview.content)
                seg_len = len(get_data['segments'])
                intv_duration = get_data['segments'][seg_len - 1]['end']
                intv_duration = math.ceil(intv_duration/60000)   # milisec to minutes
                Interviews.objects.filter(pk=interview.pk).update(duration=intv_duration)
            except Exception as e:
                print(f"DurationUpdateError:{e}")

    elif msg == 'speakers':
        for interview in interviews:
            speakers_out = ""
            gs_mac = ""
            gs_cyp = ""
            content_data = dict()
            try:
                with open(interview.content, 'rb') as sent_file:
                    rdata = sent_file.read()
                    content = dec(cyp_key, aad, nonce, rdata, interview.gd_cmk)
                    if content is None:
                        continue
                    if content == b'':
                        continue
            except Exception as e:
                print(f"Interview data FileOpen Error::")

            try:
                content_data = binary_to_dict(content)
                get_data = content_data['speakers']
                speakers_out = json.dumps(get_data).replace('false', r'"false"').replace('true', r'"true"')
            except Exception as e:
                print(f"Speaker UpdateError:")


            try:
                group_idx = 0
                content_div = []
                prev_speaker = 'SuperMan'
                stn_no_speaker = {}
                speakers_list = content_data["speakers"]
                seg_data = content_data["segments"]

                for i in range(len(speakers_list)):
                    stn_no_speaker[speakers_list[i]["label"]] = 0


                for i in range(len(seg_data)):
                    cur_text = seg_data[i]['text']
                    if cur_text == '':
                        continue

                    speaker = seg_data[i]['speaker']['label']
                    start_time = seg_data[i]['start']
                    end_time = seg_data[i]['end']

                    content_div.append({"speaker": speaker, "name": chr(ord(speaker) + 16), "sentence": cur_text,
                                       "first_sentence": "false",
                                       "quiet_time": 0, "start": start_time, "end": end_time, "senti": "None",
                                       "sent_no": 0})

                    if prev_speaker != speaker:
                        stn_no_speaker[speaker] = stn_no_speaker[speaker] + 1
                        prev_speaker = speaker
                        content_div[group_idx]["first_sentence"] = "true"

                    content_div[group_idx]["sent_no"] = stn_no_speaker[speaker]

                    if i != 0:
                        content_div[group_idx]["quiet_time"] = round((content_div[group_idx]["start"] - content_div[group_idx - 1]["end"]) / 1000)
                    else:
                        content_div[group_idx]["quiet_time"] = 0
                    group_idx = group_idx + 1
                    #print(f"Sent::{i} ")
                gs_cyp, gs_mac = enc(cyp_key, aad, nonce, dict_to_binary(content_div))
            except Exception as e:
                print(f"SpeakerUpdate Encryp Error::{e}")

            try:
                with open(interview.content_div, 'wb') as outfile2:
                    outfile2.write(gs_cyp)

            except Exception as e:
                print(f"SpeakerUpdat Write Error::{e}")

            Interviews.objects.filter(pk=interview.pk).update(speakers=speakers_out, gs_cmk=gs_mac)

    return redirect('/interviews/')

def load_model():
    bmodel = BartForConditionalGeneration.from_pretrained('interviews/kobart_summary')
    # tokenizer = get_kobart_tokenizer()
    return bmodel

def inaction(request):
    return render(
        request,
        'interviews/interviews_inaction.html',
    )

def addspeaker(request, pk):
    if request.method == "POST":
        new_speaker = request.POST.get("new_speaker")
        intv = Interviews.objects.get(pk=pk)
        speakers = intv.speakers

        #speakers = speakers.replace("'",'"')
        #print(f"Speaker append::{ speakers }")
        speakers = json.loads(speakers)

        speakers.append({"label":"","name":""})
        speakers[len(speakers)-1]["label"] = chr(ord('0')+len(speakers))
        speakers[len(speakers)-1]["name"] = new_speaker
        print(f"Speaker append0::{ speakers }")
        speakers = json.dumps(speakers)
        print(f"Speaker append1::{ speakers }")
        #speakers = speakers.replace("'",'"')
        #print(f"Speaker append2::{ speakers }")
        Interviews.objects.filter(pk=pk).update(speakers=speakers)
        return HttpResponse("Sentence Updated")

def sentenceUpdate(request, pk):
    current_user = request.user
    if not current_user.is_authenticated:
        return redirect('/interviews/')
    gen_idx = -1
    gen_sentences = []

    org_sent = dict()
    if request.method == "POST":
        intv = Interviews.objects.get(pk=pk)

        speakers = intv.speakers
        speakers = json.loads(speakers)

        all_sentence = request.POST.get("all_sentence")
        quiet_basis = request.POST.get("quiet_basis")
        title = request.POST.get("title")

        #intv_sentences = json.loads(intv.content_div)
        with open(intv.content_div, 'rb') as sent_file:
            rdata = sent_file.read()
            sent_data = dec(cyp_key, aad, nonce, rdata, intv.gs_cmk)

        intv_sentences = binary_to_dict(sent_data)

        all_sentence = json.loads(all_sentence)

        stn_no_speaker = {}
        prev_speaker = 'superman'
        for si in range(len(speakers)):
            stn_no_speaker[speakers[si]["label"]] = 0

        i = 0
        for sent in all_sentence:

            if sent['generated'] == 'false':
                gen_idx = gen_idx + 1

            fspk = sent['speaker']

            gen_sentences.append({})
            gen_sentences[i] = copy.deepcopy(intv_sentences[gen_idx])
            gen_sentences[i]['sentence'] = sent['sentence']

            gen_sentences[i]['speaker'] = fspk
            sindex = next((index for (index, d) in enumerate(speakers) if d["label"] == fspk), None)

            gen_sentences[i]['name'] = speakers[sindex]['name']

            speaker = gen_sentences[i]['speaker']
            if prev_speaker != speaker:
                stn_no_speaker[speaker] = stn_no_speaker[speaker] + 1
                prev_speaker = speaker
                gen_sentences[i]['first_sentence'] = "true"
            else :
                gen_sentences[i]['first_sentence'] = "false"

            gen_sentences[i]["sent_no"] = stn_no_speaker[speaker]

            i = i + 1

        try:
            gs_cyp, gs_mac = enc(cyp_key, aad, nonce, dict_to_binary(gen_sentences))

        except Exception as e:
            print(f"SentenceUpdate Encryp Error::{e}")
            return HttpResponse("SentenceUpdate Encryp Error")

        try:
            with open(intv.content_div, 'wb') as outfile1:
                outfile1.write(gs_cyp)
        except Exception as e:
            print(f"SentenceUpdate Write Error::{e}")
            return HttpResponse("SentenceUpdate Write Error")

        Interviews.objects.filter(pk=pk).update(gs_cmk=gs_mac, quiet_basis= quiet_basis, title= title)
        return HttpResponse("Sentence Updated")

def sentimental(request, pk):
    interviews = Interviews.objects.get(pk=pk)

    with open(interviews.sentimental, 'rb') as sent_file:
        rdata = sent_file.read()
        sent_data = dec(cyp_key, aad, nonce, rdata, interviews.sm_cmk)
    #sent_data = binary_to_dict(sent_data)
    sentimental = sent_data.decode("utf-8")

    res = Manager.objects.filter(mid=request.user).get()
    return render(
        request,
        'interviews/interviews_anal.html',
        {
            'interviews': interviews,
            'clients_list': Client.objects.filter(counselor=request.user),
            'client_unknown': Interviews.objects.filter(client_name='', author=res),
            'client_info': interviews.client,
            'manager': res,
            'sentimental': sentimental,
        }
    )

def wordcloud(request, pk):
    interviews = Interviews.objects.get(pk=pk)

    with open(interviews.sentimental, 'rb') as sent_file:
        rdata = sent_file.read()
        sent_data = dec(cyp_key, aad, nonce, rdata, interviews.sm_cmk)
    #sent_data = binary_to_dict(sent_data)
    sentimental = sent_data.decode("utf-8")

    res = Manager.objects.filter(mid=request.user).get()
    return render(
        request,
        'interviews/interviews_wordcloud.html',
        {
            'interviews': interviews,
            'clients_list': Client.objects.filter(counselor=request.user),
            'client_unknown': Interviews.objects.filter(client_name='', author=res),
            'client_info': interviews.client,
            'manager': res,
            'sentimental': sentimental,
        }
    )

def ExceptRedirect(request, msg):
    res = Manager.objects.filter(mid=request.user).get()
    return render(
        request,
        'interviews/interviews_clientlist.html',
        {
            'interviews_list': Interviews.objects.filter(author=res),
            #'clients_list': Client.objects.exclude(name='고객미정'),
            'clients_list': Client.objects.filter(counselor=request.user),
            'client_unknown': Interviews.objects.filter(client_name='고객미정',author=res).order_by('-created_at'),
            'manager': res,
            'pw_result': msg
        }
    )

def document(request, pk):
    interviews = Interviews.objects.get(pk=pk)
    if request.method == 'POST':
        ccomment = request.POST['comment'].strip()
        Client.objects.filter(name=interviews.client_name, counselor=request.user).update(comment=ccomment)
        return redirect(f'/interviews/document/{pk}/')
    else:
        res = Manager.objects.filter(mid=request.user).get()
        return render(
            request,
            'interviews/interviews_document.html',
            {
                'interviews': interviews,
                'clients_list': Client.objects.filter(counselor=request.user),
                'client_unknown': Interviews.objects.filter(client_name='', author=res),
                'client_info': interviews.client,
                'manager': res,
            }
        )

def delete(request, interview_pk):
    #intv = Interviews.objects.get(pk=interview_pk)
    intv = Interviews.objects.filter(pk=interview_pk).update(delete_flag="true")
    #intv.delete()
    return redirect('/interviews')


# First connect
def start(request):
    cuser = request.user
    if cuser.is_authenticated:
        try:
            res = Manager.objects.get(mid=request.user)
        except ObjectDoesNotExist:
            #res = Manager.objects.create(mid=request.user, use_time=0, max_time=300)   # 300 minutes
            res = Manager.objects.create(mid=request.user, use_time=0, max_time=0, paid_time=60)  # 300 minutes

        if date.today() >= res.expire_at:
            Manager.objects.filter(mid=request.user).update(use_time=0, max_time=0)
    return redirect('/interviews/list/norm')



#internal access
def start_interviews(request):
    return redirect('/interviews/list/norm')

def clientlist(request, msg):

    if request.method == "POST":
        cuser = request.user
        if not cuser.is_authenticated:
            return redirect("/interviews")

        audio_file = request.FILES.get("file_upload")
        title = request.POST.get("title")
        nums_speaker = request.POST.get("nums_speaker")
        client_name = request.POST.get("client_name")
        stt_lang = request.POST.get("stt_lang")
        stt_engine = request.POST.get("stt_engine")

        if not title:
            title = "대화녹음_"+datetime.now().strftime('%Y%m%d-%H-%M-%S')

        intv = Interviews.objects.create(title=title, file_upload=audio_file)

        intv.save()

        if client_name == '':
            client_name = '고객미정'

        try:
            clt = Client.objects.filter(name=client_name, counselor=cuser).get()
        except ObjectDoesNotExist:
            clt = Client.objects.create(name='고객미정', counselor=cuser)

        speaker_nums= nums_speaker #2
        ret, pauthor, get_data, group_sent, timestr, sentimental, intv_duration, speakers, all_confidence = InterviewAnalysis(cuser, speaker_nums, intv.file_upload.name, stt_lang, stt_engine)

        if ret == -1:
            print(f'Return Fail')
            return redirect('/interviews/list/recfail')
        elif ret == -2:
            print(f'Time Shortage')
            return redirect('/interviews/list/notime')

        wstr = intv.file_upload.path
        tpath = wstr[0:wstr.rfind('\\')+1]    # last index

        gdpath = tpath + "STT_data_" + timestr + ".faj"
        gspath = tpath + "Spker_data_" + timestr + ".faj"
        smpath = tpath + "Senti_data_" + timestr + ".faj"

        try:
            gd_cyp, gd_mac = enc(cyp_key, aad, nonce, dict_to_binary(get_data))
            gs_cyp, gs_mac = enc(cyp_key, aad, nonce, dict_to_binary(group_sent))
            sm_cyp, sm_mac = enc(cyp_key, aad, nonce, dict_to_binary(sentimental))
        except Exception as e:
            print(f"Cypher Error Message::{e}")

        try:
            with open(gdpath, 'wb') as outfile:
                outfile.write(gd_cyp)
            with open(gspath, 'wb') as outfile1:
                outfile1.write(gs_cyp)
            with open(smpath, 'wb') as outfile2:
                outfile2.write(sm_cyp)

        except Exception as e:
            print(f"JSON File Gen Error Message::{e}")

        get_data = gdpath
        group_sent = gspath
        sentimental = smpath
        speakers = json.dumps(speakers, ensure_ascii=False)

        Interviews.objects.filter(pk=intv.pk).update(content=get_data, content_div=group_sent,
                                  sentimental=sentimental, client_name=client_name, confidence=all_confidence,
                                  client=clt, author=pauthor, duration=intv_duration, gd_cmk=gd_mac, gs_cmk=gs_mac, sm_cmk=sm_mac, speakers=speakers)

        #print(f'Record Interview Created:{intv.pk}: duration:{intv.duration}')

        #messages.success(request, "Audio recording successfully added!")
        return redirect('/interviews')

    elif request.method == "GET":
        current_user = request.user
        if not current_user.is_authenticated:
            return render(
                request,
                'interviews/interviews_clientlist.html',
                {
                    'pw_result': 'none'
                }
            )

        try:
            res = Manager.objects.filter(mid=request.user).get()
        except ObjectDoesNotExist:
            res = Manager.objects.create(mid=request.user, use_time=0, max_time=300)   # 300 minutes

        env = environ.Env(
            # set casting, default value
            DEBUG=(bool, False)
        )        
        environ.Env.read_env(os.path.join(BASE_DIR, '.env'))        

        sec_key = env('STORE_SEC_KEY')
        acc_key = env('STORE_ACC_KEY') 

        return render(
            request,
            'interviews/interviews_clientlist.html',
            {
                'interviews_list': Interviews.objects.filter(author=res),
                'clients_list': Client.objects.filter(counselor=request.user),
                'client_unknown': Interviews.objects.filter(client_name='고객미정', author=res).order_by('-created_at'),
                'manager': res,
                'pw_result': msg,
                'sec_key': sec_key,
                'acc_key':acc_key
            }
        )

def client_delete(request, pk):
    clt = Client.objects.get(pk=pk)
    ilist = Interviews.objects.filter(client=None)
    clt.delete()
    #print("Client Delete")
    #print(ilist)
    for itv in ilist:
        Interviews.objects.filter(pk=itv.pk).update(client_name='')
    return redirect('/interviews')

def client_pwcheck(request,pk):
    client = Client.objects.get(pk=pk)
    res = Manager.objects.filter(mid=request.user).get()
    if request.method == 'POST':
        print("Client Password Check")
        cpwd = request.POST['password']
        if client.password == cpwd:
            return redirect(f'/interviews/client/{pk}/')
        else:
            #return redirect(f'/interviews/')
            return render(
                request,
                'interviews/interviews_clientlist.html',
                {
                    'interviews_list': Interviews.objects.filter(author=res),   #Interviews.objects.all(),
                    # 'clients_list': Client.objects.exclude(name='고객미정'),
                    'clients_list': Client.objects.filter(counselor=request.user),
                    'client_unknown': Interviews.objects.filter(client_name='고객미정', author=res),
                    'pw_result' : 'fail'
                }
            )
    else:
        return render(
            request,
            'interviews/client_pwcheck.html',
            {
                'client': client
            }
        )

def client_modify(request, pk):
    if request.method == 'POST':

        #print("Client Modify")

        cname = request.POST['name']
        cmail = request.POST['mail']
        cphone = request.POST['phone']
        ccomment = request.POST['comment']#.strip()
        cpw = request.POST['password']
        #print(f"ClientModify::{ccomment}")

        clt = Client.objects.filter(pk=pk).update(name=cname, mail=cmail, phone=cphone, comment=ccomment, password=cpw)
        return redirect(f'/interviews/client/modify/{pk}')

    else:
        client = Client.objects.get(pk=pk)
        try:
            res = Manager.objects.filter(mid=request.user).get()
        except ObjectDoesNotExist:
            res = Manager.objects.create(mid=request.user, use_time=0, max_time=300)
        #print(client)
        #print(client.password)
        return render(
            request,
            'interviews/interviews_clientmodify.html',
            {
                'client': client,
                'manager': res,
            }
        )

def client_page(request, pk):
    if request.method == 'POST':
        ccomment = request.POST['client_comment'].strip()
            #clt = Client.objects.filter(pk=form.cleaned_data['pk']).update(comment=ccomment)
        Client.objects.filter(pk=pk).update(comment=ccomment)
        #print(f"Client_Page")
        return redirect(f'/interviews/client/{pk}/')
    else:
        '''
        if pk==0 :
            print("Client none List")
            client_interviews = Interviews.objects.filter(client=None)
            cinfo = Client.objects.get(name='고객미정')
        else :
        '''
        try:
            res = Manager.objects.filter(mid=request.user).get()
        except ObjectDoesNotExist:
            res = Manager.objects.create(mid=request.user, use_time=0, max_time=300)

        client_interviews = Interviews.objects.filter(client=pk, author=res).order_by('-created_at')
        cinfo = Client.objects.get(pk=pk)

        return render(
            request,
            'interviews/interviews_clientpage.html',
            {
                'client_interviews': client_interviews,
                'client_info': cinfo,
                'manager' : res,
            }
        )

def purchase_ownlist(request):
    mgr = Manager.objects.get(mid=request.user)
    if request.method == 'POST':

        if request.user.is_superuser:
            max_time = mgr.max_time
            paid_time = mgr.paid_time
            expire_at = mgr.expire_at

            coupon = request.POST['coupon_code']

            try:
                pur = Purchase.objects.get(code=coupon)
            except ObjectDoesNotExist:
                return redirect('/interviews/purchase/regist/none/')
            
            user_list = json.loads(pur.user_list)
            user_count = pur.user_count
            used_count = pur.used_count
            usable = pur.usable

            if usable != 'true':
                return redirect('/interviews/purchase/regist/notapproved/')

            if request.user.username in user_list:
                return redirect('/interviews/purchase/regist/already/')

            if date.today() > pur.expire_at:
                return redirect('/interviews/purchase/regist/expired/')

            if used_count >= user_count:
                return redirect('/interviews/purchase/regist/overcount/')

            if pur.type == 'months':
                max_time = pur.amount * pur.coupon_count
                expire_at = date.today() + timedelta(days=31)
            elif pur.type == 'hours':
                paid_time = paid_time + (pur.amount * pur.coupon_count)

            #user_list += request.user.username
            user_list.append(request.user.username)
            used_count += 1

            Manager.objects.filter(mid=request.user).update(max_time= max_time, paid_time= paid_time, expire_at= expire_at)
            Purchase.objects.filter(code=coupon).update(user_list=json.dumps(user_list, ensure_ascii=False), used_count=used_count, usable=usable)

            return redirect('/interviews/purchase/regist/success/')            
        
        coupon = request.POST.get('cancel_coupon')
        reason = request.POST.get('cancel_reason')
        #reason = "고객변심"
        purchase = Purchase.objects.get(code=coupon)
        pkey =  purchase.paymentKey #request.POST.get['paymentKey']
        owner = User.objects.get(pk=purchase.owner_id)
        cancel_amount = 0
        msg = ''

        if purchase.amount == 60:
            cancel_amount = 5500 * purchase.coupon_count
            msg += '취소 - [1시간권]'
        elif purchase.amount == 240:
            cancel_amount = 4*4950 * purchase.coupon_count
            msg += '취소 - [4시간권]'
        elif purchase.amount == 600:
            cancel_amount = 10*4400 * purchase.coupon_count
            msg += '취소 - [10시간권]'
        elif purchase.amount == 1:
            cancel_amount =  100 * purchase.coupon_count
            msg += '취소 - [1분권]' 
        
        msg += f", {cancel_amount}원, {owner.username}"
        
        env = environ.Env(
            # set casting, default value
            DEBUG=(bool, False)
        )        
        environ.Env.read_env(os.path.join(BASE_DIR, '.env'))        
        #skey = f"{env('SECRET_KEY')}:"
        sec_key = env('SECRET_KEY')
        #print(f"Secret from environ: {skey}")
        sec_key = f"{sec_key}:"
        sec_key = sec_key.encode("utf-8")
        sec_key = base64.b64encode(sec_key).decode("utf-8")
        secret_key =f"Basic {sec_key}"

        invoke_url = 'https://api.tosspayments.com/v1/payments/'
        # length_of_string = 8
        # rstr=''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length_of_string))
        request_body = {
            'cancelReason': reason,
            'cancelAmount' : cancel_amount,
        }

        headers = {
            #'Authorization': 'Basic dGVzdF9za19CRTkyTEFhNVBWYkoxUjZiWkRXVjdZbXBYeUpqOg==',
            #'Authorization': 'Basic bGl2ZV9za19MQmE1UHpSMEFybnc0RGFNWDF2OHZtWW5OZURNOg==',
            'Authorization': secret_key,
            'Content-Type': 'application/json;UTF-8',
        }

        try:
            res= requests.post(headers=headers,
                                 url=invoke_url + pkey +'/cancel',
                                 data=json.dumps(request_body).encode('UTF-8'))

            pay_data = res.json() #json.loads(res)
            #print(f"Cancel Response::: {pay_data}")
        except Exception as e:
            print(f"Cancel Ack Error::{e}")
            return redirect('/interviews/purchase/request')
        
        if 'totalAmount' not in pay_data:
            #print(f"{pay_data['code']}")
            return redirect('/interviews/purchase/request')

        '''
        cancel_list = Purchase.objects.filter(paymentKey=pkey)

        cancel_amount = 0
        for purch in cancel_list:
            cancel_amount = cancel_amount + purch.amount*purch.coupon_count
        '''

        #Purchase.objects.filter(paymentKey=pkey).update(usable='cancel')
        bot = telegram.Bot(token='1631327665:AAEX8hykT_WuTjQXWYnxigN1jM1WBqHAip4')
        bot.sendMessage(chat_id=-1001681320740, text=msg)

        purchase.usable = 'cancel'
        purchase.save()
        #mgr.paid_time = mgr.paid_time-cancel_amount
        mgr.paid_time = mgr.paid_time-purchase.amount
        mgr.save()

        pidx = len(pay_data['cancels'])
        return render(
            request,
            'interviews/paysuccess.html',
            {
                #'orderName': pay_data.orderName,
                'orderAmount': pay_data['cancels'][pidx-1]['cancelAmount'],                
                'addTime' : purchase.amount,
                'message' : 'cancel',
                'manager' : mgr,
            }
        )

    else:
        ownlist = Purchase.objects.filter(owner=request.user).exclude(paymentKey="")
        #mgr = Manager.objects.get(mid=request.user)
        return render(
            request,
            'interviews/purchase_ownlist.html',
            {
                'ownlist': ownlist,
                'manager': mgr,
            }
        )

def purchase_codeApprove(request):
    if request.method == "POST":
        code = request.POST.get("purchase_code")
        Purchase.objects.filter(code=code).update(usable='true')
        return HttpResponse("Code Approved!!")

def purchase_request(request):
    if request.method == "POST":
        purchase_list = request.POST.get("purchase_list")
        purchase_list = json.loads(purchase_list)
        total_price = request.POST.get("total_price")
        orderID = request.POST.get("orderID")
        buyWhere = request.POST.get("buyWhere")
        #print(f'Purchase received:::{purchase_list}')
        for i in range(len(purchase_list)):
            owner = request.user
            type = 'hours'
            amount = purchase_list[i]['amount']
            code = gen_purchaseCode()
            #expire_at = date.today() + timedelta(days=1825)  # 5 year
            expire_at = datetime.now() + timedelta(days=365)  # 5 year
            #expire_at = expire_at.strftime("%Y-%m-%d")
            user_count = purchase_list[i]['userCount']
            coupon_count = purchase_list[i]['couponCount']
            #Purchase.objects.create(owner=owner, type=type, amount=amount, code=code, expire_at=expire_at, user_count=user_count, used_count=0, coupon_count=coupon_count)

            if owner.is_superuser:
                usable = 'inUse'   #'true'
                paymentKey = buyWhere               
            else:
                usable = 'false'
                paymentKey = ''                

            Purchase.objects.create(owner=owner, type=type, amount=amount, code=code, expire_at=expire_at,
                                    user_count=user_count, used_count=0, coupon_count=coupon_count, 
                                    usable=usable, orderID=orderID, paymentKey=paymentKey)
            
            '''
            ret = purchase_RegistByCode(code, request.user)
            if ret == 'nonexist':
                return redirect('/interviews/purchase/regist/none/')
            elif ret == 'notapproved' :
                return redirect('/interviews/purchase/regist/notapproved/')
            elif ret == 'already' :
                return redirect('/interviews/purchase/regist/already/')
            elif ret == 'expired' :
                return redirect('/interviews/purchase/regist/expired/')
            elif ret == 'overcount' :
                return redirect('/interviews/purchase/regist/overcount/')
            '''

        return HttpResponse("Purchase Request Complete")
    elif request.method == "GET":
        mgr = Manager.objects.get(mid=request.user)
        env = environ.Env()        
        environ.Env.read_env(os.path.join(BASE_DIR, '.env'))        
        #skey = f"{env('SECRET_KEY')}:"
        ckey = env('CLIENT_KEY')        
        return render(
            request,
            'interviews/purchase_request.html',
            {
                'clientKey': ckey,
                'manager': mgr,
            }
        )

def create_oid():
    return 'test' + datetime.utcnow().strftime('%Y%m%d%H%M%S%f')

def gen_purchaseCode():
    length_of_string = 10
    rstr = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length_of_string))
    rstr = getdatestr() + rstr
    return rstr

def getdatestr():
    today = date.today()
    year = str(today.year)[-2:]
    month = '0' + str(today.month)
    month = month[-2:]
    day = '0' + str(today.day)
    day = day[-2:]
    return year+month+day


def purchase_RegistByCode(coupon, ruser):
    mgr = Manager.objects.get(mid=ruser)
    max_time = mgr.max_time
    paid_time = mgr.paid_time
    expire_at = mgr.expire_at

    try:
        pur = Purchase.objects.get(code=coupon)
    except ObjectDoesNotExist:
        return 'nonexist'

    user_list = json.loads(pur.user_list)
    user_count = pur.user_count
    used_count = pur.used_count
    usable = pur.usable

    if usable != 'true':
        return 'notapproved'
    elif ruser.username in user_list:
        return 'already'
    elif date.today() > pur.expire_at:
        return 'expired'
    elif used_count >= user_count:
        return 'overcount'

    if pur.type == 'months':
        max_time = pur.amount * pur.coupon_count
        expire_at = date.today() + timedelta(days=31)
    elif pur.type == 'hours':
        paid_time = paid_time + (pur.amount * pur.coupon_count)

    # user_list += request.user.username
    user_list.append(ruser.username)
    used_count += 1

    Manager.objects.filter(mid=ruser).update(max_time=max_time, paid_time=paid_time, expire_at=expire_at)
    Purchase.objects.filter(code=coupon).update(user_list=json.dumps(user_list, ensure_ascii=False), used_count=used_count,
                                                usable=usable)


def purchase_regist(request, msg):
    mgr = Manager.objects.get(mid=request.user)
    if request.method == 'POST':
        max_time = mgr.max_time
        paid_time = mgr.paid_time
        expire_at = mgr.expire_at

        coupon = request.POST['coupon_code']

        try:
            pur = Purchase.objects.get(code=coupon)
        except ObjectDoesNotExist:
            return redirect('/interviews/purchase/regist/none/')

        user_list = json.loads(pur.user_list)
        user_count = pur.user_count
        used_count = pur.used_count
        usable = pur.usable

        if usable != 'inUse' and usable != 'true':
            return redirect('/interviews/purchase/regist/notapproved/')

        if request.user.username in user_list:
            return redirect('/interviews/purchase/regist/already/')

        if date.today() > pur.expire_at:
            return redirect('/interviews/purchase/regist/expired/')

        if used_count >= user_count:
            return redirect('/interviews/purchase/regist/overcount/')

        if pur.type == 'months':
            max_time = pur.amount * pur.coupon_count
            expire_at = date.today() + timedelta(days=31)
        elif pur.type == 'hours':
            paid_time = paid_time + (pur.amount * pur.coupon_count)

        #user_list += request.user.username
        user_list.append(request.user.username)
        used_count += 1

        Manager.objects.filter(mid=request.user).update(max_time= max_time, paid_time= paid_time, expire_at= expire_at)
        Purchase.objects.filter(code=coupon).update(user_list=json.dumps(user_list, ensure_ascii=False), used_count=used_count, usable=usable)

        return redirect('/interviews/purchase/regist/success/')
    else:
        return render(
            request,
            'interviews/purchase_regist.html',
            {
                'message': msg,
                'manager': mgr,
            }
        )

class PurchaseManageList(ListView):
    model = Purchase
    paginate_by = 50
    template_name = 'interviews/purchase_managelist.html'

    ordering = ['-expire_at']

    def get_context_data(self, **kwargs):
        context = super(PurchaseManageList, self).get_context_data()
        context['manager'] = Manager.objects.get(mid=self.request.user)
        return context

class PurchaseCreate(CreateView):
    model = Purchase

    template_name = 'interviews/purchase.html'

    fields = ['type', 'amount', 'code', 'expire_at', 'user_count']


    def get_context_data(self, **kwargs):
        context = super(PurchaseCreate, self).get_context_data()
        context['manager'] = Manager.objects.get(mid=self.request.user)
        return context

    def form_invalid(self, form):
        print('Form invalid!!!.')
        print(f"1){form.instance.type}:2){form.instance.amount}:3){form.instance.code}:4){form.instance.expire_at}:5){form.instance.user_count}")
       # form.instance.client_name = self.get_object().client_name
        return super().form_invalid(form)

    def form_valid(self, form):
        current_user = self.request.user
        #print(f"1){form.instance.type}:2){form.instance.amount}:3){form.instance.code}:4){form.instance.expire_at}:5){form.instance.user_count}")
        if current_user.is_authenticated and current_user.is_superuser:
            super(PurchaseCreate, self).form_valid(form)   # Database 저장
            return redirect('/interviews/purchase/list/')
        return redirect('/interviews/purchase/list/')

class ClientCreate(CreateView):
    model = Client
    fields = ['name', 'mail', 'phone', 'comment', 'password']
    template_name = 'interviews/client_create.html'


    def get_context_data(self, **kwargs):
        context = super(ClientCreate, self).get_context_data()
        context['clients_list'] = Client.objects.filter(counselor=self.request.user)
        return context

    def form_valid(self, form):
        redir = self.kwargs['redir']
        #print(f"ClientCreate redirect: {redir}")
        current_user = self.request.user
        if current_user.is_authenticated:
            #super(ClientCreate, self).form_valid(form)
            #ccomment = form.instance.comment.strip()
            #form.instance.comment = ccomment

            form.instance.counselor = current_user
            super(ClientCreate, self).form_valid(form)
            if redir == "cltlist":
                return redirect('/interviews')   # redirect('/interviews')
            elif redir == "ivcreate":
                return redirect('/interviews/create/norm/')  # redirect('/interviews')
        else:
            return redirect('/interviews')


class InterviewsUpdatePrev(UpdateView):
    model = Interviews
    template_name = 'interviews/interviews_update_form.html'
    fields = ['title', 'content', 'summary', 'sentimental']


class InterviewsList(ListView):
    model = Interviews
    ordering = '-created_at'
    template_name = 'interviews/interviews_list_v2.html'

    def get_context_data(self, **kwargs):

        try:
            res = Manager.objects.filter(mid=self.request.user).get()
        except ObjectDoesNotExist:
            res = Manager.objects.create(mid=self.request.user, use_time=0, max_time=300)

        context = super(InterviewsList, self).get_context_data()
        context['clients_list'] = Client.objects.filter(counselor=self.request.user)
        context['client_unknown'] = Interviews.objects.filter(client_name='', author=res)
        return context


#class InterviewsDetail(DetailView):
class InterviewsUpdate(UpdateView):
    model = Interviews
    template_name = 'interviews/interviews_detail.html'
    #fields = ['role_label0', 'role_label1', 'role_label2','role_label3']
    #fields = ['client_name', 'client_comment', 'speakers']
    fields = ['client_name', 'speakers','title']

    cur_client = None
    client_pk = None
    #tpath = ''

    '''
    def get_context_data(self, **kwargs):
        # 기본 구현을 먼저 호출해 콘텍스트를 얻는다.
        self.fields = []
        context = super(InterviewsUpdate, self).get_context_data(**kwargs)
         #cdata = Interviews.objects.get(pk__exact=self.kwargs['pk'])
        cdata = Interviews.objects.get(pk=self.kwargs['pk'])
        print('######### cdata ::    ')
        print(cdata)

        sd = json.loads(cdata.content)
        sinfo = sd['speakers']
        for i in range(len(sinfo)):
            self.fields.append('role_label'+str(i))
        print('######### fields ::    ')
        print(self.fields)
    '''
    # for GET passing parameter

    '''
    def dispatch(self, request, *args, **kwargs):
        # 기본 구현을 먼저 호출해 콘텍스트를 얻는다.
        # 요청을 검사해서 HTTP의 메소드(GET, POST)를 알아낸다
        #self.fields = ['client_name','client_comment']

        cdata = Interviews.objects.get(pk=self.kwargs['pk'])    #'pk'

        with open(cdata.content, 'rb') as sent_file:
            rdata = sent_file.read()
            sd = dec(cyp_key, aad, nonce, rdata, cdata.gd_cmk)
            sd = binary_to_dict(sd)

        #sinfo = sd['speakers']
        sinfo = json.loads(cdata.speakers)
        for i in range(len(sinfo)):
            self.fields.append('role_label'+str(i))

        if request.user.is_authenticated and request.user == self.get_object().author.mid:
            return super(InterviewsUpdate, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied
    '''

    def get_context_data(self, **kwargs):
        context = super(InterviewsUpdate, self).get_context_data()
        res = Manager.objects.filter(mid=self.request.user).get()
        idata = Interviews.objects.filter(pk=self.kwargs['pk']).get()


        try:

            with open(idata.content_div, 'rb') as sent_file:
                rdata = sent_file.read()
                div_data = dec(cyp_key, aad, nonce, rdata, idata.gs_cmk)
                div_data = div_data.decode("utf-8")
        except Exception as e:
            print(f"Interv Detail Open Error::{e}")
            div_data = ''


        try:

            with open(idata.content, 'rb') as sent_file:
                rdata = sent_file.read()
                get_data = dec(cyp_key, aad, nonce, rdata, idata.gd_cmk)
                get_data = get_data.decode("utf-8")

        except Exception as e:
            print(f"Getdata Detail Open Error::{e}")
            get_data = ''

        #sent_data = binary_to_dict(sent_data)



        #print(f"GetContext::{sent_data}")
        context['intv_sentence'] = div_data
        context['intv_data'] = get_data
        context['clients_list'] = Client.objects.filter(counselor=self.request.user)
        context['client_unknown'] = Interviews.objects.filter(client_name='', author=res)
        context['client_info'] = idata.client #clt
        context['manager'] = res
        context['mode'] = self.kwargs['mode']
        #print(f"ContextData:: {idata.client.name}")
        return context
    
    def form_invalid(self, form):
        print('Form invalid!!!.')
        print(f"1){form.instance.client_name}:2){form.instance.speakers}3){form.instance.title}")
       # form.instance.client_name = self.get_object().client_name
        return super().form_invalid(form)
    # for POST parameter receiving

    def form_valid(self, form):
        print('##############  Form valid')
        print(f"{form.instance.title}::{form.instance.client_name}:: {form.instance.speakers}")
        #super(InterviewsUpdate, self).form_valid(form)

        try:
            with open(form.instance.content_div, 'rb') as sent_file:
                rdata = sent_file.read()
                div_data = dec(cyp_key, aad, nonce, rdata, form.instance.gs_cmk)
                div_data = json.loads(div_data)
        except Exception as e:
            print(f"Interv Detail DivFileOpen Error::{e}")

        trans = form.instance.speakers
        trans = trans.replace("&quot;","'")
        #trans = trans.replace("&quot;",'"')

        #print(f"InterviewUpdateValid0::{trans}")
        #trans = trans.replace("'", '"')
        speakers = json.loads(trans)
        #print(f"InterviewUpdateValid::{speakers}, ClientName::{form.instance.client_name}")

        try:
            clt = Client.objects.filter(name=form.instance.client_name, counselor=self.request.user).get()
        except ObjectDoesNotExist:
            print("Client not exist")
            clt = Client.objects.create(name=form.instance.client_name, counselor=self.request.user)

        clt.comment = form.instance.client_comment

        #print(f"CLient valid:: {clt.name}:{clt.comment}")
        form.instance.client = clt



        sent_len = len(div_data)
        for i in range(sent_len):
            sindex = next((index for (index, d) in enumerate(speakers) if d["label"] == div_data[i]["speaker"]), None)
            div_data[i]["name"] = speakers[sindex]["name"]



        try:
            gs_cyp, gs_mac = enc(cyp_key, aad, nonce, dict_to_binary(div_data))
        except Exception as e:
            print(f"SentenceUpdate Encryp Error::{e}")

        try:
            with open(form.instance.content_div, 'wb') as outfile2:
                outfile2.write(gs_cyp)
        except Exception as e:
            print(f"SentenceUpdate Write Error::{e}")
            return HttpResponse("SentenceUpdate Write Error")

        form.instance.gs_cmk = gs_mac
        response = super(InterviewsUpdate, self).form_valid(form)
        return response


def get_play_time(filename):
    aext = os.path.splitext(filename)
    alist = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.ac3','.m4a']
    vlist = ['.avi', '.mov', '.mp4', '.wmv', '.flv', '.mkv']

    if aext[1] in alist or aext[1] in vlist:
        cmd = 'ffprobe -i {} -show_entries format=duration -v quiet -of csv="p=0"'.format(filename)
        output = subprocess.check_output(
            cmd,
            shell=True,  # Let this run in the shell
            stderr=subprocess.STDOUT
        )
        output = float(output.decode('utf-8'))
        output = math.ceil(output)

    else:
        print("Not Supporting File Type")
        return -1

    return output
    '''
    if aext[1] in alist or aext[1] in vlist:
        cmnd = ['ffprobe', '-show_format', '-pretty', '-loglevel', 'quiet', filename]
        p = subprocess.Popen(cmnd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        print(f"MediaInfo::{out}")
        if err:
            print(f"Media ReadError:{err}")
    else:
        print("Not Supporting File Type")
    '''


    ''' tinytag 기반
    aext = os.path.splitext(filename)

    if aext[1] in alist:
        audio = TinyTag.get(filename)
        print(f"Title:{audio.title}")
        print(f"Duration:{audio.duration}")

    elif aext[1] in vlist:
        video = TinyTag.get(filename)
        print(f"Video:{video}")
        print(f"Title:{video.title}")
        print(f"Duration:{video.duration}")
    '''

    ''' mugen 기반 
    aext = os.path.splitext(filename)
    play_time = 0
    if aext[1] == '.mp3':
        play_time = mp3.MP3(filename).info.length
    elif aext[1] == '.mp4':
        play_time = mp4.MP4(filename).info.length
    elif aext[1] == '.wav':
        play_time = wave.WAVE(filename).info.length
    elif aext[1] == '.ogg':
        play_time = oggvorbis.OggVorbis(filename).info.length
    print(f"PlayTime:::{filename}:{aext[1]}:{play_time}")
    return play_time
    '''


class InterviewsCreate(CreateView):
    model = Interviews
    fields = ['title', 'client_name', 'file_upload', 'nums_speaker', 'stt_lang', 'stt_engine']
    #fields = ['title', 'client_name', 'object_path', 'nums_speaker', 'stt_lang']

    def get_context_data(self, **kwargs):
        env = environ.Env(
            # set casting, default value
            DEBUG=(bool, False)
        )        
        environ.Env.read_env(os.path.join(BASE_DIR, '.env'))        

        sec_key = env('STORE_SEC_KEY')
        acc_key = env('STORE_ACC_KEY')          
        context = super(InterviewsCreate, self).get_context_data()
        mgr = Manager.objects.get(mid=self.request.user)
        context['clients_list'] = Client.objects.filter(counselor=self.request.user)
        #print(Interviews.objects.filter(client=None))
        context['client_unknown'] = Interviews.objects.filter(client_name='', author=mgr)
        context['manager'] = mgr
        context['file_chk'] = self.kwargs['msg']
        context['sec_key'] = sec_key
        context['acc_key'] = acc_key

        return context

    def form_invalid(self, form):
        print(f"Form Invalid!!:: {form.instance.file_upload.name}")

    def form_valid(self, form):

        cuser = self.request.user
        #current_user = Manager.objects.get(mid=cuser)
        if not cuser.is_authenticated:
            return redirect('/interviews')

        response = super(InterviewsCreate, self).form_valid(form)

        if form.instance.client_name == '':
            form.instance.client_name = '고객미정'

        try:
            clt = Client.objects.filter(name=form.instance.client_name, counselor=cuser).get()
        except ObjectDoesNotExist:
            clt = Client.objects.create(name=form.instance.client_name, counselor=cuser) # current_user->  form.instance.author

        


        form.instance.client = clt

        print(f"Stt Lang:: {form.instance.stt_lang}")


        if form.instance.stt_engine == 'vito':
            ret, pauthor, get_data, group_sent, timestr, sentimental, intv_duration, speakers, all_confidence = \
            InterviewVitoAnalysis(cuser, form.instance.nums_speaker, form.instance.file_upload.name, "ko-KR")     
        else: #form.instance.stt_engine == 'naver':
            ret, pauthor, get_data, group_sent, timestr, sentimental, intv_duration, speakers, all_confidence = \
            InterviewAnalysis(cuser, form.instance.nums_speaker, form.instance.file_upload.name, form.instance.stt_lang)
            #speakers = json.dumps(speakers).replace('false', r'"false"').replace('true', r'"true"')


        if ret == -1:
            return redirect("/interviews/create/fail/")

        if ret == -2:
            return redirect("/interviews/create/timeover/")

        if not form.instance.title :
            form.instance.title = form.instance.get_file_name().split('.')[0]


        wstr = form.instance.file_upload.path
        tpath = wstr[0:wstr.rfind('\\')+1]    # last index
        
        gdpath = tpath + "STT_data_" + timestr + ".faj"
        gspath = tpath + "Spker_data_" + timestr + ".faj"
        smpath = tpath + "Senti_data_" + timestr + ".faj"

        try:
            gd_cyp, gd_mac = enc(cyp_key, aad, nonce, dict_to_binary(get_data))
            gs_cyp, gs_mac = enc(cyp_key, aad, nonce, dict_to_binary(group_sent))
            sm_cyp, sm_mac = enc(cyp_key, aad, nonce, dict_to_binary(sentimental))
        except Exception as e:
            print(f"Cypher Error Message::{e}")

        try:
            with open(gdpath, 'wb') as outfile:
                outfile.write(gd_cyp)
            with open(gspath, 'wb') as outfile1:
                outfile1.write(gs_cyp)
            with open(smpath, 'wb') as outfile2:
                outfile2.write(sm_cyp)
        except Exception as e:
            print(f"Object Store Error Message::{e}")

        speakers = json.dumps(speakers).replace(r"'false'", r'"false"').replace(r"'true'", r'"true"')

        form.instance.gd_cmk = gd_mac
        form.instance.gs_cmk = gs_mac
        form.instance.sm_cmk = sm_mac
        form.instance.author = pauthor
        form.instance.duration = intv_duration #/1000
        form.instance.content = gdpath #json.dumps(get_data, ensure_ascii=False)
        form.instance.content_div = gspath #json.dumps(group_sent, ensure_ascii=False)
        form.instance.hwp_file = "ReportHWP_"+timestr+".hwp"
        form.instance.pdf_file = "ReportHTML_"+timestr+".html"
        #form.instance.summary = json.dumps(summa, ensure_ascii=False)
        form.instance.sentimental = smpath #json.dumps(sentimental, ensure_ascii=False)
        form.instance.speakers = speakers
        form.instance.confidence = all_confidence

        response = super(InterviewsCreate, self).form_valid(form)
        return response



def InterviewAnalysis(cuser, nums_speaker, file_upload_name, stt_lang):
#def InterviewAnalysis(cuser, form):

    try:
        pauthor = Manager.objects.filter(mid=cuser).get()    # cuser = self.request.user
    except ObjectDoesNotExist:
        pauthor = Manager.objects.create(mid=cuser, use_time=0, max_time=300)   # 300 minutes   millisec * 60000


    diarize_set = {
        "enable": True,
        "speakerCountMin": nums_speaker,
        "speakerCountMax": nums_speaker
    }

    #cont4s = {'full': []}  # content aggregate in one paragraph for summary
    group_sent = []
    #temp_cont = {'full': ''}  # to check the size limit of 2000 character

    #senten = {'full': []}
    sentimental = dict()
    #get_data = dict()

    try:
        res = ClovaSpeechClient().req_upload(file=u'./_media/{}'.format(file_upload_name),
                                            completion='sync', diarization=diarize_set, stt_lang=stt_lang)
        #print(f"ClovaRes:{res}")
        get_data = json.loads(res.text)
        #print(f"Analysis:{get_data}")
        spklen = get_data['segments'][-1]['end']
        speakers = get_data['speakers']
        all_confidence = int(get_data['confidence']*1000)
        #print(f"Analysis::{speakers}")
        #speakers = json.dumps(speakers).replace('false', r'"false"').replace('true', r'"true"')
        #speakers = json.loads(speakers)
    except Exception as e:
        print(f"Error Message::{e}")
        # print(f"Res.text::{get_data['result']}")
        # return redirect("/interviews/create/fail/")
        return -1, '','','','','','',''
    seg_len = len(get_data['segments'])


    # cs = ClovaSentimental()  # disaple sentence setimental analysis

    # 스피커 별 문장 개수 카운드 변수
    stn_no_speaker = {}
    for i in range(len(speakers)):
        stn_no_speaker[speakers[i]["label"]] = 0

    prev_speaker = 'superman'
    #prev_speaker = get_data['segments'][0]['speaker']['label']
    group_idx = 0


    if get_data['segments'][0]['text'] == '':
        get_data['segments'][0]['text'] = '공백'


    for i in range(seg_len):
        #xls_col = 1
        cur_text = get_data['segments'][i]['text']

        if cur_text == '': continue

        # speaker = get_data['segments'][i]['speaker']['name']
        speaker = get_data['segments'][i]['speaker']['label']
        start_time = get_data['segments'][i]['start']
        end_time = get_data['segments'][i]['end']
        sent_confidence = get_data['segments'][i]['confidence']
        #################################
        # for sentimental
        ###################################
        if speaker not in sentimental:
            sentimental[speaker] = dict()
            sentimental[speaker] = {"word_count": 0, "speak_len": 0, "speed": 0, "speak_rate": 0, "senti": "unknown",
                                    "pos_count": 0, "neg_count": 0, "type_count": 0, "word_freq": {}, "wc_svg": ''}

        group_sent.append({"speaker": speaker, "name": chr(ord(speaker) + 16), "sentence": cur_text, "first_sentence": "false",
                            "quiet_time": 0, "start": start_time, "end": end_time, "senti": "None", "sent_no": 0, "confidence": sent_confidence})

        if prev_speaker != speaker:
            stn_no_speaker[speaker] = stn_no_speaker[speaker] + 1
            prev_speaker = speaker
            group_sent[group_idx]["first_sentence"] = "true"

        group_sent[group_idx]["sent_no"] = stn_no_speaker[speaker]

        if i != 0:
            group_sent[group_idx]["quiet_time"] = round((group_sent[group_idx]["start"] - group_sent[group_idx-1]["end"])/1000)
        else:
            group_sent[group_idx]["quiet_time"] = 0

        group_idx = group_idx + 1

        #################################
        # for sentimental analysis module
        ###################################

        if 'words' in get_data['segments'][i]:
            sentimental[speaker]['word_count'] = sentimental[speaker]['word_count'] + len(
                get_data['segments'][i]['words'])
        sentimental[speaker]['speak_len'] = sentimental[speaker]['speak_len'] + get_data['segments'][i]['end'] - \
                                            get_data['segments'][i]['start']

    # Last segments
    # disable sentimental analysis
    '''
    cs_res = cs.req_url(scont=group_sent[group_idx]['sentence'])
    cs_data = json.loads(cs_res.text)

    try:
        sdata = cs_data['document']
        group_sent[group_idx]['senti'] = sdata['sentiment']
    except KeyError:
        group_sent[group_idx]['senti'] = "none"

    if group_sent[group_idx]['senti'] == 'negative':
        sentimental[speaker]['neg_count'] = sentimental[speaker]['neg_count'] + 1
    elif group_sent[group_idx]['senti'] == 'positive':
        sentimental[speaker]['pos_count'] = sentimental[speaker]['pos_count'] + 1
    '''

    nlp = Okt()
    # nlp = Hannanum()
    timestr = datetime.now().strftime('%Y-%m-%d-%H+%M+%S')

    # 불용어 처리
    with open("./interviews/stopwords_korean.txt", "rt", encoding="utf-8") as f:
        lines = f.readlines()

    # txt 읽을 때 \n표시를 제거
    stop_words = []
    for line in lines:
        line = line.replace('\n', '')
        stop_words.append(line)

    for key, value in sentimental.items():
        if value['pos_count'] > value['neg_count']:
            sentimental[key]['senti'] = "positive"
        else:
            sentimental[key]['senti'] = "negative"

        # sentimental[key]["speed"] = (sentimental[key]['word_count']*60000)/sentimental[key]['speak_len']
        chr_len = 0
        for ti in group_sent:
            if (key == ti['speaker']):
                chr_len = chr_len + len(ti['sentence'])
        #for ti in cont4s[key] :
        #    chr_len = chr_len + len(ti)

        sentimental[key]['speed'] = (chr_len * 60000) / sentimental[key]['speak_len']
        sentimental[key]['speak_rate'] = sentimental[key]['speak_len'] / spklen

        # for word cloud
        if stt_lang == 'ko-KR':
            cc = ''
            for ti in group_sent:
                if(key==ti['speaker']):
                    cc = cc + ti['sentence'] + '\n'
             
            nouns = nlp.nouns(cc.replace('\n', ''))
            ft_nouns = [each_word for each_word in nouns
                        if each_word not in stop_words]
            ncount = Counter(ft_nouns)
            nfreq = ncount.most_common(10)
            palettes = ['spring', 'summer', 'seismic', 'PuBu', 'winter']

            try:
                wordcloud = WordCloud(width=400, height=300, margin=20, font_path='./interviews/font/NanumGothic.ttf',
                                      background_color='white',
                                      # wordcloud = WordCloud(font_path='./interviews/font/NanumGothic.ttf', background_color='white',
                                      colormap=palettes[3]).generate_from_frequencies(dict(ncount))
                #                      colormap='winter', stopwords=stop_words).generate_from_frequencies(dict(ncount))

                wc_file = MEDIA_ROOT + "\interviews\img\svgfile_" + key + "_" + timestr + '.svg'
                sentimental[key]['wc_svg'] = '/media/interviews/img/svgfile_' + key + "_" + timestr + '.svg'

                plt.figure(figsize=(4, 3))
                plt.imshow(wordcloud)
                plt.axis('off'), plt.xticks([]), plt.yticks([])
                plt.tight_layout()
                plt.subplots_adjust(left=0, bottom=0, right=1, top=1, hspace=0, wspace=0)

                # plt.savefig(wc_file, pad_inches=0, format="svg")
                plt.savefig(wc_file, dpi=700, format="svg")

                sentimental[key]["type_count"] = len(ncount)

                for i in nfreq:
                    sentimental[key]["word_freq"][i[0]] = i[1]

            except Exception as e:
                print(f"WC Error Message::{e}")

    intv_duration = get_data['segments'][-1]['end']
    intv_duration = math.ceil(intv_duration/60000)
    use_time = pauthor.use_time + intv_duration #play_time
    paid_time = pauthor.paid_time
    if use_time > pauthor.max_time:
        if pauthor.paid_time <= 0:
            return -2, '','','','','','','',''
        else :
            paid_time = pauthor.paid_time - (use_time-pauthor.max_time)
            use_time = pauthor.max_time

    accum_time = pauthor.accum_time + intv_duration #play_time
    Manager.objects.filter(mid=cuser).update(use_time=use_time, accum_time=accum_time, paid_time=paid_time)

    #rget_data = json.dumps(get_data, ensure_ascii=False)
    #rgroup_sent = json.dumps(group_sent, ensure_ascii=False)
    #rsentimental = json.dumps(sentimental, ensure_ascii=False)

    return 1, pauthor, get_data, group_sent, timestr, sentimental, intv_duration, speakers, all_confidence




def InterviewVitoAnalysis(cuser, nums_speaker, file_upload_name, stt_lang):
    try:
        pauthor = Manager.objects.filter(mid=cuser).get()    # cuser = self.request.user
    except ObjectDoesNotExist:
        pauthor = Manager.objects.create(mid=cuser, use_time=0, max_time=300)   # 300 minutes   millisec * 60000

    group_sent = []
    sentimental = dict()
    speakers = [{"label":"0","name":"A","edited":"false"},{"label":"1","name":"B","edited":"false"}]
    try:
        res = vito_auto_process(u'./_media/{}'.format(file_upload_name))
        get_data = res['results']['utterances']

        spklen = get_data[-1]['start_at'] + get_data[-1]['duration']

        all_confidence = 0
        #print(f"Analysis::{speakers}")
        #speakers = json.dumps(speakers).replace('false', r'"false"').replace('true', r'"true"')
        #speakers = json.loads(speakers)
    except Exception as e:
        print(f"Error Message::{e}")
        # print(f"Res.text::{get_data['result']}")
        # return redirect("/interviews/create/fail/")
        return -1, '','','','','','',''
    seg_len = len(get_data)


    # cs = ClovaSentimental()  # disaple sentence setimental analysis

    # 스피커 별 문장 개수 카운드 변수
    stn_no_speaker = {}
    for i in range(len(speakers)):
        stn_no_speaker[speakers[i]["label"]] = 0

    prev_speaker = 'superman'
    #prev_speaker = get_data['segments'][0]['speaker']['label']
    group_idx = 0


    if get_data[0]['msg'] == '':
        get_data[0]['msg'] = '공백'


    for i in range(seg_len):
        #xls_col = 1
        cur_text = get_data[i]['msg']

        if cur_text == '': continue

        s1 = get_data[i]['spk']

        if s1 == 11 :
            s1 = 1

        speaker = str(s1) #str(get_data[i]['spk'])
        start_time = get_data[i]['start_at']
        end_time = get_data[i]['start_at'] + get_data[i]['duration']
        sent_confidence = 0
        #################################
        # for sentimental
        ###################################
        if speaker not in sentimental:
            sentimental[speaker] = dict()
            sentimental[speaker] = {"word_count": 0, "speak_len": 0, "speed": 0, "speak_rate": 0, "senti": "unknown",
                                    "pos_count": 0, "neg_count": 0, "type_count": 0, "word_freq": {}, "wc_svg": ''}

        group_sent.append({"speaker": speaker, "name": chr(ord(speaker) + 17), "sentence": cur_text, "first_sentence": "false",
                            "quiet_time": 0, "start": start_time, "end": end_time, "senti": "None", "sent_no": 0, "confidence": sent_confidence})

        if prev_speaker != speaker:
            stn_no_speaker[speaker] = stn_no_speaker[speaker] + 1
            prev_speaker = speaker
            group_sent[group_idx]["first_sentence"] = "true"

        group_sent[group_idx]["sent_no"] = stn_no_speaker[speaker]

        if i != 0:
            group_sent[group_idx]["quiet_time"] = round((group_sent[group_idx]["start"] - group_sent[group_idx-1]["end"])/1000)
        else:
            group_sent[group_idx]["quiet_time"] = 0

        group_idx = group_idx + 1

        #################################
        # for sentimental analysis module
        ###################################

        sentimental[speaker]['word_count'] = sentimental[speaker]['word_count'] + cur_text.count(' ') + 1
            #len(get_data['segments'][i]['words'])
        sentimental[speaker]['speak_len'] = sentimental[speaker]['speak_len'] + get_data[i]['duration']


    nlp = Okt()
    # nlp = Hannanum()
    timestr = datetime.now().strftime('%Y-%m-%d-%H+%M+%S')

    # 불용어 처리
    with open("./interviews/stopwords_korean.txt", "rt", encoding="utf-8") as f:
        lines = f.readlines()

    # txt 읽을 때 \n표시를 제거
    stop_words = []
    for line in lines:
        line = line.replace('\n', '')
        stop_words.append(line)

    for key, value in sentimental.items():
        if value['pos_count'] > value['neg_count']:
            sentimental[key]['senti'] = "positive"
        else:
            sentimental[key]['senti'] = "negative"

        # sentimental[key]["speed"] = (sentimental[key]['word_count']*60000)/sentimental[key]['speak_len']
        chr_len = 0
        for ti in group_sent:
            if (key == ti['speaker']):
                chr_len = chr_len + len(ti['sentence'])
        #for ti in cont4s[key] :
        #    chr_len = chr_len + len(ti)

        sentimental[key]['speed'] = (chr_len * 60000) / sentimental[key]['speak_len']
        sentimental[key]['speak_rate'] = sentimental[key]['speak_len'] / spklen

        # for word cloud
        if stt_lang == 'ko-KR':
            cc = ''
            for ti in group_sent:

                if(key==ti['speaker']):
                    cc = cc + ti['sentence'] + '\n'
             
            nouns = nlp.nouns(cc.replace('\n', ''))
            ft_nouns = [each_word for each_word in nouns
                        if each_word not in stop_words]
            ncount = Counter(ft_nouns)
            nfreq = ncount.most_common(10)
            palettes = ['spring', 'summer', 'seismic', 'PuBu', 'winter']

            try:
                wordcloud = WordCloud(width=400, height=300, margin=20, font_path='./interviews/font/NanumGothic.ttf',
                                      background_color='white',
                                      # wordcloud = WordCloud(font_path='./interviews/font/NanumGothic.ttf', background_color='white',
                                      colormap=palettes[3]).generate_from_frequencies(dict(ncount))
                #                      colormap='winter', stopwords=stop_words).generate_from_frequencies(dict(ncount))

                wc_file = MEDIA_ROOT + "\interviews\img\svgfile_" + key + "_" + timestr + '.svg'
                sentimental[key]['wc_svg'] = '/media/interviews/img/svgfile_' + key + "_" + timestr + '.svg'

                plt.figure(figsize=(4, 3))
                plt.imshow(wordcloud)
                plt.axis('off'), plt.xticks([]), plt.yticks([])
                plt.tight_layout()
                plt.subplots_adjust(left=0, bottom=0, right=1, top=1, hspace=0, wspace=0)

                # plt.savefig(wc_file, pad_inches=0, format="svg")
                plt.savefig(wc_file, dpi=700, format="svg")

                sentimental[key]["type_count"] = len(ncount)

                for i in nfreq:
                    sentimental[key]["word_freq"][i[0]] = i[1]

            except Exception as e:
                print(f"WC Error Message::{e}")


    intv_duration = get_data[-1]['start_at'] + get_data[-1]['duration']
    intv_duration = math.ceil(intv_duration/60000)
    use_time = pauthor.use_time + intv_duration #play_time
    paid_time = pauthor.paid_time
    if use_time > pauthor.max_time:
        if pauthor.paid_time <= 0:
            return -2, '','','','','','',''
        else :
            paid_time = pauthor.paid_time - (use_time-pauthor.max_time)
            use_time = pauthor.max_time

    accum_time = pauthor.accum_time + intv_duration #play_time
    Manager.objects.filter(mid=cuser).update(use_time=use_time, accum_time=accum_time, paid_time=paid_time)

    return 1, pauthor, get_data, group_sent, timestr, sentimental, intv_duration, speakers, all_confidence


class InterviewsSearch(InterviewsList):
    paginate_by = None

    def get_queryset(self):
        q = self.kwargs['q']
        interviews_list = Interviews.objects.filter(
            Q(title__contains=q)
            #Q(title__contains=q) | Q(tags__name__contains=q)
        ).distinct()
        print(f"Queryset:: {interviews_list}")
        return interviews_list

    def get_context_data(self, **kwargs):
        context = super(InterviewsSearch, self).get_context_data()
        q = self.kwargs['q']
        context['search_info'] = f'Search: {q} ({self.get_queryset().count()})'

        return context

    
