from django import forms
from rango.models import Page,Category
from rango.models import UserProfile
from django.contrib.auth.models import User

class CategoryForm(forms.ModelForm):
    name = forms.CharField(max_length=128,help_text="Please enter the category name")
    views = forms.IntegerField(widget=forms.HiddenInput(),initial=0)
    likes = forms.IntegerField(widget=forms.HiddenInput(),initial=0)

    #Inline Class for additionak info of the form
    class Meta:
        model = Category


class PageForm(forms.ModelForm):
    title = forms.CharField(max_length=128,help_text="Please enter the Page name")
    url = forms.URLField(max_length=200,help_text="Please enter the URL of the Page")
    views = forms.IntegerField(widget=forms.HiddenInput(),initial=0)

    def clean(self):
        cleaned_data = self.cleaned_data
        url = cleaned_data.get('url')

        # If url is not empty and doesn't start with 'http://', prepend 'http://'.
        if url and not url.startswith('http://'):
            url = 'http://' + url
            cleaned_data['url'] = url

        return cleaned_data
    class Meta:
        #Asociation of the model that the form is going to
        model = Page

        # What fields do we want to include in our form?
        # This way we don't need every field in the model present.
        # Some fields may allow NULL values, so we may not want to include them...
        # Here, we are hiding the foreign key.
        fields = ('title', 'url', 'views')

class UserForm(forms.ModelForm):
    username = forms.CharField(help_text="Please enter a username.")
    email = forms.CharField(help_text="Please enter your email.")
    password = forms.CharField(widget=forms.PasswordInput(), help_text="Please enter a password.")

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

class UserProfileForm(forms.ModelForm):
    website = forms.URLField(help_text="Please enter your website.", required=False)
    picture = forms.ImageField(help_text="Select a profile image to upload.", required=False)
    class Meta:
        model = UserProfile
        fields = ('website', 'picture')

class LoginForm(forms.Form):
    username = forms.CharField(max_length=123,help_text="UserName:",required=True)
    password = password = forms.CharField(widget=forms.PasswordInput(),required=True,help_text="Password:")

