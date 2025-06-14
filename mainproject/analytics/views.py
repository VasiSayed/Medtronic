from django.db.models import Count
from django.shortcuts import render
from products.models import SearchProduct, AttachmentDownloadLog, Product, ProductType, ProductCategory
from services.models import RequestLog  
from datetime import timedelta
from accounts.models import User, UserActivity
from datetime import datetime, timedelta
from django.utils.timezone import now
from collections import defaultdict



def vendor_list_view(request):
    vendors = User.objects.filter(role='user')
    return render(request, 'analytics/list.html', {'title': 'All Vendors', 'vendors': vendors})

def active_vendors_view(request):
    recent_date = now() - timedelta(days=30)
    vendor_ids = UserActivity.objects.filter(login_date__gte=recent_date, user__role='user').values_list('user', flat=True).distinct()
    vendors = User.objects.filter(id__in=vendor_ids)
    return render(request, 'analytics/list.html', {'title': 'Active Vendors (Last 30 Days)', 'vendors': vendors})

def logged_in_vendors_view(request):
    vendor_ids = UserActivity.objects.filter(user__role='user').values_list('user', flat=True).distinct()
    vendors = User.objects.filter(id__in=vendor_ids)
    return render(request, 'analytics/list.html', {'title': 'Vendors Logged In At Least Once', 'vendors': vendors})

def new_vendors_week_view(request):
    start_of_week = now() - timedelta(days=now().weekday())
    vendors = User.objects.filter(role='user', date_joined__gte=start_of_week)
    return render(request, 'analytics/list.html', {'title': 'New Vendors This Week', 'vendors': vendors})

def new_vendors_month_view(request):
    start_of_month = now().replace(day=1)
    vendors = User.objects.filter(role='user', date_joined__gte=start_of_month)
    return render(request, 'analytics/list.html', {'title': 'New Vendors This Month', 'vendors': vendors})

def dau_view(request):
    today = now().date()
    vendor_ids = UserActivity.objects.filter(login_date=today, user__role='user').values_list('user', flat=True).distinct()
    vendors = User.objects.filter(id__in=vendor_ids)
    return render(request, 'analytics/list.html', {'title': 'Daily Active Vendors (Today)', 'vendors': vendors})

def wau_view(request):
    start_of_week = now() - timedelta(days=now().weekday())
    vendor_ids = UserActivity.objects.filter(login_date__gte=start_of_week, user__role='user').values_list('user', flat=True).distinct()
    vendors = User.objects.filter(id__in=vendor_ids)
    return render(request, 'analytics/list.html', {'title': 'Weekly Active Vendors', 'vendors': vendors})

def mau_view(request):
    start_of_month = now().replace(day=1)
    vendor_ids = UserActivity.objects.filter(login_date__gte=start_of_month, user__role='user').values_list('user', flat=True).distinct()
    vendors = User.objects.filter(id__in=vendor_ids)
    return render(request, 'analytics/list.html', {'title': 'Monthly Active Vendors', 'vendors': vendors})

def dormant_vendors_view(request):
    logged_in_ids = UserActivity.objects.filter(user__role='user').values_list('user_id', flat=True).distinct()
    vendors = User.objects.filter(role='user').exclude(id__in=logged_in_ids)
    return render(request, 'analytics/list.html', {'title': 'Dormant Vendors (Never Logged In)', 'vendors': vendors})


def avg_session_view(request):
    activities = UserActivity.objects.filter(user__role='user', end_time__isnull=False)
    vendor_data = defaultdict(list)

    for act in activities:
        duration = datetime.combine(now(), act.end_time) - datetime.combine(now(), act.start_time)
        vendor_data[act.user].append(duration)

    vendor_sessions = []
    for user, sessions in vendor_data.items():
        total_duration = sum(sessions, timedelta())
        total_sessions = len(sessions)
        avg_duration = total_duration / total_sessions if total_sessions else timedelta()

        total_minutes = round(total_duration.total_seconds() / 60, 2)
        avg_minutes = round(avg_duration.total_seconds() / 60, 2)

        vendor_sessions.append({
            'user': user,
            'total_sessions': total_sessions,
            'total_duration': f"{total_minutes} minutes",
            'avg_duration': f"{avg_minutes} minutes"
        })

    return render(request, 'analytics/avg_session.html', {'vendor_sessions': vendor_sessions})



def most_viewed_products(request):
    data = (
        SearchProduct.objects
        .values('product__name')
        .annotate(view_count=Count('id'))
        .order_by('-view_count')[:10]
    )
    return render(request, 'analytics/most_viewed_products.html', {'products': data})

def hero_products(request):
    searched = SearchProduct.objects.values('product__id').annotate(count=Count('id')).order_by('-count')[:5]
    downloaded = AttachmentDownloadLog.objects.values('product__id').annotate(count=Count('id')).order_by('-count')[:5]
    quoted = RequestLog.objects.values('product__id').annotate(count=Count('id')).order_by('-count')[:5]

    product_ids = set()
    for group in [searched, downloaded, quoted]:
        product_ids.update([entry['product__id'] for entry in group])

    products = Product.objects.filter(id__in=product_ids)
    return render(request, 'analytics/hero_products.html', {'products': products})

def top_categories_engagement(request):
    data = (
        SearchProduct.objects
        .values('product__product_type__product_category__name')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )
    return render(request, 'analytics/top_categories.html', {'categories': data})

def most_downloaded_brochures(request):
    data = (
        AttachmentDownloadLog.objects
        .values('product__name')
        .annotate(downloads=Count('id'))
        .order_by('-downloads')[:10]
    )
    return render(request, 'analytics/most_downloaded.html', {'downloads': data})

def most_requested_products(request):
    data = (
        RequestLog.objects
        .values('product__name')
        .annotate(requests=Count('id'))
        .order_by('-requests')[:10]
    )
    return render(request, 'analytics/most_requested.html', {'products': data})



def support_metrics_view(request):
    period = request.GET.get('period', 'month')  
    today = now()

    if period == 'today':
        logs = RequestLog.objects.filter(date__date=today.date())
    elif period == 'year':
        logs = RequestLog.objects.filter(date__year=today.year)
    else: 
        logs = RequestLog.objects.filter(date__year=today.year, date__month=today.month)

    demo_count = logs.filter(request_type__name='Demo').count()
    training_count = logs.filter(request_type__name='Training').count()
    support_count = logs.filter(request_type__name='Support').count()

    common_issues = (
        logs.filter(request_type__name='Support')
        .values('name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    return render(request, 'analytics/suport_metrix.html', {
        'demo_count': demo_count,
        'training_count': training_count,
        'support_count': support_count,
        'common_issues': common_issues,
        'selected_period': period,
    })
