#from django.core.urlresolvers import reverse
from django import forms
from django.urls import reverse
from django.utils.translation import ugettext as _

from allauth.account.forms import LoginForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from .models import Client, Purchase
from django.utils.translation import gettext_lazy as _

'''
class PurchaseForm(ModelForm):
    class Meta:
        model = Purchase
        fields = ['type', 'amount', 'user_count']
        labels = {
            'type': _('구매유형'),
            'amount': _('구매수량'),
            'user_count': _('사용자수'),
        }
'''

class ClientForm_v2(forms.Form):
    class Meta:
        model = Client
        fields = ('name', 'phone', 'mail', 'password', 'comment')
        password = forms.CharField(widget=forms.PasswordInput)
        comment = forms.CharField(max_length=1000, widget=forms.Textarea)
        '''
        widgets = {
            'comment': forms.Textarea,
            'password': forms.PasswordInput(),
        }
        '''

class ClientForm(forms.Form):
    name = forms.CharField(max_length=50)
    mail = forms.CharField(max_length=50)
    phone = forms.CharField(max_length=50)
    comment = forms.CharField(max_length=1000, widget=forms.Textarea)
    pk = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput, max_length=50)


class MyCustomLoginForm(LoginForm):

    def __init__(self, *args, **kwargs):
        super(MyCustomLoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        # Add magic stuff to redirect back.
        self.helper.layout.append(
            HTML(
              #  "<form class ='login' method='POST' action='{% url 'account_login' %}' >"
                "{% csrf_token %}"
              #  "{{ form.as_p }}"  # as_table(), as_p(), as_ul()
                "{% if redirect_field_value %}"
                "<input type='hidden' name='{{ redirect_field_name }}'"
                " value='{{ redirect_field_value }}' />"
                "{% endif %}"
            )
        )
        # Add password reset link.
        self.helper.layout.append(
            HTML(
                "<p><a class='button secondaryAction' href={url}>{text}</a></p>".format(
                    url=reverse('account_reset_password'),
                    text=_('Forgot Password?')
                )
            )
        )
        # Add submit button like in original form.
        self.helper.layout.append(
            HTML(
                "<button class='btn btn-primary btn-block' type='submit'>{text}</button>".format(
                    text=_('Sign In')
                )
            )
        )

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-xs-2 hide'
        self.helper.field_class = 'col-xs-4'     #8

''' 
    def login(self, *args, **kwargs):
        self.helper = FormHelper(self)
        # Add magic stuff to redirect back.
        self.helper.layout.append(
            HTML(
              #  "<form class ='login' method='POST' action='{% url 'account_login' %}' >"
              #  "{% csrf_token %}"
              #  "{{form.as_p}}"
                "{% if redirect_field_value %}"
                "<input type='hidden' name='{{ redirect_field_name }}'"
                " value='{{ redirect_field_value }}' />"
                "{% endif %}"
            )
        )
        # Add password reset link.
        self.helper.layout.append(
            HTML(
                "<p><a class='button secondaryAction' href={url}>{text}</a></p>".format(
                  #  url=reverse('account_reset_password'),
                    url=_('account_reset_password'),
                    text=_('Forgot Password?')
                )
            )
        )
        # Add submit button like in original form.
        self.helper.layout.append(
            HTML(
                '<button class="btn btn-primary btn-block" type="submit">'
                '%s</button>' % _('Sign In')
            )
        )

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-xs-2 hide'
        self.helper.field_class = 'col-xs-4'
        return super(MyCustomLoginForm, self).login(*args, **kwargs)
'''