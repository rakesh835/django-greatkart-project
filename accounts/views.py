from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
import requests

from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from cart.views import _cart_id
from cart.models import Cart, CartItem
from orders.models import Order, OrderProduct


def register(request):
	if request.method == 'POST':
		form = RegistrationForm(request.POST)

		if form.is_valid():
			first_name = form.cleaned_data['first_name']
			last_name = form.cleaned_data['last_name']
			email = form.cleaned_data['email']
			phone_number = form.cleaned_data['phone_number']
			password = form.cleaned_data['password']
			
			username = email.split('@')[0]

			if len(phone_number) != 10:
				messages.warning(request, 'Phone number must contain 10 digits.')
				return redirect('register')

			user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)

			user.phone_number = phone_number
			user.save()

			# Create User Profile

			profile = UserProfile()
			profile.user_id = user.id
			profile.profile_picture = '/default/download.png'
			profile.save()


			# USER ACTIVATION
			current_site = get_current_site(request)
			mail_subject = 'Please activate your account'
			message = render_to_string('accounts/account_verification_email.html', {
				'user': user,
				'domain': current_site,
				'uid': urlsafe_base64_encode(force_bytes(user.id)),
				'token': default_token_generator.make_token(user), 
				})
			to_mail = email
			send_email = EmailMessage(mail_subject, message, to=[to_mail])
			send_email.send()

			# messages.success(request, 'Successfully registered. You can login now.')
			return redirect('/accounts/login/?command=verification&email='+email)
	else:
		form = RegistrationForm()

	context = {
			'form': form,
	}
	return render(request, 'accounts/register.html', context)



def login(request):
	if request.method == 'POST':
		email = request.POST['email']
		password = request.POST['password']

		user = auth.authenticate(email=email, password=password)

		if user is not None:
			try:
				cart = Cart.objects.get(cart_id=_cart_id(request))
				is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
				if is_cart_item_exists:
					cart_items = CartItem.objects.filter(cart=cart)


					product_variation = []
					for item in cart_items:
						variation = item.variations.all()
						product_variation.append(list(variation))
					
					cart_items = CartItem.objects.filter(user=user)
					ex_var_list = []
					id = []
					for item in cart_items:
						existing_variation = item.variations.all()
						ex_var_list.append(list(existing_variation))
						id.append(item.id)
					

					for pr in product_variation:
						if pr in ex_var_list:
							index = ex_var_list.index(pr)
							item_id = id[index]
							item = CartItem.objects.get(id=item_id)
							item.quantity += 1
							item.user = user
							item.save()
						
						else:
							cart_item = CartItem.objects.filter(cart=cart)
							for item in cart_item:
								item.user = user
								item.save()
			except:
				pass

			auth.login(request, user)
			url = request.META.get('HTTP_REFERER')
			try:
				print("going goog")
				query = requests.utils.urlparse(url).query
				print("query", query)
				params = dict(x.split('=') for x in query.split('&'))
				print('params', params)

				if 'next' in params:
					nextPage = params['next']
					return redirect(nextPage)
			except:
				return redirect('dashboard')
		else:
			messages.error(request, 'Invalid credentials')
			return redirect('login')

	return render(request, 'accounts/login.html')



def logout_view(request):
	logout(request)
	return redirect('home')



def activate(request, uidb64, token):
	try:
		uid = urlsafe_base64_decode(uidb64).decode()
		user = Account._default_manager.get(pk=uid)
	except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
		user = None

	if user is not None and default_token_generator.check_token(user, token):
		user.is_active = True
		user.save()
		messages.success(request, 'Congratulations! Your account is activated.')
		return redirect('login')
	else:
		messages.error(request, 'Invalid activation link.')
		return redirect('register')




def dashboard(request):
	orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
	orders_count = orders.count()

	userprofile = get_object_or_404(UserProfile, user=request.user)

	context = {
			'orders_count': orders_count,
			'userprofile': userprofile,
	}

	return render(request, 'accounts/dashboard.html', context)


