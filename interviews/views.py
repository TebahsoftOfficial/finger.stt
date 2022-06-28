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

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = os.path.join(BASE_DIR, '_media')

#key = bytes([0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF])
cyp_key = bytes([0x0f, 0x1e, 0x2d, 0x3c, 0x4b, 0x5a, 0x69, 0x78, 0x87, 0x96, 0xA5, 0xB4, 0xC3, 0xD2, 0xE1, 0xF0])
aad = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E])  #
nonce = bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC])  # 기본 12(96bit)byte이며 길이 변경 가능.


def RealtimeInterviews(request):
    return render(
        request,
        'interviews/interviews_realtime.html',
    )  

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


    elif msg == 'encrypt':
        i = 0
        for interview in interviews:
            update = 0
            timestr = datetime.now().strftime('%Y%m%d-%H-%M-%S')
            try:
                wstr = interview.file_upload.path
            except Exception as e:
                print(f"FilePath NonExist::{e}")
                continue
            tpath = wstr[0:wstr.rfind('\\') + 1]  # last index

            gdpath =f"{tpath}STT_data{i}_{timestr}.faj"
            gspath =f"{tpath}Spker_data{i}_{timestr}.faj"
            smpath =f"{tpath}Senti_data{i}_{timestr}.faj"
            smrpath = f"{tpath}Smry_data{i}_{timestr}.faj"

            i = i + 1

            try:
                fstr = interview.content
                fidx = fstr.rfind('.')
                if fidx != -1:
                    fext = fstr[fidx + 1:fidx + 4]
                else:
                    fext = "non"


                if fext != "faj": # faj가 아닌경우 암호화 진행
                    update = 1
                    if fext == "jso":
                        with open(fstr,'r') as f:
                            get_data = json.load(f)
                            sbin = dict_to_binary(get_data)
                    else:
                        sbin = fstr.encode("utf-8")
                    gd_cyp, gd_mac = enc(cyp_key, aad, nonce, sbin)
                    with open(gdpath, 'wb') as outfile:
                        outfile.write(gd_cyp)
                    Interviews.objects.filter(pk=interview.pk).update(content=gdpath,  gd_cmk=gd_mac)
                    print("1Enc")
            except Exception as e:
                print(f"Cypher1 Error Message::{e}")

            try:
                fstr = interview.content_div
                fidx = fstr.rfind('.')
                if fidx!=-1:
                    fext = fstr[fidx + 1:fidx + 4]
                else:
                    fext = "non"
                if fext != "faj":
                    update = 1
                    if fext=="jso":
                        with open(fstr, 'r') as f:
                            group_sent = json.load(f)
                            sbin = dict_to_binary(group_sent)
                    else:
                        sbin = fstr.encode("utf-8")
                    gs_cyp, gs_mac = enc(cyp_key, aad, nonce, sbin)
                    with open(gspath, 'wb') as outfile1:
                        outfile1.write(gs_cyp)
                    Interviews.objects.filter(pk=interview.pk).update(content_div=gspath,  gs_cmk=gs_mac)
                    print("2Enc")
            except Exception as e:
                print(f"Cypher2 Error Message::{e}")

            try:
                fstr = interview.sentimental
                fidx = fstr.rfind('.')
                if fidx!=-1:
                    fext = fstr[fidx + 1:fidx + 4]
                else:
                    fext = "non"
                if fext != "faj":
                    update = 1
                    if fext=="jso":
                        with open(fstr, 'r') as f:
                            sentimental = json.load(f)
                            sbin = dict_to_binary(sentimental)
                    else:
                        sbin = fstr.encode("utf-8")
                    sm_cyp, sm_mac = enc(cyp_key, aad, nonce, sbin)
                    with open(smpath, 'wb') as outfile2:
                        outfile2.write(sm_cyp)
                    Interviews.objects.filter(pk=interview.pk).update(sentimental=smpath,  sm_cmk=sm_mac)
                    print("3Enc")
            except Exception as e:
                print(f"Cypher3 Error Message::{e}")

            try:
                fstr = interview.summary
                fidx = fstr.rfind('.')

                if fidx != -1:
                    fext = fstr[fidx + 1:fidx + 4]
                else:
                    fext = "non"
                print(f"SummaryFormat::{fext}")

                if fext != "faj":
                    update = 1
                    if fext == "jso":
                        with open(fstr, 'r') as f:
                            summary = json.load(f)
                            sbin = dict_to_binary(summary)
                    else:
                        #summary = json.loads(fstr)
                        sbin = fstr.encode("utf-8")
                    smr_cyp, smr_mac = enc(cyp_key, aad, nonce, sbin)
                    with open(smrpath, 'wb') as outfile3:
                        outfile3.write(smr_cyp)
                    Interviews.objects.filter(pk=interview.pk).update(summary=smrpath,  smr_cmk=smr_mac)
                    print("4Enc")
            except Exception as e:
                print(f"Cypher4 Error Message::{e}")

    elif msg == 'wordcloud':
        wordcloudUpdate(request)


    '''
    elif msg == 'sec2min':  # Warning Just one time running
        for interview in interviews:
            try:
                dur = ((interview.duration)+59)/60
                Interviews.objects.filter(pk=interview.pk).update(duration=dur)
            except Exception as e:
                print(f"Sec2MinError:{e}")
    '''

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

