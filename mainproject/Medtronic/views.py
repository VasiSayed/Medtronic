from collections import defaultdict
from datetime import datetime, timedelta
from django.shortcuts import render
from django.utils.timezone import now
from django.db.models import Count, Q, F, ExpressionWrapper, DurationField, Sum
from products.models import SearchProduct, OrderProductOnline, Wishlist
from accounts.models import User, UserActivity

def home_view(request):
    if request.user.is_authenticated and request.user.role == 'admin':
        today = now()
        period = request.GET.get('period', 'month')

        # Filters for search and order stats
        if period == "today":
            search_filter = {'date__date': today.date()}
            order_filter = {'order_date__date': today.date()}
        elif period == "year":
            search_filter = {'date__year': today.year}
            order_filter = {'order_date__year': today.year}
        else:  # default to month
            search_filter = {'date__month': today.month, 'date__year': today.year}
            order_filter = {'order_date__month': today.month, 'order_date__year': today.year}

        # Top Searched Products
        searches = (
            SearchProduct.objects.filter(**search_filter)
            .values('product__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        # Top Ordered Products
        orders = (
            OrderProductOnline.objects.filter(**order_filter)
            .values('product__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        # Top Users by Session Duration
        activity = UserActivity.objects.exclude(end_time=None)
        user_durations = defaultdict(timedelta)

        for a in activity:
            if a.end_time and a.start_time:
                duration = datetime.combine(today, a.end_time) - datetime.combine(today, a.start_time)
                user_durations[a.user.username] += duration

        top_users = sorted(
            [{'user__username': user, 'total_duration': str(duration)} for user, duration in user_durations.items()],
            key=lambda x: x['total_duration'],
            reverse=True
        )[:5]

        # Most Wishlisted Products
        wishlist_data = (
            Wishlist.objects.filter(is_active=True)
            .values('product__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        # VENDOR ANALYTICS
        all_vendors = User.objects.filter(role='user')
        total_vendors = all_vendors.count()

        last_30_days = today - timedelta(days=30)
        active_vendors_30_days = UserActivity.objects.filter(
            login_date__gte=last_30_days,
            user__role='user'
        ).values('user').distinct().count()

        vendors_logged_in_once = UserActivity.objects.filter(
            user__role='user'
        ).values('user').distinct().count()

        # New Vendors this week/month
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        new_vendors_week = all_vendors.filter(date_joined__gte=start_of_week).count()
        new_vendors_month = all_vendors.filter(date_joined__gte=start_of_month).count()

        # Daily/Weekly/Monthly Active Vendors (DAU/WAU/MAU)
        dau = UserActivity.objects.filter(
            login_date=today.date(),
            user__role='user'
        ).values('user').distinct().count()

        wau = UserActivity.objects.filter(
            login_date__gte=start_of_week,
            user__role='user'
        ).values('user').distinct().count()

        mau = UserActivity.objects.filter(
            login_date__gte=start_of_month,
            user__role='user'
        ).values('user').distinct().count()

        # Dormant Vendors (Never Logged In)
        vendors_who_logged_in = UserActivity.objects.filter(
            user__role='user'
        ).values_list('user_id', flat=True).distinct()
        dormant_vendors = all_vendors.exclude(id__in=vendors_who_logged_in).count()

        # Vendor Retention Rate (simple version based on login overlap this and last week)
        last_week_start = start_of_week - timedelta(weeks=1)
        last_week_end = start_of_week - timedelta(days=1)

        retained_this_week = UserActivity.objects.filter(
            user__role='user',
            login_date__range=(start_of_week, today.date())
        ).values_list('user', flat=True).distinct()

        retained_last_week = UserActivity.objects.filter(
            user__role='user',
            login_date__range=(last_week_start, last_week_end)
        ).values_list('user', flat=True).distinct()

        retained_overlap = len(set(retained_this_week).intersection(set(retained_last_week)))
        retention_rate = round((retained_overlap / len(retained_last_week)) * 100, 2) if retained_last_week else 0.0

        # Average Session Duration per Vendor
        duration_expr = ExpressionWrapper(
            F('end_time') - F('start_time'),
            output_field=DurationField()
        )

        avg_session_data = (
            UserActivity.objects.filter(user__role='user', end_time__isnull=False)
            .annotate(duration=duration_expr)
            .values('user')
            .annotate(total_duration=Sum('duration'))
        )

        avg_session_duration = sum([entry['total_duration'].total_seconds() for entry in avg_session_data], 0.0)
        avg_session_duration = avg_session_duration / len(avg_session_data) if avg_session_data else 0.0
        avg_session_duration_minutes = round(avg_session_duration / 60, 2)

        return render(request, 'admin.html', {
            'search_data': list(searches),
            'order_data': list(orders),
            'top_users': list(top_users),
            'wishlist_data': list(wishlist_data),
            'total_vendors': total_vendors,
            'active_vendors_30_days': active_vendors_30_days,
            'vendors_logged_in_once': vendors_logged_in_once,
            'new_vendors_week': new_vendors_week,
            'new_vendors_month': new_vendors_month,
            'dau': dau,
            'wau': wau,
            'mau': mau,
            'dormant_vendors': dormant_vendors,
            'retention_rate': retention_rate,
            'avg_session_duration_minutes': avg_session_duration_minutes,
        })

    return render(request, 'base.html')
