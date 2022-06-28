from django.db import models
from django.contrib.auth.models import User
import os
import uuid
from datetime import datetime, date, timedelta

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=200, unique=True, allow_unicode=True)

    def __str__(self):
        return self.name

class Manager(models.Model):
    mid = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    use_time = models.IntegerField(blank=True, default=0)
    max_time = models.IntegerField(blank=True, default=0)
    paid_time = models.IntegerField(blank=True, default=0)  #used-max > 0 ==> paid - (used-max)
    accum_time = models.IntegerField(blank=True, default=0) #used를 0으로 reset할때, accum+=used
    expire_at = models.DateField(blank=True,default=date.today() + timedelta(days=31))   # 월단위 구독 만료일자.
    def __str__(self):
        return f'{self.mid}'

class Client(models.Model):
    name = models.CharField(max_length=50)
    mail = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    comment = models.TextField("참조내용", blank=True)
    password = models.CharField(max_length=50, blank=True)
    #counserlor = models.CharField(max_length=50, blank=True)
    counselor = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/interviews/client/{self.pk}/'


class Interviews(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField("상담제목", blank=True, max_length=100)
    confidence = models.IntegerField(blank=True, default=0)

    content = models.TextField("상담내용", blank=True)
    duration = models.IntegerField(blank=True, default=0)
    quiet_basis = models.IntegerField(blank=True, default=0)
    delete_flag = models.CharField(blank=True, default="false", max_length=7)
    share_flag = models.CharField(blank=True, default="false", max_length=7)
    speakers = models.TextField("화자리스트", blank=True, default="")

    content_div = models.TextField("화자별 문장", blank=True)
    summary = models.TextField("요약", blank=True)
    sentimental = models.TextField("감정분석", blank=True)
    created_at = models.DateTimeField("상담날짜", auto_now_add=True)

    #file_upload = models.FileField(upload_to='interviews/files/', blank=True)
    file_upload = models.FileField(upload_to='interviews/files/%Y/%m/%d', blank=True)
    #object_url = models.CharField(blank=True, default="", max_length=192)
    object_path = models.CharField(blank=True, default="", max_length=128)

    hwp_file = models.TextField(blank=True)
    #pdf_file = models.TextField(blank=True)
    stt_lang = models.CharField(default="ko-KR", max_length=16)
    nums_speaker = models.IntegerField(default=2)

    '''
    role_label0 = models.CharField(default="A", max_length=30)
    role_label1 = models.CharField(default="B", max_length=30)
    role_label2 = models.CharField(default="C", max_length=30)
    role_label3 = models.CharField(default="D", max_length=30)
    role_label4 = models.CharField(default="E", max_length=30)
    '''

    client_name = models.CharField("고객이름", blank=True, max_length=30)
    client_comment = models.TextField("참조내용", blank=True)
    client = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL)

    author = models.ForeignKey(Manager, null=True, blank=True, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    gd_cmk = models.BinaryField(default=0x00, blank=True, max_length=64)
    gs_cmk = models.BinaryField(default=0x00, blank=True, max_length=64)
    sm_cmk = models.BinaryField(default=0x00, blank=True, max_length=64)
    smr_cmk = models.BinaryField(default=0x00, blank=True, max_length=64)
    def __str__(self):
        return f'[{self.pk}]{self.title}::{self.author}'

    def get_pk(self):
        return self.pk

    def get_absolute_url(self):
        return f'/interviews/detail/view/{self.pk}/'
        #return f'/update/{self.pk}/'

    def get_file_name(self):
        return os.path.basename(self.file_upload.name)

    def get_file_ext(self):
        return self.get_file_name().split('.')[-1]

    def get_summary_url(self):
        return f'/interviews/summary/{self.pk}/'

    def get_update_url(self):
        return f'/interviews/update/{self.pk}/'

    def get_sentimental_url(self):
        return f'/interviews/sentimental/{self.pk}/'

    def get_wordcloud_url(self):
        return f'/interviews/wordcloud/{self.pk}/'

    def get_document_url(self):
        return f'/interviews/document/{self.pk}/'

class CodeShare(models.Model):
    mid = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    code = models.CharField("공유코드", max_length=20)
    interview_obj = models.ForeignKey(Interviews, null=True, blank=True, on_delete=models.CASCADE)
    expire_at = models.DateTimeField("종료일자", default=date.today() + timedelta(days=7))
    owner_list = models.TextField(blank=True, default='')
    def __str__(self):
        return f'{self.code}'

class Purchase(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    type = models.CharField(blank=True, max_length=20, verbose_name='구매유형')
    amount = models.IntegerField(default=0, verbose_name='구매시간')
    code = models.CharField(default='', max_length=32, verbose_name='쿠폰코드')
    created_at = models.DateField(default=date.today(), blank=True, verbose_name='생성일자')
    expire_at = models.DateField(default=date.today() + timedelta(days=365), blank=True, verbose_name='등록만료일자')
    user_list = models.TextField(default='[]', verbose_name='사용자리스트')
    user_count = models.IntegerField(default=1, verbose_name='그룹인원')
    used_count = models.IntegerField(default=0, verbose_name='사용된인원')
    coupon_count = models.IntegerField(default=1, verbose_name='쿠폰개수')  # 구매시간*쿠폰개수 만큼 시간 충전
    usable = models.CharField(default='false', max_length=10, verbose_name='입금확인')
    paymentKey = models.CharField(default='', max_length=56)
    orderID = models.CharField(default='', max_length=26)

    def get_absolute_url(self):
        return f'/interviews/purchase/list/'