def wordcloudUpdate(req):
    nlp = Okt()

    interviews = Interviews.objects.all()
    #interviews = Interviews.objects.filter(client_name='오정섭')

    #res = Manager.objects.filter(mid=req.user).get()
    '''
    try :
        own = User.objects.filter(username="이병훈").get()
        res = Manager.objects.filter(mid=own).get()
        interviews = Interviews.objects.filter(author=res)
    except Exception as e:
        print(f"Object Get Error:{e}")
    '''

    # 불용어 처리
    with open("./interviews/stopwords_korean.txt", "rt", encoding="utf-8") as f:
        lines = f.readlines()
    stop_words = []
    for line in lines:
        line = line.replace('\n', '')
        stop_words.append(line)
   #print(f"StopWords:::{stop_words}")

    fig = plt.figure(figsize=(4, 3))

    for interview in interviews:
        spk_sent = dict()  # { '1':'sentence','2':'sentence'}
        senti = dict()  # { '1':{ ...}, '2': {...},}
        get_data = []  # [ {'speaker':'1', ....}, {'speaker':'2',....}]

        timestr = datetime.now().strftime('%Y%m%d-%H-%M-%S')
        print(f"Title:{interview.title}")
        try:
            senti = json.loads(interview.sentimental)
            get_data = json.loads(interview.content_div)
            #print(f"Senti1:{senti}")
            for ti in get_data:
                speaker = ti['speaker']
                if speaker not in spk_sent:
                    spk_sent[speaker] = ''
                spk_sent[speaker] = spk_sent[speaker] + ti['sentence']
        except Exception as e:
            print(f"WC DataReadError:{e}")
            continue

        for key, value in spk_sent.items():
            nouns = nlp.nouns(value.replace('\n', ''))
            # nouns = nlp.nouns(cont4s[key].replace('\n', ''))

            ft_nouns = [each_word for each_word in nouns
                        if each_word not in stop_words]

            #print(f"FTNouns:::{ft_nouns}")
            ncount = Counter(ft_nouns)
            nfreq = ncount.most_common(10)

            palettes = ['spring', 'summer', 'seismic', 'PuBu', 'winter']

            try:
                wordcloud = WordCloud(width=400, height=300, margin=20, font_path='./interviews/font/NanumGothic.ttf',
                                      background_color='white',
                                      colormap=palettes[3]).generate_from_frequencies(dict(ncount))

                wc_file = MEDIA_ROOT + "\interviews\img\svgfile_" + key + "_" + timestr + '.svg'
                #senti[key]["wc_svg"] = '/media/interviews/img/svgfile_' + key + "_" + timestr + '.svg'

                #fig = plt.figure(figsize=(4, 3))
                plt.imshow(wordcloud)
                plt.axis('off'), plt.xticks([]), plt.yticks([])
                plt.tight_layout()
                plt.subplots_adjust(left=0, bottom=0, right=1, top=1, hspace=0, wspace=0)

                #plt.savefig(wc_file, dpi=700, format="svg")
                wcf = MEDIA_ROOT + senti[key]["wc_svg"].replace('/', '\\').replace('\\media','')
                plt.savefig(wcf, dpi=700, format="svg")
                plt.clf()
                #plt.close(fig)

                senti[key]["type_count"] = len(ncount)
                senti[key]["word_freq"] = {}
                for i in nfreq:
                    senti[key]["word_freq"][i[0]] = i[1]

            except Exception as e:

                print(f"WC Error Message::{e}")
                break
            ft_nouns.clear()
            nfreq.clear()
            ncount.clear()
            nouns.clear()
        #print(f"SentiG {senti}")
        Interviews.objects.filter(pk=interview.pk).update(sentimental = json.dumps(senti))
    print("WordCloud Update COmpleted!!!")


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

        '''
        print("All Sentences\n")
        i=0
        for sent in all_sentence:
            print(f"{i}::{sent}\n")
            i = i+1

        print("Intv Sentences\n")
        i=0
        #for sent in intv_sentences:
        for i in range(len(intv_sentences)):
            print(f"{i}::{intv_sentences[i]}\n")
        '''



        stn_no_speaker = {}
        prev_speaker = 'superman'
        for si in range(len(speakers)):
            stn_no_speaker[speakers[si]["label"]] = 0

        i = 0
        for sent in all_sentence:

            if sent['generated'] == 'false':
                #print("Falsed")
                #org_sent = copy.deepcopy(intv_sentences[gen_idx])

                gen_idx = gen_idx + 1

            fspk = sent['speaker']
            #print(f"Index::{gen_idx}")
            #print(f"Append>data{gen_idx}::{org_sent}")
            gen_sentences.append({})
            gen_sentences[i] = copy.deepcopy(intv_sentences[gen_idx])
           #gen_sentences.append(org_sent)


            #intv_sentences[i]['sentence'] = all_sentence[i]['sentence']
            gen_sentences[i]['sentence'] = sent['sentence']

            #intv_sentences[i]['speaker'] = fspk
            gen_sentences[i]['speaker'] = fspk
            sindex = next((index for (index, d) in enumerate(speakers) if d["label"] == fspk), None)
            #intv_sentences[i]['name'] = speakers[sindex]['name']
            gen_sentences[i]['name'] = speakers[sindex]['name']
            #print(f"Speakerss::{intv_sentences[i]['speaker']}:{intv_sentences[i]['name']}")

            # sentence number update
            #speaker = intv_sentences[i]['speaker']
            speaker = gen_sentences[i]['speaker']
            if prev_speaker != speaker:
                stn_no_speaker[speaker] = stn_no_speaker[speaker] + 1
                prev_speaker = speaker
                #intv_sentences[i]["first_sentence"] = "true"
                gen_sentences[i]['first_sentence'] = "true"
            else :
                gen_sentences[i]['first_sentence'] = "false"

            #intv_sentences[i]["sent_no"] = stn_no_speaker[speaker]
            gen_sentences[i]["sent_no"] = stn_no_speaker[speaker]



            i = i + 1
            #gen_sentences.append(base_sentence)

        try:
            #gs_cyp, gs_mac = enc(cyp_key, aad, nonce, dict_to_binary(intv_sentences))
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
        #print(f"sentenceUpdate::{all_sentence[0]['speaker']}:{all_sentence[0]['sentence']}")
        return HttpResponse("Sentence Updated")

