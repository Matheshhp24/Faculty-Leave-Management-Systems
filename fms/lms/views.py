from django.shortcuts import render, redirect
from .forms import CreateUserForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .forms import CreateUserForm, StaffDetailsForm
from django.contrib.auth.decorators import login_required
from datetime import datetime
from datetime import date
from django.core.files.storage import FileSystemStorage
from .models import *
import pytz
from django.http import FileResponse, Http404
from django.utils import timezone
from django.db.models import Min
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.conf import settings
from email.mime.text import MIMEText
import smtplib
from email.mime.multipart import MIMEMultipart
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
import io
from django.utils.timezone import make_naive
from django.utils.timezone import is_aware
import pandas as pd
from .forms import LeaveDownloadForm,FreezeDatesForm,CancelLeaveForm
import json
from django.db.models import Max
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from .forms import LoginForm
from itertools import chain
from django.db.models import Q
from urllib.parse import quote




class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'login.html'


def notification_save(notification_username,notification_message):
    staff_notify = StaffDetails.objects.get(username_copy = notification_username)
    staff_notify.notification_message = notification_message
    staff_notify.notification_display = True
    staff_notify.save()



def send_email(subject, body, to_email, is_html=False):
    """
    Sends an email with the specified subject, body, and recipient.
    
    Parameters:
    - subject: Subject of the email
    - body: Body of the email
    - to_email: Recipient's email address
    - is_html: Boolean flag indicating whether the body is HTML or plain text
    """
    # Create the MIME object
    message = MIMEMultipart()
    message['From'] = "srecflms@gmail.com"
    message['To'] = to_email
    message['Subject'] = subject

    # Attach the body of the email
    if is_html:
        # If the body is HTML, use 'html' subtype
        message.attach(MIMEText(body, 'html'))
    else:
        # If the body is plain text, use 'plain' subtype
        message.attach(MIMEText(body, 'plain'))

    # Establish a connection to the SMTP server
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        try:
            # Upgrade the connection to a secure TLS connection
            server.starttls()

            # Log in to the SMTP server
            server.login('srecflms@gmail.com', 'nbot lqvl ybfi euik')

            # Send the email
            server.sendmail('srecflms@gmail.com', to_email, message.as_string())

            print(f"Email sent successfully to {to_email}")
        except Exception as e:
            print(f"Error sending email to {to_email}: {e}")

def get_user_common_context(request):
    staff_notification = StaffDetails.objects.get(username_copy = request.user.username)
    if staff_notification.notification_display:
        answer = True
        notification_message= staff_notification.notification_message
        staff_notification.notification_display = False
        staff_notification.save()
    else:
        answer = False
        notification_message = None
    feedback_staffname = request.user.first_name + " " + request.user.last_name
    pre_filled_url = (
        "https://docs.google.com/forms/d/e/1FAIpQLSe584zLdwG2mseMFQByO54Eu2PakllhW_M7bOZrAxctdEV7tA/viewform"
        f"?usp=pp_url"
        f"&entry.1992171459={quote(feedback_staffname)}"
        f"&entry.1136181252={quote(request.user.username)}"
        f"&entry.1209612741={quote(request.user.email)}"
        f"&entry.949894776={quote(StaffDetails.objects.get(username_copy = request.user.username).department)}"
    )

    user_common_context = {
        'notify':answer,
        'notification_message':notification_message,
        'bell_message' : StaffDetails.objects.get(username_copy = request.user.username).notification_message,
        'username': request.user.first_name,
        'email': request.user.email,
        'feedback_url':pre_filled_url
        
    }


    return user_common_context


@login_required
def home(request):
    username = request.user.username
    # if request.user.check_password('srec@123'):
    #     return redirect("AccountSettings")



    last_leave = {}

# Define a list of all leave model classes
    leave_models = [casual_leave, LOP_leave, earnLeave, vaccationLeave, onDuty, specialOnduty, medicalLeave, CH_leave,maternityLeave,Permission,CHProof]

    # Loop through each leave model class
    for leave_model in leave_models:
        try:
            # Get the latest leave record for the current model
            last_leave_instance = leave_model.objects.filter(username=username).latest('date_Applied')
        # Ensure the datetime is timezone-aware
            last_leave_instance_date_applied = timezone.localtime(last_leave_instance.date_Applied)
            # Store the latest date applied in the dictionary with the leave type as the key
            last_leave[leave_model.__name__] = last_leave_instance_date_applied.strftime("%d/%m/%y %I:%M %p")
        except leave_model.DoesNotExist:

        # If no record exists for the current model, set the value to "Not Applied Yet"
            last_leave[leave_model.__name__] = "Not Applied Yet" # No records found for this leave type
    total_list = []


#0
    casual_total = float(Leave_Availability.objects.get(username = request.user.username).initial_casual_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).casual_remaining)
    total_taken = float(casual_total)-float(remaining)
    total_list.append(total_taken)
#1
    vaccation_total = float(Leave_Availability.objects.get(username = request.user.username).initial_vaccation_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).vaccation_remaining)
    total_taken = vaccation_total-remaining
    total_list.append(total_taken)
#2
    onduty_total = float(Leave_Availability.objects.get(username = request.user.username).initial_onduty_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).onduty_remaining)
    total_taken = onduty_total-remaining
    total_list.append(total_taken)
#3
    medical_total = float(Leave_Availability.objects.get(username = request.user.username).initial_medical_leave_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).medical_leave_remaining)
    total_taken = medical_total-remaining
    total_list.append(total_taken)
#4
    ch_total = float(Leave_Availability.objects.get(username = request.user.username).initial_ch_leave_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).ch_leave_remaining)
    total_taken = ch_total-remaining
    total_list.append(total_taken)
#5
    earn_total = float(Leave_Availability.objects.get(username = request.user.username).initial_earn_leave_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).earn_leave_remaining)
    total_taken = float(earn_total)-float(remaining)
    total_list.append(total_taken)
    print(total_list)

#6
    mal_total = float(Leave_Availability.objects.get(username = request.user.username).initial_maternity_leave_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).maternity_leave_remaining)
    total_taken = float(mal_total)-float(remaining)
    total_list.append(total_taken)
    print(total_list)
    

    casual_leave_status = casual_leave.objects.filter(username=username, status__in=['Reviewing', 'Approved(1)']).exists()
    earn_leave_status = earnLeave.objects.filter(username=username, status__in=['Reviewing', 'Approved(1)']).exists()
    vacation_leave_status = vaccationLeave.objects.filter(username=username, status__in=['Reviewing', 'Approved(1)']).exists()
    onduty_leave_status = onDuty.objects.filter(username=username, status__in=['Reviewing', 'Approved(1)']).exists()
    ch_leave_status = CH_leave.objects.filter(username=username, status__in=['Reviewing', 'Approved(1)']).exists()
    ml_leave_status = medicalLeave.objects.filter(username=username, status__in=['Reviewing', 'Approved(1)']).exists()
    sod_leave_status = specialOnduty.objects.filter(username=username, status__in=['Reviewing', 'Approved(1)']).exists()
    llp_leave_status = LOP_leave.objects.filter(username=username, status__in=['Reviewing', 'Approved(1)']).exists()
    mal_leave_status = maternityLeave.objects.filter(username=username, status__in=['Reviewing', 'Approved(1)']).exists()
    permission_leave_status = Permission.objects.filter(username=username, status__in=['Reviewing', 'Approved(1)']).exists()


    
    highlight = StaffDetails.objects.get(username_copy = request.user.username).notification_display


    specific_context = {
        'last_leave': last_leave,
        'total_days': total_list,
        'casual_leave_status': casual_leave_status,
        'earn_leave_status': earn_leave_status,
        'vacation_leave_status':vacation_leave_status,
        'onduty_leave_status':onduty_leave_status,
        'ch_leave_status':ch_leave_status,
        'ml_leave_status':ml_leave_status,
        'sod_leave_status':sod_leave_status,
        'llp_leave_status':llp_leave_status,
        'mal_leave_status':mal_leave_status,
        'permission_leave_status':permission_leave_status,
        'highlight_feedback' : highlight,
    }
    print(highlight)
    user_common_context = get_user_common_context(request)
    context = merge_contexts(user_common_context,specific_context)
    return render(request, 'index.html', context)


@login_required
def profile(request):

    specific_context = {

         'firstname':request.user.first_name,
         'lastname':request.user.last_name,
         'Department':StaffDetails.objects.get(username_copy = request.user.username).department,
         'Doj':StaffDetails.objects.get(username_copy = request.user.username).doj,
         'staff_id':request.user.username
    }
    user_common_context = get_user_common_context(request)
    context = merge_contexts(user_common_context,specific_context)
    return render(request, 'profile.html',context)

def freeze_dates_view(request):
    # Retrieve or create the FrozenDates object
    try:
        frozen_dates = FrozenDates.objects.get(id=1)  # Assuming only one object exists
    except FrozenDates.DoesNotExist:
        frozen_dates = FrozenDates.objects.create(dates_and_reasons={})

    if request.method == 'POST':
        if 'add_date' in request.POST:
            form = FreezeDatesForm(request.POST)
            if form.is_valid():
                date = form.cleaned_data['date']
                reason = form.cleaned_data['reason']
                date_str = date.strftime('%d-%m-%Y')
                frozen_dates.dates_and_reasons[date_str] = reason
                frozen_dates.save()
                messages.success(request, 'Date has been successfully frozen.')
                return redirect('freeze_dates')

        elif 'delete_date' in request.POST:
            date_to_delete = request.POST.get('date_to_delete')
            if date_to_delete in frozen_dates.dates_and_reasons:
                del frozen_dates.dates_and_reasons[date_to_delete]
                frozen_dates.save()
                messages.success(request, f'Date {date_to_delete} has been successfully deleted.')
                return redirect('freeze_dates')

    form = FreezeDatesForm()
    context = {
        'form': form,
        'frozen_dates': frozen_dates.dates_and_reasons,
    }

    return render(request, 'custom_admin/freeze_dates.html', context)


@login_required
def casual_leave_function(request):
    if request.method == 'POST':
        username = request.user.username
        fromDate_str = request.POST.get("fromDate")
        toDate_str = request.POST.get("toDate")
        fromDate = datetime.strptime(fromDate_str, '%Y-%m-%d')
        toDate = datetime.strptime(toDate_str, '%Y-%m-%d')
        date_difference = toDate - fromDate
        days_difference = (date_difference.days) + 1
        session = request.POST.get("session")


        frozen_dates = FrozenDates.objects.first() 
        if frozen_dates:
            frozen_dates_dict = frozen_dates.dates_and_reasons
            frozen_dates_list = []
            for frozen_date_str, reason in frozen_dates_dict.items():
                frozen_date = datetime.strptime(frozen_date_str, '%d-%m-%Y')
                if fromDate <= frozen_date <= toDate:
                    frozen_dates_list.append(f"{frozen_date_str} - ({reason})")

            if frozen_dates_list:
                alert_data = {
                    'title': '🚫 Leave Application Blocked!',
                    'message': f"🚨 Selected Date was Blocked.📝\n\n{', '.join(frozen_dates_list)}"
                }
            
            # Serialize the dictionary to a JSON string
                alert_data_json = json.dumps(alert_data)

                # Pass the JSON string as a message
                messages.add_message(request, messages.WARNING, alert_data_json)
                return redirect('CasualLeave')


        if session == 'fullDay':
            tot_days = days_difference
        else:
            tot_days = float(days_difference) / 2

        document = request.FILES.get('file', None)
        remaining = float(Leave_Availability.objects.get(username=username).casual_remaining)
           # Set base month (June) and base year
        base_month = 6
        base_year = fromDate.year if fromDate.month >= base_month else fromDate.year - 1

        # Calculate total available leave based on past months' history
        current_month = fromDate.month
        current_year = fromDate.year
        max_leave_days = 1

        for i in range(1, 4):  # Check up to the last 3 months
            check_month = (current_month - i) % 12 or 12
            check_year = current_year if current_month - i > 0 else current_year - 1

            # Skip the month check if it's before the base month of the base year
            if check_year < base_year or (check_year == base_year and check_month < base_month):
                continue

            leave_count_result = casual_leave.objects.filter(
                username=username,
                status='Approved'
            )

            leave_days = 0
            for leave in leave_count_result:
                leave_from_date = datetime.strptime(leave.from_Date, '%Y-%m-%d')
                leave_to_date = datetime.strptime(leave.to_Date, '%Y-%m-%d')

                if (leave_from_date.month == check_month and leave_from_date.year == check_year) or (leave_to_date.month == check_month and leave_to_date.year == check_year):
                    if leave.session == 'fullDay':
                        leave_days += (leave_to_date - leave_from_date).days + 1
                    else:
                        leave_days += (leave_to_date - leave_from_date).days + 1 / 2

            if leave_days == 0:
                max_leave_days += 1
            elif leave_days == 0.5:
                max_leave_days += 0.5

        # Cap the max leave days at 3
        max_leave_days = min(max_leave_days, 3)

        leave_count_result = casual_leave.objects.filter(
            username=username,
            status='Approved'
        )

        current_month_leave_days = 0
        for leave in leave_count_result:
            leave_from_date = datetime.strptime(leave.from_Date, '%Y-%m-%d')
            leave_to_date = datetime.strptime(leave.to_Date, '%Y-%m-%d')

            if (leave_from_date.month == current_month and leave_from_date.year == current_year) or (leave_to_date.month == current_month and leave_to_date.year == current_year):
                if leave.session == 'fullDay':
                    current_month_leave_days += (leave_to_date - leave_from_date).days + 1
                else:
                    current_month_leave_days += (leave_to_date - leave_from_date).days + 1 / 2

        if float(remaining) <= 0 or float(remaining) < float(tot_days) or float(days_difference) <= 0 or float(tot_days) > float(max_leave_days) or float(current_month_leave_days) > 0:
            specific_context = {
                "remaining": remaining,
                "flag": True,
                'user': username,
                "this_month": current_month_leave_days
            }
            user_common_context = get_user_common_context(request)
            context = merge_contexts(user_common_context, specific_context)

            alert_data = {
            'title': '🚨 Limit Exceeded!',
            'message': "🚫 Oops! You've hit your CASUAL LEAVE limit. Try switching it up with a different leave type📝."
        }
        
        # Serialize the dictionary to a JSON string
            alert_data_json = json.dumps(alert_data)

            # Pass the JSON string as a message
            messages.add_message(request, messages.WARNING, alert_data_json)
            
            return redirect('CasualLeave')

        casual_leave_instance = casual_leave(
            username=username,
            date_Applied=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            from_Date=fromDate_str,
            to_Date=toDate_str,
            session=session,
            remaining=remaining,
            total_leave=tot_days,
            reason=request.POST.get("reason"),
            document=document
        )
        casual_leave_instance.save()
        messages.success(request, "🎉 Your Casual Leave request is in review. Stay tuned! 📋")
        return redirect('Home')
    else:
        context = get_user_common_context(request)
        return render(request, 'casual_leave.html', context)



@login_required
def lop_leave_function(request):
    if request.method=='POST':
        username = request.user.username
        fromDate_str = request.POST.get("fromDate")
        toDate_str = request.POST.get("toDate")
        fromDate = datetime.strptime(fromDate_str, '%Y-%m-%d')
        toDate = datetime.strptime(toDate_str, '%Y-%m-%d')
        date_difference = toDate - fromDate
        days_difference = (date_difference.days)+1
        session = request.POST.get("session")

        frozen_dates = FrozenDates.objects.first() 
        if frozen_dates:
            frozen_dates_dict = frozen_dates.dates_and_reasons
            frozen_dates_list = []
            for frozen_date_str, reason in frozen_dates_dict.items():
                frozen_date = datetime.strptime(frozen_date_str, '%d-%m-%Y')
                if fromDate <= frozen_date <= toDate:
                    frozen_dates_list.append(f"{frozen_date_str} - ({reason})")

            if frozen_dates_list:
                alert_data = {
                    'title': '🚫 Leave Application Blocked!',
                    'message': f"🚨 Selected Date was Blocked.📝\n\n{', '.join(frozen_dates_list)}"
                }
            
            # Serialize the dictionary to a JSON string
                alert_data_json = json.dumps(alert_data)

                # Pass the JSON string as a message
                messages.add_message(request, messages.WARNING, alert_data_json)
                return redirect('LopLeave')
            
        if 'file' in request.FILES:
            document = request.FILES['file']
            print(document)
        else:
            document = None
            print(document)
        if session == 'fullDay':
            tot_days = days_difference
        else:
            tot_days = (days_difference)/2
        date_difference_days = date_difference.days
        # username = request.session.get('username')
        if days_difference <= 0:
            specific_context = {
                "flag" : True,
                "message" : "Date Invalid"
            }
            user_common_context = get_user_common_context(request)
            context = merge_contexts(user_common_context,specific_context)
            return render(request, 'lop_leave.html',context=context)




        LOP_leave_instance  = LOP_leave(
        username = username,
        date_Applied = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        from_Date = fromDate_str,
        to_Date = toDate_str,
        session = request.POST.get("session"),
        total_leave = tot_days,
        reason = request.POST.get("reason"),
        document = document
        )
        LOP_leave_instance.save()

        messages.success(request, "🎉 Your LLP Leave request is in review. Stay tuned! 📋")
        return redirect('Home')
    else:
        context = get_user_common_context(request)
        return render(request,'lop_leave.html',context)



