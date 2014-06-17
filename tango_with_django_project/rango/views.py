from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render,render_to_response
from django.template import RequestContext
from rango.models import Category,Page,UserProfile,User
from rango.forms import CategoryForm,PageForm,UserProfileForm,UserForm,LoginForm
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from datetime import datetime
from rango.bing_search import run_query
from django.shortcuts import redirect

@login_required
def add_page(request,category_name_url):
    context = RequestContext(request)
    category_name = category_name_url.replace('_', ' ')
    if request.method == 'POST':
        print ("POST DETECTED")
        form = PageForm(request.POST)

        if form.is_valid():
            # This time we cannot commit straight away.
            # Not all fields are automatically populated!
            print ("form is valid!")
            page = form.save(commit=False)

            # Retrieve the associated Category object so we can add it.
            # Wrap the code in a try block - check if the category actually exists!
            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                # If we get here, the category does not exist.
                # Go back and render the add category form as a way of saying the category does not exist.
                return render_to_response('rango/add_category.html', {}, context)

            # Also, create a default value for the number of views.
            page.views = 0

            # With this, we can then save our new model instance.
            page.save()

            # Now that the page is saved, display the category instead.
            return category(request, category_name_url)
        else:
            print ("form is Not valid!")
            print form.errors
    else:
        form = PageForm()

    return render_to_response( 'rango/add_page.html',
            {'category_name_url': category_name_url,
             'category_name': category_name, 'form': form},
             context)

@login_required
def add_category(request):
    context = RequestContext(request)

    #An HTTP Post?
    if request.method =='POST':
        form = CategoryForm(request.POST)

        #Verifying if the form is valid
        if form.is_valid():
            #Saving category to database
            form.save(commit=True)
            #Return user to he homepage
            return index(request)
        else:
            print form.errors
    else:
        #If the request was not post, display the form to enter data
        form = CategoryForm()

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render_to_response('rango/add_category.html', {'form': form}, context)

def index (request):
    request.session.set_test_cookie()
    ##Request the context  of the request
    #El context contiene informacion como  detalles la maquina del cliente,
    context = RequestContext(request)


    #Obtaining Categories
    cat_list = Category.objects.order_by('likes')[:5]
    most_viewed = Category.objects.order_by('-views')[:5]


    for category in cat_list:
        category.url = category.name.replace(' ', '_')
    for category in most_viewed:
        category.url = category.name.replace(' ', '_')

    #Se construye un diccionario para pasarlo como el context al template engine
    #Passing categories to context dictionary in order to show it on a template
    context_dict = {'categories':cat_list}
    context_dict['most_viewed']= most_viewed
    context_dict['cat_list']=cat_list

    #COOKIES
    response = render_to_response('rango/index.html',context_dict,context)

    if request.session.get('last_visit'):
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits',0)
        if (datetime.now() - datetime.strptime(last_visit_time[:-7],"%Y-%m-%d %H:%M:%S")).seconds >5:
            request.session['visits'] = visits+1
            request.session['last_visit'] = str(datetime.now())
    else:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = 1
    # Return response back to the user, updating any cookies that need changed.
    return render_to_response('rango/index.html', context_dict, context)

def category(request,category_name_url):
    context = RequestContext(request)
    #Sutituyendo espacios con _ para construir la URL
    category_name = category_name_url.replace('_',' ')
    categories = Category.objects.order_by('likes')[:5]
    for category in categories:
        category.url = category.name.replace(' ', '_')

    #Creando context dictionay
    context_dict = {'category_name':category_name,'categories':categories}

    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)
            context_dict['result_list']=result_list


    try:
        #Intentamos obtener la categoria en base al nombre de la base de datos
        category = Category.objects.get(name=category_name)

        # Add category to the context so that we can access the id and likes
        context_dict['category'] = category
        #Obtenemos las paginas asociadas a a categoria obtenida
        pages = Page.objects.filter(category=category).order_by('views')[:5].reverse()



        #Agregamos el resultado al diccionario del contexto
        context_dict['pages']= pages

        #Agregamos tambien la categoria al diccionario
        context_dict['category'] = category
        context_dict['category_name_url'] = category_name_url
    except Category.DoesNotExist:
        #No hacemos nada, el tenplate mostrara un mensaje indicando que no hay categorias
        pass
    return render_to_response('rango/category.html',context_dict,context)