def record(request):
    if request.method == "POST":
        audio_file = request.FILES.get("recorded_audio")
        title = request.POST.get("rec_title")

        if not title :
            title = "대화녹음_"+datetime.now().strftime('%Y%m%d-%H-%M-%S')

        intv = Interviews.objects.create(title=title, file_upload=audio_file)
        intv.save()
        #messages.success(request, "Audio recording successfully added!")
        #print(f'1Record posted:{audio_file}')

        cuser = request.user
        if not cuser.is_authenticated:
            return JsonResponse(
                {
                    "url": '/interviews',
                    "success": True,
                }
            )
        try:
            clt = Client.objects.filter(name='고객미정', counselor=cuser).get()
        except ObjectDoesNotExist:
            clt = Client.objects.create(name='고객미정', counselor=cuser)

        speaker_nums = 2
        ret, pauthor, get_data, group_sent, timestr, sentimental, speakers = InterviewAnalysis(cuser, speaker_nums, intv.file_upload.name)

        if ret == -1:
            print(f'Return Fail')
            return JsonResponse(
                {
                    "url": '/interviews/list/recfail',
                    "success": True,
                }
            )
        rget_data = json.dumps(get_data, ensure_ascii=False)
        rgroup_sent = json.dumps(group_sent, ensure_ascii=False)
        rsentimental = json.dumps(sentimental, ensure_ascii=False)
        speakers = json.dumps(speakers, ensure_ascii=False)



        Interviews.objects.filter(pk=intv.pk).update(content=rget_data, content_div=rgroup_sent,
                                  sentimental=rsentimental, client_name='고객미정', client=clt, author=pauthor, speakers=speakers)

        #print(f'Record Interview Created:{intv.pk}')

        #messages.success(request, "Audio recording successfully added!")
        return JsonResponse(
            {
                "url": '/interviews',
                "success": True,
            }
        )
        '''
        return render(
            request,
            'interviews/interviews_clientlist.html',
            {
                'interviews_list': Interviews.objects.all(),
                'clients_list': Client.objects.all(),
                'client_unknown': Interviews.objects.filter(client_name='고객미정').order_by('-created_at'),
                'manager': Manager.objects.get(mid=request.user),
                'pw_result': intv.pk
            }
        )
        '''




def summary_ready(request, pk):
    interviews = Interviews.objects.get(pk=pk)
    res = Manager.objects.filter(mid=request.user).get()
    if interviews.summary != "":
        return redirect(f'/interviews/summary/{pk}/exist/')  # exist
    else:
        #return redirect(f'/interviews/summary/{pk}/b/')  # exist
        return render(
            request,
            'interviews/interviews_summary_ready.html',
            {
                'interviews': interviews,
                'clients_list': Client.objects.filter(counselor=request.user),
                'client_unknown': Interviews.objects.filter(client_name='고객미정', author=res),
                'client_info': interviews.client,
                'manager': res,
            }
        )


def summary(request, pk, stype):
    nlp = Okt()
    intv = Interviews.objects.get(pk=pk)
    # 불용어 처리
    with open("./interviews/stopwords_korean.txt", "rt", encoding="utf-8") as f:
        lines = f.readlines()

    # txt 읽을 때 \n표시를 제거
    stop_words = []
    for line in lines:
        line = line.replace('\n', '')
        stop_words.append(line)

    if stype != 'exist':
        timestr = datetime.now().strftime('%Y%m%d-%H-%M-%S')

        if stype == 'a':
            with open(intv.content, 'rb') as sent_file:
                rdata = sent_file.read()
                sent_data = dec(cyp_key, aad, nonce, rdata, intv.gd_cmk)
            sent_data = binary_to_dict(sent_data)
            sum_sentence = summary_type_a(sent_data)

        elif stype == 'b':
            with open(intv.content_div, 'rb') as sent_file:
                rdata = sent_file.read()
                sent_data = dec(cyp_key, aad, nonce, rdata, intv.gs_cmk)
            sent_data = binary_to_dict(sent_data)
            sum_sentence = summary_type_b(sent_data, intv.stt_lang)

        for key, value in sum_sentence.items():

            for i, document in enumerate(value):
                clean_words = []
                for word in word_tokenize(document):
                    if word not in stop_words:  # 불용어 제거
                        clean_words.append(word)
                #print(f"Clean words::{clean_words}")
                sum_sentence[key][i] = ' '.join(clean_words)


        wstr = intv.object_path #file_upload.path
        wstr = wstr[0:wstr.rfind('/')+1]
        wstr = wstr.replace('/','\\')
        wstr = wstr.replace('data','',1)
        tpath = MEDIA_ROOT + wstr



        smrpath = tpath + "Smry_data_" + timestr + ".faj"

        try:
            smr_cyp, smr_mac = enc(cyp_key, aad, nonce, dict_to_binary(sum_sentence))
        except Exception as e:
            print(f"SummaryCypher Error Message::{e}")

        try:
            with open(smrpath, 'wb') as outfile:
                outfile.write(smr_cyp)
        except Exception as e:
            print(f"Summary JSON File Gen Error Message::{e}")

        Interviews.objects.filter(pk=pk).update(summary=smrpath, smr_cmk=smr_mac)

    interviews = Interviews.objects.get(pk=pk)
    res = Manager.objects.filter(mid=request.user).get()

    with open(interviews.summary, 'rb') as sent_file:
        rdata = sent_file.read()
        smry_data = dec(cyp_key, aad, nonce, rdata, interviews.smr_cmk)
    smry_data = smry_data.decode("utf-8")  #binary_to_dict(smry_data)

    return render(
        request,
        'interviews/interviews_summary.html',
        {
            'interviews': interviews,
            'clients_list': Client.objects.filter(counselor=request.user),
            'client_unknown': Interviews.objects.filter(client_name='고객미정', author=res),
            'client_info': intv.client,
            'manager': res,
            'summary': smry_data,
        }
    )

