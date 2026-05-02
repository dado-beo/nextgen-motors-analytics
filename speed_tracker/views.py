import pandas as pd
import json
import io
from django.shortcuts import render, redirect
from .calculators import kmh_to_ms, calculate_rectangle, calculate_trapezoidal, calculate_simpson

def upload_csv(request):
    # Manage session clear if requested
    if request.method == "GET" and request.GET.get('clear') == 'true':
        request.session.flush()  # This will clear the session data, including the 'history' key
        return redirect(request.path) # Redirect to the same page to avoid resubmission issues and to show the cleared state

    # Initialize session history if it doesn't exist. This ensures we have a place to store the history of runs without running into KeyErrors later on when we try to append to it.
    if 'history' not in request.session:
        request.session['history'] = []
        request.session.modified = True # Mark the session as modified to ensure it gets saved even if we just initialized the history list

    results = None
    chart_data_current = None
    
    results = None
    chart_data_current = None

    if request.method == "POST":
        df = None
        
        # Read data from the uploaded CSV file or from the manual input. We check for the presence of the file first, and if it's not there, we look for manual data. 
        # This allows users to choose their preferred method of input without confusion.
        if request.FILES.get('csv_file'):
            file = request.FILES['csv_file']
            df = pd.read_csv(file)
            
        elif 'manual_data' in request.POST and request.POST['manual_data'].strip():
            raw_data = request.POST['manual_data'].strip()
            if not raw_data.startswith('time'):
                raw_data = "time,speed\n" + raw_data
            df = pd.read_csv(io.StringIO(raw_data))

        # Elaboration of the data only if we have a valid dataframe. 
        # This prevents errors in case the user submits an empty form or a file that doesn't contain the expected columns. 
        # We also check for the presence of the 'speed' and 'time' columns to ensure we have the necessary data to perform our calculations.
        if df is not None and 'speed' in df.columns and 'time' in df.columns:
            
            # Filter data to include only speeds up to 100 km/h. 
            # This is a sanity check to prevent unrealistic data from skewing our results.
            test_data = df[df['speed'] <= 100]
            
            time_list = test_data['time'].tolist()
            speed_kmh = test_data['speed'].tolist()
            
            # Empty data check: 
            # We only proceed with the calculations and saving the run if we actually have valid data in our lists.
            if len(time_list) > 0 and len(speed_kmh) > 0:
                speed_ms = kmh_to_ms(speed_kmh)
                h = 0.5

                results = {
                    'rectangle': round(calculate_rectangle(speed_ms, h), 2),
                    'trapezoidal': round(calculate_trapezoidal(speed_ms, h), 2),
                    'simpson': round(calculate_simpson(speed_ms, h), 2),
                }
                
                # Prepare the data for the current run to be displayed in the chart. 
                # This includes the time labels and the corresponding speed values in km/h.
                chart_data_current = {
                    'labels': time_list,
                    'values': speed_kmh
                }
                
                # Save the current run's data to the session history. 
                # This allows us to keep track of all the runs the user has performed during their session and display them in the history section of the frontend.
                request.session['history'].append(chart_data_current)
                request.session.modified = True 

    # Render the results and the chart data to the template. 
    # We pass both the current run's data and the entire history of runs to the frontend, allowing for a comprehensive display of the user's activity.
    return render(request, 'speed_tracker/index.html', {
        'results': results,
        'chart_data_current': json.dumps(chart_data_current) if chart_data_current else None,
        'chart_data_history': json.dumps(request.session.get('history', []))
    })