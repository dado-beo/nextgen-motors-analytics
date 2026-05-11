import pandas as pd
import json
import io
from django.shortcuts import render, redirect
from .calculators import kmh_to_ms, calculate_rectangle, calculate_trapezoidal, calculate_simpson

def upload_csv(request):
    """
    Processes CSV/Manual input with strict validation.
    Returns error_message if data is invalid, otherwise returns calculation results.
    """
    
    # Session reset logic
    if request.method == "GET" and request.GET.get('clear') == 'true':
        request.session.flush()
        return redirect(request.path)

    if 'history' not in request.session:
        request.session['history'] = []
        request.session.modified = True

    results = None
    chart_data_current = None
    error_message = None 

    if request.method == "POST":
        df = None
        
        try:
            # --- DATA ACQUISITION ---
            if request.FILES.get('csv_file'):
                file = request.FILES['csv_file']
                df = pd.read_csv(file)
                
            elif 'manual_data' in request.POST and request.POST['manual_data'].strip():
                raw_data = request.POST['manual_data'].strip()
                if not raw_data.lower().startswith('time'):
                    raw_data = "time,speed\n" + raw_data
                df = pd.read_csv(io.StringIO(raw_data))

            # --- DATA VALIDATION ---
            if df is not None:
                # 1. Check for required columns
                if 'speed' not in df.columns or 'time' not in df.columns:
                    raise ValueError("Missing 'time' or 'speed' columns.")

                # 2. Force numeric conversion and drop invalid rows
                df['speed'] = pd.to_numeric(df['speed'], errors='coerce')
                df['time'] = pd.to_numeric(df['time'], errors='coerce')
                df = df.dropna(subset=['speed', 'time'])

                # 3. Check for minimum points (at least 2)
                if len(df) < 2:
                    raise ValueError("Insufficient data. Please provide at least 2 valid numeric points.")

                # 4. Logical check for negative speed or non-increasing time
                if (df['speed'] < 0).any():
                    raise ValueError("Speed values cannot be negative.")
                if not df['time'].is_monotonic_increasing:
                    raise ValueError("Time values must be strictly increasing.")

                # --- PROCESSING VALID DATA ---
                test_data = df[df['speed'] <= 200]
                time_list = test_data['time'].tolist()
                speed_kmh = test_data['speed'].tolist()
                
                speed_ms = kmh_to_ms(speed_kmh)
                h = 0.5 # Default interval

                results = {
                    'rectangle': round(calculate_rectangle(speed_ms, h), 2),
                    'trapezoidal': round(calculate_trapezoidal(speed_ms, h), 2),
                    'simpson': round(calculate_simpson(speed_ms, h), 2),
                }
                
                chart_data_current = {
                    'labels': time_list,
                    'values': speed_kmh
                }
                
                # Save to history only if processing succeeded
                request.session['history'].append(chart_data_current)
                request.session.modified = True 
            else:
                raise ValueError("No data provided.")

        except Exception as e:
            # Capture the specific error string for the UI
            error_message = str(e)
            # Ensure results is None so the results section disappears
            results = None

    return render(request, 'speed_tracker/index.html', {
        'results': results,
        'error_message': error_message,
        'chart_data_current': json.dumps(chart_data_current) if chart_data_current else None,
        'chart_data_history': json.dumps(request.session.get('history', []))
    })