def summary_type_b(scontent, stt_lang):
    #get_data = json.loads(scontent)
    get_data = scontent

    full_sort = []
    full_cnt = 0
    sent_cnt = {}
    sum_sentence={}   #  { '1':["sen1","sen2"], '2':[] }  => mod: { '1': [ { 'sentence':'bdbdbd','sent_no':0}, { 'sentence':'bdbdbd',{'sent_no':2}  ...] , '2':[] }
    csumm = ClovaSummary()
    opti = {'language': 'ko', 'model': 'general', 'tone': 2, 'summaryCount': 2}

    summary1 = {'full': []}

    for sent in get_data :
        slabel=sent['speaker']
        tsent ={}

        if slabel not in sum_sentence:
            sum_sentence[slabel] = []
            sent_cnt[slabel] = 0
            #sum_sentence[slabel].append(sent['sentence'])
            tsent['sentence'] = sent['sentence']
            tsent['sent_no'] = sent['sent_no']
            #sum_sentence[slabel].append(tsent)
            sum_sentence[slabel].append({})
            sum_sentence[slabel][len(sum_sentence[slabel])-1] = copy.deepcopy(tsent)
            #full_sort.append(tsent)
            full_sort.append({})
            full_sort[len(full_sort) - 1] = copy.deepcopy(tsent)
        else:
            if sum_sentence[slabel][sent_cnt[slabel]]['sent_no'] == sent['sent_no'] :
                temp1 = sum_sentence[slabel][sent_cnt[slabel]]['sentence'] + ' ' + sent['sentence']
                if len(temp1) < 1900:
                    sum_sentence[slabel][sent_cnt[slabel]]['sentence'] = temp1
                temp2 = full_sort[full_cnt]['sentence'] + ' ' + sent['sentence']
                if len(temp2) < 1900:
                    full_sort[full_cnt]['sentence'] = temp2
            else:
                tsent['sentence'] = sent['sentence']
                tsent['sent_no'] = sent['sent_no']
                #sum_sentence[slabel].append(tsent)
                sum_sentence[slabel].append({})
                sum_sentence[slabel][len(sum_sentence[slabel]) - 1] = copy.deepcopy(tsent)
                #full_sort.append(tsent)
                full_sort.append({})
                full_sort[len(full_sort) - 1] = copy.deepcopy(tsent)
                sent_cnt[slabel] = sent_cnt[slabel] + 1
                full_cnt = full_cnt + 1
        #print(f"ExtSent: {sum_sentence}")

    for spart in sum_sentence:
        sum_sentence[spart] = sorted(sum_sentence[spart], key=lambda sent: len(sent['sentence']), reverse=True)
        if len(sum_sentence[spart]) < 2:
            summary1[spart] = []
            #summary1[spart].append("[요약에 적합하지 않은 문장입니다.]" )
            summary1[spart].append(sum_sentence[spart][0]['sentence'])
            continue

        sen_len = len(sum_sentence[spart])//10
        if sen_len <= 1:
            sen_len = 1
        sum_sentence[spart] = sum_sentence[spart][0:sen_len]
        sum_sentence[spart] = sorted(sum_sentence[spart], key=lambda sent: sent['sent_no'], reverse=False)
        #print(f"Sentence::{spart}::{sum_sentence[spart]}")

        for i in range(sen_len):
            docum = {'content': ''}
            docum['content'] = sum_sentence[spart][i]['sentence'].replace('\n', '')
            summary = ""


            if stt_lang == 'ko-KR':

                try:
                    res2 = csumm.req_url(document=docum, option=opti)
                    smm_data = json.loads(res2.text)
                    summary = smm_data['summary']
                except Exception as e:
                    if smm_data['error']['errorCode'] == "E100":  # "Insufficient valid sentence"
                        summary = docum['content']+'[E1]'
                    else:
                        summary = docum['content']+'[E2]'

            elif stt_lang == 'en-US':
                nlp = spacy.load("en_core_web_sm")
                nlp.add_pipe("textrank");
                doc = nlp(docum['content'])
                tr = doc._.textrank
                for sent in tr.summary(limit_phrases=15, limit_sentences=2):
                    summary = summary + str(sent) + ' '


            if i == 0:
                summary1[spart] = []
                summary1[spart].append(summary)
                #summary1[spart].append(smm_data['summary'])
            else:
                summary1[spart].append(summary)
                #summary1[spart].append(smm_data['summary'])



    if len(full_sort) < 2:
        #summary1['full'].append("[요약에 적합하지 않은 문장입니다.]")
        summary1['full'].append(full_sort[0]['sentence'])
        return summary1
    #full_sort = sorted(get_data, key=lambda sent: len(sent['sentence']), reverse=True)
    full_sort = sorted(full_sort, key=lambda sent: len(sent['sentence']), reverse=True)

    sen_len = len(full_sort)//10
    if sen_len <= 1:
        sen_len = 1
    # print(f"LengthSentence:{sen_len},,TenPercent:{sen_len//10}")
    full_sort = full_sort[0:sen_len]
    full_sort = sorted(full_sort, key=lambda sent: sent['sent_no'], reverse=False)


    for i in range(sen_len):
        docum = {'content': ''}

        docum['content'] = full_sort[i]['sentence'].replace('\n', '')
        summary = ""
        if stt_lang == 'ko-KR':
            try:
                res2 = csumm.req_url(document=docum, option=opti)
                smm_data = json.loads(res2.text)
                summary = smm_data['summary']
            except Exception as e:
                if smm_data['error']['errorCode'] == "E100":  # "Insufficient valid sentence"
                    summary = docum['content']+'[E1]'
                else:
                    summary = docum['content']+'[E2]'
        elif stt_lang == 'en-US':
            nlp = spacy.load("en_core_web_sm")
            nlp.add_pipe("textrank");
            doc = nlp(docum['content'])
            tr = doc._.textrank
            for sent in tr.summary(limit_phrases=15, limit_sentences=2):
                summary = summary + str(sent) + ' '

        summary1['full'].append(summary)

    return summary1


