import pandas as pd
import json
import io
from django.shortcuts import render, redirect
from django.contrib import messages
from .calculators import kmh_to_ms, calculate_rectangle, calculate_trapezoidal, calculate_simpson

def upload_csv(request):
    """
    Handles CSV upload and manual data entry with robust error validation.
    All logic, comments, and user messages are in English.
    """
    
    # Manage session clear if requested via GET parameter
    if request.method == "GET" and request.GET.get('clear') == 'true':
        request.session.flush()
        return redirect(request.path)

    # Initialize session history if it doesn't exist
    if 'history' not in request.session:
        request.session['history'] = []
        request.session.modified = True

    results = None
    chart_data_current = None
    error_message = None  # Variable to store validation errors

    if request.method == "POST":
        df = None
        
        try:
            # --- PHASE 1: DATA ACQUISITION ---
            if request.FILES.get('csv_file'):
                file = request.FILES['csv_file']
                # Read CSV and catch formatting errors
                df = pd.read_csv(file)
                
            elif 'manual_data' in request.POST and request.POST['manual_data'].strip():
                raw_data = request.POST['manual_data'].strip()
                # Ensure the header is present for the CSV parser
                if not raw_data.lower().startswith('time'):
                    raw_data = "time,speed\n" + raw_data
                df = pd.read_csv(io.StringIO(raw_data))

            # --- PHASE 2: DATA VALIDATION ---
            if df is not None:
                # Check if required columns exist
                if 'speed' not in df.columns or 'time' not in df.columns:
                    raise ValueError("Missing 'time' or 'speed' columns in input.")

                # Convert columns to numeric, forcing errors to NaN (Not a Number)
                df['speed'] = pd.to_numeric(df['speed'], errors='coerce')
                df['time'] = pd.to_numeric(df['time'], errors='coerce')

                # Remove any rows with NaN (invalid numbers or text) or empty values
                df = df.dropna(subset=['speed', 'time'])

                # Check if we have enough points for calculation (minimum 2 points)
                if len(df) < 2:
                    raise ValueError("Insufficient data. Please provide at least 2 valid numeric points.")

                # Logic check: speed shouldn't be negative and time should be increasing
                if (df['speed'] < 0).any():
                    raise ValueError("Speed values cannot be negative.")
                
                if not df['time'].is_monotonic_increasing:
                    raise ValueError("Time values must be strictly increasing.")

                # Filter data to a realistic range (e.g., max 200 km/h for safety)
                test_data = df[df['speed'] <= 200]
                
                time_list = test_data['time'].tolist()
                speed_kmh = test_data['speed'].tolist()
                
                # --- PHASE 3: CALCULATIONS ---
                speed_ms = kmh_to_ms(speed_kmh)
                h = 0.5 # Default time step for the demo

                results = {
                    'rectangle': round(calculate_rectangle(speed_ms, h), 2),
                    'trapezoidal': round(calculate_trapezoidal(speed_ms, h), 2),
                    'simpson': round(calculate_simpson(speed_ms, h), 2),
                }
                
                chart_data_current = {
                    'labels': time_list,
                    'values': speed_kmh
                }
                
                # Update history session
                request.session['history'].append(chart_data_current)
                request.session.modified = True 

            else:
                raise ValueError("No data provided.")

        except Exception as e:
            # Catch all errors (formatting, value errors, etc.) and pass to template
            error_message = str(e)

    # Render context including potential error messages
    return render(request, 'speed_tracker/index.html', {
        'results': results,
        'error_message': error_message,
        'chart_data_current': json.dumps(chart_data_current) if chart_data_current else None,
        'chart_data_history': json.dumps(request.session.get('history', []))
    })