def earn_leave_function(request):
    if request.method=='POST':
        username = request.user.username

        fromDate_str = request.POST.get("fromDate")
        toDate_str = request.POST.get("toDate")
        fromDate = datetime.strptime(fromDate_str, '%Y-%m-%d')
        fromDate_month = fromDate.month
        toDate = datetime.strptime(toDate_str, '%Y-%m-%d')
        date_difference = toDate - fromDate
        days_difference = (date_difference.days)+1
        selected_option = request.POST.get('option')


        frozen_dates = FrozenDates.objects.first() 
        if frozen_dates:
            frozen_dates_dict = frozen_dates.dates_and_reasons
            frozen_dates_list = []
            for frozen_date_str, reason in frozen_dates_dict.items():
                frozen_date = datetime.strptime(frozen_date_str, '%d-%m-%Y')
                if fromDate <= frozen_date <= toDate:
                    frozen_dates_list.append(f"{frozen_date_str} - ({reason})")

            if frozen_dates_list:
                alert_data = {
                    'title': '🚫 Leave Application Blocked!',
                    'message': f"🚨 Selected Date was Blocked.📝\n\n{', '.join(frozen_dates_list)}"
                }
            
            # Serialize the dictionary to a JSON string
                alert_data_json = json.dumps(alert_data)

                # Pass the JSON string as a message
                messages.add_message(request, messages.WARNING, alert_data_json)
                return redirect('EarnLeave')
        if 'file' in request.FILES:
            document = request.FILES['file']
            print(document)
        else:
            document = None
            print(document)
        tot_days = days_difference
        # username = request.session.get('username')
        print("CS" , username)
        print("Name:",  )
        # result = earnLeave.objects.filter(username=username)
        year_instance = StaffDetails.objects.filter(username_copy = request.user.username)
        # print(result)

        applying_year = fromDate.year
        # Get the year of the applying date and the joined date
        joined_year = year_instance[0].doj.year

        # Calculate the year 3 years after the joined date
        eligible_year = joined_year + 3

        # print(applying_year)
        print(eligible_year)
        print(joined_year)
        # Check if the applying year is at least 3 years greater than the joined year


        remaining = float(Leave_Availability.objects.get(username = request.user.username).earn_leave_remaining)
        total_leave = tot_days



        print(tot_days,'--=-')
        print(remaining,'remmmmmm')

        leave_count_result = earnLeave.objects.filter(username=username, status='Approved', from_Date__startswith=f'{fromDate.year}-{fromDate.month:02}')
        print(len(leave_count_result),'--')
        if remaining<=0 or float(remaining)<float(tot_days):
            alert_data = {
            'title': '🚨 Limit Exceeded!',
            'message': 'You have exceeded your EARN LEAVE limit. Please review your leave balance or apply for a different type of leave.'
        }
        
        # Serialize the dictionary to a JSON string
            alert_data_json = json.dumps(alert_data)

            # Pass the JSON string as a message
            messages.add_message(request, messages.WARNING, alert_data_json)

            return redirect('EarnLeave')


        if applying_year < eligible_year or days_difference <= 0 :
            specific_context = {
                "remaining" : remaining,
                "flag" : True,
                'user':username,
                "this_month" : len(leave_count_result)

            }
            user_common_context = get_user_common_context(request)
            context = merge_contexts(user_common_context,specific_context)
            print("Exceed")
            alert_data = {
                'title': '🚨 NOT Eligible',
                'message': 'You are not Eligible to apply Earn Leave.'
            }
        
        # Serialize the dictionary to a JSON string
            alert_data_json = json.dumps(alert_data)

            # Pass the JSON string as a message
            messages.add_message(request, messages.WARNING, alert_data_json)
            return redirect("EarnLeave")
        # print(remaining)



        earn_leave_instance  = earnLeave(
        leave_type = selected_option,
        username = username,
        date_Applied = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        from_Date = fromDate_str,
        to_Date = toDate_str,
        session = request.POST.get("session"),
        remaining = remaining,
        total_leave = total_leave,
        reason = request.POST.get("reason"),
        document = document
        )
        earn_leave_instance.save()

        messages.success(request, f"🎉 Your {selected_option} request is in review. Stay tuned! 📋")
        return redirect('Home')
    else:
        context = get_user_common_context(request)
        return render(request, 'earn_leave.html',context)


def vaccation_leave_function(request):
    if request.method=='POST':

        fromDate_str = request.POST.get("fromDate")
        toDate_str = request.POST.get("toDate")
        fromDate = datetime.strptime(fromDate_str, '%Y-%m-%d')
        toDate = datetime.strptime(toDate_str, '%Y-%m-%d')
        date_difference = toDate - fromDate
        days_difference = (date_difference.days)+1
        session = request.POST.get("session")
        selected_option = request.POST.get('option')


        
        frozen_dates = FrozenDates.objects.first() 
        if frozen_dates:
            frozen_dates_dict = frozen_dates.dates_and_reasons
            frozen_dates_list = []
            for frozen_date_str, reason in frozen_dates_dict.items():
                frozen_date = datetime.strptime(frozen_date_str, '%d-%m-%Y')
                if fromDate <= frozen_date <= toDate:
                    frozen_dates_list.append(f"{frozen_date_str} - ({reason})")

            if frozen_dates_list:
                alert_data = {
                    'title': '🚫 Leave Application Blocked!',
                    'message': f"🚨 Selected Date was Blocked.📝\n\n{', '.join(frozen_dates_list)}"
                }
            
            # Serialize the dictionary to a JSON string
                alert_data_json = json.dumps(alert_data)

                # Pass the JSON string as a message
                messages.add_message(request, messages.WARNING, alert_data_json)
                return redirect('VaccationLeave')
        if 'file' in request.FILES:
            document = request.FILES['file']
            print(document)
        else:
            document = None
            print(document)
        if session == 'fullDay':
            tot_days = days_difference
        else:
            tot_days = (days_difference)/2
        username = request.user.username
        staff_name = request.user.first_name
        remaining = Leave_Availability.objects.get(username = username).vaccation_remaining
        print(remaining)
        if float(remaining)<=0 or float(remaining)<float(tot_days) or days_difference <= 0:
            specific_context = {
            "days" : tot_days,
            "flag" : True,
            "leave_type" : "Vaccation Leave",
            'user':username,

            }

            user_common_context = get_user_common_context(request)
            context = merge_contexts(user_common_context,specific_context)
            alert_data = {
                'title': '🚨 Exceeds Limit!',
                'message': 'You have exceeded your VACATION LEAVE limit. Please review your leave balance or apply for a different type of leave.'
            }
        
        # Serialize the dictionary to a JSON string
            alert_data_json = json.dumps(alert_data)

            # Pass the JSON string as a message
            messages.add_message(request, messages.WARNING, alert_data_json)
            return redirect('VaccationLeave')


        total_leave = tot_days
        # if len((result))>0:
        #     total_leave = result[len(result)-1].total_leave
        #     total_leave+=float(tot_days)




        vaccation_leave_instance  = vaccationLeave(
        username = username,
        leave_type = selected_option,
        date_Applied = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        from_Date = fromDate_str,
        to_Date = toDate_str,
        session = request.POST.get("session"),
        total_leave = total_leave,
        reason = request.POST.get("reason"),
        document = document
        )
        vaccation_leave_instance.save()
        messages.success(request, f"🎉 Your {selected_option} request is in review. Stay tuned! 📋")


        return redirect("Home")
    else:
        context = get_user_common_context(request)
        return render(request,'vaccation_leave.html',context)

def onduty_function(request):
    if request.method=='POST':
        username = request.user.username

        fromDate_str = request.POST.get("fromDate")
        toDate_str = request.POST.get("toDate")
        fromDate = datetime.strptime(fromDate_str, '%Y-%m-%d')
        fromDate_month = fromDate.month
        toDate = datetime.strptime(toDate_str, '%Y-%m-%d')
        date_difference = toDate - fromDate
        print(date_difference)
        days_difference = (date_difference.days)+1
        session = request.POST.get("session")

        frozen_dates = FrozenDates.objects.first() 
        if frozen_dates:
            frozen_dates_dict = frozen_dates.dates_and_reasons
            frozen_dates_list = []
            for frozen_date_str, reason in frozen_dates_dict.items():
                frozen_date = datetime.strptime(frozen_date_str, '%d-%m-%Y')
                if fromDate <= frozen_date <= toDate:
                    frozen_dates_list.append(f"{frozen_date_str} - ({reason})")

            if frozen_dates_list:
                alert_data = {
                    'title': '🚫 Leave Application Blocked!',
                    'message': f"🚨 Selected Date was Blocked.📝\n\n{', '.join(frozen_dates_list)}"
                }
            
            # Serialize the dictionary to a JSON string
                alert_data_json = json.dumps(alert_data)

                # Pass the JSON string as a message
                messages.add_message(request, messages.WARNING, alert_data_json)
                return redirect('OnDuty')
        if 'file' in request.FILES:
            document = request.FILES['file']
            print(document)
        else:
            document = None
            print(document)
        # tot_days = days_difference
        if session == 'fullDay':
            tot_days = days_difference
        else:
            tot_days = float(days_difference) / 2
        # username = request.session.get('username')
        print("CS" , username)
        print(tot_days)
        result = onDuty.objects.filter(username=username)
        remaining = Leave_Availability.objects.get(username = username).onduty_remaining
        print(remaining,days_difference)
        total_leave = tot_days
        # if len((result))>0:

        #      remaining = result.aggregate(Min('remaining'))['remaining__min']
        #      print("rem",remaining)


        print(tot_days,'--=-')
        print(username)


        # leave_count_result = onDuty.objects.filter(username=username, status='Approved', from_Date__startswith=f'{fromDate.year}-{fromDate.month:02}')
        # print(len(leave_count_result),'--')
        if float(remaining)<=0 or float(remaining)<tot_days  or  days_difference <= 0:
            specific_context = {
                "remaining" : remaining,
                "flag" : True,
                "user":username
                # "this_month" : len(leave_count_result)

            }
            print("Exceed")
            user_common_context = get_user_common_context(request)
            context = merge_contexts(user_common_context,specific_context)
            alert_data = {
                'title': '🚨 Exceeds Limit!',
                'message': "🚫 You've maxed out your Onduty limit! Time to try SOD"
            }
        
        # Serialize the dictionary to a JSON string
            alert_data_json = json.dumps(alert_data)

            # Pass the JSON string as a message
            messages.add_message(request, messages.WARNING, alert_data_json)
            return redirect('OnDuty')


        onduty_instance  = onDuty(
        username = username,
        date_Applied = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        from_Date = fromDate_str,
        to_Date = toDate_str,
        session = request.POST.get("session"),
        remaining = remaining,
        total_leave = total_leave,
        reason = request.POST.get("reason"),
        document = document
        )
        onduty_instance.save()

        messages.success(request, f"🎉 Your On Duty request is in review. Stay tuned! 📋")
        return redirect("Home")
    else:
        context = get_user_common_context(request)
        return render(request,'onduty.html',context)

def special_onduty_function(request):
    if request.method=='POST':
        fromDate_str = request.POST.get("fromDate")
        toDate_str = request.POST.get("toDate")
        fromDate = datetime.strptime(fromDate_str, '%Y-%m-%d')
        toDate = datetime.strptime(toDate_str, '%Y-%m-%d')
        date_difference = toDate - fromDate
        days_difference = (date_difference.days)+1
        session = request.POST.get("session")
        selected_option = request.POST.get('option')

        
        frozen_dates = FrozenDates.objects.first() 
        if frozen_dates:
            frozen_dates_dict = frozen_dates.dates_and_reasons
            frozen_dates_list = []
            for frozen_date_str, reason in frozen_dates_dict.items():
                frozen_date = datetime.strptime(frozen_date_str, '%d-%m-%Y')
                if fromDate <= frozen_date <= toDate:
                    frozen_dates_list.append(f"{frozen_date_str} - ({reason})")

            if frozen_dates_list:
                alert_data = {
                    'title': '🚫 Leave Application Blocked!',
                    'message': f"🚨 Selected Date was Blocked.📝\n\n{', '.join(frozen_dates_list)}"
                }
            
            # Serialize the dictionary to a JSON string
                alert_data_json = json.dumps(alert_data)

                # Pass the JSON string as a message
                messages.add_message(request, messages.WARNING, alert_data_json)
                return redirect('SpecialOnDuty')
        if 'file' in request.FILES:
            document = request.FILES['file']
            print(document)
        else:
            document = None
            print(document)
        if session == 'fullDay':
            tot_days = days_difference
        else:
            tot_days = (days_difference)/2
        username = request.user.username

        if days_difference <= 0:
            specific_context = {
                "flag" : True,
                "message" : "Date Invalid"
            }
            user_common_context = get_user_common_context(request)
            context = merge_contexts(user_common_context,specific_context)
            return render(request, 'special_onduty.html',context=context)




        speical_onduty_instance  = specialOnduty(
        username = username,
        leave_type = selected_option,
        date_Applied = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        from_Date = fromDate_str,
        to_Date = toDate_str,
        session = request.POST.get("session"),
        total_leave = tot_days,
        reason = request.POST.get("reason"),
        document = document
        )
        speical_onduty_instance.save()
        messages.success(request, f"🎉 Your {selected_option} request is in review. Stay tuned! 📋")

        return redirect("Home")
    else:
        context = get_user_common_context(request)
        return render(request, 'special_onduty.html',context)

def CH_leave_function(request):
    if request.method=='POST':
        username = request.user.username

        fromDate_str = request.POST.get("fromDate")
        toDate_str = request.POST.get("toDate")
        fromDate = datetime.strptime(fromDate_str, '%Y-%m-%d')
        fromDate_month = fromDate.month
        toDate = datetime.strptime(toDate_str, '%Y-%m-%d')
        date_difference = toDate - fromDate
        days_difference = (date_difference.days)+1
        session = request.POST.get("session")


        frozen_dates = FrozenDates.objects.first() 
        if frozen_dates:
            frozen_dates_dict = frozen_dates.dates_and_reasons
            frozen_dates_list = []
            for frozen_date_str, reason in frozen_dates_dict.items():
                frozen_date = datetime.strptime(frozen_date_str, '%d-%m-%Y')
                if fromDate <= frozen_date <= toDate:
                    frozen_dates_list.append(f"{frozen_date_str} - ({reason})")

            if frozen_dates_list:
                alert_data = {
                    'title': '🚫 Leave Application Blocked!',
                    'message': f"🚨 Selected Date was Blocked.📝\n\n{', '.join(frozen_dates_list)}"
                }
            
            # Serialize the dictionary to a JSON string
                alert_data_json = json.dumps(alert_data)

                # Pass the JSON string as a message
                messages.add_message(request, messages.WARNING, alert_data_json)
                return redirect('CHLeave')
        if session == 'fullDay':
            tot_days = days_difference
        else:
            tot_days = float((days_difference)/2)
            print("TOTTTTT",tot_days)
        if 'file' in request.FILES:
            document = request.FILES['file']
            print(document)
        else:
            document = None
            print(document)
        # username = request.session.get('username')
        print("CS" , username)
        result = CH_leave.objects.filter(username=username)
        print(result)
        # remaining_q = login_details.objects.get(username=username)
        remaining = Leave_Availability.objects.get(username = username).ch_leave_remaining


        total_leave = tot_days





        print(tot_days,'--=-')

        if float(remaining)<=0 or float(remaining)<float(tot_days)  or  float(days_difference) <= 0 :
            specific_context = {
                "remaining" : remaining,
                "flag" : True,
                'user':request.user.username

            }
            user_common_context = get_user_common_context(request)
            context = merge_contexts(user_common_context,specific_context)
            print("Exceed")
            alert_data = {
                'title': '🚨 Exceeds Limit!',
                'message': " You've maxed out your Compensations limit! Time to try SOD🚫"
            }
        
        # Serialize the dictionary to a JSON string
            alert_data_json = json.dumps(alert_data)

            # Pass the JSON string as a message
            messages.add_message(request, messages.WARNING, alert_data_json)

            return redirect("CHLeave")
        # print(remaining)



        CH_leave_instance  = CH_leave(
        username = username.upper(),
        date_Applied = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        from_Date = fromDate_str,
        to_Date = toDate_str,
        session = request.POST.get("session"),
        total_leave = total_leave,
        remaining = remaining,
        reason = request.POST.get("reason"),
        document = document
        )
        CH_leave_instance.save()
        messages.success(request, f"🎉 Your Compensated Holiday request is in review. Stay tuned! 📋")

        return redirect("Home")
    else:
        context = get_user_common_context(request)
        return render(request,'ch_leave.html',context)


def medical_leave_function(request):
    if request.method=='POST':
        username = request.user.username

        fromDate_str = request.POST.get("fromDate")
        toDate_str = request.POST.get("toDate")
        fromDate = datetime.strptime(fromDate_str, '%Y-%m-%d')
        fromDate_month = fromDate.month
        toDate = datetime.strptime(toDate_str, '%Y-%m-%d')
        date_difference = toDate - fromDate
        days_difference = (date_difference.days)+1
        frozen_dates = FrozenDates.objects.first() 
        if frozen_dates:
            frozen_dates_dict = frozen_dates.dates_and_reasons
            frozen_dates_list = []
            for frozen_date_str, reason in frozen_dates_dict.items():
                frozen_date = datetime.strptime(frozen_date_str, '%d-%m-%Y')
                if fromDate <= frozen_date <= toDate:
                    frozen_dates_list.append(f"{frozen_date_str} - ({reason})")

            if frozen_dates_list:
                messages.error(request, f"Cannot apply leave on frozen dates: {', '.join(frozen_dates_list)}")
                return redirect('MedicalLeave') 
 
        if 'file' in request.FILES:
            document = request.FILES['file']
            print(document)
        else:
            document = None
            print(document)
        tot_days = days_difference
        # username = request.session.get('username')
        print("CS" , username)
        result = medicalLeave.objects.filter(username=username.upper())
        user_login_details = StaffDetails.objects.get(username_copy=request.user.username)

    # Get the year of the applying date and the joined date
        applying_year = fromDate.year
        joined_year = user_login_details.doj.year

        # Calculate the year 3 years after the joined date
        eligible_year = joined_year + 3

        print(applying_year)
        print(eligible_year)
        # Check if the applying year is at least 3 years greater than the joined year


        remaining = Leave_Availability.objects.get(username =username).medical_leave_remaining

        total_leave = tot_days
        # if len((result))>0:

        #      remaining = int(result.aggregate(Min('remaining'))['remaining__min'])
        #      print("rem",remaining)


        print(tot_days,'--=-')


        leave_count_result = medicalLeave.objects.filter(username=username, status='Approved', from_Date__startswith=f'{fromDate.year}-{fromDate.month:02}')
        print(len(leave_count_result),'--')
        if float(remaining)<0 or float(remaining)<float(tot_days):
            alert_data = {
                'title': '🚨 Exceeds Limit!',
                'message': " You've maxed out your Medical Leave limit!🚫"
            }
        
        # Serialize the dictionary to a JSON string
            alert_data_json = json.dumps(alert_data)

            # Pass the JSON string as a message
            messages.add_message(request, messages.WARNING, alert_data_json)
            return redirect("MedicalLeave")


        if applying_year < eligible_year or float(days_difference) <= 0:
            specific_context = {
                "remaining" : remaining,
                "flag" : True,
                'user':username.upper(),
                "this_month" : len(leave_count_result)

            }
            user_common_context = get_user_common_context(request)
            context = merge_contexts(user_common_context,specific_context)
            print("Exceed")
            alert_data = {
                'title': '🚨 Not Eligible',
                'message': " You are not Eligible to apply Medical Leave!🚫"
            }
        
        # Serialize the dictionary to a JSON string
            alert_data_json = json.dumps(alert_data)

            # Pass the JSON string as a message
            messages.add_message(request, messages.WARNING, alert_data_json)
            return redirect('MedicalLeave')
        # print(remaining)



        medical_leave_instance  = medicalLeave(
        username = username.upper(),
        date_Applied = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        from_Date = fromDate_str,
        to_Date = toDate_str,
        session = request.POST.get("session"),
        remaining = remaining,
        total_leave = total_leave,
        reason = request.POST.get("reason"),
        document = document
        )
        medical_leave_instance.save()
        messages.success(request, f"🎉 Your Medical Leave request is in review. Stay tuned! 📋")

        return redirect("Home")
    else:
        context = get_user_common_context(request)
        return render(request,'medical_leave.html',context)