def about(request):
    context = RequestContext(request)
    var = "This is the About Page."
    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0
    context_dict = {'variable':var,'count':count}
    return render_to_response('rango/about.html',context_dict,context)

def register(request):
    context=RequestContext(request)
    if request.session.test_cookie_worked():
        print ">>>> TEST COOKIE WORKED!"
        request.session.delete_test_cookie()
        context=RequestContext(request)

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered= False
    #If its a post method we will process the data in the form
    if request.method == 'POST':

        #Attempting to get all the data from both of the forms from the users input
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)
        #If forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            #save them to database
            user = user_form.save()

            #hashing the password with get_password method
            user.set_password(user.password)
            user.save()

           # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
           # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            #Checking if the user provided a profile picture
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()

                #Boolean to true to tell the template regitration was succesful
            registered = True
        #If form is no valid
        else:
            #Print errors
            print user_form.errors,profile_form.errors
    #Not an HTTP Post..?
    else:
        #Diplay the forms to get the data
        user_form = UserForm()
        profile_form = UserProfileForm()
    # Render the templates depending on the context
    return render_to_response('rango/register.html',{'user_form':user_form,'profile_form':profile_form,'registered':registered},context)

def user_login(request):
    context=RequestContext(request)

    if request.method =='POST':

        form = LoginForm(request.POST)
        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user:
                #The accounts is active? Could have been disabled
                if user.is_active:
                    login(request,user)
                    return HttpResponseRedirect('/rango/')

                else:        # An inactive account was used - no logging in!
                    return HttpResponse("Your Rango account is disabled.")
            else:
                form = LoginForm
                return HttpResponse("Invalid login details supplied.")
        else:
            print form.errors
        # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        form = LoginForm()
        return render_to_response('rango/login.html', {'form':form}, context)

@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/rango/')

@login_required
def restricted(request):
    context = RequestContext(request)
    return render_to_response('rango/restricted.html',{},context)

def search(request):
    context = RequestContext(request)
    result_list = []
    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    return render_to_response('rango/search.html', {'result_list': result_list}, context)

@login_required
def auto_add_page(request):
    context = RequestContext(request)
    cat_id = None
    url = None
    title = None
    if request.method =='GET':
        cat_id = request.GET['category_id']
        url = request.GET['url']
        title = request.GET['title']
        if cat_id:
            category = Category.objects.get(id=int(cat_id))
            p = Page.objects.get_or_create(category=category, title=title, url=url)

            pages = Page.objects.filter(category=category).order_by('-views')

            # Adds our results list to the template context under name pages.
            context_dict['pages'] = pages

    return render_to_response('rango/page_list.html', context_dict, context)

@login_required
def profile(request):
    context = RequestContext(request)
    #Getting current logged in user
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    return render_to_response('rango/profile.html',{'user':user,'user_profile':user_profile},context)

def track_url(request):
    context = RequestContext(request)
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass
    return redirect(url)

@login_required
def like_category(request):
    context = RequestContext(request)
    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']
    likes = 0
    if cat_id:
        category = Category.objects.get(id=int(cat_id))
        if category:
            likes = category.likes +1
            category.likes = likes
            category.save()
    return HttpResponse(likes)

def suggest_category(request):
        context = RequestContext(request)
        cat_list = []
        starts_with = ''
        if request.method == 'GET':
                starts_with = request.GET['suggestion']

        cat_list = get_category_list(8, starts_with)

        return render_to_response('rango/category_list.html', {'cat_list': cat_list }, context)

#Helper Functions
def encode_url(category_name_url):
    return category_name_url.replace('_', ' ')

def decode_url(category_name_url):
    return category_name_url.replace(' ', '_')

def get_category_list(max_results = 0,starts_with=''):
    cat_list = []
    if starts_with:
            cat_list = Category.objects.filter(name__istartswith=starts_with)
    else:
            cat_list = Category.objects.all()

    if max_results > 0:
            if len(cat_list) > max_results:
                    cat_list = cat_list[:max_results]

    for cat in cat_list:
            cat.url = encode_url(cat.name)

    return cat_list