def forgotPassword(request):

	if request.method == 'POST':
		email = request.POST.get('email')

		if Account.objects.filter(email=email).exists():
			user = Account.objects.get(email__exact=email)

			# RESET PASSWORD EMAIL
			current_site = get_current_site(request)
			mail_subject = 'RESET YOUR PASSWORD'
			message = render_to_string('accounts/reset_password_email.html', {
				'user': user,
				'domain': current_site,
				'uid': urlsafe_base64_encode(force_bytes(user.id)),
				'token': default_token_generator.make_token(user), 
				})
			to_mail = email
			send_email = EmailMessage(mail_subject, message, to=[to_mail])
			send_email.send()

			messages.success(request, 'Password reset link has been sent to your email address.')
			return redirect('login')

		else:
			messages.error(request, 'Account does not exists!')
			return redirect('forgotPassword')

	return render(request, 'accounts/forgotPassword.html')



def resetpassword_validate(request, uidb64, token):
	try:
		uid = urlsafe_base64_decode(uidb64).decode()
		user = Account._default_manager.get(pk=uid)
	except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
		user = None

	if user is not None and default_token_generator.check_token(user, token):
		request.session['uid'] = uid
		messages.success(request, 'Please resest your password.')
		return redirect('resetPassword')

	else:
		messages.error(request, 'This link has been expired!')
		return redirect('login')


def resetPassword(request):
	if request.method == 'POST':
		password = request.POST.get('password')
		confirm_password = request.POST.get('confirm_password')


		if password != confirm_password:
			messages.error(request, 'Passwor do not match!')
			return redirect('resetPassword')
		else:
			uid = request.session.get('uid')
			user = Account.objects.get(pk=uid)

			user.set_password(password)
			user.save()
			messages.success(request, 'Your password has been changed successfully.')
			return redirect('login')
	
	else:
		return render(request, 'accounts/resetPassword.html')




@login_required(login_url='login')
def my_orders(request):
	orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')

	context = {
			'orders': orders,
	}

	return render(request, 'accounts/my_orders.html', context)




@login_required(login_url='login')
def edit_profile(request):
	userprofile = get_object_or_404(UserProfile, user=request.user)

	if request.method == 'POST':
		user_form = UserForm(request.POST, instance=request.user)
		profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
		if user_form.is_valid() and profile_form.is_valid():
			user_form.save()
			profile_form.save()
			messages.success(request, 'Your profile has been updated.')
			return redirect('edit_profile')
	else:
		user_form = UserForm(instance=request.user)
		profile_form = UserProfileForm(instance=userprofile)

	
	context = {
			'user_form': user_form,
			'profile_form': profile_form,
			'userprofile': userprofile,
	}
	print('userprofile:  ', userprofile.profile_picture)

	return render(request, 'accounts/edit_profile.html', context)




@login_required(login_url='login')
def change_password(request):
	if request.method == 'POST':
		current_password = request.POST.get('current_password')
		new_password = request.POST.get('new_password')
		confirm_password = request.POST.get('confirm_password')

		user = Account.objects.get(username__exact=request.user.username)

		if new_password == confirm_password:
			success = user.check_password(current_password)
			if success:
				user.set_password(new_password)
				user.save()
				messages.success(request, 'Your password has been updated successfully.')
			else:
				messages.error(request, 'Your current password is not correct.')
				return redirect('change_password')
		else:
			messages.error(request, 'new and confirm password are not same')
			return redirect('change_password')

	return render(request, 'accounts/change_password.html')



@login_required(login_url='login')
def order_detail(request, order_id):
	order_detail = OrderProduct.objects.filter(order__order_number=order_id)
	order = Order.objects.get(order_number=order_id)

	subtotal = 0
	for item in order_detail:
		subtotal += item.product_price * item.quantity

	context = {
			'order_detail': order_detail,
			'order': order,
			'subtotal': subtotal,
	}

	return render(request, 'accounts/order_detail.html', context)