def maternity_leave_function(request):
    if request.method == "POST":
        username = request.user.username
        fromDate_str = request.POST.get("fromDate")
        toDate_str = request.POST.get("toDate")
        fromDate = datetime.strptime(fromDate_str, '%Y-%m-%d')
        toDate = datetime.strptime(toDate_str, '%Y-%m-%d')
        date_difference = toDate - fromDate
        days_difference = (date_difference.days) + 1
        session = request.POST.get("session")
        print(username,fromDate_str,toDate_str,fromDate,toDate,date_difference,days_difference,session)


        frozen_dates = FrozenDates.objects.first() 
        if frozen_dates:
            frozen_dates_dict = frozen_dates.dates_and_reasons
            frozen_dates_list = []
            for frozen_date_str, reason in frozen_dates_dict.items():
                frozen_date = datetime.strptime(frozen_date_str, '%d-%m-%Y')
                if fromDate <= frozen_date <= toDate:
                    frozen_dates_list.append(f"{frozen_date_str} - ({reason})")

            if frozen_dates_list:
                alert_data = {
                    'title': '🚫 Leave Application Blocked!',
                    'message': f"🚨 Selected Date was Blocked.📝\n\n{', '.join(frozen_dates_list)}"
                }
            
            # Serialize the dictionary to a JSON string
                alert_data_json = json.dumps(alert_data)

                # Pass the JSON string as a message
                messages.add_message(request, messages.WARNING, alert_data_json)
                return redirect('CasualLeave')


        if 'file' in request.FILES:
            document = request.FILES['file']
            print(document)
        else:
            document = None
            print(document)
        tot_days = days_difference
        # result = medicalLeave.objects.filter(username=username.upper())
        user_login_details = StaffDetails.objects.get(username_copy=request.user.username)

    # Get the year of the applying date and the joined date
        applying_year = fromDate.year
        joined_year = user_login_details.doj.year

        # Calculate the year 3 years after the joined date
        eligible_year = joined_year + 2

        print(applying_year)
        print(eligible_year)
        remaining = Leave_Availability.objects.get(username =username).maternity_leave_remaining
        print(remaining)
        print(tot_days)
        print(applying_year)
        print(eligible_year)
        print(days_difference)
        total_leave = tot_days
        if float(remaining)<0 or float(remaining)<float(tot_days):
            alert_data = {
                'title': '🚨 Exceeds Limit!',
                'message': " You've maxed out your Maternity Leave limit!🚫"
            }
        
        # Serialize the dictionary to a JSON string
            alert_data_json = json.dumps(alert_data)

            # Pass the JSON string as a message
            messages.add_message(request, messages.WARNING, alert_data_json)
            return redirect("MaternityLeave")
        
        if applying_year < eligible_year or float(days_difference) <= 0:
            specific_context = {
                'error_message':'You are not eligible',
                'flag':True,
                'user':username.upper(),
            }
            user_common_context = get_user_common_context(request)
            context = merge_contexts(user_common_context,specific_context)
            alert_data = {
                'title': '🚨 Not Eligible',
                'message': " You are not Eligible to apply Maternity Leave!🚫"
            }
        
        # Serialize the dictionary to a JSON string
            alert_data_json = json.dumps(alert_data)

            # Pass the JSON string as a message
            messages.add_message(request, messages.WARNING, alert_data_json)
            return redirect('MaternityLeave')
        

        maternity_leave_instance = maternityLeave(
            username=username,
            date_Applied=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            from_Date=fromDate_str,
            to_Date=toDate_str,
            session=session,
            remaining=remaining,
            total_leave=tot_days,
            reason=request.POST.get("reason"),
            document=document
        )
        maternity_leave_instance.save()
        messages.success(request, f"🎉 Your Maternity Leave request is in review. Stay tuned! 📋")
        return redirect('Home')
   
    else:
        context = get_user_common_context(request)
        return render(request,'maternity_leave.html',context=context)


def hr_view_function(request):

    return render(request,'custom_admin/index.html')


