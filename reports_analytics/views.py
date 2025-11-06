from django.shortcuts import render
from django.contrib.auth.decorators import login_required # Use your @staff_required
from cases.models import Blotter, IncidentLog
from cases.choices import INCIDENT_TYPE_CHOICES
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth, TruncQuarter, TruncDay
import calendar
import datetime
import json


@login_required
def reports_hub_view(request):
    return render(request, 'reports_analytics/hub.html')

@login_required
def lupon_report_view(request):
    year = request.GET.get('year', datetime.date.today().year)
    
    # Prepare a list of all 12 months
    months = [{'num': i, 'name': datetime.date(year, i, 1).strftime('%B')} for i in range(1, 13)]
    
    # Get all settled cases (based on the final log)
    settled_cases_pks = IncidentLog.objects.filter(result='Settled', date_processed__year=year).values_list('case_id', flat=True)
    
    # Define statuses
    settled_statuses = ['Mediation', 'Conciliation']
    unsettled_statuses = ['Repudiated', 'Withdrawn', 'Dismissed', 'Certified']

    # Query the data
    monthly_data = Blotter.objects.filter(date_filed__year=year)\
        .annotate(month=TruncMonth('date_filed'))\
        .values('month')\
        .annotate(
            summon_count=Count('id', filter=Q(status='summon', pk__in=settled_cases_pks)),
            mediation_count=Count('id', filter=Q(status='Mediation', pk__in=settled_cases_pks)),
            conciliation_count=Count('id', filter=Q(status='Conciliation', pk__in=settled_cases_pks)),
            repudiated_count=Count('id', filter=Q(status='Repudiation')),
            withdrawn_count=Count('id', filter=Q(status='Withdrawn')),
            dismissed_count=Count('id', filter=Q(status='Dismissed')),
            certified_count=Count('id', filter=Q(status='Certified')),
        ).order_by('month')
        
    # Map data to months
    data_map = {d['month'].month: d for d in monthly_data}
    for month in months:
        month_data = data_map.get(month['num'], {})
        month['summon'] = month_data.get('summon_count', 0)
        month['mediation'] = month_data.get('mediation_count', 0)
        month['conciliation'] = month_data.get('conciliation_count', 0)
        month['repudiated'] = month_data.get('repudiated_count', 0)
        month['withdrawn'] = month_data.get('withdrawn_count', 0)
        month['dismissed'] = month_data.get('dismissed_count', 0)
        month['certified'] = month_data.get('certified_count', 0)

    context = { 'months_data': months, 'selected_year': year, 'years': range(datetime.date.today().year, 2022, -1)}
    return render(request, 'reports_analytics/lupon_report.html', context)


@login_required
def incident_type_report_view(request):
    try:
        year = int(request.GET.get('year', datetime.date.today().year))
    except (ValueError, TypeError):
        year = datetime.date.today().year

    # Prepare a list of all 12 months and incident types
    months = {i: datetime.date(year, i, 1).strftime('%B') for i in range(1, 13)}
    incident_types = INCIDENT_TYPE_CHOICES # (val, display) format

    # Query and group by month and incident_type
    data = Blotter.objects.filter(date_filed__year=year)\
        .annotate(month=TruncMonth('date_filed'))\
        .values('month', 'incident_type')\
        .annotate(count=Count('id'))\
        .order_by('month')

    # --- DATA PROCESSING ---
    monthly_data = {month_num: {it[0]: 0 for it in incident_types} for month_num in range(1, 13)}
    for item in data:
        month_num = item['month'].month
        monthly_data[month_num][item['incident_type']] = item['count']

    # Calculate monthly totals
    for month_num, counts in monthly_data.items():
        counts['total'] = sum(counts.values())

    # Calculate quarterly and annual totals
    quarters = {q: {it[0]: 0 for it in incident_types} for q in range(1, 5)}
    totals = {it[0]: 0 for it in incident_types}
    
    for month_num, counts in monthly_data.items():
        q = (month_num - 1) // 3 + 1
        for itype, count in counts.items():
            if itype != 'total':
                quarters[q][itype] += count
                totals[itype] += count

    for q_num, q_data in quarters.items():
        q_data['total'] = sum(q_data.values())
    
    totals['total'] = sum(totals.values())

    context = {
        'incident_types': incident_types,
        'monthly_data': monthly_data,
        'month_names': months,
        'quarters': quarters,
        'totals': totals,
        'selected_year': year,
        'years': range(datetime.date.today().year, 2022, -1),
    }
    return render(request, 'reports_analytics/incident_type_report.html', context)

@login_required
def monthly_analytics_view(request):
    today = datetime.date.today()
    # Kunin ang year at month mula sa URL, kung wala, gamitin ang current
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        year, month = today.year, today.month

    # Kunin lahat ng blotters para sa specific na buwan at taon
    cases_in_month = Blotter.objects.filter(date_filed__year=year, date_filed__month=month)

    # 1. Highest at Lowest Incident Day
    daily_counts = cases_in_month.annotate(day=TruncDay('date_filed')) \
        .values('day').annotate(count=Count('id')).order_by('day')
    
    highest_day = sorted(daily_counts, key=lambda x: x['count'], reverse=True)[0] if daily_counts else None
    lowest_day = sorted(daily_counts, key=lambda x: x['count'])[0] if daily_counts else None
    
    # 2. Line Chart Data (Daily Incidents)
    num_days_in_month = calendar.monthrange(year, month)[1]
    line_chart_labels = list(range(1, num_days_in_month + 1))
    line_chart_values = [0] * num_days_in_month
    for item in daily_counts:
        day_index = item['day'].day - 1
        line_chart_values[day_index] = item['count']

    # 3. Pie Chart Data (Incident Types for the Month)
    pie_chart_data = cases_in_month.values('incident_type').annotate(count=Count('id')).order_by('-count')
    incident_type_map = dict(INCIDENT_TYPE_CHOICES)
    pie_chart_labels = [incident_type_map.get(item['incident_type'], item['incident_type']) for item in pie_chart_data]
    pie_chart_values = [item['count'] for item in pie_chart_data]
    
    # Data para sa dropdown filters
    years = range(datetime.date.today().year, 2022, -1)
    months = [{'num': i, 'name': calendar.month_name[i]} for i in range(1, 13)]

    context = {
        'selected_year': year,
        'selected_month': month,
        'years': years,
        'months': months,
        'highest_day': highest_day,
        'lowest_day': lowest_day,
        
        # Ipasa natin ang raw Python lists, hindi na JSON strings
        'line_chart_labels': line_chart_labels,
        'line_chart_values': line_chart_values,
        'pie_chart_labels': pie_chart_labels,
        'pie_chart_values': pie_chart_values,
    }
    
    return render(request, 'reports_analytics/monthly_analytics.html', context)