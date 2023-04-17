from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages

from .models import Product, ReviewRating, ProductGallary
from category.models import Category
from cart.views import _cart_id
from cart.models import CartItem
from .forms import ReviewForm
from orders.models import OrderProduct

# Create your views here.

def store(request, category_slug=None):

	if category_slug!=None:
		category = get_object_or_404(Category, slug=category_slug)
		products = Product.objects.filter(category=category, is_available=True)
		product_count = products.count()
		paginator = Paginator(products, 1)
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)
		
	else:

		products = Product.objects.all().filter(is_available=True).order_by('id')
		product_count = products.count()
		paginator = Paginator(products, 2)
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)
	
	context = {
				'products': page_obj,
				'product_count': product_count,
	}
	return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
	try:
		single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
		in_cart = CartItem.objects.filter(product=single_product, cart__cart_id=_cart_id(request)).exists()
		
	except Exception as e:
		raise e

	if request.user.is_authenticated:
		try:
			orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
		except OrderProduct.DoesNotExist:
			orderproduct = None
	else:
		orderproduct = None
		

	# Get the review
	reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

	# Get the product gallary
	product_gallary = ProductGallary.objects.filter(product_id=single_product.id)


	context={
			'single_product': single_product,
			'in_cart': in_cart,
			'orderproduct': orderproduct,
			'reviews': reviews,
			'product_gallary': product_gallary,
	}

	return render(request, 'store/product_detail.html', context)



def search(request):
	items_per_page = 2

	if request.GET:
		keyword = request.GET['keyword']
		
		if keyword:
			products = Product.objects.filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword)).order_by('-created_date')
			product_count = products.count()
			paginator = Paginator(products, items_per_page, allow_empty_first_page=True)
			page_number = request.GET.get('page')
			
			page_obj = paginator.get_page(page_number)
		else:
			keyword = ''
			page_obj = None
			product_count = 0
	

	context={
		'products': page_obj,
		'product_count': product_count,
		'query': str(keyword),
	}
	
	return render(request, 'store/search_result.html', context)



def submit_review(request, product_id):
	url = request.META.get('HTTP_REFERER')

	if request.method == "POST":
		try:
			reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
			form = ReviewForm(request.POST, instance=reviews)
			form.save()
			messages.success(request, 'Your review has been updated.')
			return redirect(url)
		except ReviewRating.DoesNotExist:
			form = ReviewForm(request.POST)
			if form.is_valid():
				data = ReviewRating()
				data.subject = form.cleaned_data.get('subject')
				data.rating = form.cleaned_data.get('rating')
				data.review = form.cleaned_data.get('review')
				data.ip = request.META.get('REMOTE_ADDR')
				data.product_id = product_id
				data.user_id = request.user.id
				data.save()
				messages.success(request, 'Your review has beeb submitted.')
				return redirect(url)