def admin_login(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        print(username,password)
        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                staff_details = StaffDetails.objects.get(username_copy=username).is_principal
                print(staff_details)
            except StaffDetails.DoesNotExist:
                staff_details = False

        # print(staff_details)
        if user is not None and user.is_superuser and user.is_staff and user.is_active:
            login(request, user)
            print('1')
            if password=="srec@123":
                print("Same" ,password)
                return redirect('AdminAccount')
            
            return redirect('AdminPage')
        elif user is not None and user.is_active and user.is_staff and not user.is_superuser:
            login(request,user)
            print("HOD ACC")
            if password=="srec@123":
                return redirect('HODAdminAccount')
            return redirect("HODPage")
        elif user is not None and  user.is_active and not user.is_staff and staff_details and not user.is_superuser:
            login(request, user)
            print(2)
            if password=="srec@123":
                return redirect('AdminAccount')
            return redirect('AdminPage')
        else:
            context={
                'error_message':"Wrong Username or Password"
            }
            return render(request,'admin-login.html',context)

    else:
        return render(request,'admin-login.html')

def get_common_context(request,principal_username):
    user_details = StaffDetails.objects.get(username_copy=request.user.username)
    leave_types = [
            casual_leave, LOP_leave, CH_leave, medicalLeave,
            earnLeave, vaccationLeave, specialOnduty, onDuty,maternityLeave

            
        ]

    all_records = []

    for leave_type in leave_types:
        records = leave_type.objects.filter(status='Approved(1)').order_by('-date_Applied')
        all_records = list(chain(all_records, records))

    all_records_sorted = sorted(all_records, key=lambda x: x.date_Applied, reverse=True)

    recent_records = all_records_sorted[:5]

    recent_data = [{'username': record.username, 'leave_type': record.leave_type} for record in recent_records]

    casual_leave_count = casual_leave.objects.filter(status='Approved(1)').count()
    LOP_leave_count = LOP_leave.objects.filter(status='Approved(1)').count()
    CH_leave_count = CH_leave.objects.filter(status='Approved(1)').count()
    medicalLeave_count = medicalLeave.objects.filter(status='Approved(1)').count()
    earnLeave_count = earnLeave.objects.filter(status='Approved(1)').count()
    vaccationLeave_count = vaccationLeave.objects.filter(status='Approved(1)').count()
    specialOnduty_count = specialOnduty.objects.filter(status='Approved(1)').count()
    onDuty_count = onDuty.objects.filter(status='Approved(1)').count()
    maternityLeave_count = maternityLeave.objects.filter(status='Approved(1)').count()
    
    
    cancel_casual_leave_count = casual_leave.objects.filter(status='Pending').count()
    cancel_LOP_leave_count = LOP_leave.objects.filter(status='Pending').count()
    cancel_CH_leave_count = CH_leave.objects.filter(status='Pending').count()
    cancel_medicalLeave_count = medicalLeave.objects.filter(status='Pending').count()
    cancel_earnLeave_count = earnLeave.objects.filter(status='Pending').count()
    cancel_vaccationLeave_count = vaccationLeave.objects.filter(status='Pending').count()
    cancel_specialOnduty_count = specialOnduty.objects.filter(status='Pending').count()
    cancel_onDuty_count = onDuty.objects.filter(status='Pending').count()
    cancel_maternityLeave_count = maternityLeave.objects.filter(status='Pending').count()
    cancel_permission_count = Permission.objects.filter(status='Pending').count()


    chproof_count = CHProof.objects.filter(status='Reviewing').count()


    # Sum of all counts
    total_approved_count = (
        casual_leave_count + LOP_leave_count + CH_leave_count + medicalLeave_count +
        earnLeave_count + vaccationLeave_count + specialOnduty_count + onDuty_count + maternityLeave_count
    )


    cancel_total_approved_count = (
        cancel_casual_leave_count + cancel_LOP_leave_count + cancel_CH_leave_count + cancel_medicalLeave_count +
        cancel_earnLeave_count + cancel_vaccationLeave_count + cancel_specialOnduty_count + cancel_onDuty_count +cancel_maternityLeave_count
        + cancel_permission_count
    )
    if principal_username:
        admin = "Vice Prinicpal"
    else:
        admin = "HR"

    common_context = {
        'notification_message': user_details.notification_message,
        'recent_data': recent_data,
        'pending':int(total_approved_count),
        'cancel_count': int(cancel_total_approved_count),
        'chproof_count':int(chproof_count),
        'admin': admin,
        'is_principal':principal_username
    }
    return common_context

def merge_contexts(common_context, specific_context):
    context = common_context.copy()
    context.update(specific_context)
    return context



def make_timezone_naive(data):
    for item in data:
        for key, value in item.items():
            if isinstance(value, datetime):
                if value.tzinfo is not None:
                    item[key] = value.astimezone(pytz.UTC).replace(tzinfo=None)
    return data



def add_department(request):
    if request.method == "POST":
        department_name = request.POST.get('department_name')

        if department_name:
            # Get or create the DepartmentList instance
            department_list, created = StaffDepartment.objects.get_or_create(id=1)

            # Add department to the list
            department_list.add_department(department_name)

            messages.success(request, "Department added successfully.")
        else:
            messages.error(request, "Department name cannot be empty.")

        return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def admin_page(request , username=None):
    user = request.user
    is_superuser = user.is_superuser
    is_staff = user.is_staff
    principal_username = StaffDetails.objects.get(username_copy = request.user.username).is_principal
    print('principal',principal_username)

    if request.user.is_superuser or principal_username:
        print("User is a superuser")
        common_context = get_common_context(request,principal_username)
        if request.resolver_match.url_name == "NewRequests" and principal_username:
            print("New Request")

            result = casual_leave.objects.all()

            data_list_of_dicts = []
            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                print(settings.MEDIA_URL + str(item.document) )
                data_list_of_dicts.append(data_dict)

            result = LOP_leave.objects.all()

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)

                }
                print(settings.MEDIA_URL + str(item.document) )
                data_list_of_dicts.append(data_dict)
                # print(data_list_of_dicts)

            result = CH_leave.objects.all()

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)

                }
                data_list_of_dicts.append(data_dict)

            result = medicalLeave.objects.all()

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)

            result = earnLeave.objects.all()

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)

            result = vaccationLeave.objects.all()

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)

            result = specialOnduty.objects.all()

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)

            result = onDuty.objects.all()

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)
            
            result = maternityLeave.objects.all()

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)
           
            # print(data_list_of_dicts)

            specific_context = {
                'admin_list' : data_list_of_dicts
            }
            context = merge_contexts(common_context,specific_context)

            return render(request, 'custom_admin/new_requests.html', context=context)

        elif request.resolver_match.url_name == "AddStaff":
            if request.method == 'POST':
                print(request.POST)
                user_form = CreateUserForm(request.POST)
                staff_form = StaffDetailsForm(request.POST)

                if user_form.is_valid() and staff_form.is_valid():
                    is_staff = request.POST.get('is_staff')
                    is_superuser = request.POST.get('is_superuser')
                    is_principal = request.POST.get('is_principal')
                    principal_flag = False


                    user = user_form.save(commit=False)
                    if is_staff:
                        user.is_staff = True
                    if is_superuser:
                        user.is_superuser = True
                        user.is_staff = True
                    if is_principal:
                        principal_flag = True

                    user.save()
                    staff_details = staff_form.save(commit=False)
                    staff_details.user = user
                    staff_details.first_name = user.first_name
                    staff_details.last_name = user.last_name
                    staff_details.is_principal = principal_flag
                    print(user.username)
                    casual = request.POST.get("casual")
                    vaccation = request.POST.get("vaccation")
                    onduty = request.POST.get("onduty")
                    medical = request.POST.get("medical")
                    earn = request.POST.get("earn")
                    mal = request.POST.get("mal")
                    permission = request.POST.get("permission")
                    print("earn",earn)

                    default_leave_table = default_table.objects.first()

                    default_leave_table.casual_leave_default = float(casual)
                    default_leave_table.vaccationLeave_default = float(vaccation)
                    default_leave_table.onDuty_default = float(onduty)
                    default_leave_table.medicalLeave_default = float(medical)
                    default_leave_table.earnLeave_default = float(earn)

                    default_leave_table.save()

                    leave_availability_instance = Leave_Availability(
                        username = user.username,
                        casual_remaining = float(casual),
                        initial_casual_remaining = float(casual),
                        vaccation_remaining = float(vaccation),
                        initial_vaccation_remaining = float(vaccation),
                        onduty_remaining = float(onduty),
                        initial_onduty_remaining = float(onduty),
                        medical_leave_remaining = float(medical),
                        initial_medical_leave_remaining = float(medical),
                        earn_leave_remaining = float(earn),
                        initial_earn_leave_remaining = float(earn),
                        ch_leave_remaining = 0,
                        initial_ch_leave_remaining = 0,
                        maternity_leave_remaining = float(mal),
                        initial_maternity_leave_remaining = float(mal),
                        permission_remaining = float(permission),
                        initial_permission_remaining = float(permission),

                    )
                    leave_availability_instance.save()

                    staff_details.save()

                    notification_save(request.user.username,f"New Staff {user.username} was added Successfully")

                    messages.info(request, "Staff was added Successfully")
                    return redirect('AddStaff')
            else:
                user_form = CreateUserForm()
                staff_form = StaffDetailsForm()
            default_leave_table_instance = default_table.objects.all()
            print(default_leave_table_instance)
            for instance in default_leave_table_instance:
                casual_leave_default = instance.casual_leave_default
                LOP_leave_default = instance.LOP_leave_default
                CH_leave_default = instance.CH_leave_default
                medicalLeave_default = instance.medicalLeave_default
                earnLeave_default = instance.earnLeave_default
                vaccationLeave_default = instance.vaccationLeave_default
                specialOnduty_default = instance.specialOnduty_default
                onDuty_default = instance.onDuty_default


            specific_context = {
                'user_form': user_form,
                'staff_form': staff_form,
                'cld':casual_leave_default,
                'lld':LOP_leave_default,
                'chd':CH_leave_default,
                'mld':medicalLeave_default,
                'eld':earnLeave_default,
                'vld':vaccationLeave_default,
                'sod':specialOnduty_default,
                'ond':onDuty_default


            }
            context = merge_contexts(common_context,specific_context)
            return render(request,'custom_admin/addstaff.html', context=context)


        elif request.resolver_match.url_name == "CHProofRequests":
            result = CHProof.objects.all()

            data_list_of_dicts = []
            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.On_date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "in_time": item.in_Time,
                    "out_time": item.Out_Time,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)

            specific_context={
                'admin_list':data_list_of_dicts
            }
            context = merge_contexts(common_context,specific_context)

            return render(request,'custom_admin/chproof_requests.html',context)


        elif request.resolver_match.url_name == 'DeleteStaff':
            if request.method == 'POST':
                staff = User.objects.get(username = username)
                leave_availabilities = Leave_Availability.objects.get(username = username)
                leave_availabilities.delete()
                # check = StaffDetails.objects.get(username_copy = username).department
                # print("HII",check)
                print(staff)
                staff.delete()
                notification_save(request.user.username,f"{username} was deleted Successfully")
                messages.success(request, f'{username} details deleted successfully.')
                return redirect('DeleteStaffView')

            # print(User.objects.all())
            specific_context={
                'staff_members':User.objects.filter(Q(is_active=True) | Q(is_staff=True) , is_superuser=False)
            }
            context = merge_contexts(common_context,specific_context)
            return render(request,'custom_admin/deletestaff.html' ,context=context)


        elif request.resolver_match.url_name == 'DeleteStaffView':
            search_id = request.GET.get('search_id')
            print(search_id)

            if search_id:
                staff_members = User.objects.filter(username=search_id).filter(Q(is_active=True) | Q(is_staff=True), is_superuser=False)

            else:
                staff_members = User.objects.filter(Q(is_active=True) | Q(is_staff=True) , is_superuser=False)

            specific_context = {
                'staff_members': staff_members
            }
            context = merge_contexts(common_context,specific_context)
            return render(request,'custom_admin/deletestaff.html' ,context=context)


        elif request.resolver_match.url_name == 'EditStaffView':
            search_id = request.GET.get('search_id')
            print(search_id)

            if search_id:
                staff_details = User.objects.filter(username=search_id).filter(Q(is_active=True) | Q(is_staff=True), is_superuser=False)
                print(staff_details)

            else:
                staff_details = User.objects.filter(Q(is_active=True) | Q(is_staff=True) , is_superuser=False)

            # staff_details = User.objects.all()
            specific_context = {
                'staff_details':staff_details
            }
            context = merge_contexts(common_context,specific_context)
            return render(request, "custom_admin/editstaff.html",context=context)


        elif request.resolver_match.url_name == 'EditStaff':
            if request.method == "POST":
                username_from_function = username
                staff_instance = User.objects.get(username=username_from_function)
                username = request.POST.get("username")
                first_name = request.POST.get("first_name")
                last_name = request.POST.get("last_name")
                email = request.POST.get("email")
                is_active = request.POST.get('is_active') == 'on'  # Convert 'on' to boolean
                is_staff = request.POST.get('is_staff') == 'on'
                is_superuser = request.POST.get('is_superuser') == 'on'

                # Assuming you already have the user instance



                # Update user attributes
                staff_instance.username = username
                staff_instance.first_name = first_name
                staff_instance.last_name = last_name
                staff_instance.email = email
                staff_instance.is_active = is_active
                staff_instance.is_staff = is_staff
                staff_instance.is_superuser = is_superuser

                staff_instance.save()
                notification_save(request.user.username,f"{username_from_function} user was edited Successfully")
                messages.info(request, f"{username_from_function} user was edited Successfully!")

                return redirect('EditStaffView')


        elif request.resolver_match.url_name == "AvailLeaveView":
            search_id = request.GET.get('search_id')
            if search_id:
                staff_members = User.objects.filter(username=search_id).filter(Q(is_active=True) | Q(is_staff=True), is_superuser=False)

            else:
                staff_members = User.objects.filter(Q(is_active=True) | Q(is_staff=True) , is_superuser=False)
            specific_context = {
                'staff_members':staff_members
            }
            context = merge_contexts(common_context,specific_context)
            return render(request,'custom_admin/availleave.html' , context = context)


        elif request.resolver_match.url_name == "AvailLeave":
            if request.method == "POST":

                LEAVE_TYPE_MODEL_MAP = {
                'Casual Leave': 'casual_leave_avail',
                'LOP Leave': 'LOP_leave_avail',
                'Compensated Holiday': 'CH_leave_avail',
                'Medical Leave': 'medicalLeave_avail',
                'Earn Leave': 'earnLeave_avail',
                'Vacation Leave': 'vaccationLeave_avail',
                'Special Onduty': 'specialOnduty_avail',
                'Onduty': 'onDutye_avail',
            }
                username_from_function = username
                print(username_from_function)
                leave_type = request.POST.get("leave_type")
                field_name = LEAVE_TYPE_MODEL_MAP[leave_type]
                value = request.POST.get("value")

                print(leave_type)
                leave_instance = StaffDetails.objects.get(username_copy=username_from_function)

                leave_avail = float(getattr(leave_instance, field_name))
                action = request.POST.get('action')  # Get the selected action

                leave_availibility_remaining = Leave_Availability.objects.get(username = username_from_function)

                REMAINING_TYPE_MODEL_MAP = {
                'Casual Leave': 'casual_remaining',
                # 'LOP Leave': LOP_leave,
                'Compensated Holiday': 'ch_leave_remaining',
                'Medical Leave': 'medical_leave_remaining',
                'Earn Leave': 'earn_leave_remaining',
                'Vacation Leave': 'vaccation_remaining',
                # 'Special Onduty': specialOnduty,
                'Onduty': 'onduty_remaining',
            }
                INITIAL_REMAINING_TYPE_MODEL_MAP = {
                'Casual Leave': 'intial_casual_remaining',
                # 'LOP Leave': LOP_leave,
                'Compensated Holiday': 'intial_ch_leave_remaining',
                'Medical Leave': 'intial_medical_leave_remaining',
                'Earn Leave': 'intial_earn_leave_remaining',
                'Vacation Leave': 'intial_vaccation_remaining',
                # 'Special Onduty': specialOnduty,
                'Onduty': 'intial_onduty_remaining',
            }
                field_name1 = REMAINING_TYPE_MODEL_MAP[leave_type]
                intiall_field_name1 = INITIAL_REMAINING_TYPE_MODEL_MAP[leave_type]
                existing_remaining = float(getattr(leave_availibility_remaining, field_name1))
                # intial_existing_remaining = float(getattr(leave_availibility_remaining, intiall_field_name1))


                if action == 'increment':
                    leave_avail += float(value)
                    new_value = float(existing_remaining) + float(value)
                    action_text = "incremented"
                elif action == 'decrement':
                    leave_avail -= float(value)
                    new_value = float(existing_remaining) - float(value)
                    action_text = "decremented"
                # REMAINING_TYPE_MODEL_MAP[leave_type] = new_value

                print(REMAINING_TYPE_MODEL_MAP[leave_type])

                print(Leave_Availability.objects.get(username = username_from_function).casual_remaining)

                setattr(leave_instance, field_name, leave_avail)
                setattr(leave_availibility_remaining, field_name1, new_value)
                # setattr(leave_availibility_remaining, intiall_field_name1, new_value)
                leave_instance.save()
                leave_availibility_remaining.save()

                # leave_availibility_remaining.save()
                notification_save(request.user.username,f"{value} day(s) of {leave_type} was successfully {action_text} for the user {username_from_function}")
                messages.info(request,f"{value} day(s) of {leave_type} was successfully {action_text} for the user {username_from_function}")

                return redirect('AvailLeaveView')


        elif request.resolver_match.url_name == "DownloadView":
            search_id = request.GET.get('search_id')
            if search_id:
                staff_members = User.objects.filter(username=search_id).filter(Q(is_active=True) | Q(is_staff=True), is_superuser=False)

            else:
                staff_members = User.objects.filter(Q(is_active=True) | Q(is_staff=True) , is_superuser=False)
            specific_context = {
                'staff_members':staff_members
            }
            context = merge_contexts(common_context,specific_context)
            return render(request,'custom_admin/download.html' , context = context)


        elif request.resolver_match.url_name == "Download":
            if request.method == 'POST':
                form = LeaveDownloadForm(request.POST)
                if form.is_valid():
                    leave_type = form.cleaned_data['leave_type']

                    # Query data based on leave type
                    if leave_type == 'All':
                        leaves = []
                        for model in [casual_leave, LOP_leave, CH_leave, medicalLeave, earnLeave, vaccationLeave, specialOnduty, onDuty]:
                            leaves.extend(model.objects.filter(username=username))
                    else:
                        model_dict = {
                            'Casual Leave': casual_leave,
                            'LOP Leave': LOP_leave,
                            'CH Leave': CH_leave,
                            'Medical Leave': medicalLeave,
                            'Earn Leave': earnLeave,
                            'Vacation Leave': vaccationLeave,
                            'Onduty': onDuty,
                            'Special Onduty': specialOnduty,
                        }
                        leaves = model_dict[leave_type].objects.filter(username=username)

                    # Create a DataFrame from the queryset
                    data = []

                    for leave in leaves:
                        user_staff = User.objects.get(username = leave.username)
                        staffname = f"{user_staff.first_name} {user_staff.last_name}"
                        date_applied_local = timezone.localtime(leave.date_Applied).strftime("%d/%m/%y %I:%M %p")

                        data.append([
                            leave.username,staffname, leave.leave_type, date_applied_local, leave.from_Date,
                            leave.to_Date, leave.session, leave.remaining, leave.total_leave,
                            leave.status, leave.reason
                        ])
                    df = pd.DataFrame(data, columns=['Username','Staff Name' ,'Leave Type', 'Date Applied', 'From Date', 'To Date', 'Session', 'Remaining', 'Applied Leave', 'Status', 'Reason'])

                    # Create an in-memory Excel file
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='Leaves')
                        workbook = writer.book
                        worksheet = writer.sheets['Leaves']

                        # Set column width and format
                        format = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
                        for col_num, value in enumerate(df.columns.values):
                            max_len = max(df[value].astype(str).map(len).max(), len(value)) + 2  # Add a little extra space
                            worksheet.set_column(col_num, col_num, max_len, format)

                    # Send the response with the Excel file
                    output.seek(0)
                    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = f'attachment; filename={leave_type}_leaves.xlsx'
                    return response
            else:
                form = LeaveDownloadForm()
            return render(request, 'custom_admin/download.html', {'form': form})


        elif request.resolver_match.url_name == "DownloadAll":
            if request.method == 'POST':
                form = LeaveDownloadForm(request.POST)
                if form.is_valid():
                    leave_type = form.cleaned_data['leave_type']

                    # Query data based on leave type
                    if leave_type == 'All':
                        leaves = []
                        for model in [casual_leave, LOP_leave, CH_leave, medicalLeave, earnLeave, vaccationLeave, specialOnduty, onDuty]:
                            leaves.extend(model.objects.all())
                    else:
                        model_dict = {
                            'Casual Leave': casual_leave,
                            'LOP Leave': LOP_leave,
                            'CH Leave': CH_leave,
                            'Medical Leave': medicalLeave,
                            'Earn Leave': earnLeave,
                            'Vacation Leave': vaccationLeave,
                            'Onduty': onDuty,
                            'Special Onduty': specialOnduty,
                        }
                        leaves = model_dict[leave_type].objects.all()

                    # Create a DataFrame from the queryset
                    data = []
                    for leave in leaves:
                        user_staff = User.objects.get(username = leave.username)
                        staffname = f"{user_staff.first_name} {user_staff.last_name}"
                        date_applied_local = timezone.localtime(leave.date_Applied).strftime("%d/%m/%y %I:%M %p")

                        data.append([
                            leave.username,staffname, leave.leave_type, date_applied_local, leave.from_Date,
                            leave.to_Date, leave.session, leave.remaining, leave.total_leave,
                            leave.status, leave.reason
                        ])
                    df = pd.DataFrame(data, columns=['Username','Staff Name' ,'Leave Type', 'Date Applied', 'From Date', 'To Date', 'Session', 'Remaining', 'Applied Leave', 'Status', 'Reason'])

                    # Create an in-memory Excel file
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='Leaves')
                        workbook = writer.book
                        worksheet = writer.sheets['Leaves']

                        # Set column width and format
                        format = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
                        for col_num, value in enumerate(df.columns.values):
                            max_len = max(df[value].astype(str).map(len).max(), len(value)) + 2  # Add a little extra space
                            worksheet.set_column(col_num, col_num, max_len, format)

                    # Send the response with the Excel file
                    output.seek(0)
                    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = f'attachment; filename={leave_type}_leaves.xlsx'
                    return response
            else:
                form = LeaveDownloadForm()
            return render(request, 'custom_admin/download.html', {'form': form})


        elif request.resolver_match.url_name == "LeaveAvailability":

            staff_members = User.objects.filter(Q(is_active=True) | Q(is_staff=True), is_superuser=False)

            # Get the usernames of the filtered users
            staff_usernames = staff_members.values_list('username', flat=True)

            # Filter Leave_Availability based on these usernames
            leave_data = Leave_Availability.objects.filter(username__in=staff_usernames)

            data_dics = [
            {
            'username': leave.username,
            'staff_name': f"{User.objects.get(username=leave.username).first_name} {User.objects.get(username=leave.username).last_name}",
            'casual_remaining': leave.casual_remaining,
            'vaccation_remaining': leave.vaccation_remaining,
            'onduty_remaining': leave.onduty_remaining,
            'medical_leave_remaining': leave.medical_leave_remaining,
            'earn_leave_remaining': leave.earn_leave_remaining,
            'ch_leave_remaining': leave.ch_leave_remaining,
            'permission_remaining':leave.permission_remaining
            } for leave in leave_data
            ]
            specific_context = {
                'data_dics':data_dics
            }
            context = merge_contexts(common_context,specific_context)
            print(staff_usernames)
            return render(request,'custom_admin/leave_availability.html', context)


        elif request.resolver_match.url_name == "DownloadLeaveAvailability":
                staff_members = User.objects.filter(Q(is_active=True) | Q(is_staff=True), is_superuser=False)
                staff_usernames = staff_members.values_list('username', flat=True)

                # Get the leave data for these users
                leave_data = Leave_Availability.objects.filter(username__in=staff_usernames).values(
                    'username',
                    'casual_remaining',
                    'vaccation_remaining',
                    'onduty_remaining',
                    'medical_leave_remaining',
                    'earn_leave_remaining',
                    'ch_leave_remaining'
                )

                # Convert the leave data to a pandas DataFrame
                df = pd.DataFrame(list(leave_data))

                # Create a response object and set the appropriate headers
                response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename=leave_data.xlsx'

                # Use pandas to write the DataFrame to an Excel file
                with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Leave Data')

                return response


        elif request.resolver_match.url_name == "DeleteAndReset":
            if request.method == 'POST':
                    # Filter active and staff users who are not superusers
                staff_members = User.objects.filter(Q(is_active=True) | Q(is_staff=True), is_superuser=False)
                staff_usernames = staff_members.values_list('username', flat=True)

                # Get leave data for the specified models
                model_dict = {
                    'Casual Leave': casual_leave,
                    'LOP Leave': LOP_leave,
                    'CH Leave': CH_leave,
                    'Medical Leave': medicalLeave,
                    'Earn Leave': earnLeave,
                    'Vacation Leave': vaccationLeave,
                    'Onduty': onDuty,
                    'Special Onduty': specialOnduty,
                }

                # Create a DataFrame to hold all leave data
                all_leave_data = []

                for leave_type, model in model_dict.items():
                    leaves = model.objects.filter(username__in=staff_usernames)
                    for leave in leaves:
                        all_leave_data.append([
                            leave.username, leave.leave_type, make_naive(leave.date_Applied), leave.from_Date,
                            leave.to_Date, leave.session, leave.remaining, leave.total_leave,
                            leave.status, leave.reason
                        ])

                df = pd.DataFrame(all_leave_data, columns=[
                    'Username', 'Leave Type', 'Date Applied', 'From Date', 'To Date',
                    'Session', 'Remaining', 'Total Leave', 'Status', 'Reason'
                ])

                # Create an in-memory Excel file
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Leave Data')

                # Send the response with the Excel file
                output.seek(0)
                response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename=leave_data.xlsx'

                # Reset the leave availability
                leave_availability = Leave_Availability.objects.filter(username__in=staff_usernames)
                for record in leave_availability:
                    record.casual_remaining = record.initial_casual_remaining
                    record.vaccation_remaining = record.initial_vaccation_remaining
                    record.onduty_remaining = record.initial_onduty_remaining
                    record.medical_leave_remaining = record.initial_medical_leave_remaining
                    record.earn_leave_remaining = record.initial_earn_leave_remaining
                    record.ch_leave_remaining = record.initial_ch_leave_remaining
                    record.save()

                # Delete leave records
                for model in model_dict.values():
                    model.objects.filter(username__in=staff_usernames).delete()
                CHProof.objects.all().delete()
                    

                return response


        elif request.resolver_match.url_name == "AdminAccount":
            # is_default_password = request.user.check_password("srec@123")
            specific_context = {
                'email':request.user.email,
                # 'is_default_password':is_default_password
            }
            context = merge_contexts(common_context,specific_context)
            return render(request,'custom_admin/account_settings.html',context)

        elif request.resolver_match.url_name == "freeze_dates":
                    # Retrieve or create the FrozenDates object
            try:
                frozen_dates = FrozenDates.objects.get(id=1)  # Assuming only one object exists
            except FrozenDates.DoesNotExist:
                frozen_dates = FrozenDates.objects.create(dates_and_reasons={})

            if request.method == 'POST':
                if 'add_date' in request.POST:
                    form = FreezeDatesForm(request.POST)
                    if form.is_valid():
                        dateinfreeze = form.cleaned_data['date']
                        reason = form.cleaned_data['reason']
                        date_str = dateinfreeze.strftime('%d-%m-%Y')
                        frozen_dates.dates_and_reasons[date_str] = reason
                        frozen_dates.save()
                        messages.success(request, 'Date has been successfully frozen.')
                        return redirect('freeze_dates')

                elif 'delete_date' in request.POST:
                    date_to_delete = request.POST.get('date_to_delete')
                    if date_to_delete in frozen_dates.dates_and_reasons:
                        del frozen_dates.dates_and_reasons[date_to_delete]
                        frozen_dates.save()
                        messages.success(request, f'Date {date_to_delete} has been successfully deleted.')
                        return redirect('freeze_dates')

            form = FreezeDatesForm()
            specific_context = {
                'form': form,
                'frozen_dates': frozen_dates.dates_and_reasons,
            }
            context = merge_contexts(common_context,specific_context)
            return render(request, 'custom_admin/freeze_dates.html', context)


        elif request.resolver_match.url_name == "AdminCancellation":
            data_list_of_dicts=[]
            leave_models = [casual_leave, LOP_leave, earnLeave, vaccationLeave, onDuty, specialOnduty, medicalLeave, CH_leave,maternityLeave,Permission]
            for model in leave_models:
                result = model.objects.filter(status='Pending')
                print(result)

                for item in result:
                    result1 = CancelLeave.objects.filter(unique_id = item.unique_id , leave_type = item.leave_type).first()
                    print(result1)
                    if result1:
                        user_name = User.objects.get(username=item.username)
                        if item.leave_type == 'Permission':
                            data_dict = {
                                "cancel_reason": result1.reason if result1 else 'N/A',
                                "reason": "Matheesh",
                                "unique_id": item.unique_id,
                                "staff_name": f"{user_name.first_name} {user_name.last_name}",
                                "username": item.username,
                                "department": StaffDetails.objects.get(username_copy=item.username).department,
                                "leave_type": item.leave_type,
                                "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                                "from_Date": datetime.strptime(item.On_date, "%Y-%m-%d").strftime("%d-%m-%y"),
                                "session": item.session.upper(),
                                "remaining": item.remaining,
                                "status": item.status,
                                "document_url": settings.MEDIA_URL + str(result1.document) if result1 else '',
                                "cancel_document_url": settings.MEDIA_URL + str(item.document)
                            }
                        else:
                            data_dict = {
                                "cancel_reason": result1.reason if result1 else 'N/A',
                                "reason": item.reason,
                                "unique_id": item.unique_id,
                                "staff_name": f"{user_name.first_name} {user_name.last_name}",
                                "username": item.username,
                                "department": StaffDetails.objects.get(username_copy=item.username).department,
                                "leave_type": item.leave_type,
                                "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                                "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                                "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                                "session": item.session.upper(),
                                "remaining": item.remaining,
                                "total_leave": item.total_leave,
                                "status": item.status,
                                "document_url": settings.MEDIA_URL + str(result1.document) if result1 else '',
                                "cancel_document_url": settings.MEDIA_URL + str(item.document)
                            }
                        data_list_of_dicts.append(data_dict)
        
                

        
        
            specific_context = {
                'pending_leaves': data_list_of_dicts
            }
            context = merge_contexts(common_context,specific_context)
            return render(request,'custom_admin/cancellation_request.html',context=context)
        
        elif request.resolver_match.url_name == "LeaveData":
            leave_models = [casual_leave, LOP_leave, earnLeave, vaccationLeave, onDuty, specialOnduty, medicalLeave, CH_leave,maternityLeave]

            leave_data = []

            for model in leave_models:
                for item in model.objects.all():
                    try:
                        staff_details = StaffDetails.objects.get(username_copy=item.username)
                        user_name = StaffDetails.objects.get(username_copy=item.username)
                    except StaffDetails.DoesNotExist:
                        continue  # Skip if no matching staff details

                    formatted_data = {
                        "reason" : item.reason,
                        "unique_id": item.unique_id,
                        "username": item.username,
                        "department" : StaffDetails.objects.get(username_copy = item.username).department,
                        "staff_name": user_name.first_name + ' ' + user_name.last_name,
                        "leave_type": item.leave_type,
                        "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                        "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                        "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                        "session": item.session.upper(),
                        "remaining": item.remaining,
                        "total_leave": item.total_leave,
                        "status" : item.status,
                        "document_url": settings.MEDIA_URL + str(item.document)
                    }
                    print(settings.MEDIA_URL + str(item.document))
                    
                    leave_data.append(formatted_data)
            
            specific_context={
                        'leave_data': leave_data
                    }
            context = merge_contexts(common_context,specific_context)

            return render(request, 'custom_admin/leave_data.html', context)
        
            

        today = date.today()
        print(today)


        # Query each model and count the instances where date_Applied matches today's date
        casual_leave_count = casual_leave.objects.filter(date_Applied__date=today).count()
        LOP_leave_count = LOP_leave.objects.filter(date_Applied__date=today).count()
        CH_leave_count = CH_leave.objects.filter(date_Applied__date=today).count()
        medicalLeave_count = medicalLeave.objects.filter(date_Applied__date=today).count()
        earnLeave_count = earnLeave.objects.filter(date_Applied__date=today).count()
        vaccationLeave_count = vaccationLeave.objects.filter(date_Applied__date=today).count()
        specialOnduty_count = specialOnduty.objects.filter(date_Applied__date=today).count()
        onDuty_count = onDuty.objects.filter(date_Applied__date=today).count()
        maternityLeave_count = maternityLeave.objects.filter(date_Applied__date=today).count()

        # Sum up the counts from all models
        total_count = (
            casual_leave_count + LOP_leave_count + CH_leave_count +
            medicalLeave_count + earnLeave_count + vaccationLeave_count +
            specialOnduty_count + onDuty_count + maternityLeave_count
        )



        specific_context = {
            'total_user': User.objects.filter(Q(is_active=True) | Q(is_staff=True) , is_superuser=False).count(),
            'total_hod' : User.objects.filter(is_active=True,is_staff=True, is_superuser=False).count(),
            'today_applied' : total_count,

            'announcement_list':Announcement.objects.all().order_by('-timestamp'),
        }

        context = merge_contexts(common_context,specific_context)
        print(context)
        return render(request,'custom_admin/index.html', context=context)