def summary_type_a(scontent):
    #get_data = json.loads(scontent)
    get_data = scontent

    seg_len = len(get_data['segments'])
    temp_cont = {'full': ''}  # to check the size limit of 2000 character
    wdcnt = {'full': 0}
    cont4s = {'full': []}  # content aggregate in one paragraph for summary
    summa = {}
    temp_cont = {'full': ''}  # to check the size limit of 2000 character

    csumm = ClovaSummary()

    for i in range(seg_len):
        cur_text = get_data['segments'][i]['text']
        speaker = get_data['segments'][i]['speaker']['label']
        if speaker in temp_cont:
            wdcnt[speaker] = wdcnt[speaker] + len(cur_text)
            if wdcnt[speaker] < 1900:
                temp_cont[speaker] = temp_cont[speaker] + cur_text
            else:
                cont4s[speaker].append(temp_cont[speaker])
                temp_cont[speaker] = cur_text
                wdcnt[speaker] = len(cur_text)
        else:
            cont4s[speaker] = []
            wdcnt[speaker] = len(cur_text)
            temp_cont[speaker] = cur_text

        wdcnt['full'] = wdcnt['full'] + len(cur_text)
        if wdcnt['full'] < 1900:
            temp_cont['full'] = temp_cont['full'] + cur_text
        else:
            cont4s['full'].append(temp_cont['full'])
            temp_cont['full'] = cur_text
            wdcnt['full'] = len(cur_text)

    # for문 종료 후 남아있는 마지막 문장 저장
    for key, value in temp_cont.items():
        cont4s[key].append(value)

    opti = {'language': 'ko', 'model': 'general', 'tone': 3, 'summaryCount': 3}
    for key, value in cont4s.items():

        if value and len(value) >= 50:  # 글자수가 50글자 이상인 문장만 요약

            # Naver Summary
            docum = {'content': ''}

            temp_summ = value

            for raw_senten in temp_summ:
                docum['content'] = raw_senten.replace('\n', '')
                res2 = csumm.req_url(document=docum, option=opti)
                smm_data = json.loads(res2.text)
                if key not in summa:
                    summa[key] = ''
                try:
                    # if len(summa[key]+smm_data['summary'])<=2000 :
                    summa[key] = summa[key] + smm_data['summary'] + '\n'
                except KeyError:
                    if smm_data['error']['errorCode'] == "E100":  # "Insufficient valid sentence"
                        summa[key] = summa[key] + cont4s[key][0]
                    #else:
                    #    summa[key] = summa[key] + cont4s[key][0] + ' [' + smm_data['error'][
                    #        'errorCode'] + ']' + '\n'

        else:
            summa[key] = cont4s[key][0]  # 'Too Short sentence'
    return summa

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

def code_generate(request):
    #length_of_string = 8
    #rstr=''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length_of_string))
    if request.method == 'POST':
        code_generate = request.POST['code_generate']
        interview_id = request.POST['interview_id']
        #print(f"Generate Code:: {code_generate}== Interview_ID::{interview_id}")
        CodeShare.objects.create(mid=request.user, code=code_generate,
                                 interview_obj=Interviews.objects.get(pk=interview_id),
                                 expire_at=datetime.now()+ timedelta(weeks=1))
    return redirect(f'/interviews/list/norm')


def code_regist(request):
    msg = 'default'

    if request.method == 'POST':
        code_regist = request.POST['code_regist']
        #print(f"Regist Code:: {code_regist}")

        try:
            cs_obj = CodeShare.objects.get(code=code_regist)
        except ObjectDoesNotExist:
            cs_obj = None
            print("Regist Code Not Exist")
            msg = "misspell"
            return HttpResponse(msg)

        if datetime.now() > cs_obj.expire_at:
            #print("Regist Code Expired!!")
            msg = "expiredcode"

        else:
            msg = "none"
            interviews = cs_obj.interview_obj
            #print(f"Client:{interviews.client_name}")
            try:
                clt = Client.objects.filter(name="고객미정", counselor=request.user).get()
                print(f"Find client::{clt.name}")
            except ObjectDoesNotExist:
            #except Exception as e:
            #    print(f"Except :: {e}")
                clt = Client.objects.create(name=interviews.client_name, counselor=request.user)

            head, tail = os.path.split(interviews.content)
            cp_con = head+"/\CP_"+tail
            shutil.copyfile(interviews.content, cp_con)
            head, tail = os.path.split(interviews.content_div)
            cp_cdiv = head+"/\CP_"+tail
            shutil.copyfile(interviews.content_div, cp_cdiv)
            cp_summ = ''
            if interviews.summary != '':
                head, tail = os.path.split(interviews.summary)
                cp_summ = head + "/\CP_" + tail
                shutil.copyfile(interviews.summary, cp_summ)
            head, tail = os.path.split(interviews.sentimental)
            cp_senti = head+"/\CP_"+tail
            shutil.copyfile(interviews.sentimental, cp_senti)

            Interviews.objects.create(title=interviews.title, content=cp_con, content_div=cp_cdiv,
                                      duration=interviews.duration, summary=cp_summ, sentimental=cp_senti,
                                      created_at=interviews.created_at, file_upload=interviews.file_upload,
                                      nums_speaker=interviews.nums_speaker, client_name="고객미정", #interviews.client_name,
                                      client=clt, quiet_basis=interviews.quiet_basis, client_comment=clt.comment,#client_comment=interviews.client_comment,
                                      author=Manager.objects.get(mid=request.user), share_flag="true",
                                      gd_cmk=interviews.gd_cmk, gs_cmk=interviews.gs_cmk,
                                      sm_cmk=interviews.sm_cmk, smr_cmk=interviews.smr_cmk, speakers=interviews.speakers,
                                      confidence=interviews.confidence, object_path=interviews.object_path)

    return HttpResponse(msg)
    #return HttpResponse(json.dumps({'message': msg}), content_type="application/json")
    #return redirect(f'/interviews/list/{msg}/')


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
        #print(f"Document::{ccomment}")
            #clt = Client.objects.filter(pk=form.cleaned_data['pk']).update(comment=ccomment)
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


