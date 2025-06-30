from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load data from each continent
continent_files = {
    "Africa": "data/Africa_data.csv",
    "Asia": "data/Asia_data.csv",
    "Europe": "data/Europe_data.csv",
    "North America": "data/North America_data.csv",
    "South America": "data/South America_data.csv",
    "Oceania": "data/Oceania_data.csv"
}

# Route: Landing Page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        disease = request.form['disease']  # Get disease name from the form
        session['disease'] = disease  # Store disease in session
        return redirect(url_for('discussion'))  # Redirect to the discussion page
    return render_template('index8.html')


# Route: Bot Discussion Page
@app.route('/discussion')
def discussion():
    disease = session.get('disease')  # Get the disease name from session

    if not disease:
        return redirect(url_for('index'))  # Redirect back to the index if disease is not found in session

    results = []
    treatment_counter = {}

    # Iterate through continents and calculate treatment success
    for continent, file_path in continent_files.items():
        df = pd.read_csv(file_path)
        match = df[df['Disease Name'].str.lower() == disease.lower()]
        if not match.empty:
            row = match.iloc[0]
            treatment = row['Treatment']
            success = row['Success Rate (%)']
            complications = row['Complications']
            advantage = row['Treatment Advantage']

            results.append({
                'continent': continent,
                'treatment': treatment,
                'success': success,
                'complications': complications,
                'advantage': advantage
            })

            treatment_counter[treatment] = treatment_counter.get(treatment, 0) + 1

    if not treatment_counter:
        return render_template('dicuss8.html', results=[], chart_img="", disease_name=disease, final_treatment=None)

    # Find the majority treatment
    max_votes = max(treatment_counter.values())
    tied_treatments = [t for t, count in treatment_counter.items() if count == max_votes]

    if len(tied_treatments) == 1:
        majority_treatment = tied_treatments[0]
    else:
        treatment_success_averages = {}
        for treatment in tied_treatments:
            rates = [float(r['success']) for r in results if r['treatment'] == treatment]
            treatment_success_averages[treatment] = sum(rates) / len(rates)
        majority_treatment = max(treatment_success_averages, key=treatment_success_averages.get)

    for result in results:
        result['is_majority'] = (result['treatment'] == majority_treatment)

    session['final_treatment'] = majority_treatment

    # Create chart
    def create_chart(results):
        continents = []
        success_rates = []

        for result in results:
            continents.append(result['continent'])
            success_rates.append(float(result['success']))

        plt.style.use('dark_background')
        plt.figure(figsize=(10, 6))
        bars = plt.bar(continents, success_rates, color='skyblue')

        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, height + 1, f'{height:.1f}%', ha='center', color='white', fontsize=12)

        plt.xlabel('Continent', fontsize=14, color='white')
        plt.ylabel('Success Rate (%)', fontsize=14, color='white')
        plt.title('Treatment Success Rate by Continent', fontsize=16, color='white')
        plt.ylim(0, 100)
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        img = BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        plt.close()
        img.seek(0)
        chart_data = base64.b64encode(img.getvalue()).decode()
        chart_uri = 'data:image/png;base64,' + chart_data
        return chart_uri

    chart_img = create_chart(results)

    return render_template('dicuss8.html', results=results, chart_img=chart_img, disease_name=disease, final_treatment=majority_treatment)


# Route: Final Treatment Recommendation
data = pd.read_csv('data/healthcare_treatment.csv', encoding='latin1')

@app.route('/recommendation')
def recommendation():
    disease = session.get('disease')  # Get the disease name from session
    if not disease:
        return redirect(url_for('index'))  # If disease is not found, redirect to index

    result = data[data['Disease Name'].str.lower() == disease.lower()]
    if result.empty:
        return f"No data found for {disease}"

    record = result.iloc[0].to_dict()
    return render_template('recommendation.html', record=record)


if __name__ == '__main__':
    app.run(debug=True)