def get_hod_common_context(request):
    hod_department = StaffDetails.objects.get(username_copy = request.user.username).department
    HOD_Department = hod_department.strip().replace(" ", "").upper()
    dept_users = StaffDetails.objects.filter(department=HOD_Department).values_list('user__username', flat=True)
    casual_leave_count = casual_leave.objects.filter(status='Reviewing', username__in=dept_users).count()
    LOP_leave_count = LOP_leave.objects.filter(status='Reviewing', username__in=dept_users).count()
    CH_leave_count = CH_leave.objects.filter(status='Reviewing', username__in=dept_users).count()
    medicalLeave_count = medicalLeave.objects.filter(status='Reviewing', username__in=dept_users).count()
    earnLeave_count = earnLeave.objects.filter(status='Reviewing', username__in=dept_users).count()
    vaccationLeave_count = vaccationLeave.objects.filter(status='Reviewing', username__in=dept_users).count()
    specialOnduty_count = specialOnduty.objects.filter(status='Reviewing', username__in=dept_users).count()
    onDuty_count = onDuty.objects.filter(status='Reviewing', username__in=dept_users).count()
    maternityLeave_count = maternityLeave.objects.filter(status='Reviewing', username__in=dept_users).count()
    permission_count = Permission.objects.filter(status="Reviewing",username__in=dept_users).count()

    total_approved_count = (
        casual_leave_count + LOP_leave_count + CH_leave_count + medicalLeave_count +
        earnLeave_count + vaccationLeave_count + specialOnduty_count + onDuty_count + maternityLeave_count
    )


    leave_types = [
        casual_leave, LOP_leave, CH_leave, medicalLeave,
        earnLeave, vaccationLeave, specialOnduty, onDuty,maternityLeave
    ]

    # Initialize list to store all records
    all_records = []

    # Query and concatenate records for each leave type
    for leave_type in leave_types:
        records = leave_type.objects.filter(status='Reviewing').order_by('-date_Applied')
        all_records.extend(records)

    # Sort all records by date applied in descending order
    all_records_sorted = sorted(all_records, key=lambda x: x.date_Applied, reverse=True)

    # Get recent 5 records
    recent_records = all_records_sorted[:5]

    # Filter recent data for ECE department
    recent_data = []
    ece_staff_usernames = StaffDetails.objects.filter(department=HOD_Department).values_list('username_copy', flat=True)

    for record in recent_records:
        if record.username in ece_staff_usernames:
            recent_data.append({'username': record.username, 'leave_type': record.leave_type})


    hod_common_context = {
        'is_hod':True,
        'pending':int(total_approved_count),
        'permission_count':permission_count,
        'recent_data': recent_data,
        'admin':HOD_Department
    }

    return hod_common_context



@login_required
def hod_page(request,username=None):
    if request.user.is_staff and request.user.is_active:
        hod_department = StaffDetails.objects.get(username_copy = request.user.username).department
        print(hod_department)
        HOD_Department = hod_department.strip().replace(" ", "").upper()
        print(HOD_Department)
        hod_common_context = get_hod_common_context(request)
        if request.resolver_match.url_name == 'HODNewRequests':
            print("New Request")

            result = casual_leave.objects.filter(username__in=StaffDetails.objects.filter(department=HOD_Department).values_list('username_copy', flat=True))

            data_list_of_dicts = []
            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)
                print(data_list_of_dicts)

            result = LOP_leave.objects.filter(username__in=StaffDetails.objects.filter(department=HOD_Department).values_list('username_copy', flat=True))

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                print(settings.MEDIA_URL + str(item.document) )
                data_list_of_dicts.append(data_dict)
                # print(data_list_of_dicts)

            result = CH_leave.objects.filter(username__in=StaffDetails.objects.filter(department=HOD_Department).values_list('username_copy', flat=True))

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)

                }
                data_list_of_dicts.append(data_dict)

            result = medicalLeave.objects.filter(username__in=StaffDetails.objects.filter(department=HOD_Department).values_list('username_copy', flat=True))

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)

            result = earnLeave.objects.filter(username__in=StaffDetails.objects.filter(department=HOD_Department).values_list('username_copy', flat=True))

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)

            result = vaccationLeave.objects.filter(username__in=StaffDetails.objects.filter(department=HOD_Department).values_list('username_copy', flat=True))

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)

            result = specialOnduty.objects.filter(username__in=StaffDetails.objects.filter(department=HOD_Department).values_list('username_copy', flat=True))

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)

            result = onDuty.objects.filter(username__in=StaffDetails.objects.filter(department=HOD_Department).values_list('username_copy', flat=True))

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)

            result = maternityLeave.objects.filter(username__in=StaffDetails.objects.filter(department=HOD_Department).values_list('username_copy', flat=True))

            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "leave_type": item.leave_type,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "from_Date": datetime.strptime(item.from_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "to_Date": datetime.strptime(item.to_Date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                data_list_of_dicts.append(data_dict)
            print(data_list_of_dicts)

            specific_context = {
                'admin_list' : data_list_of_dicts,

            }
            context = merge_contexts(hod_common_context,specific_context)

            return render(request, 'custom_admin/hod_new_requests.html', context=context)



        elif request.resolver_match.url_name == 'HODLeaveAvailability':
            print("HI")

            staff_members = User.objects.filter(Q(is_active=True) | Q(is_staff=True), is_superuser=False)
            staff_usernames = staff_members.values_list('username', flat=True)

            # Step 2: Filter Leave_Availability based on these usernames
            leave_data = Leave_Availability.objects.filter(username__in=staff_usernames)

            # Step 3: Join with Staff_Details and filter for department 'ECE'
            ece_staff = StaffDetails.objects.filter(department=HOD_Department, username_copy__in=leave_data.values_list('username', flat=True))
            ece_usernames = ece_staff.values_list('username_copy', flat=True)

            # Step 4: Filter Leave_Availability for ECE staff and create data_dics
            ece_leave_data = leave_data.filter(username__in=ece_usernames)
            data_dics = [
                {
                    'username': leave.username,
                    'staff_name': f"{User.objects.get(username=leave.username).first_name} {User.objects.get(username=leave.username).last_name}",
                    'casual_remaining': leave.casual_remaining,
                    'vaccation_remaining': leave.vaccation_remaining,
                    'onduty_remaining': leave.onduty_remaining,
                    'medical_leave_remaining': leave.medical_leave_remaining,
                    'earn_leave_remaining': leave.earn_leave_remaining,
                    'ch_leave_remaining': leave.ch_leave_remaining,
                } for leave in ece_leave_data
            ]

            # Step 5: Pass context to template
            specific_context = {
                'data_dics': data_dics
            }
            context = merge_contexts(hod_common_context,specific_context)

            return render(request, 'custom_admin/leave_availability.html' ,context)


        elif request.resolver_match.url_name == "HODDownloadLeaveAvailability":
            print('JI')
            staff_members = User.objects.filter(Q(is_active=True) | Q(is_staff=True), is_superuser=False)
            staff_usernames = staff_members.values_list('username', flat=True)

            ece_staff = StaffDetails.objects.filter(department=HOD_Department, username_copy__in=staff_usernames)
            ece_usernames = ece_staff.values_list('username_copy', flat=True)
            # Get the leave data for these users
            print(ece_usernames)
            leave_data = Leave_Availability.objects.filter(username__in=ece_usernames).values(
                'username',
                'casual_remaining',
                'vaccation_remaining',
                'onduty_remaining',
                'medical_leave_remaining',
                'earn_leave_remaining',
                'ch_leave_remaining',
                'permission_remaining'
            )

            # Convert the leave data to a pandas DataFrame
            df = pd.DataFrame(list(leave_data))

            # Create a response object and set the appropriate headers
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=leave_data.xlsx'

            # Use pandas to write the DataFrame to an Excel file
            with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Leave Data')

            return response


        elif request.resolver_match.url_name == "HODDownloadView":
            search_id = request.GET.get('search_id')

            if search_id:
                staff_members = User.objects.filter(username=search_id).filter(Q(is_active=True) | Q(is_staff=True), is_superuser=False)
            else:
                staff_members = User.objects.filter(Q(is_active=True) | Q(is_staff=True), is_superuser=False)

            # Join with Staff_Details to filter for department 'ECE'
            ece_staff = StaffDetails.objects.filter(department=HOD_Department, username_copy__in=staff_members.values_list('username', flat=True))
            ece_usernames = ece_staff.values_list('username_copy', flat=True)

            # Filter User for ECE staff
            ece_staff_members = staff_members.filter(username__in=ece_usernames)

            specific_context = {
                'staff_members': ece_staff_members
            }
            context = merge_contexts(hod_common_context, specific_context)
            return render(request, 'custom_admin/download.html', context=context)


        elif request.resolver_match.url_name == "HODDownload":
            if request.method == 'POST':
                form = LeaveDownloadForm(request.POST)
                if form.is_valid():
                    leave_type = form.cleaned_data['leave_type']

                    # Query data based on leave type
                    if leave_type == 'All':
                        leaves = []
                        for model in [casual_leave, LOP_leave, CH_leave, medicalLeave, earnLeave, vaccationLeave, specialOnduty, onDuty]:
                            leaves.extend(model.objects.filter(username=username))
                    else:
                        model_dict = {
                            'Casual Leave': casual_leave,
                            'LOP Leave': LOP_leave,
                            'CH Leave': CH_leave,
                            'Medical Leave': medicalLeave,
                            'Earn Leave': earnLeave,
                            'Vacation Leave': vaccationLeave,
                            'Onduty': onDuty,
                            'Special Onduty': specialOnduty,
                        }
                        leaves = model_dict[leave_type].objects.filter(username=username)

                    # Create a DataFrame from the queryset
                    data = []
                    for leave in leaves:
                        user_staff = User.objects.get(username = leave.username)
                        staffname = f"{user_staff.first_name} {user_staff.last_name}"
                        date_applied_local = timezone.localtime(leave.date_Applied).strftime("%d/%m/%y %I:%M %p")

                        data.append([
                            leave.username,staffname, leave.leave_type, date_applied_local, leave.from_Date,
                            leave.to_Date, leave.session, leave.remaining, leave.total_leave,
                            leave.status, leave.reason
                        ])
                    df = pd.DataFrame(data, columns=['Username','Staff Name' ,'Leave Type', 'Date Applied', 'From Date', 'To Date', 'Session', 'Remaining', 'Applied Leave', 'Status', 'Reason'])

                    # Create an in-memory Excel file
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='Leaves')
                        workbook = writer.book
                        worksheet = writer.sheets['Leaves']

                        # Set column width and format
                        format = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
                        for col_num, value in enumerate(df.columns.values):
                            max_len = max(df[value].astype(str).map(len).max(), len(value)) + 2  # Add a little extra space
                            worksheet.set_column(col_num, col_num, max_len, format)

                    # Send the response with the Excel file
                    output.seek(0)
                    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = f'attachment; filename={leave_type}_leaves.xlsx'
                    return response
            else:
                form = LeaveDownloadForm()
            return render(request, 'custom_admin/download.html', {'form': form})


        elif request.resolver_match.url_name == "HODDownloadAll":
            if request.method == 'POST':
                form = LeaveDownloadForm(request.POST)
                if form.is_valid():
                    leave_type = form.cleaned_data['leave_type']

                    # Query ECE department staff members
                    ece_staff = StaffDetails.objects.filter(department=HOD_Department)
                    ece_usernames = ece_staff.values_list('username_copy', flat=True)

                    # Query data based on leave type
                    if leave_type == 'All':
                        leaves = []
                        for model in [casual_leave, LOP_leave, CH_leave, medicalLeave, earnLeave, vaccationLeave, specialOnduty, onDuty]:
                            leaves.extend(model.objects.filter(username__in=ece_usernames))
                    else:
                        model_dict = {
                            'Casual Leave': casual_leave,
                            'LOP Leave': LOP_leave,
                            'CH Leave': CH_leave,
                            'Medical Leave': medicalLeave,
                            'Earn Leave': earnLeave,
                            'Vacation Leave': vaccationLeave,
                            'Onduty': onDuty,
                            'Special Onduty': specialOnduty,
                        }
                        leaves = model_dict[leave_type].objects.filter(username__in=ece_usernames)

                    # Create a DataFrame from the queryset
                    data = []
                    for leave in leaves:
                        user_staff = User.objects.get(username = leave.username)
                        staffname = f"{user_staff.first_name} {user_staff.last_name}"
                        date_applied_local = timezone.localtime(leave.date_Applied).strftime("%d/%m/%y %I:%M %p")

                        data.append([
                            leave.username,staffname, leave.leave_type, date_applied_local, leave.from_Date,
                            leave.to_Date, leave.session, leave.remaining, leave.total_leave,
                            leave.status, leave.reason
                        ])
                    df = pd.DataFrame(data, columns=['Username','Staff Name' ,'Leave Type', 'Date Applied', 'From Date', 'To Date', 'Session', 'Remaining', 'Applied Leave', 'Status', 'Reason'])
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='Leaves')
                        workbook = writer.book
                        worksheet = writer.sheets['Leaves']

                        # Set column width and format
                        format = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
                        for col_num, value in enumerate(df.columns.values):
                            max_len = max(df[value].astype(str).map(len).max(), len(value)) + 2  # Add a little extra space
                            worksheet.set_column(col_num, col_num, max_len, format)

                    # Send the response with the Excel file
                    output.seek(0)
                    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = f'attachment; filename={leave_type}_leaves.xlsx'
                    return response
            else:
                form = LeaveDownloadForm()
            return render(request, 'custom_admin/download.html', {'form': form})


        elif request.resolver_match.url_name == "HODAdminAccount":
            # is_default_password = request.user.check_password('srec@123')
            specific_context = {
                'email':request.user.email,
                # 'is_default_password':is_default_password
            }
            context = merge_contexts(hod_common_context,specific_context)
            return render(request,'custom_admin/account_settings.html',context)


        elif request.resolver_match.url_name == "PermissionRequests":
            result = Permission.objects.filter(username__in=StaffDetails.objects.filter(department=HOD_Department).values_list('username_copy', flat=True))

            data_list_of_dicts = []
            for item in result:
                user_name = User.objects.get(username=item.username)
                data_dict = {
                    "reason" : item.reason,
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "department" : StaffDetails.objects.get(username_copy = item.username).department,
                    "staff_name": user_name.first_name + ' ' + user_name.last_name,
                    "date_Applied": timezone.localtime(item.date_Applied).strftime("%d-%m-%y %I:%M %p"),
                    "session": item.session.upper(),
                    "On_date": datetime.strptime(item.On_date, "%Y-%m-%d").strftime("%d-%m-%y"),
                    "leave_type": item.leave_type,
                    "remaining": item.remaining,
                    "status" : item.status,
                    "document_url": settings.MEDIA_URL + str(item.document)
                }
                print(settings.MEDIA_URL + str(item.document) )
                data_list_of_dicts.append(data_dict)
            specific_context = {
                'admin_list':data_list_of_dicts
            }
            context = merge_contexts(hod_common_context,specific_context)
            return render(request,"custom_admin/permission_requests.html",context)

        


        today = timezone.now().date()
        dept_users = StaffDetails.objects.filter(department=hod_department).values_list('user__username', flat=True)
        casual_leave_count = casual_leave.objects.filter(date_Applied__date=today, username__in=dept_users).count()
        LOP_leave_count = LOP_leave.objects.filter(date_Applied__date=today, username__in=dept_users).count()
        CH_leave_count = CH_leave.objects.filter(date_Applied__date=today, username__in=dept_users).count()
        medicalLeave_count = medicalLeave.objects.filter(date_Applied__date=today, username__in=dept_users).count()
        earnLeave_count = earnLeave.objects.filter(date_Applied__date=today, username__in=dept_users).count()
        vaccationLeave_count = vaccationLeave.objects.filter(date_Applied__date=today, username__in=dept_users).count()
        specialOnduty_count = specialOnduty.objects.filter(date_Applied__date=today, username__in=dept_users).count()
        onDuty_count = onDuty.objects.filter(date_Applied__date=today, username__in=dept_users).count()


        total_count = (
            casual_leave_count + LOP_leave_count + CH_leave_count +
            medicalLeave_count + earnLeave_count + vaccationLeave_count +
            specialOnduty_count + onDuty_count
        )





        specific_context={
            'total_user': User.objects.filter(Q(is_active=True) | Q(is_staff=True) , is_superuser=False).count(),
            'total_hod' : StaffDetails.objects.filter(department = hod_department).count(),
            'today_applied' : total_count,
            'announcement_list':Announcement.objects.all().order_by('-timestamp')
        }
        context = merge_contexts(hod_common_context,specific_context)
        return render(request,'custom_admin/index.html',context)






def requests_handling(request):
    if request.method == "POST":
        data = request.POST
        print(data)


        if data.get('partial')  == 'yes':
            subject = "Leave Update"
            body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap');
        
        body {{
            font-family: 'Montserrat', sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background: linear-gradient(to bottom right, #f0f4f8, #dbe2e8);
            position: relative;
            overflow: hidden;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
            position: relative;
            z-index: 1;
        }}
        h1 {{
            font-size: 26px;
            color: #333;
            margin-bottom: 20px;
        }}
        p {{
            font-size: 16px;
            margin: 10px 0;
        }}
        .footer {{
            font-size: 14px;
            color: #666;
            margin-top: 20px;
        }}
        .footer p {{
            margin: 5px 0;
        }}
        .background-particles {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url('https://www.transparenttextures.com/patterns/white-squares.png') repeat;
            opacity: 0.1;
            z-index: 0;
        }}
        h2 {{
            color: #0056b3;
            font-size: 22px;
        }}
    </style>
</head>
<body>
    <div class="background-particles"></div>
    <div class="container">
        <h2>Dear Sir/Madam,</h2>
        <p>We would like to inform you that your <strong>{data.get('rowData[leave_type]')}</strong> request, applied on <strong>{data.get('rowData[date_Applied]')}</strong>, has been <strong>{data.get('action')}</strong> by HOD.</p>
        <p><strong>Reason:</strong> {data.get('decreason')}</p>
        <p>In case of any queries, contact us.</p>
        <div class="footer">
            <p>With regards,</p>
            <p>Administrative Office,<br>
            Sri Ramakrishna Engineering College,<br>
            Vattamalaipalayam,<br>
            Coimbatore - 641022.</p>
        </div>
    </div>