def verbatim(request, pk, doc_type, quiet_basis):
    Interviews.objects.filter(pk=pk).update(quiet_basis=quiet_basis)
    intv = Interviews.objects.get(pk=pk)
    #iverb = json.loads(intv.content_div)
    wstr = intv.content #file_upload.path
    wstr = wstr[wstr.find('interviews')-1:wstr.rfind('\\')+1]
    #wstr = wstr.replace('data','',1)
    upath = wstr.replace('\\','/')
    upath = f"/media{upath}"
    #wstr = wstr.replace('/','\\')

    #wstr = wstr[0:wstr.rfind('\\')+1]
    tpath = MEDIA_ROOT + wstr      

    fname = ''
    #timestr = datetime.now().strftime('%Y-%m-%d-%H+%M+%S')
    fname = f"Verbatim_{intv.title}"    

    with open(intv.content_div, 'rb') as sent_file:
        rdata = sent_file.read()
        sent_data = dec(cyp_key, aad, nonce, rdata, intv.gs_cmk)
    iverb = binary_to_dict(sent_data)

    if doc_type == 'hwp':
        fname = hwp_gen(iverb, int(quiet_basis),tpath, fname);
    elif doc_type == 'doc':
        fname = doc_gen(iverb, int(quiet_basis), tpath, fname);
    return render(
        request,
        'interviews/verbatim_down.html',
        {
            'vfile': upath+fname,
            'interview_pk': pk
        }
    )

def set_col_widths(table):
    widths = (Inches(1.5), Inches(6))
    for row in table.rows:
        for idx, width in enumerate(widths):
            row.cells[idx].width = width

def doc_gen(iverb, quiet_basis, tpath, fname):
    #doc = Document()
  
    timestr = datetime.now().strftime('%Y%m%d-%H-%M-%S')
    file_name = f"{fname}.docx"
    #out_file =f"{MEDIA_ROOT}\interviews\hwp\{fname}"    
    out_file = f"{tpath}{file_name}"
    shutil.copyfile(f"{MEDIA_ROOT}\interviews\hwp\Verbatim_form.docx", out_file)

    doc = Document(out_file)
    #p = doc.add_paragraph('축어록')
    #p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    #para = doc.paragraphs[0].runs
    #for run in para:
    #    run.font.size = Pt(20)

    table = doc.add_table(rows= 1, cols= 2)
    table.style = doc.styles['Table Grid']

    row_cells = table.rows[0].cells
    row_cells[0].text = '화자'
    row_cells[1].text = '발언내용'
    prev_spker = 'tbfirst'
    vsent = ' '
    for vcont in iverb:
        if prev_spker != vcont['name']:
            if prev_spker == 'tbfirst':
                vsent = vsent + vcont['sentence']
            else:
                row_cells[1].text = vsent
            row_cells = table.add_row().cells
            row_cells[0].text = f"""{vcont['name']}{ vcont['sent_no']:0>3}"""
            vsent = ' '
        if quiet_basis != 0 and vcont['quiet_time'] >= quiet_basis:
            vsent = vsent + '(침묵' + str(vcont['quiet_time']) + '초) '

        vsent = vsent + vcont['sentence']
        #row_data[1].text = vsent

        prev_spker = vcont['name']

    row_cells[1].text = vsent

    set_col_widths(table)
    #for cell in table.columns[0].cells:
    #    cell.width = Inches(1.0)

    doc.save(out_file)
    return file_name


def hwp_gen(iverb, quiet_basis, tpath, fname):
    timestr = datetime.now().strftime('%Y%m%d-%H-%M-%S')
    pythoncom.CoInitialize()  # 추가) com 라이브러리 초기화하기
    #file_name = "Verbatim_" + timestr + ".hwp"
    file_name = f"{fname}.hwp"
    #out_file =f"{MEDIA_ROOT}\interviews\hwp\{fname}"
    out_file = f"{tpath}{file_name}"
    shutil.copyfile(f"{MEDIA_ROOT}\interviews\hwp\Verbatim_form.hwp", out_file)
    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
    hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    hwp.Open(out_file)
    row = len(iverb)+2
    col = 2
    hwp.HAction.GetDefault("TableCreate", hwp.HParameterSet.HTableCreation.HSet)

    hwp.HParameterSet.HTableCreation.Rows = row
    hwp.HParameterSet.HTableCreation.Cols = col
    hwp.HParameterSet.HTableCreation.WidthType = 0
    hwp.HParameterSet.HTableCreation.HeightType = 0
    hwp.HParameterSet.HTableCreation.WidthValue = hwp.MiliToHwpUnit(148.0)
    hwp.HParameterSet.HTableCreation.CreateItemArray("ColWidth",col)
    hwp.HParameterSet.HTableCreation.ColWidth.SetItem(0, hwp.MiliToHwpUnit(15))
    hwp.HParameterSet.HTableCreation.ColWidth.SetItem(1, hwp.MiliToHwpUnit(124))   #110+15
    #hwp.HParameterSet.HTableCreation.ColWidth.SetItem(2, hwp.MiliToHwpUnit(15))
    hwp.HParameterSet.HTableCreation.CreateItemArray("RowHeight", row)

    hwp.HAction.Execute("TableCreate", hwp.HParameterSet.HTableCreation.HSet)

    vi = 0
    hwp.HParameterSet.HInsertText.Text = "화자"
    hwp.HAction.Execute("InsertText", hwp.HParameterSet.HInsertText.HSet)
    hwp.Run("MoveRight")
    hwp.HParameterSet.HInsertText.Text ="발언내용"
    hwp.HAction.Execute("InsertText", hwp.HParameterSet.HInsertText.HSet)
    hwp.Run("MoveRight")
    #hwp.HParameterSet.HInsertText.Text = "감정"
    #hwp.HAction.Execute("InsertText", hwp.HParameterSet.HInsertText.HSet)
    #hwp.Run("MoveRight")
    prev_spker = 'none'
    for vcont in iverb:
        if prev_spker != vcont['name']:
            if (vi != 0):
                hwp.Run("MoveRight")
            hwp.HParameterSet.HInsertText.Text = f"""{vcont['name']}{ vcont['sent_no']:0>3}"""
            hwp.HAction.Execute("InsertText", hwp.HParameterSet.HInsertText.HSet)
            hwp.Run("MoveRight")
        vsent = ' '
        if quiet_basis != 0 and vcont['quiet_time'] >= quiet_basis:
            vsent = vsent + '(침묵' + str(vcont['quiet_time']) + '초) '
            hwp.HParameterSet.HInsertText.Text = vcont['sentence']
        vsent = vsent + vcont['sentence']
        hwp.HParameterSet.HInsertText.Text = vsent
        hwp.HAction.Execute("InsertText", hwp.HParameterSet.HInsertText.HSet)

        #hwp.HParameterSet.HInsertText.Text= vcont['senti']
        #hwp.HAction.Execute("InsertText", hwp.HParameterSet.HInsertText.HSet)
        #hwp.Run("MoveRight")
        vi = vi + 1
        prev_spker = vcont['name']
    hwp.Save()
    hwp.Quit()
    pythoncom.CoUninitialize()  # 추가) 종료하기
    #return redirect(f'/media/interviews/hwp/{fname}')
    return file_name