</body>
</html>
"""

            username = data.get('rowData[username]')
            to_email = User.objects.get(username = username).email
            print(to_email)

            leave_type = data.get('rowData[leave_type]')
            unique_id = int(data.get('rowData[unique_id]'))
            print(leave_type)


            if leave_type == 'LOP Leave':
                result = LOP_leave.objects.filter(unique_id = unique_id)
                action = str(data.get('action'))
                if str(action) == 'Declined':
                    action = 'Declined(1)'

                elif str(action) == 'Approved':
                        action = 'Approved(1)'
                result.update(status=action)
            elif leave_type == "CH Leave":
                result = CH_leave.objects.filter(unique_id = unique_id)
                action = str(data.get('action'))
                if str(action) == 'Declined':
                    action = 'Declined(1)'
                elif str(action) == 'Approved':
                    action = 'Approved(1)'
                result.update(status=action)
            elif leave_type == "Casual Leave":
                result = casual_leave.objects.filter(unique_id = unique_id)
                action = str(data.get('action'))
                if str(action) == 'Declined':
                    action = 'Declined(1)'
                elif str(action) == 'Approved':
                    action = 'Approved(1)'
                result.update(status=action)
            elif leave_type == "Medical Leave":
                result = medicalLeave.objects.filter(unique_id = unique_id)
                action = str(data.get('action'))
                if str(action) == 'Declined':
                    action = 'Declined(1)'
                elif str(action) == 'Approved':
                    action = 'Approved(1)'
                result.update(status=action)
            elif leave_type == "Accumulation":
                result = earnLeave.objects.filter(unique_id = unique_id)
                action = str(data.get('action'))
                if str(action) == 'Declined':
                    action = 'Declined(1)'
                elif str(action) == 'Approved':
                    action = 'Approved(1)'
                result.update(status=action)
            elif leave_type == "Encashment":
                result = earnLeave.objects.filter(unique_id = unique_id)
                action = str(data.get('action'))
                if str(action) == 'Declined':
                    action = 'Declined(1)'
                elif str(action) == 'Approved':
                    action = 'Approved(1)'
                result.update(status=action)
            elif leave_type == "Vaccation Leave":
                result = vaccationLeave.objects.filter(unique_id = unique_id)
                action = str(data.get('action'))
                if str(action) == 'Declined':
                    action = 'Declined(1)'
                elif str(action) == 'Approved':
                    action = 'Approved(1)'
                result.update(status=action)
            elif leave_type == "Vaccation Earn Leave":
                result = vaccationLeave.objects.filter(unique_id = unique_id)
                action = str(data.get('action'))
                if str(action) == 'Declined':
                    action = 'Declined(1)'
                elif str(action) == 'Approved':
                    action = 'Approved(1)'
                result.update(status=action)
            elif leave_type == "Special Onduty":
                result = specialOnduty.objects.filter(unique_id = unique_id)
                action = str(data.get('action'))
                if str(action) == 'Declined':
                    action = 'Declined(1)'
                elif str(action) == 'Approved':
                    action = 'Approved(1)'
                result.update(status=action)
            elif leave_type == "Sevatical Special Onduty":
                result = specialOnduty.objects.filter(unique_id = unique_id)
                action = str(data.get('action'))
                if str(action) == 'Declined':
                    action = 'Declined(1)'
                elif str(action) == 'Approved':
                    action = 'Approved(1)'
                result.update(status=action)
            elif leave_type == "Onduty":
                result = onDuty.objects.filter(unique_id = unique_id)
                action = str(data.get('action'))
                if str(action) == 'Declined':
                    action = 'Declined(1)'
                elif str(action) == 'Approved':
                    action = 'Approved(1)'
                result.update(status=action)
            elif leave_type == "Maternity Leave":
                result = maternityLeave.objects.filter(unique_id = unique_id)
                action = str(data.get('action'))
                if str(action) == 'Declined':
                    action = 'Declined(1)'
                elif str(action) == 'Approved':
                    action = 'Approved(1)'
                result.update(status=action)
            elif leave_type == "Permission":
                result = Permission.objects.filter(unique_id = unique_id)
                action = str(data.get('action'))
                reducing_remaining = Leave_Availability.objects.get(username = username)
                if str(action) == 'Approved':
                    total_leave = 1
                    remaining = float(reducing_remaining.permission_remaining) - float(total_leave)
                    reducing_remaining.permission_remaining = remaining
                    reducing_remaining.save()
                    result.update(status=data.get('action'))
                    body = f"""

                        Hello {data.get('rowData[username]')},

                        We would like to inform you that your {data.get('rowData[leave_type]')} request, applied on {data.get('rowData[date_Applied]')}, has been {data.get('action')}.

                            Request Details:
                                - Leave Type: {data.get('rowData[leave_type]')}
                                - Applied Date: {data.get('rowData[date_Applied]')}
                                - Reason: {data.get('rowData[reason]')}
                                - Session: {data.get('rowData[session]')}
                                - Remaining Leave: {data.get('rowData[remaining]')}

                                Status: {data.get('action')}

                            If you have any questions or concerns, please feel free to contact us.

                        With regards,
                            Administrative Office,
                            Sri Ramakrishna Engineering College,
                            Vattamalaipalayam,
                            Coimbatore - 641022.
                        """
                    body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap');
        
        body {{
            font-family: 'Roboto', sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(to bottom right, #f9f9f9, #e0e0e0);
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        h2 {{
            color: #0056b3;
            font-size: 22px;
        }}
        p {{
            font-size: 16px;
            margin: 10px 0;
        }}
        .details {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .details p {{
            margin: 5px 0;
        }}
        .footer {{
            font-size: 14px;
            color: #666;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Dear Sir/Madam,</h2>
        <p>   We would like to inform you that your <strong>{data.get('rowData[leave_type]')}</strong> request, applied on <strong>{data.get('rowData[date_Applied]')}</strong>, has been <strong>{data.get('action')}</strong>.</p>
        
        <div class="details">
            <p><strong>Request Details:</strong></p>
            <p>Leave Type: {data.get('rowData[leave_type]')}</p>
            <p>Applied Date: {data.get('rowData[date_Applied]')}</p>
            <p>Reason: {data.get('rowData[reason]')}</p>
            <p>Session: {data.get('rowData[session]')}</p>
            <p>Remaining: {float(data.get('rowData[remaining]'))-float(1)}</p>
            <p><strong>Status:</strong> {data.get('action')}</p>
        </div>
        
        <p>In case of any queries, contact us.</p>
        
        <div class="footer">
            <p>With regards,</p>
            <p>Administrative Office,<br>
            Sri Ramakrishna Engineering College,<br>
            Vattamalaipalayam,<br>
            Coimbatore - 641022.</p>
        </div>
    </div>
</body>
</html>
"""

                    
                    send_email(subject, body, to_email,is_html=True)

                elif str(action)== 'Declined':
                    result.update(status='Declined')
                    send_email(subject, body, to_email,is_html=True)
                    
            
            if action =='Declined(1)':
                print("JJJJJJJJJJJ")
                send_email(subject, body, to_email,is_html=True)
                staff_notify = StaffDetails.objects.get(username_copy = data.get('rowData[username]'))
                notification_message = f"Your {data.get('rowData[leave_type]')} request was Declined by HOD"
                staff_notify.notification_message = notification_message
                staff_notify.notification_display = True

                staff_notify.save()
            elif action == 'Approved(1)':
                staff_notify = StaffDetails.objects.get(username_copy = data.get('rowData[username]'))
                notification_message = f"Your {data.get('rowData[leave_type]')} request was Approved by HOD"
                staff_notify.notification_message = notification_message
                staff_notify.notification_display = True
                staff_notify.save()




        elif data.get('partial')  == 'no':
            print(data)
            leave_type = data.get('rowData[leave_type]')

            unique_id = int(data.get('rowData[unique_id]'))
            username = data.get('rowData[username]')
            print(username)
            to_email = User.objects.get(username=username).email
            print(to_email)
            try:
                remaining_leave = float(data.get('rowData[remaining]', '0'))
            except ValueError:
                remaining_leave = 0  # Default value if conversion fails

            # Total leave is assumed to be a valid float
            total_leave = float(data.get('rowData[total_leave]', '0'))
            body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap');
        
        body {{
            font-family: 'Montserrat', sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background: linear-gradient(to bottom right, #f0f4f8, #dbe2e8);
            position: relative;
            overflow: hidden;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
            position: relative;
            z-index: 1;
        }}
        h1, h2 {{
            color: #333;
            font-weight: 600;
        }}
        h1 {{
            font-size: 26px;
            margin-bottom: 15px;
        }}
        h2 {{
            font-size: 22px;
            margin-top: 25px;
            margin-bottom: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        table th, table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        table th {{
            background: linear-gradient(to right, #007bff, #00c6ff);
            color: #ffffff;
            font-size: 16px;
        }}
        table td {{
            font-size: 14px;
        }}
        .footer {{
            font-size: 14px;
            color: #666;
            margin-top: 20px;
        }}
        .footer p {{
            margin: 5px 0;
        }}
        h2 {{
            color: #0056b3;
            font-size: 22px;
        }}
        .background-particles {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url('https://www.transparenttextures.com/patterns/white-squares.png') repeat;
            opacity: 0.1;
            z-index: 0;
        }}
    </style>
</head>
<body>
    <div class="background-particles"></div>
    <div class="container">
        <h2>Dear Sir/Madam,</h2>
        <p>   We would like to inform you that your <strong>{data.get('rowData[leave_type]')}</strong> request, applied on <strong>{data.get('rowData[date_Applied]')}</strong>, has been <strong>{data.get('action')}</strong>.</p>
        <h2>Request Details:</h2>
        <table>
            <tr><th>Leave Type</th><td>{data.get('rowData[leave_type]')}</td></tr>
            <tr><th>Applied Date</th><td>{data.get('rowData[date_Applied]')}</td></tr>
            <tr><th>From Date</th><td>{data.get('rowData[from_Date]')}</td></tr>
            <tr><th>To Date</th><td>{data.get('rowData[to_Date]')}</td></tr>
            <tr><th>Reason</th><td>{data.get('rowData[reason]')}</td></tr>
            <tr><th>Session</th><td>{data.get('rowData[session]')}</td></tr>
            <tr><th>Total Leave</th><td>{data.get('rowData[total_leave]')}</td></tr>
            {f'<tr><th>Remaining Leave</th><td>{remaining_leave - total_leave}</td></tr>' if remaining_leave > 0 else ''}
            <tr><th>Status</th><td>{data.get('action')}</td></tr>
        </table>
        <p>In case of any queries, please contact us.</p>
        <div class="footer">
            <p>With regards,</p>
            <p>Administrative Office,<br>
            Sri Ramakrishna Engineering College,<br>
            Vattamalaipalayam,<br>
            Coimbatore - 641022.</p>
        </div>
    </div>
</body>
</html>
"""


            if data.get('action') == "Declined":
                body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap');
        
        body {{
            font-family: 'Montserrat', sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background: linear-gradient(to bottom right, #f0f4f8, #dbe2e8);
            position: relative;
            overflow: hidden;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
            position: relative;
            z-index: 1;
        }}
        h1 {{
            font-size: 26px;
            color: #333;
            margin-bottom: 20px;
        }}
        p {{
            font-size: 16px;
            margin: 10px 0;
        }}
        .footer {{
            font-size: 14px;
            color: #666;
            margin-top: 20px;
        }}
        .footer p {{
            margin: 5px 0;
        }}
        .background-particles {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url('https://www.transparenttextures.com/patterns/white-squares.png') repeat;
            opacity: 0.1;
            z-index: 0;
        }}
    </style>
</head>
<body>
    <div class="background-particles"></div>
    <div class="container">
        <p>Dear Sir/Madam,</p>
        <p>We would like to inform you that your <strong>{data.get('rowData[leave_type]')}</strong> request, applied on <strong>{data.get('rowData[date_Applied]')}</strong>, has been <strong>{data.get('action')}</strong>.</p>
        <p><strong>Reason:</strong> {data.get('decreason')}</p>
        <p>If you have any queries, please do not hesitate to contact us.</p>
        <div class="footer">
            <p>With regards,</p>
            <p>Administrative Office,<br>
            Sri Ramakrishna Engineering College,<br>
            Vattamalaipalayam,<br>
            Coimbatore - 641022.</p>
        </div>
    </div>
</body>
</html>
"""


            if leave_type == 'LOP Leave':
                result = LOP_leave.objects.filter(unique_id = unique_id)
                result.update(status=data.get('action'))

                username = data.get('rowData[username]')

                subject = "Leave Update"

                send_email(subject, body, to_email,is_html=True)

            elif leave_type == 'Special Onduty':
                result = specialOnduty.objects.filter(unique_id = unique_id)
                result.update(status=data.get('action'))

                subject = "Leave Update"

                send_email(subject, body, to_email,is_html=True)

                print("Approved")

            elif leave_type == 'Sevatical Special Onduty':
                result = specialOnduty.objects.filter(unique_id = unique_id)
                result.update(status=data.get('action'))
                subject = "Leave Update"

                send_email(subject, body, to_email,is_html=True)

                print("Approved")

            elif leave_type == 'Vaccation Leave':
                result = vaccationLeave.objects.filter(unique_id = unique_id)
                result.update(status=data.get('action'))
                reducing_remaining = Leave_Availability.objects.get(username = data.get('rowData[username]'))
                if data.get('action') == "Approved":
                    total_leave = data.get('rowData[total_leave]')
                    remaining = float(reducing_remaining.vaccation_remaining) - float(total_leave)
                    reducing_remaining.vaccation_remaining = remaining
                    reducing_remaining.save()



                subject = "Leave Update"

                send_email(subject, body, to_email,is_html=True)

                print("Approved")

            elif leave_type == 'Vaccation Earn Leave':
                result = vaccationLeave.objects.filter(unique_id = unique_id)
                result.update(status=data.get('action'))

                subject = "Leave Update"

                send_email(subject, body, to_email,is_html=True)

                print("Approved")

            elif leave_type == "CH Leave":
                result = CH_leave.objects.filter(unique_id = unique_id)

                result.update(status=data.get('action'))

                requesting_remaining = Leave_Availability.objects.get(username = data.get('rowData[username]'))

                if data.get('action') == "Approved":
                    total_leave = data.get('rowData[total_leave]')
                    remaining = float(requesting_remaining.ch_leave_remaining) - float(total_leave)
                    requesting_remaining.ch_leave_remaining = remaining
                    requesting_remaining.save()
                #     remaining = result1.ch_avail
                    # result1_queryset = result1.filter(username=username).order_by('ch_avail')
                    # least_remaining_result = result1_queryset.first()
                    # least_remaining_value = least_remaining_result.remaining
                    # result.update(remaining = remaining)
                    # filterered = login_details.objects.filter(username=username)
                    # filterered.update(ch_avail =( remaining))

                subject = "Leave Update"


                send_email(subject, body, to_email,is_html=True)

            elif leave_type == "Casual Leave":

                result = casual_leave.objects.filter(unique_id = unique_id)
                username = data.get('rowData[username]')
                print('user',username)
                # result1 = casual_leave.objects.filter(username = username)
                reducing_remaining = Leave_Availability.objects.get(username = username)


                result.update(status=data.get('action'))

                # result1_queryset = result1.filter(username=username).order_by('remaining')
                # least_remaining_result = result1_queryset.first()
                # least_remaining_value = least_remaining_result.remaining
                # if least_remaining_value == 0:
                #     staff_detail = StaffDetails.objects.get(username_copy = username)
                #     least_remaining_value += float(staff_detail.casual_leave_avail)

                if data.get('action') == "Approved":
                    total_leave = data.get('rowData[total_leave]')
                    remaining = float(reducing_remaining.casual_remaining) - float(total_leave)
                    reducing_remaining.casual_remaining = remaining
                    reducing_remaining.save()

                    # print('leasst',least_remaining_value )

                # remaining = least_remaining_value

                    subject = "Leave Update"

                    send_email(subject, body, to_email,is_html=True)

            elif leave_type == "Onduty":

                result = onDuty.objects.filter(unique_id = unique_id)
                username = data.get('rowData[username]')
                print('user',username)
                result1 = onDuty.objects.filter(username = username)
                reducing_remaining = Leave_Availability.objects.get(username = username)

                result.update(status=data.get('action'))

                if data.get('action') == "Approved":
                    total_leave = data.get('rowData[total_leave]')
                    remaining = float(reducing_remaining.onduty_remaining) - float(total_leave)
                    reducing_remaining.onduty_remaining = remaining
                    reducing_remaining.save()


                    print('leasst',remaining )


                subject = "Leave Update"

                send_email(subject, body, to_email,is_html=True)

            elif leave_type == "Medical Leave":

                result = medicalLeave.objects.filter(unique_id = unique_id)
                username = data.get('rowData[username]')
                reducing_remaining = Leave_Availability.objects.get(username = username)
                print('user',username)
                result1 = medicalLeave.objects.filter(username = username)
                result.update(status=data.get('action'))
                if data.get('action') == "Approved":
                    total_leave = data.get('rowData[total_leave]')
                    remaining = float(reducing_remaining.medical_leave_remaining) - float(total_leave)
                    reducing_remaining.medical_leave_remaining = remaining
                    reducing_remaining.save()

                subject = "Leave Update"

                send_email(subject, body, to_email,is_html=True)

            elif leave_type == "Accumulation":

                result = earnLeave.objects.filter(unique_id = unique_id)
                username = data.get('rowData[username]')
                print('user',username)
                result1 = Leave_Availability.objects.get(username = username)
                result.update(status=data.get('action'))
                if data.get('action') == "Approved":
                    total_leave = data.get('rowData[total_leave]')
                    remaining = float(result1.earn_leave_remaining) - float(total_leave)
                    result1.earn_leave_remaining = remaining
                    result1.save()

                    # print('leasst',least_remaining_value )

                subject = "Leave Update"


                send_email(subject, body, to_email,is_html=True)

                    # data_list_of_dicts =[]

            elif leave_type == "Encashment":

                result = earnLeave.objects.filter(unique_id = unique_id)
                username = data.get('rowData[username]')
                print('user',username)
                result1 = Leave_Availability.objects.get(username = username)
                result.update(status=data.get('action'))
                if data.get('action') == "Approved":
                    total_leave = data.get('rowData[total_leave]')
                    # result1.earn_leave_remaining = float()
                    remaining = float(result1.earn_leave_remaining) - float(total_leave)
                    result1.earn_leave_remaining = remaining
                    result1.save()


                    # result.update(remaining = float(least_remaining_value) - float(total_leave))

                    # print('leasst',least_remaining_value )


                subject = "Leave Update"


                send_email(subject, body, to_email,is_html=True)

            elif leave_type == "Maternity Leave":

                result = maternityLeave.objects.filter(unique_id = unique_id)
                username = data.get('rowData[username]')
                print('user',username)
                result1 = Leave_Availability.objects.get(username = username)
                result.update(status=data.get('action'))
                if data.get('action') == "Approved":
                    total_leave = data.get('rowData[total_leave]')
                    # result1.earn_leave_remaining = float()
                    remaining = float(result1.maternity_leave_remaining) - float(total_leave)
                    result1.maternity_leave_remaining = remaining
                    result1.save()


                    # result.update(remaining = float(least_remaining_value) - float(total_leave))

                    # print('leasst',least_remaining_value )


                subject = "Leave Update"


                send_email(subject, body, to_email,is_html=True)

                    # data_list_of_dicts =[]

            elif leave_type == "CHProof":
                if data.get('action') == "Approved":
                    result = CHProof.objects.filter(unique_id = unique_id)
                    ch_remaining = Leave_Availability.objects.get(username = username)
                    print(ch_remaining.ch_leave_remaining)
                    ch_remaining.ch_leave_remaining = float(ch_remaining.ch_leave_remaining)+1
                    ch_remaining.initial_ch_leave_remaining = float(ch_remaining.initial_ch_leave_remaining)+1
                    print(ch_remaining.ch_leave_remaining)
                    ch_remaining.save()
                    subject = "Leave Update"
                    body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap');

        body {{
            font-family: 'Roboto', sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(to bottom right, #f9f9f9, #e0e0e0);
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        .icon {{
            font-size: 50px;
            color: #4CAF50;
        }}
        h2 {{
            color: #0056b3;
            font-size: 22px;
            margin-bottom: 20px;
        }}
        p {{
            font-size: 18px;
            margin: 10px 0;
            color: #555;
        }}
        .footer {{
            font-size: 14px;
            color: #666;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🎉</div>
        <h2>Congratulations!</h2>
        <p>1 more Compensated Holiday has been added to your account!</p>
        <p>Enjoy your time off and make the most of it.</p>
        <div class="footer">
            <p>With regards,</p>
            <p></p>
        </div>
    </div>
</body>
</html>
"""

                    result.update(status = "Approved")
                    send_email(subject, body, to_email,is_html=True)
                elif data.get('action')=="Declined":
                    result.update(status = "Declined")
                    subject = "Leave Update"

                    print("HEllo")
                    send_email(subject, body, to_email,is_html=True)


            staff_notify = StaffDetails.objects.get(username_copy = data.get('rowData[username]'))
            notification_message = f"Your {data.get('rowData[leave_type]')} request was {data.get('action')} by Vice Principal"
            staff_notify.notification_message = notification_message
            staff_notify.notification_display = True
            staff_notify.save()
        return HttpResponse("Success")

@login_required
def add_announcement(request, username, timestamp):
    principal_username = StaffDetails.objects.get(username_copy = request.user.username).is_principal
    if request.user.is_superuser or principal_username or request.user.is_staff:
        if request.method == "POST":
            announcement = request.POST.get("announcement")
            username = f'{request.user.first_name} {request.user.last_name}'
            timestamp = datetime.now()
            print('ANnouncement')
            announcement_instance = Announcement(
                username = username,
                announcement = announcement,
                timestamp = timestamp
            )
            print(announcement_instance)
            announcement_instance.save()
            if request.user.is_staff:
                return redirect('HODPage')
            return redirect('AdminPage')
        elif request.resolver_match.url_name == 'DeleteAnnouncement':
            announcement = get_object_or_404(Announcement, username=username, timestamp=timestamp)
            print(announcement)
            announcement.delete()
            print("deleted")
            if request.user.is_staff:
                return redirect('HODPage')
            return redirect('AdminPage')

@login_required
def dashboard(request):

    data_list_of_dicts = []
    print(request.user.username)
    result = casual_leave.objects.filter(username=request.user.username)
    for item in result:
                data_dict = {
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "leave_type": item.leave_type,
                    "date_Applied": item.date_Applied.isoformat() if isinstance(item.date_Applied, (date, datetime)) else item.date_Applied,
                    "from_Date": item.from_Date,
                    "to_Date": item.to_Date,
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "reason":item.reason,
                    "status" : item.status
                }
                data_list_of_dicts.append(data_dict)
        # print(data_list)
    result = LOP_leave.objects.filter(username=request.user.username)
    for item in result:
                data_dict = {
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "leave_type": item.leave_type,
                    "date_Applied": item.date_Applied.isoformat() if item.date_Applied else None,
                    "from_Date": item.from_Date,
                    "to_Date": item.to_Date,
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "reason":item.reason,
                    "status" : item.status
                }
                data_list_of_dicts.append(data_dict)
        # print(data_list)
    result = CH_leave.objects.filter(username=request.user.username)
    for item in result:
                data_dict = {
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "leave_type": item.leave_type,
                    "date_Applied": item.date_Applied.isoformat() if item.date_Applied else None,
                    "from_Date": item.from_Date,
                    "to_Date": item.to_Date ,
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "reason":item.reason,
                    "status" : item.status
                }
                data_list_of_dicts.append(data_dict)
    result = medicalLeave.objects.filter(username=request.user.username)
    for item in result:
                data_dict = {
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "leave_type": item.leave_type,
                    "date_Applied": item.date_Applied.isoformat() if item.date_Applied else None,
                    "from_Date": item.from_Date,
                    "to_Date": item.to_Date,
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "reason":item.reason,
                    "status" : item.status
                }
                data_list_of_dicts.append(data_dict)
    result = earnLeave.objects.filter(username=request.user.username)
    for item in result:
                data_dict = {
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "leave_type": item.leave_type,
                    "date_Applied": item.date_Applied.isoformat() if item.date_Applied else None,
                    "from_Date": item.from_Date,
                    "to_Date": item.to_Date,
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "reason":item.reason,
                    "status" : item.status
                }
                data_list_of_dicts.append(data_dict)
    result = vaccationLeave.objects.filter(username=request.user.username)
    for item in result:
                data_dict = {
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "leave_type": item.leave_type,
                    "date_Applied": item.date_Applied.isoformat() if item.date_Applied else None,
                    "from_Date": item.from_Date,
                    "to_Date": item.to_Date,
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "reason":item.reason,
                    "status" : item.status
                }
                data_list_of_dicts.append(data_dict)
    result = specialOnduty.objects.filter(username=request.user.username)
    for item in result:
                data_dict = {
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "leave_type": item.leave_type,
                    "date_Applied": item.date_Applied.isoformat() if item.date_Applied else None,
                    "from_Date": item.from_Date,
                    "to_Date": item.to_Date,
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "reason":item.reason,
                    "status" : item.status
                }
                data_list_of_dicts.append(data_dict)
    result = onDuty.objects.filter(username=request.user.username)
    for item in result:
                data_dict = {
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "leave_type": item.leave_type,
                    "date_Applied": item.date_Applied.isoformat() if item.date_Applied else None,
                    "from_Date": item.from_Date,
                    "to_Date": item.to_Date,
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "reason":item.reason,
                    "status" : item.status
                }
                data_list_of_dicts.append(data_dict)
    result = maternityLeave.objects.filter(username=request.user.username)
    for item in result:
                data_dict = {
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "leave_type": item.leave_type,
                    "date_Applied": item.date_Applied.isoformat() if item.date_Applied else None,
                    "from_Date": item.from_Date,
                    "to_Date": item.to_Date,
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": item.total_leave,
                    "reason":item.reason,
                    "status" : item.status
                }
                data_list_of_dicts.append(data_dict)
    result = Permission.objects.filter(username=request.user.username)
    for item in result:
                data_dict = {
                    "unique_id": item.unique_id,
                    "username": item.username,
                    "leave_type": item.leave_type,
                    "date_Applied": item.date_Applied.isoformat() if item.date_Applied else None,
                    "from_Date": '-',
                    "to_Date": '-',
                    "session": item.session.upper(),
                    "remaining": item.remaining,
                    "total_leave": '-',
                    "reason":item.reason,
                    "status" : item.status
                }
                data_list_of_dicts.append(data_dict)


    staff_notification = StaffDetails.objects.get(username_copy = request.user.username)
    if staff_notification.notification_display:
        answer = True
        notification_message= staff_notification.notification_message
        staff_notification.notification_display = False
        staff_notification.save()
    else:
        answer = False
        notification_message = None

    feedback_staffname = request.user.first_name + " " + request.user.last_name
    pre_filled_url = (
        "https://docs.google.com/forms/d/e/1FAIpQLSe584zLdwG2mseMFQByO54Eu2PakllhW_M7bOZrAxctdEV7tA/viewform"
        f"?usp=pp_url"
        f"&entry.1992171459={quote(feedback_staffname)}"
        f"&entry.1136181252={quote(request.user.username)}"
        f"&entry.1209612741={quote(request.user.email)}"
        f"&entry.949894776={quote(StaffDetails.objects.get(username_copy = request.user.username).department)}"
    )
    context = {
        'username': request.user.first_name,
        'email': request.user.email,
        'notify':answer,
        'notification_message':notification_message,
        'data_dics':json.dumps(data_list_of_dicts),
        'bell_message' : StaffDetails.objects.get(username_copy = request.user.username).notification_message,
        'feedback_url':pre_filled_url
    }



    print(data_list_of_dicts)
    return render(request,'datatables.html',context=context)


def card_dashboard(request):

    total_list=[]
    remaining_list=[]
    percentage_taken = []
    total_days = []

    #0.casual leave

    casual_total = float(Leave_Availability.objects.get(username = request.user.username).initial_casual_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).casual_remaining)
    total_taken = float(casual_total)-float(remaining)
    taken = (total_taken /casual_total)*100
    percentage_taken.append(taken)
    total_list.append(total_taken)
    remaining_list.append(remaining)
    total_days.append(casual_total)


    #1. Vaccation leave

    vaccation_total = float(Leave_Availability.objects.get(username = request.user.username).initial_vaccation_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).vaccation_remaining)
    total_taken = vaccation_total-remaining
    taken = (total_taken/vaccation_total)* 100
    print(taken)
    percentage_taken.append(taken)
    total_list.append(total_taken)
    remaining_list.append(remaining)
    total_days.append(vaccation_total)

    #2. On duty

    onduty_total = float(Leave_Availability.objects.get(username = request.user.username).initial_onduty_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).onduty_remaining)
    total_taken = onduty_total-remaining
    taken = (total_taken/onduty_total)* 100
    print(taken)
    percentage_taken.append(taken)
    total_list.append(total_taken)
    remaining_list.append(remaining)
    total_days.append(onduty_total)


    #3. Medical Leave

    medical_total = float(Leave_Availability.objects.get(username = request.user.username).initial_medical_leave_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).medical_leave_remaining)
    total_taken = medical_total-remaining
    taken = (total_taken/medical_total)* 100
    print(taken)
    percentage_taken.append(taken)
    total_list.append(total_taken)
    remaining_list.append(remaining)
    total_days.append(medical_total)

    #4 ch avail

    ch_total = float(Leave_Availability.objects.get(username = request.user.username).initial_ch_leave_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).ch_leave_remaining)
    total_taken = ch_total-remaining
    if ch_total != 0:
        taken = (total_taken / ch_total) * 100
    else:
        taken = 0

    print(taken)
    percentage_taken.append(taken)
    total_list.append(total_taken)
    remaining_list.append(remaining)
    total_days.append(ch_total)

    #5 earn leave

    earn_total = float(Leave_Availability.objects.get(username = request.user.username).initial_earn_leave_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).earn_leave_remaining)
    total_taken = float(earn_total)-float(remaining)
    taken = (total_taken/earn_total)* 100
    print(taken)
    percentage_taken.append(taken)
    total_list.append(total_taken)
    remaining_list.append(remaining)
    total_days.append(earn_total)

    #6 Maternity Leave

    mal_total = float(Leave_Availability.objects.get(username = request.user.username).initial_maternity_leave_remaining)
    remaining = float(Leave_Availability.objects.get(username = request.user.username).maternity_leave_remaining)
    total_taken = float(mal_total)-float(remaining)
    taken = (total_taken/mal_total)* 100
    print(taken)
    percentage_taken.append(taken)
    total_list.append(total_taken)
    remaining_list.append(remaining)
    total_days.append(mal_total)

    staff_notification = StaffDetails.objects.get(username_copy = request.user.username)
    if staff_notification.notification_display:
        answer = True
        notification_message= staff_notification.notification_message
        staff_notification.notification_display = False
        staff_notification.save()
    else:
        answer = False
        notification_message = None
    feedback_staffname = request.user.first_name + " " + request.user.last_name
    pre_filled_url = (
        "https://docs.google.com/forms/d/e/1FAIpQLSe584zLdwG2mseMFQByO54Eu2PakllhW_M7bOZrAxctdEV7tA/viewform"
        f"?usp=pp_url"
        f"&entry.1992171459={quote(feedback_staffname)}"
        f"&entry.1136181252={quote(request.user.username)}"
        f"&entry.1209612741={quote(request.user.email)}"
        f"&entry.949894776={quote(StaffDetails.objects.get(username_copy = request.user.username).department)}"
    )

    context = {
        'username': request.user.first_name,
        'email': request.user.email,
        'notify':answer,
        'notification_message':notification_message,
        'bell_message' : StaffDetails.objects.get(username_copy = request.user.username).notification_message,
        'total':total_list,
        'remaining':remaining_list,
        'percentage':percentage_taken,
        'total_days' :total_days,
        'feedback_url':pre_filled_url
    }




    return render(request,'card_dashboard.html',context=context)


@login_required
def announcement_view(request):
    new_announcement = Announcement.objects.all().order_by('-timestamp')
    staff_notification = StaffDetails.objects.get(username_copy = request.user.username)
    if staff_notification.notification_display:
        answer = True
        notification_message= staff_notification.notification_message
        staff_notification.notification_display = False
        staff_notification.save()
    else:
        answer = False
        notification_message = None

    feedback_staffname = request.user.first_name + " " + request.user.last_name
    pre_filled_url = (
        "https://docs.google.com/forms/d/e/1FAIpQLSe584zLdwG2mseMFQByO54Eu2PakllhW_M7bOZrAxctdEV7tA/viewform"
        f"?usp=pp_url"
        f"&entry.1992171459={quote(feedback_staffname)}"
        f"&entry.1136181252={quote(request.user.username)}"
        f"&entry.1209612741={quote(request.user.email)}"
        f"&entry.949894776={quote(StaffDetails.objects.get(username_copy = request.user.username).department)}"
    )
    context = {
        'username': request.user.first_name,
        'email': request.user.email,
        'notify':answer,
        'notification_message':notification_message,
        'bell_message' : StaffDetails.objects.get(username_copy = request.user.username).notification_message,
        'announcements':new_announcement,
        'feedback_url':pre_filled_url
    }
    return render(request,'announcement.html',context)

def parse_date(date_value):
    """Convert date string to datetime object if it's a string."""
    if isinstance(date_value, str):
        try:
            return pd.to_datetime(date_value)  # Convert string to datetime
        except ValueError:
            return None  # Return None if conversion fails
    return date_value

def download_individual(request, leave_type):
    if leave_type == 'All':
        leaves = []
        for model in [
            casual_leave, LOP_leave, CH_leave, medicalLeave,
            earnLeave, vaccationLeave, specialOnduty, onDuty,
            Permission, maternityLeave
        ]:
            model_leaves = model.objects.filter(username=request.user.username)
            
            for leave in model_leaves:
                if model.__name__ == 'Permission':
                    leave.from_date = leave.On_date  # Assign On_Date to from_date for consistency
                    leave.to_date = leave.On_date  # Permissions typically apply to a single day
                else:
                    leave.from_date = getattr(leave, 'from_Date', '')  # Safely assign from_Date
                    leave.to_date = getattr(leave, 'to_Date', '')  # Safely assign to_Date
                
                # Append the leave object with its new attributes to the list
                leaves.append(leave)
    else:
        model_dict = {
            'Casual Leave': casual_leave,
            'LOP Leave': LOP_leave,
            'CH Leave': CH_leave,
            'Medical Leave': medicalLeave,
            'Earn Leave': earnLeave,
            'Vacation Leave': vaccationLeave,
            'Onduty': onDuty,
            'Special Onduty': specialOnduty,
            'Maternity Leave': maternityLeave,
            'Permission': Permission
        }
        leaves = model_dict[leave_type].objects.filter(username=request.user.username)

    # Create a DataFrame from the queryset
    data = []
    
    for leave in leaves:
        user = User.objects.get(username=leave.username)
        staff_details = StaffDetails.objects.get(username_copy=leave.username)
        staff_name = f"{user.first_name} {user.last_name}"
        
        # Handle date_applied separately if it's a common field
        date_applied = parse_date(leave.date_Applied)
        
        # Use conditional checks for from_Date and to_Date
        from_date = parse_date(getattr(leave, 'from_Date', None))
        to_date = parse_date(getattr(leave, 'to_Date', None))

        # Format dates to DD/MM/YYYY
        date_applied_str = date_applied.strftime('%d/%m/%Y %H:%M:%S') if date_applied else ''
        from_date_str = from_date.strftime('%d/%m/%Y') if from_date else ''
        to_date_str = to_date.strftime('%d/%m/%Y') if to_date else ''

        # Check if attributes exist before accessing them
        session = getattr(leave, 'session', None)
        remaining = getattr(leave, 'remaining', None)
        total_leave = getattr(leave, 'total_leave', None)
        status = getattr(leave, 'status', None)
        reason = getattr(leave, 'reason', None)

        # Correct leave type display
        leave_type_display = leave.leave_type if leave.leave_type != 'LOP Leave' else 'LLP Leave'
        print(leave_type_display)

        data.append([
            leave.username, staff_name, leave_type_display, date_applied_str, from_date_str,
            to_date_str, session, remaining, total_leave, status, reason
        ])
    
    df = pd.DataFrame(data, columns=['Username', 'Staff Name', 'Leave Type', 'Date Applied', 'From Date', 'To Date', 'Session', 'Remaining', 'Applied Leave', 'Status', 'Reason'])

    # Create an in-memory Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Leaves')
        workbook = writer.book
        worksheet = writer.sheets['Leaves']
        
        # Set column width and format
        format = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
        for col_num, value in enumerate(df.columns.values):
            max_len = max(df[value].astype(str).map(len).max(), len(value)) + 2  # Add a little extra space
            worksheet.set_column(col_num, col_num, max_len, format)

    # Send the response with the Excel file
    output.seek(0)
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    if leave_type == "LOP Leave":
        leave_type ="LLP Leave"
    response['Content-Disposition'] = f'attachment; filename={leave_type}_leaves.xlsx'
    return response


def account_settings(request):


    # Check if the user's password is the default one
    # is_default_password = request.user.check_password('srec@123')
    # print("default",is_default_password)

    staff_notification = StaffDetails.objects.get(username_copy = request.user.username)
    if staff_notification.notification_display:
        answer = True
        notification_message= staff_notification.notification_message
        staff_notification.notification_display = False
        staff_notification.save()
    else:
        answer = False
        notification_message = None
    feedback_staffname = request.user.first_name + " " + request.user.last_name
    pre_filled_url = (
        "https://docs.google.com/forms/d/e/1FAIpQLSe584zLdwG2mseMFQByO54Eu2PakllhW_M7bOZrAxctdEV7tA/viewform"
        f"?usp=pp_url"
        f"&entry.1992171459={quote(feedback_staffname)}"
        f"&entry.1136181252={quote(request.user.username)}"
        f"&entry.1209612741={quote(request.user.email)}"
        f"&entry.949894776={quote(StaffDetails.objects.get(username_copy = request.user.username).department)}"
    )

    context = {
        'username': request.user.first_name,
        'email': request.user.email,
        'notify':answer,
        'notification_message':notification_message,
        'bell_message' : StaffDetails.objects.get(username_copy = request.user.username).notification_message,
        'is_default_password': is_default_password,
        'feedback_url':pre_filled_url

    }
    return render(request,'account_settings.html',context)


@csrf_exempt
# @login_required
def get_otp(request):
    if request.method == "POST":
        print("POST request received")
        print("Request body:", request.POST)
        email = request.POST.get("email")
        print(f"Email: {email}")

        if not email:
            return JsonResponse({'status': 'error', 'message': 'Email is required'}, status=400)

        try:
            user = User.objects.get(email=email)
            print("User found")
        except User.DoesNotExist:
            messages.error(request, 'User does not exist. Please log in or sign up.')
            return JsonResponse({'status': 'error', 'message': 'User does not exist'}, status=400)

        user_name = user.username

        otp = random.randint(100000, 999999)
        subject = "OTP"
        body = f"Your otp to update password is {otp}"
        send_email(subject, body, email)
        otp_save = StaffDetails.objects.get(username_copy=user_name)
        otp_save.otp = otp
        otp_save.save()

        return JsonResponse({'status': 'success', 'message': 'OTP sent successfully'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)



@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        otp_input = request.POST.get("otp")
        email = request.POST.get("email")
        print(request)
        print(email)
        user = User.objects.get(email=email)
        user_name = user.username
        user_details = StaffDetails.objects.get(username_copy=user_name)

        if str(user_details.otp) == otp_input:
            return JsonResponse({'status': 'success', 'message': 'OTP verified successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid OTP'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@csrf_exempt

def update_password(request):
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        email = request.POST.get("email")
        user = User.objects.get(email=email)
        print(user.username)  # Retrieve the User object

        if new_password == confirm_password:
            pass_staff = StaffDetails.objects.get(username_copy = user.username)
            pass_staff.password = new_password
            pass_staff.save()
            # Set the new password for the current user
            user.set_password(new_password)
            user.save()
            logout(request)

            return JsonResponse({'status': 'success', 'message': 'Password updated successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Passwords do not match'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def update_email(request):
    if request.method == "POST":
        new_email = request.POST.get("email")
        user = request.user
        user.email = new_email
        user.save()
        messages.info(request,"Email updated successfully")

        if (user is not None) and ((user.is_active and user.is_staff and not user.is_superuser) or (user.is_superuser and user.is_staff and user.is_active)):

            return redirect("AdminAccount")
        else:
            return redirect("AccountSettings")



# def cancellation_request(request):
#     last_leave = {}

#     # Define a list of all leave model classes
#     leave_models = [casual_leave, LOP_leave, earnLeave, vaccationLeave, onDuty, specialOnduty, medicalLeave, CH_leave]

#     for leave_model in leave_models:
#         try:
#             # Get the latest leave record for the current model
#             last_leave_instance = leave_model.objects.filter(
#                 username=request.user.username,
#                 status__in=['Approved', 'Pending']
#             ).latest('date_Applied')            
#             print(last_leave_instance)
#             # Convert datetime fields to string format
#             last_leave[leave_model.__name__] = {
#                 'leave_type': last_leave_instance.leave_type,
#                 'date_Applied': last_leave_instance.date_Applied.isoformat() if last_leave_instance.date_Applied else '',
#                 'from_Date': last_leave_instance.from_Date,
#                 'to_Date': last_leave_instance.to_Date,
#                 'session': last_leave_instance.session,
#                 'remaining': last_leave_instance.remaining,
#                 'total_leave': last_leave_instance.total_leave,
#                 'reason': last_leave_instance.reason,
#                 'status': last_leave_instance.status,
#                 'unique_id':last_leave_instance.unique_id
#             }
#         except leave_model.DoesNotExist:
#             # If no record exists for the current model, set the value to "Not Applied Yet"
#             last_leave[leave_model.__name__] = {
#                 'leave_type': leave_model.__name__,
#                 'date_Applied': '',
#                 'from_Date': '',
#                 'to_Date': '',
#                 'session': '',
#                 'remaining': '',
#                 'total_leave': '',
#                 'reason': '',
#                 'status': 'Not Applied Yet',
#                 'unique_id':''
#             }

#     # Convert to JSON format for JavaScript
#     # print(last_leave.values())
#     context = {'data_list': list(last_leave.values())}
#     return render(request, 'cancellation_request.html', context)


def cancel_leave(request):
    if request.method == 'POST':
        form = CancelLeaveForm(request.POST, request.FILES)
        
        if form.is_valid():
            leave_id = form.cleaned_data['unique_id']
            reason = form.cleaned_data['reason']
            document = form.cleaned_data['document']
            leave_type = form.cleaned_data['leave_type']

            print(f"Leave ID: {leave_id}")
            print(f"Reason: {reason}")
            print(f"Document: {document}")
            print(f"Leave Type: {leave_type}")

            model_dict = {
                'Casual Leave': casual_leave,
                'LOP Leave': LOP_leave,
                'CH Leave': CH_leave,
                'Medical Leave': medicalLeave,
                'Earn Leave': earnLeave,
                'Vaccation Leave': vaccationLeave,
                'Onduty': onDuty,
                'Special Onduty': specialOnduty,
                'Accumulation':earnLeave,
                'Encashment':earnLeave,
                'Sevatical Special Onduty':specialOnduty,
                'Vaccation Earn Leave': vaccationLeave,
                'Maternity Leave':maternityLeave,
                'Permission':Permission
            }
            
            leave_model = model_dict.get(leave_type)
            
            if leave_model:
                try:
                    leave_request = leave_model.objects.get(unique_id=leave_id)
                    
                    # Process the leave request cancellation
                    leave_request.status = 'Pending'
                    leave_request.save()
                    
                    # Save the cancellation record
                    form.save()
                    
                    # Redirect to a success page or back to the history page
                    messages.success(request, f"🎉 Your Cancellation request for {leave_type} is in review. Stay tuned! 📋")
                    return redirect('cancel_leave')  # Adjust URL name as needed
                except leave_model.DoesNotExist:
                    print(f"Leave request with ID {leave_id} not found.")
            else:
                print(f"Leave type {leave_type} is not valid.")
        else:
            print(form.errors)  # Print form errors to debug

    else:
        # Handle GET request or invalid POST
        pass

    # Define a list of all leave model classes
    leave_models = [
        casual_leave, 
        LOP_leave, 
        earnLeave, 
        vaccationLeave, 
        onDuty, 
        specialOnduty, 
        medicalLeave, 
        CH_leave,
        maternityLeave,
        Permission
    ]
    
    last_leave = {}

    for leave_model in leave_models:
        try:
            # If model is earnLeave, vaccationLeave, or specialOnduty, handle specific leave types
            if leave_model in [earnLeave, vaccationLeave, specialOnduty]:
                leave_types = leave_model.objects.filter(username=request.user.username).values_list('leave_type', flat=True).distinct()

                for leave_type in leave_types:
                    last_leave_instance = leave_model.objects.filter(
                        username=request.user.username,
                        leave_type=leave_type,
                        status__in=['Approved', 'Pending']
                    ).latest('date_Applied')
    
                    last_leave[f"{leave_model.__name__}_{leave_type}"] = {
                        'leave_type': last_leave_instance.leave_type,
                        'date_Applied': last_leave_instance.date_Applied.isoformat() if last_leave_instance.date_Applied else '',
                        'from_Date': last_leave_instance.from_Date,
                        'to_Date': last_leave_instance.to_Date,
                        'session': last_leave_instance.session,
                        'remaining': last_leave_instance.remaining,
                        'total_leave': last_leave_instance.total_leave,
                        'reason': last_leave_instance.reason,
                        'status': last_leave_instance.status,
                        'unique_id': last_leave_instance.unique_id
                    }
            else:
                # Handle other leave models normally
                last_leave_instance = leave_model.objects.filter(
                    username=request.user.username,
                    status__in=['Approved', 'Pending']
                ).latest('date_Applied')
                if leave_model == Permission:
                    last_leave[leave_model.__name__] = {
                        'leave_type': last_leave_instance.leave_type,
                        'date_Applied': last_leave_instance.date_Applied.isoformat() if last_leave_instance.date_Applied else '',
                        'from_Date': last_leave_instance.On_date,
                        # 'to_Date': '-',
                        'session': last_leave_instance.session.upper(),
                        'remaining': last_leave_instance.remaining,
                        # 'total_leave': '-',
                        'reason': last_leave_instance.reason,
                        'status': last_leave_instance.status,
                        'unique_id': last_leave_instance.unique_id
                    }
                else:
                    last_leave[leave_model.__name__] = {
                        'leave_type': last_leave_instance.leave_type,
                        'date_Applied': last_leave_instance.date_Applied.isoformat() if last_leave_instance.date_Applied else '',
                        'from_Date': last_leave_instance.from_Date,
                        'to_Date': last_leave_instance.to_Date,
                        'session': last_leave_instance.session,
                        'remaining': last_leave_instance.remaining,
                        'total_leave': last_leave_instance.total_leave,
                        'reason': last_leave_instance.reason,
                        'status': last_leave_instance.status,
                        'unique_id': last_leave_instance.unique_id
                    }
        except leave_model.DoesNotExist:
            last_leave[leave_model.__name__] = {
                'leave_type': leave_model.__name__,
                'date_Applied': '',
                'from_Date': '',
                'to_Date': '',
                'session': '',
                'remaining': '',
                'total_leave': '',
                'reason': '',
                'status': 'Not Applied Yet',
                'unique_id': ''
            }
    form = CancelLeaveForm()
    user_common_context = get_user_common_context(request)
    specific_context = {'data_list': list(last_leave.values()), 'form': form}
    context = merge_contexts(user_common_context,specific_context)

    return render(request, 'cancellation_request.html', context)

def cancel_requests_handling(request):
    if request.method == "POST":
        data = request.POST
        print("THisis the data ",data)
        leave_type = data.get('rowData[leave_type]')
        unique_id = int(data.get('rowData[unique_id]'))
        username = data.get('rowData[username]')

        if leave_type == "Casual Leave":

            result = casual_leave.objects.filter(unique_id = unique_id)
            username = data.get('rowData[username]')
            print('user',username)
            # result1 = casual_leave.objects.filter(username = username)
            reducing_remaining = Leave_Availability.objects.get(username = username)
            if data.get('action') == "Approved":
                total_leave = data.get('rowData[total_leave]')
                remaining = float(reducing_remaining.casual_remaining) + float(total_leave)
                reducing_remaining.casual_remaining = remaining
                reducing_remaining.save()
                result.update(status = "Cancelled")
            elif data.get('action') == "Declined":
                result.update(status="Approved")
            
        elif leave_type == 'LOP Leave':
            result = LOP_leave.objects.filter(unique_id = unique_id)
            if data.get('action') == "Approved":
                result.update(status = "Cancelled")

                username = data.get('rowData[username]')
            elif data.get('action') == "Declined":
                result.update(status="Approved")
        
        elif leave_type == 'Special Onduty':
            result = specialOnduty.objects.filter(unique_id = unique_id)
            if data.get('action') == "Approved":
                result.update(status = "Cancelled")

            elif data.get('action') == "Declined":
                result.update(status="Approved")


        elif leave_type == 'Sevatical Special Onduty':
            result = specialOnduty.objects.filter(unique_id = unique_id)
            if data.get('action') == "Approved":
                result.update(status = "Cancelled")

            elif data.get('action') == "Declined":
                result.update(status="Approved")

        elif leave_type == 'Vaccation Leave':
            result = vaccationLeave.objects.filter(unique_id = unique_id)
            
            reducing_remaining = Leave_Availability.objects.get(username = data.get('rowData[username]'))
            if data.get('action') == "Approved":
                total_leave = data.get('rowData[total_leave]')
                remaining = float(reducing_remaining.vaccation_remaining) + float(total_leave)
                result.update(status = "Cancelled")
                reducing_remaining.vaccation_remaining = remaining
                reducing_remaining.save()

            elif data.get('action') == "Declined":
                result.update(status="Approved")

        elif leave_type == 'Vaccation Earn Leave':
            result = vaccationLeave.objects.filter(unique_id = unique_id)
            if data.get('action') == "Approved":
                result.update(status = "Cancelled")

            elif data.get('action') == "Declined":
                result.update(status="Approved")


        elif leave_type == "CH Leave":
            result = CH_leave.objects.filter(unique_id = unique_id)

            

            requesting_remaining = Leave_Availability.objects.get(username = data.get('rowData[username]'))

            if data.get('action') == "Approved":
                total_leave = data.get('rowData[total_leave]')
                result.update(status = "Cancelled")
                remaining = float(requesting_remaining.ch_leave_remaining) + float(total_leave)
                requesting_remaining.ch_leave_remaining = remaining
                requesting_remaining.save()
            #     remaining = result1.ch_avail
                # result1_queryset = result1.filter(username=username).order_by('ch_avail')
                # least_remaining_result = result1_queryset.first()
                # least_remaining_value = least_remaining_result.remaining
                # result.update(remaining = remaining)
                # filterered = login_details.objects.filter(username=username)
   
            elif data.get('action') == "Declined":
                result.update(status="Approved")

           
        elif leave_type == "Onduty":

            result = onDuty.objects.filter(unique_id = unique_id)
            username = data.get('rowData[username]')
            print('user',username)
            result1 = onDuty.objects.filter(username = username)
            reducing_remaining = Leave_Availability.objects.get(username = username)

            result.update(status=data.get('action'))

            if data.get('action') == "Approved":
                total_leave = data.get('rowData[total_leave]')
                remaining = float(reducing_remaining.onduty_remaining) + float(total_leave)
                reducing_remaining.onduty_remaining = remaining
                result.update(status = "Cancelled")
                reducing_remaining.save()

            elif data.get('action') == "Declined":
                result.update(status="Approved")

        elif leave_type == "Medical Leave":

            result = medicalLeave.objects.filter(unique_id = unique_id)
            username = data.get('rowData[username]')
            reducing_remaining = Leave_Availability.objects.get(username = username)
            print('user',username)
            result1 = medicalLeave.objects.filter(username = username)
            if data.get('action') == "Approved":
                total_leave = data.get('rowData[total_leave]')
                remaining = float(reducing_remaining.medical_leave_remaining) + float(total_leave)
                reducing_remaining.medical_leave_remaining = remaining
                result.update(status = "Cancelled")
                reducing_remaining.save()

            elif data.get('action') == "Declined":
                result.update(status="Approved")



        elif leave_type == "Accumulation":

            result = earnLeave.objects.filter(unique_id = unique_id)
            username = data.get('rowData[username]')
            print('user',username)
            result1 = Leave_Availability.objects.get(username = username)
            if data.get('action') == "Approved":
                total_leave = data.get('rowData[total_leave]')
                remaining = float(result1.earn_leave_remaining) + float(total_leave)
                result1.earn_leave_remaining = remaining
                result.update(status = "Cancelled")
                result1.save()

            elif data.get('action') == "Declined":
                result.update(status="Approved")


        elif leave_type == "Encashment":

            result = earnLeave.objects.filter(unique_id = unique_id)
            username = data.get('rowData[username]')
            print('user',username)
            result1 = Leave_Availability.objects.get(username = username)
            if data.get('action') == "Approved":
                total_leave = data.get('rowData[total_leave]')
                # result1.earn_leave_remaining = float()
                remaining = float(result1.earn_leave_remaining) + float(total_leave)
                result1.earn_leave_remaining = remaining
                result.update(status = "Cancelled")
                result1.save()

            elif data.get('action') == "Declined":
                result.update(status="Approved")

        elif leave_type == "Maternity Leave":

            result = maternityLeave.objects.filter(unique_id = unique_id)
            username = data.get('rowData[username]')
            print('user',username)
            result1 = maternityLeave.objects.filter(username = username)
            reducing_remaining = Leave_Availability.objects.get(username = username)
            if data.get('action') == "Approved":
                total_leave = data.get('rowData[total_leave]')
                remaining = float(reducing_remaining.maternity_leave_remaining) + float(total_leave)
                reducing_remaining.maternity_leave_remaining = remaining
                result.update(status = "Cancelled")
                reducing_remaining.save()

            elif data.get('action') == "Declined":
                result.update(status="Approved")


        elif leave_type == "Permission":

            result = Permission.objects.filter(unique_id = unique_id)
            username = data.get('rowData[username]')
            print('user',username)
            result1 = Permission.objects.filter(username = username)
            reducing_remaining = Leave_Availability.objects.get(username = username)
            if data.get('action') == "Approved":
                total_leave = 1
                remaining = float(reducing_remaining.permission_remaining) + float(total_leave)
                reducing_remaining.permission_remaining = remaining
                result.update(status = "Cancelled")
                reducing_remaining.save()

            elif data.get('action') == "Declined":
                result.update(status="Approved")
    return HttpResponse("Success")


def permission_view_function(request):
    if request.method == "POST":
        reason = request.POST.get("reason")
        fromDate = request.POST.get("fromDate")
        session = request.POST.get("session")
        if 'file' in request.FILES:
            document = request.FILES['file']
            print(document)
        else:
            document = None
            print(document)
        

        now = timezone.now()
        current_year = now.year  # E.g., 2024
        current_month = now.month  # E.g., 8 for August

        # Filter the Permission objects
        approved_permissions_count = Permission.objects.filter(
            status='Approved',
            On_date__startswith=f"{current_year}-{str(current_month).zfill(2)}"
        ).count()
        print(f"Approved permissions for this month: {approved_permissions_count}")
        per_rem = Leave_Availability.objects.get(username = request.user.username)
        print(per_rem.permission_remaining)
        if float(approved_permissions_count) == 0 and float(per_rem.permission_remaining) == 0:
            print('rem',per_rem)
            initial_per_rem = per_rem.initial_permission_remaining
            per_rem.permission_remaining = initial_per_rem
            per_rem.save()
            print('Saved')

        remaining = Leave_Availability.objects.get(username=request.user.username).permission_remaining

        if float(remaining)<=0 :
            context = {
                "remaining" : remaining,
                "flag" : True,
                }
            alert_data = {
                'title': '🚨 Exceeds Limit!',
                'message': " 🚫 Oops! You've Hit Your Limit! 🚫 You've exceeded your permission limit. Try"
            }
        
        # Serialize the dictionary to a JSON string
            alert_data_json = json.dumps(alert_data)

            # Pass the JSON string as a message
            messages.add_message(request, messages.WARNING, alert_data_json)
            return redirect("Permission")

        print(reason,session)
        permission_instance = Permission(
            username = request.user.username,
            date_Applied = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            session = session.upper(),
            remaining = remaining,
            On_date = fromDate,
            reason = request.POST.get("reason"),
            document = document
        )
        permission_instance.save()
        messages.success(request, f"🎉 Your Permission request is in review. Stay tuned! 📋")
        return redirect("Home")
    else:
        context = get_user_common_context(request)
    return render(request,'permission.html',context)


def ch_proof_function(request):
    if request.method =="POST":
        fromDate = request.POST.get("fromDate")
        inTime = request.POST.get("inTime")
        outTime = request.POST.get("outTime")
        # print(fromDate,inTime,outTime)
        if 'file' in request.FILES:
            document = request.FILES['file']
            print(document)
        else:
            document = None
            print(document)
        ch_proof_instance = CHProof(
            username = request.user.username,
            date_Applied = timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            On_date = fromDate,
            in_Time = inTime,
            Out_Time = outTime,
            document = document
        )
        ch_proof_instance.save()
        messages.success(request, f"🎉 Your CH Proof is in review. Stay tuned! 📋")
        return redirect("Home")
    else:
        context = get_user_common_context(request)
        return render(request,'chproof.html',context)