def verbatim0(request, pk):
    intv = Interviews.objects.get(pk=pk)
    iverb = json.loads(intv.content_div)
    timestr = datetime.now().strftime('%Y%m%d-%H-%M-%S')
    pythoncom.CoInitialize()  # 추가) com 라이브러리 초기화하기
    fname = "Verbatim_" + timestr + ".hwp"
    out_file =f"{MEDIA_ROOT}\interviews\hwp\{fname}"
    shutil.copyfile(f"{MEDIA_ROOT}\interviews\hwp\Verbatim_form.hwp", out_file)
    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
    hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    hwp.Open(out_file)
    vi = 0
    for vcont in iverb:
        hwp.PutFieldText(f"Speaker{{{{{vi}}}}}", f"""{vcont['name']}{ vcont['sent_no']}""")
        hwp.PutFieldText(f"Contents{{{{{vi}}}}}", vcont['sentence'])
        hwp.PutFieldText(f"Sentiment{{{{{vi}}}}}", vcont['senti'])
        vi = vi + 1
    hwp.Save()
    hwp.Quit()
    pythoncom.CoUninitialize()  # 추가) 종료하기
    #return redirect(f'/interviews/{pk}/')
    return redirect(f'/media/interviews/hwp/{fname}')

def report(request, pk, label):
    itv = Interviews.objects.get(pk=pk)

    with open(itv.summary, 'rb') as sent_file:
        rdata = sent_file.read()
        sent_data = dec(cyp_key, aad, nonce, rdata, itv.smr_cmk)
    isumm = binary_to_dict(sent_data)

    #isumm = json.loads(itv.summary)
    timestr = datetime.now().strftime('%Y%m%d-%H-%M-%S')

    pythoncom.CoInitialize()  # 추가) com 라이브러리 초기화하기

    if label!='full':
        speakers = json.loads(itv.speakers)
        sindex = next((index for (index, d) in enumerate(speakers) if d["label"] == label), None)
        sname = speakers[sindex]["name"] 
    else:
        sname = 'full'

    #fname = "report_" + timestr + ".hwp"
    #fname = f"Report_{itv.title}_{label}.hwp"
    fname = f"Report_{itv.title}_{sname}.hwp"
    wstr = itv.content #file_upload.path
    wstr = wstr[wstr.find('interviews')-1:wstr.rfind('\\')+1]
    ustr = wstr.replace('\\','/')

    out_file =f"{MEDIA_ROOT}{wstr}{fname}"
    shutil.copyfile(MEDIA_ROOT + "\interviews\hwp\interview_form.hwp", out_file)
    
    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
    hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    hwp.Open(out_file)
    field_list = [i for i in hwp.GetFieldList().split("\x02")]  # 누름틀 불러오기
    hwp.MovePos(2)  # 처음 으로 이동하기
    sent_all = ''

    #for sent in isumm['full']:
    for sent in isumm[label]:
        sent_all = sent_all + sent + ' '
    for field in field_list:
        if field == "InterviewSummary":
            # hwp.PutFieldText(f'{field}{{{{{0}}}}}', "한글에 요약문을 삽입하는 코드 테스트 입니다.")
            hwp.PutFieldText(f'{field}', sent_all)
        elif field == "InterviewTitle":
            hwp.PutFieldText(f'{field}', itv.title)
    hwp.Save()
    hwp.Quit()
    pythoncom.CoUninitialize()  # 추가) 종료하기
    #return redirect(f'/interviews/{pk}/')
    #return redirect(f'/media/interviews/hwp/{fname}')

    
    return redirect(f'/media{ustr}{fname}')

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

def activate_account(request, hash):
    account = get_account_from_hash(hash)
    if not account.is_active:
        account.activate()
        account.save()
        user = account.user
        login(request, user)


def pay_cancel(request):
    cuser = request.user
    
    if request.method == 'POST':  
        coupon = request.POST.get['cancel_coupon'] 
        reason = request.POST.get['cancel_reason']
        #reason = "고객변심"
        purchase = Purchase.objects.get(code=coupon)
        pkey =  purchase.paymentKey #request.POST.get['paymentKey']
        cancelAmount = 0

        if purchase.amount== 60:
            cancelAmount = 5500 * purchase.coupon_count
        elif purchase.amount == 240:
            cancelAmount = 4*4950 * purchase.coupon_count
        elif purchase.amount == 600:
            cancelAmount = 10*4400 * purchase.coupon_count
        elif purchase.amount == 1:
            cancelAmount =  100 * purchase.coupon_count            
        
        #print(f"Request Cancel Amount: {cancelAmount}")
        invoke_url = 'https://api.tosspayments.com/v1/payments/'
        # length_of_string = 8
        # rstr=''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length_of_string))
        request_body = {
            'cancelReason': reason,
            'cancelAmount' : cancelAmount,
        }

        headers = {
            'Authorization': 'Basic dGVzdF9za19CRTkyTEFhNVBWYkoxUjZiWkRXVjdZbXBYeUpqOg==',
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
        

        #for purch in plist:
        #    Purchase.objects.filter(pk=purch.pk).update(usable='true')

        return render(
            request,
            'interviews/paysuccess.html',
            {
                #'orderName': pay_data.orderName,
                'orderAmount': pay_data['totalAmount'],
            }
        )


def pay_success(request):
    if request.method == 'GET':
        oid = request.GET['orderId']      
        pkey = request.GET['paymentKey']
        amt = request.GET['amount']
        mgr = Manager.objects.filter(mid=request.user).get()
        

        paid_time = mgr.paid_time
        max_time = mgr.max_time
        expire_at = mgr.expire_at
        plist = Purchase.objects.filter(orderID=oid) #orderID 주문 금액의 합계가 amount 와 같은지 비교 
        owner = User.objects.get(pk=plist[0].owner_id)
        sum = 0
        sumTime = 0
        msg =''   
        for purch in plist:
            if purch.amount== 60:
                sum = sum + 5500 * purch.coupon_count
                msg += '[1시간권]'
            elif purch.amount == 240:
                sum = sum + 4*4950 * purch.coupon_count
                msg += '[4시간권]'
            elif purch.amount == 600:
                sum = sum + 10*4400 * purch.coupon_count
                msg += '[10시간권]'
            elif purch.amount == 1:
                sum = sum + 100 * purch.coupon_count
                msg += '[1분권]'              
        if str(sum) != amt:
            print(f"Total Price is incorrect!! sum={sum}, amount ={amt}")
            return redirect('/interviews/purchase/request')            
        
        msg += f", {sum}원, {owner.username}"

        invoke_url = 'https://api.tosspayments.com/v1/payments/'
        # length_of_string = 8
        # rstr=''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length_of_string))
        request_body = {
            'orderId': oid,
            'amount' : amt,
        }

        # Take environment variables from .env file
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
        #print(f"Secret key: {sec_key}")
        headers = {
            #'Authorization': 'Basic dGVzdF9za19CRTkyTEFhNVBWYkoxUjZiWkRXVjdZbXBYeUpqOg==',
            #'Authorization': 'Basic base64("test_sk_jZ61JOxRQVEEggz5JL0VW0X9bAqw:")',
            'Authorization': secret_key,
            'Content-Type': 'application/json;UTF-8',
        }
        try:
            res= requests.post(headers=headers,
                                 url=invoke_url + pkey,
                                 data=json.dumps(request_body).encode('UTF-8'))

            pay_data = res.json() #json.loads(res)
            #print(f"PayResponse::: {pay_data}")
        except Exception as e:
            print(f"Order Ack Error::{e}")
            return redirect('/interviews/purchase/request')
        
        for purch in plist:
            user_list = json.loads(purch.user_list)
            user_list.append(request.user.username)
            used_count = 1            
            
            if purch.type == 'months':
                max_time = purch.amount * purch.coupon_count
                expire_at = date.today() + timedelta(days=31)
            elif purch.type == 'hours':
                sumTime = sumTime + (purch.amount * purch.coupon_count)
            
            Purchase.objects.filter(pk=purch.pk).update(user_list=json.dumps(user_list, ensure_ascii=False), used_count=used_count, paymentKey=pkey, usable='true')
        
        paid_time = paid_time + sumTime
        Manager.objects.filter(mid=request.user).update(max_time= max_time, paid_time= paid_time, expire_at= expire_at)
            
        mgr = Manager.objects.filter(mid=request.user).get()

        bot = telegram.Bot(token='1631327665:AAEX8hykT_WuTjQXWYnxigN1jM1WBqHAip4')
        bot.sendMessage(chat_id=-1001681320740, text=msg)

        return render(
            request,
            'interviews/paysuccess.html',
            {
                #'orderName': pay_data.orderName,
                'addTime' : sumTime,
                'message' : 'success',
                'manager' : mgr,                
                'orderAmount': pay_data['totalAmount'],

            }
        )


def nologin(request, id):
    logout(request)
    try:
        ruser = User.objects.get(username=id)
    except ObjectDoesNotExist:
        return redirect('/interviews/list/norm')

    cuser = authenticate(username=ruser.username, password='finger.ai2021')
    #cuser = get_user_from_hash(ruser.password)

    #cuser = request.user

    if cuser is not None:
        #request.user = ruser
        login(request, cuser)
        try:
            res = Manager.objects.get(mid=ruser)
        except ObjectDoesNotExist:
            #res = Manager.objects.create(mid=request.user, use_time=0, max_time=300)   # 300 minutes
            res = Manager.objects.create(mid=ruser, use_time=0, max_time=0, paid_time=60)  # 300 minutes

        if date.today() >= res.expire_at:
            Manager.objects.filter(mid=ruser).update(use_time=0, max_time=0)

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
        ret, pauthor, get_data, group_sent, timestr, sentimental, intv_duration, speakers, all_confidence = InterviewAnalysis(cuser, speaker_nums, intv.file_upload.name, stt_lang)

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

            with open(idata.content, 'rb') as sent_file:
                rdata = sent_file.read()
                get_data = dec(cyp_key, aad, nonce, rdata, idata.gd_cmk)
                get_data = get_data.decode("utf-8")
            with open(idata.content_div, 'rb') as sent_file:
                rdata = sent_file.read()
                div_data = dec(cyp_key, aad, nonce, rdata, idata.gs_cmk)
                div_data = div_data.decode("utf-8")
        except Exception as e:
            print(f"Interv Detail Open Error::{e}")

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
    fields = ['title', 'client_name', 'file_upload', 'nums_speaker', 'stt_lang']
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

        ret, pauthor, get_data, group_sent, timestr, sentimental, intv_duration, speakers, all_confidence = \
            InterviewAnalysis(cuser, form.instance.nums_speaker, form.instance.file_upload.name, form.instance.stt_lang)

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

        speakers = json.dumps(speakers).replace('false', r'"false"').replace('true', r'"true"')

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
            
            with open(f"./sample_data_{key}.txt", "w") as f:
                f.write(cc)

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


    #intv_duration = get_data['segments'][seg_len-1]['end']
    intv_duration = get_data['segments'][-1]['end']
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

    #rget_data = json.dumps(get_data, ensure_ascii=False)
    #rgroup_sent = json.dumps(group_sent, ensure_ascii=False)
    #rsentimental = json.dumps(sentimental, ensure_ascii=False)

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

    
